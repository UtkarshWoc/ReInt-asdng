"""In-memory data repository loaded from static snapshot."""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class DataStore:
    """In-memory indexed store providing fast lookups for forecasts and actuals."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.metadata: Dict[str, Any] = {}
        self.actuals_hourly: Dict[str, float] = {}  # startTime -> average MW
        self.actuals_hourly_details: Dict[str, Dict[str, Any]] = {}
        self.actuals_half_hourly: Dict[str, Dict[str, Any]] = {}  # startTime -> record
        self.forecasts_by_target: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.available_delivery_dates: List[str] = []

        if data:
            self._load_from_dict(data)

    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Populate internal index maps from snapshot dictionary."""
        self.metadata = data.get("metadata", {})

        # 1. Index hourly actuals
        for item in data.get("actuals_hourly", []):
            st = item["startTime"]
            self.actuals_hourly[st] = float(item["generation"])
            self.actuals_hourly_details[st] = item

        # 2. Index half-hourly actuals
        for item in data.get("actuals_half_hourly", []):
            st = item["startTime"]
            self.actuals_half_hourly[st] = item

        # 3. Index forecasts by target startTime (sorted by publishTime)
        for fc in data.get("forecasts", []):
            st = fc["startTime"]
            self.forecasts_by_target[st].append(fc)

        for st in self.forecasts_by_target:
            self.forecasts_by_target[st].sort(key=lambda x: x["publishTime"])

        # 4. Extract delivery dates
        self.available_delivery_dates = sorted(
            list(self.metadata.get("available_delivery_dates", []))
        )
        if not self.available_delivery_dates:
            dates = {st[:10] for st in self.actuals_hourly}
            self.available_delivery_dates = sorted(list(dates))

        logger.info(
            f"DataStore loaded: {len(self.forecasts_by_target)} target hours, "
            f"{len(self.actuals_hourly)} hourly actuals across {len(self.available_delivery_dates)} dates."
        )

    @classmethod
    def load_from_file(cls, file_path: Path) -> "DataStore":
        """Load snapshot JSON file and initialize DataStore."""
        if not file_path.exists():
            logger.warning(f"Snapshot file not found at {file_path}. Initializing empty DataStore.")
            return cls()

        logger.info(f"Loading data snapshot from {file_path}...")
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def get_forecasts_for_target(self, target_time: str) -> List[Dict[str, Any]]:
        """Return all forecasts issued for a specific target period, sorted by publishTime."""
        return self.forecasts_by_target.get(target_time, [])

    def get_actual_hourly(self, target_time: str) -> Optional[float]:
        """Return hourly average actual generation for target period."""
        return self.actuals_hourly.get(target_time)

    def get_actual_details(self, target_time: str) -> Optional[Dict[str, Any]]:
        """Return details (including :00 and :30 generation) for an hour."""
        return self.actuals_hourly_details.get(target_time)

    def get_target_times_for_date(self, delivery_date: str) -> List[str]:
        """Return all 24 hourly target times for a given delivery date (YYYY-MM-DD)."""
        return [f"{delivery_date}T{h:02d}:00:00Z" for h in range(24)]


# Global singleton instance
_data_store_instance: Optional[DataStore] = None


def get_data_store() -> DataStore:
    """Retrieve global DataStore instance, initializing on first call."""
    global _data_store_instance
    if _data_store_instance is None:
        _data_store_instance = DataStore.load_from_file(settings.DATA_SNAPSHOT_PATH)
    return _data_store_instance


def set_data_store(store: DataStore) -> None:
    """Explicitly set global DataStore instance (useful for unit tests)."""
    global _data_store_instance
    _data_store_instance = store
