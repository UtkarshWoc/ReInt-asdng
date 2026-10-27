"""CLI script to refresh and persist the Elexon January 2026 data snapshot."""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from app.clients.elexon import ElexonClient
from app.core.config import settings
from app.services.ingestion import IngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("refresh_data")


async def main():
    parser = argparse.ArgumentParser(description="Refresh Elexon wind data snapshot.")
    parser.add_argument("--start", default="2026-01-01", help="Actuals start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-02-01", help="Actuals end date (YYYY-MM-DD)")
    parser.add_argument(
        "--forecast-from",
        default="2025-12-30T00:00:00Z",
        help="Earliest forecast publishTime (ISO UTC)",
    )
    parser.add_argument(
        "--forecast-to",
        default="2026-02-01T23:59:59Z",
        help="Latest forecast publishTime (ISO UTC)",
    )
    parser.add_argument(
        "--out",
        default=str(settings.DATA_SNAPSHOT_PATH),
        help="Output path for snapshot JSON",
    )
    args = parser.parse_args()

    output_path = Path(args.out)
    pub_from = datetime.fromisoformat(args.forecast_from.replace("Z", "+00:00"))
    pub_to = datetime.fromisoformat(args.forecast_to.replace("Z", "+00:00"))

    logger.info(f"Starting data ingestion for delivery {args.start} to {args.end}...")
    client = ElexonClient()
    ingestion = IngestionService(client=client)

    try:
        snapshot = await ingestion.build_january_2026_snapshot(
            output_path=output_path,
            actuals_start=args.start,
            actuals_end=args.end,
            forecasts_publish_from=pub_from,
            forecasts_publish_to=pub_to,
        )
        meta = snapshot["metadata"]
        logger.info(
            f"Successfully refreshed snapshot: {meta['total_forecasts']} forecasts, "
            f"{meta['total_actuals_hourly']} hourly actuals saved to {output_path}."
        )
    except Exception as e:
        logger.error(f"Failed to refresh data snapshot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
