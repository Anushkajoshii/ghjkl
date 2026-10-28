"""FastAPI entry point for Wind Forecast Intelligence."""

import asyncio
from datetime import date, timedelta
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from analysis import build_analysis, month_bounds
from elexon import fetch_actuals, fetch_forecasts

app = FastAPI(
    title="Wind Forecast Intelligence API",
    version="1.0.0",
    description="Historical UK wind generation forecast accuracy analysis.",
)

origins = [
    item.strip()
    for item in os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173,http://localhost:8080",
    ).split(",")
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "Wind Forecast Intelligence API",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/analysis")
async def analysis(
    month: str = Query(default="2026-01", pattern=r"^\d{4}-\d{2}$"),
    cutoff_hour: int = Query(default=23, ge=0, le=23),
    cutoff_minute: int = Query(default=59, ge=0, le=59),
):
    try:
        first_day, last_day = month_bounds(month)

        # January decisions concern delivery from Jan 2 through Feb 1.
        delivery_start = first_day + timedelta(days=1)
        delivery_end = last_day + timedelta(days=1)

        # Actuals can be published after their delivery period, so include
        # the following publication date to capture late-month actuals.
        actual_records, forecast_records = await asyncio.gather(
            fetch_actuals(delivery_start, delivery_end + timedelta(days=1)),
            fetch_forecasts(first_day, last_day),
        )

        return build_analysis(
            actual_records=actual_records,
            forecast_records=forecast_records,
            decision_month=month,
            cutoff_hour=cutoff_hour,
            cutoff_minute=cutoff_minute,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Log the underlying exception in the service logs, but do not
        # expose upstream payloads or internal details to the client.
        print(f"Analysis failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve or process Elexon data. Check service logs.",
        ) from exc
