"""Elexon BMRS API client with retry, backoff, and chunked requests."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.core.time_utils import format_iso_utc

logger = logging.getLogger(__name__)

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


class ElexonAPIError(Exception):
    """Raised when Elexon BMRS API returns an unrecoverable error."""
    pass


class ElexonClient:
    """Client for querying Elexon BMRS FUELHH (actuals) and WINDFOR (forecasts)."""

    def __init__(
        self,
        base_url: str = ELEXON_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def _get_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform an HTTP GET request with retry on transient errors and rate limits."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "UK-Wind-Decision-Support/0.1.0",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            import asyncio
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.get(url, params=params, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        # Stream endpoints return a list of dicts directly
                        if isinstance(data, list):
                            return data
                        # Non-stream endpoints return {"data": [...]}
                        if isinstance(data, dict) and "data" in data:
                            return data["data"]
                        return []

                    if response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", self.backoff_factor * (2 ** attempt)))
                        logger.warning(f"Rate limited (429). Retrying after {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status_code in (500, 502, 503, 504):
                        sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                        logger.warning(f"Server error {response.status_code}. Retrying in {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
                        continue

                    # Unrecoverable error (e.g. 400 Bad Request)
                    raise ElexonAPIError(
                        f"Elexon API error {response.status_code} on {url}: {response.text}"
                    )

                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    if attempt == self.max_retries:
                        raise ElexonAPIError(f"HTTP request failed after {self.max_retries} attempts: {exc}") from exc
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    logger.warning(f"Request exception {exc}. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)

        raise ElexonAPIError(f"Failed to fetch data from {url} after {self.max_retries} retries.")

    async def fetch_fuelhh_actuals(
        self,
        start_date: str,
        end_date: str,
        fuel_type: str = "WIND",
    ) -> List[Dict[str, Any]]:
        """
        Fetch outturn generation from /datasets/FUELHH/stream for specified date range.
        
        Args:
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            fuel_type: e.g. 'WIND'
        """
        params = {
            "settlementDateFrom": start_date,
            "settlementDateTo": end_date,
            "fuelType": fuel_type,
        }
        logger.info(f"Fetching FUELHH {fuel_type} actuals from {start_date} to {end_date}...")
        return await self._get_with_retry("datasets/FUELHH/stream", params=params)

    async def fetch_windfor_forecasts_chunked(
        self,
        publish_from: datetime,
        publish_to: datetime,
        chunk_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Fetch wind forecasts from /datasets/WINDFOR/stream in chunks to avoid server limits.
        
        Args:
            publish_from: Start publish datetime in UTC
            publish_to: End publish datetime in UTC
            chunk_days: Max days per chunk query (default 7 days)
        """
        all_records: List[Dict[str, Any]] = []
        current_start = publish_from

        while current_start < publish_to:
            current_end = min(current_start + timedelta(days=chunk_days), publish_to)
            params = {
                "publishDateTimeFrom": format_iso_utc(current_start),
                "publishDateTimeTo": format_iso_utc(current_end),
            }
            logger.info(f"Fetching WINDFOR batch: {params['publishDateTimeFrom']} -> {params['publishDateTimeTo']}")
            batch = await self._get_with_retry("datasets/WINDFOR/stream", params=params)
            all_records.extend(batch)
            current_start = current_end

        # Deduplicate on (publishTime, startTime) if overlapping chunks occurred
        seen = set()
        deduped = []
        for r in all_records:
            key = (r.get("publishTime"), r.get("startTime"))
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        logger.info(f"Fetched {len(deduped)} unique WINDFOR forecasts.")
        return deduped
