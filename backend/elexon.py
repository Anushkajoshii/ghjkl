"""HTTP client for Elexon BMRS dataset stream endpoints."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
TIMEOUT_SECONDS = 45.0


def to_utc_string(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def fetch_day(
    client: httpx.AsyncClient,
    dataset: str,
    day: date,
) -> list[dict[str, Any]]:
    """Fetch records published during one UTC day."""
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    response = await client.get(
        f"{BASE_URL}/datasets/{dataset}/stream",
        params={
            "publishDateTimeFrom": to_utc_string(start),
            "publishDateTimeTo": to_utc_string(end),
        },
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]

    raise ValueError(f"Unexpected {dataset} response structure")


async def fetch_range(
    dataset: str,
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    """Fetch records published across an inclusive range of UTC dates."""
    if end < start:
        raise ValueError("End date must be on or after start date")

    records: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        current = start
        while current <= end:
            records.extend(await fetch_day(client, dataset, current))
            current += timedelta(days=1)

    return records


async def fetch_actuals(start: date, end: date) -> list[dict[str, Any]]:
    return await fetch_range("FUELHH", start, end)


async def fetch_forecasts(start: date, end: date) -> list[dict[str, Any]]:
    return await fetch_range("WINDFOR", start, end)
