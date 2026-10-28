"""Historical forecast selection and forecast accuracy metrics."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

UK = ZoneInfo("Europe/London")
UTC = timezone.utc



def prepare_actuals(records: list[dict]) -> pd.DataFrame:
    columns = ["startTime", "actual_mw"]
    if not records:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(records)
    required = {"startTime", "generation", "fuelType"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"FUELHH missing required fields: {required - set(df.columns)}"
        )

    df = df[df["fuelType"].astype(str).str.upper() == "WIND"].copy()
    if df.empty:
        return pd.DataFrame(columns=columns)

    df["startTime"] = pd.to_datetime(
        df["startTime"], utc=True, errors="coerce"
    )
    df["actual_mw"] = pd.to_numeric(df["generation"], errors="coerce")
    if "publishTime" in df.columns:
        df["publishTime"] = pd.to_datetime(
            df["publishTime"], utc=True, errors="coerce"
        )

    df = df.dropna(subset=["startTime", "actual_mw"])

    # Remove identical API rows, not merely rows sharing a timestamp.
    df = df.drop_duplicates()

    # If the same timestamp and publication time contain different
    # generation values, do not silently choose one.
    version_keys = ["startTime"]
    if "publishTime" in df.columns:
        version_keys.append("publishTime")

    conflicts = (
        df.groupby(version_keys, dropna=False)["actual_mw"]
        .nunique()
        .gt(1)
    )
    if conflicts.any():
        raise ValueError(
            "Conflicting WIND actual values share the same delivery "
            "timestamp and publication time."
        )

    # If actuals were republished, keep the latest publication for each
    # delivery timestamp. If publication time is unavailable, keep the
    # single unambiguous value after conflict checks.
    if "publishTime" in df.columns:
        df = df.sort_values(["startTime", "publishTime"])
    else:
        df = df.sort_values("startTime")

    df = df.drop_duplicates("startTime", keep="last")

    return (
        df[columns]
        .sort_values("startTime")
        .reset_index(drop=True)
    )



def prepare_forecasts(records: list[dict]) -> pd.DataFrame:
    columns = ["startTime", "publishTime", "forecast_mw"]
    if not records:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(records)
    required = {"startTime", "publishTime", "generation"}

    if not required.issubset(df.columns):
        raise ValueError(f"WINDFOR missing required fields: {required - set(df.columns)}")

    df["startTime"] = pd.to_datetime(df["startTime"], utc=True, errors="coerce")
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True, errors="coerce")
    df["forecast_mw"] = pd.to_numeric(df["generation"], errors="coerce")
    df = df.dropna(subset=["startTime", "publishTime", "forecast_mw"])

    return df[columns].sort_values(["startTime", "publishTime"]).reset_index(drop=True)


def month_bounds(month: str) -> tuple[date, date]:
    """Return the first and last calendar dates for YYYY-MM."""
    try:
        first = date.fromisoformat(f"{month}-01")
    except ValueError as exc:
        raise ValueError("month must be a valid YYYY-MM value") from exc

    if first.strftime("%Y-%m") != month:
        raise ValueError("month must be a valid YYYY-MM value")

    if first.month == 12:
        next_month = date(first.year + 1, 1, 1)
    else:
        next_month = date(first.year, first.month + 1, 1)

    return first, next_month - timedelta(days=1)


def decision_cutoff_utc(
    decision_date: date,
    cutoff_hour: int,
    cutoff_minute: int,
) -> pd.Timestamp:
    local = datetime.combine(
        decision_date,
        time(cutoff_hour, cutoff_minute),
        tzinfo=UK,
    )
    return pd.Timestamp(local.astimezone(UTC))


def build_analysis(
    actual_records: list[dict],
    forecast_records: list[dict],
    decision_month: str = "2026-01",
    cutoff_hour: int = 23,
    cutoff_minute: int = 59,
) -> dict:
    """
    Evaluate delivery periods whose previous calendar-day decision date
    falls inside the requested month.

    The cutoff is a configurable pilot assumption, not an official
    market gate-closure claim.
    """
    if not 0 <= cutoff_hour <= 23:
        raise ValueError("cutoff_hour must be between 0 and 23")
    if not 0 <= cutoff_minute <= 59:
        raise ValueError("cutoff_minute must be between 0 and 59")


    first_day, last_day = month_bounds(decision_month)

    # Count source WIND records before deduplication or aggregation.
    raw_actuals_df = pd.DataFrame(actual_records)
    if not raw_actuals_df.empty and "fuelType" in raw_actuals_df.columns:
        raw_wind_df = raw_actuals_df[
            raw_actuals_df["fuelType"].astype(str).str.upper() == "WIND"
        ].copy()
    else:
        raw_wind_df = pd.DataFrame()

    raw_wind_record_count = len(raw_wind_df)
    exact_duplicate_wind_record_count = (
        int(raw_wind_df.duplicated().sum())
        if not raw_wind_df.empty
        else 0
    )

    actuals = prepare_actuals(actual_records)
    unique_actual_timestamp_count = len(actuals)
    forecasts = prepare_forecasts(forecast_records)


    # Align actuals to hourly forecasts only when the forecast source
    # has no half-hourly timestamps. Otherwise preserve native intervals.
    forecast_has_half_hours = (
        not forecasts.empty
        and forecasts["startTime"].dt.minute.eq(30).any()
    )
    actuals_have_half_hours = (
        not actuals.empty
        and actuals["startTime"].dt.minute.eq(30).any()
    )

    if actuals_have_half_hours and not forecast_has_half_hours:
        actuals = actuals.copy()
        actuals["hour_start"] = actuals["startTime"].dt.floor("h")

        hourly_actuals = (
            actuals.groupby("hour_start")
            .agg(
                actual_mw=("actual_mw", "mean"),
                half_hour_records=("actual_mw", "count"),
                half_hour_minutes=(
                    "startTime",
                    lambda values: tuple(sorted(values.dt.minute.tolist())),
                ),
            )
            .reset_index()
        )

        # Require exactly one observation at minute 00 and one at minute 30.
        hourly_actuals = hourly_actuals[
            (hourly_actuals["half_hour_records"] == 2)
            & (hourly_actuals["half_hour_minutes"] == (0, 30))
        ]

        actuals = hourly_actuals.rename(
            columns={"hour_start": "startTime"}
        )[["startTime", "actual_mw"]]

    empty_metrics = {
        "mae_mw": None,
        "rmse_mw": None,
        "bias_mw": None,
        "wape_pct": None,
        "matched_periods": 0,
    }

    if actuals.empty:
        actuals["delivery_date"] = pd.Series(dtype=object)
    else:
        actuals["delivery_date"] = (
            actuals["startTime"].dt.tz_convert(UK).dt.date
        )

    if forecasts.empty:
        forecasts["delivery_date"] = pd.Series(dtype=object)
        forecasts["decision_date"] = pd.Series(dtype=object)
    else:
        forecasts["delivery_date"] = (
            forecasts["startTime"].dt.tz_convert(UK).dt.date
        )
        forecasts["decision_date"] = forecasts["delivery_date"].map(
            lambda d: d - timedelta(days=1)
        )

        # Only decisions made in the requested month belong to this cohort.
        forecasts = forecasts[
            (forecasts["decision_date"] >= first_day)
            & (forecasts["decision_date"] <= last_day)
        ].copy()

        forecasts["cutoff_utc"] = forecasts["decision_date"].map(
            lambda d: decision_cutoff_utc(d, cutoff_hour, cutoff_minute)
        )

        # Exclude any forecast that was not published by the cutoff.
        forecasts = forecasts[
            forecasts["publishTime"] <= forecasts["cutoff_utc"]
        ].copy()

    # Select the latest eligible publication independently per target period.
    if forecasts.empty:
        selected = forecasts.copy()
        selected["selected_publish_time"] = pd.Series(dtype="datetime64[ns, UTC]")
    else:
        selected = (
            forecasts.sort_values(["startTime", "publishTime"])
            .drop_duplicates(subset=["startTime"], keep="last")
            .rename(columns={"publishTime": "selected_publish_time"})
        )

    # Decision dates in the selected month map to delivery dates
    # from the 2nd of the month through the 1st of the next month.
    delivery_start = first_day + timedelta(days=1)
    delivery_end = last_day + timedelta(days=1)
    delivery_days = (delivery_end - delivery_start).days + 1

    # Match the calendar resolution to the forecast source.
    evaluation_frequency = "30min" if forecast_has_half_hours else "h"

    expected_start_times = pd.date_range(
        start=pd.Timestamp(delivery_start, tz=UK),
        end=pd.Timestamp(delivery_end + timedelta(days=1), tz=UK),
        freq=evaluation_frequency,
        inclusive="left",
    ).tz_convert("UTC")

    expected_periods = len(expected_start_times)

    # Measure coverage only within the expected delivery calendar.
    forecast_times = (
        pd.DatetimeIndex(selected["startTime"].dropna().unique())
        if not selected.empty
        else pd.DatetimeIndex([], tz="UTC")
    )

    actual_times = (
        pd.DatetimeIndex(actuals["startTime"].dropna().unique())
        if not actuals.empty
        else pd.DatetimeIndex([], tz="UTC")
    )

    forecast_times_in_cohort = forecast_times.intersection(
        expected_start_times
    )
    actual_times_in_cohort = actual_times.intersection(
        expected_start_times
    )

    missing_forecast_count = len(
        expected_start_times.difference(forecast_times_in_cohort)
    )
    missing_actual_count = len(
        expected_start_times.difference(actual_times_in_cohort)
    )
    # startTime is the authoritative join key; the expected calendar count
    # is reported separately because source timestamps may have gaps.
    joined = selected.merge(
        actuals[["startTime", "actual_mw", "delivery_date"]],
        on="startTime",
        how="outer",
        suffixes=("_forecast", "_actual"),
        indicator=True,
    ) if not selected.empty or not actuals.empty else pd.DataFrame()

    if joined.empty:
        rows: list[dict] = []
        metrics = empty_metrics.copy()
        matched_count = 0

    else:
        # Retain only delivery periods in the requested decision cohort.
        if "delivery_date_forecast" in joined.columns:
            joined["delivery_date"] = joined["delivery_date_forecast"].combine_first(
                joined["delivery_date_actual"]
            )

        joined["decision_date"] = joined["delivery_date"].map(
            lambda d: d - timedelta(days=1) if pd.notna(d) else None
        )
        joined = joined[
            joined["decision_date"].map(
                lambda d: d is not None and first_day <= d <= last_day
            )
        ].copy()

        matched = joined[
            joined["_merge"] == "both"
        ].copy()

        matched["error_mw"] = matched["forecast_mw"] - matched["actual_mw"]
        matched["absolute_error_mw"] = matched["error_mw"].abs()

        actual_total = float(matched["actual_mw"].abs().sum()) if not matched.empty else 0.0
        metrics = {
            "mae_mw": float(matched["absolute_error_mw"].mean()) if not matched.empty else None,
            "rmse_mw": float(np.sqrt(np.square(matched["error_mw"]).mean())) if not matched.empty else None,
            "bias_mw": float(matched["error_mw"].mean()) if not matched.empty else None,
            "wape_pct": (
                float(matched["absolute_error_mw"].sum() / actual_total * 100)
                if actual_total > 0 else None
            ),
            "matched_periods": int(len(matched)),
        }

        rows = []
        for _, row in matched.sort_values("startTime").iterrows():
            rows.append({
                "start_time": row["startTime"].isoformat(),
                "delivery_date": row["delivery_date"].isoformat(),
                "decision_date": row["decision_date"].isoformat(),
                "publish_time": row["selected_publish_time"].isoformat(),
                "forecast_mw": float(row["forecast_mw"]),
                "actual_mw": float(row["actual_mw"]),
                "error_mw": float(row["error_mw"]),
            })


        matched_count = int(len(matched))

    return {
        "decision_month": decision_month,
        "cutoff": f"{cutoff_hour:02d}:{cutoff_minute:02d}",
        "timezone": "Europe/London",
        "methodology": (
            "Latest forecast published at or before the configured cutoff "
            "on the previous calendar day. Error = forecast - actual."
        ),
        "metrics": metrics,
        "rows": rows,

        "data_quality": {
            "raw_wind_records": int(raw_wind_record_count),
            "exact_duplicate_wind_records": int(exact_duplicate_wind_record_count),
            "unique_actual_timestamps_received": int(unique_actual_timestamp_count),
            "hourly_actual_periods_in_cohort": int(
                actuals["startTime"].isin(expected_start_times).sum()
            ),
            "forecast_records_received": int(len(forecast_records)),
            "eligible_forecast_records": int(len(forecasts)),
            "matched_periods": matched_count,
            "missing_forecast_periods": missing_forecast_count,
            "missing_actual_periods": missing_actual_count,
            "expected_periods_by_calendar_convention": expected_periods,
            "calendar_generated_delivery_days": delivery_days,
        },

    }
