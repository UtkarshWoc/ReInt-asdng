"""Data ingestion, validation, and snapshot creation service."""

import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.clients.elexon import ElexonClient
from app.core.time_utils import format_iso_utc, parse_iso_utc

logger = logging.getLogger(__name__)


class IngestionService:
    """Service to coordinate data fetching, alignment, and static snapshot generation."""

    def __init__(self, client: Optional[ElexonClient] = None):
        self.client = client or ElexonClient()

    @staticmethod
    def clean_fuelhh_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and normalize a raw FUELHH record."""
        try:
            start_time_raw = record.get("startTime")
            gen_raw = record.get("generation")
            if not start_time_raw or gen_raw is None:
                return None
            
            gen_val = float(gen_raw)
            if gen_val < 0:
                logger.warning(f"Negative generation encountered in FUELHH: {record}")
                return None

            dt_utc = parse_iso_utc(start_time_raw)
            return {
                "startTime": format_iso_utc(dt_utc),
                "settlementDate": record.get("settlementDate"),
                "settlementPeriod": int(record.get("settlementPeriod", 0)),
                "generation": gen_val,
            }
        except Exception as e:
            logger.warning(f"Error parsing FUELHH record {record}: {e}")
            return None

    @staticmethod
    def clean_windfor_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and normalize a raw WINDFOR forecast record."""
        try:
            pub_raw = record.get("publishTime")
            start_raw = record.get("startTime")
            gen_raw = record.get("generation")
            if not pub_raw or not start_raw or gen_raw is None:
                return None

            gen_val = float(gen_raw)
            if gen_val < 0:
                logger.warning(f"Negative generation encountered in WINDFOR: {record}")
                return None

            pub_utc = parse_iso_utc(pub_raw)
            start_utc = parse_iso_utc(start_raw)
            return {
                "publishTime": format_iso_utc(pub_utc),
                "startTime": format_iso_utc(start_utc),
                "generation": gen_val,
            }
        except Exception as e:
            logger.warning(f"Error parsing WINDFOR record {record}: {e}")
            return None

    @classmethod
    def aggregate_hourly_actuals(
        cls, cleaned_half_hourly: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate half-hourly actuals into hourly average generation.
        
        Matches :00 and :30 intervals into their parent hourly window.
        """
        hours_map: Dict[str, List[float]] = defaultdict(list)
        period_details: Dict[str, Dict[str, float]] = defaultdict(dict)

        for rec in cleaned_half_hourly:
            dt = parse_iso_utc(rec["startTime"])
            hour_start = dt.replace(minute=0, second=0, microsecond=0)
            hour_key = format_iso_utc(hour_start)
            hours_map[hour_key].append(rec["generation"])
            if dt.minute == 0:
                period_details[hour_key]["period_00"] = rec["generation"]
            elif dt.minute == 30:
                period_details[hour_key]["period_30"] = rec["generation"]

        hourly_results: List[Dict[str, Any]] = []
        for hour_key in sorted(hours_map.keys()):
            vals = hours_map[hour_key]
            avg_gen = sum(vals) / len(vals) if vals else 0.0
            hourly_results.append({
                "startTime": hour_key,
                "generation": round(avg_gen, 2),
                "half_hour_samples": len(vals),
                "period_00": period_details[hour_key].get("period_00"),
                "period_30": period_details[hour_key].get("period_30"),
            })

        return hourly_results

    async def build_january_2026_snapshot(
        self,
        output_path: Path,
        actuals_start: str = "2026-01-01",
        actuals_end: str = "2026-02-01",
        forecasts_publish_from: Optional[datetime] = None,
        forecasts_publish_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Fetch, clean, and write January 2026 dataset snapshot."""
        if forecasts_publish_from is None:
            forecasts_publish_from = datetime(2025, 12, 30, 0, 0, 0, tzinfo=UTC)
        if forecasts_publish_to is None:
            forecasts_publish_to = datetime(2026, 2, 1, 23, 59, 59, tzinfo=UTC)

        # 1. Fetch raw actuals and forecasts
        raw_fuelhh = await self.client.fetch_fuelhh_actuals(actuals_start, actuals_end, fuel_type="WIND")
        raw_windfor = await self.client.fetch_windfor_forecasts_chunked(
            forecasts_publish_from, forecasts_publish_to, chunk_days=7
        )

        # 2. Clean and validate
        cleaned_fuelhh = [r for r in (self.clean_fuelhh_record(x) for x in raw_fuelhh) if r is not None]
        cleaned_fuelhh.sort(key=lambda x: x["startTime"])

        cleaned_windfor = [r for r in (self.clean_windfor_record(x) for x in raw_windfor) if r is not None]
        cleaned_windfor.sort(key=lambda x: (x["startTime"], x["publishTime"]))

        # 3. Aggregate hourly actuals
        hourly_actuals = self.aggregate_hourly_actuals(cleaned_fuelhh)

        # 4. Assemble snapshot payload
        distinct_delivery_dates = sorted(list({x["startTime"][:10] for x in hourly_actuals}))
        snapshot_data = {
            "metadata": {
                "generated_at": format_iso_utc(datetime.now(UTC)),
                "actuals_start": actuals_start,
                "actuals_end": actuals_end,
                "forecasts_publish_from": format_iso_utc(forecasts_publish_from),
                "forecasts_publish_to": format_iso_utc(forecasts_publish_to),
                "total_forecasts": len(cleaned_windfor),
                "total_actuals_hourly": len(hourly_actuals),
                "total_actuals_half_hourly": len(cleaned_fuelhh),
                "available_delivery_dates": distinct_delivery_dates,
                "default_cutoff": "09:00",
            },
            "actuals_hourly": hourly_actuals,
            "actuals_half_hourly": cleaned_fuelhh,
            "forecasts": cleaned_windfor,
        }

        # 5. Persist to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, separators=(",", ":"))

        logger.info(
            f"Successfully built snapshot at {output_path}: "
            f"{len(cleaned_windfor)} forecasts, {len(hourly_actuals)} hourly actuals."
        )
        return snapshot_data
