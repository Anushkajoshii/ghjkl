from analysis import build_analysis, prepare_actuals, prepare_forecasts


def test_latest_forecast_before_cutoff_is_selected():
    actuals = [{
        "startTime": "2026-01-02T12:00:00Z",
        "generation": 1000,
        "fuelType": "WIND",
    }]

    forecasts = [
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T08:00:00Z",
            "generation": 900,
        },
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T20:00:00Z",
            "generation": 950,
        },
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-02T06:00:00Z",
            "generation": 800,
        },
    ]

    result = build_analysis(actuals, forecasts)

    assert len(result["rows"]) == 1
    assert result["rows"][0]["forecast_mw"] == 950
    assert result["rows"][0]["actual_mw"] == 1000


def test_metrics_for_two_periods():
    actuals = [
        {"startTime": "2026-01-02T12:00:00Z", "generation": 1000, "fuelType": "WIND"},
        {"startTime": "2026-01-02T12:30:00Z", "generation": 1200, "fuelType": "WIND"},
    ]
    forecasts = [
        {"startTime": "2026-01-02T12:00:00Z", "publishTime": "2026-01-01T20:00:00Z", "generation": 900},
        {"startTime": "2026-01-02T12:30:00Z", "publishTime": "2026-01-01T20:00:00Z", "generation": 1300},
    ]

    metrics = build_analysis(actuals, forecasts)["metrics"]

    assert metrics["mae_mw"] == 100
    assert metrics["rmse_mw"] == 100
    assert metrics["bias_mw"] == 0
    assert round(metrics["wape_pct"], 2) == 9.09
    assert metrics["matched_periods"] == 2


def test_non_wind_actuals_are_excluded():
    result = prepare_actuals([{
        "startTime": "2026-01-02T12:00:00Z",
        "generation": 1000,
        "fuelType": "GAS",
    }])

    assert result.empty


def test_invalid_numeric_records_are_excluded():
    result = prepare_forecasts([{
        "startTime": "2026-01-02T12:00:00Z",
        "publishTime": "2026-01-01T20:00:00Z",
        "generation": "not-a-number",
    }])

    assert result.empty


def test_forecast_after_cutoff_is_not_selected():
    actuals = [{
        "startTime": "2026-01-02T12:00:00Z",
        "generation": 1000,
        "fuelType": "WIND",
    }]
    forecasts = [{
        "startTime": "2026-01-02T12:00:00Z",
        "publishTime": "2026-01-02T06:00:00Z",
        "generation": 800,
    }]

    result = build_analysis(actuals, forecasts)
    assert result["rows"] == []



import pytest


def test_exact_duplicate_actual_records_are_deduplicated():
    record = {
        "startTime": "2026-01-02T12:00:00Z",
        "publishTime": "2026-01-02T12:30:00Z",
        "generation": 1000,
        "fuelType": "WIND",
    }

    result = prepare_actuals([record, record.copy()])

    assert len(result) == 1
    assert result.iloc[0]["actual_mw"] == 1000


def test_latest_actual_publication_is_selected():
    records = [
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-02T12:30:00Z",
            "generation": 1000,
            "fuelType": "WIND",
        },
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-02T13:00:00Z",
            "generation": 1100,
            "fuelType": "WIND",
        },
    ]

    result = prepare_actuals(records)

    assert len(result) == 1
    assert result.iloc[0]["actual_mw"] == 1100


def test_conflicting_actuals_at_same_publication_raise_error():
    records = [
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-02T12:30:00Z",
            "generation": 1000,
            "fuelType": "WIND",
        },
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-02T12:30:00Z",
            "generation": 1200,
            "fuelType": "WIND",
        },
    ]

    with pytest.raises(ValueError, match="Conflicting WIND actual values"):
        prepare_actuals(records)



def test_duplicate_forecast_versions_do_not_change_selected_value():
    record = {
        "startTime": "2026-01-02T12:00:00Z",
        "publishTime": "2026-01-01T20:00:00Z",
        "generation": 950,
    }

    result = build_analysis(
        actual_records=[{
            "startTime": "2026-01-02T12:00:00Z",
            "generation": 1000,
            "fuelType": "WIND",
        }],
        forecast_records=[record, record.copy()],
    )

    assert len(result["rows"]) == 1
    assert result["rows"][0]["forecast_mw"] == 950


def test_latest_eligible_forecast_is_selected_at_cutoff():
    actuals = [{
        "startTime": "2026-01-02T12:00:00Z",
        "generation": 1000,
        "fuelType": "WIND",
    }]

    forecasts = [
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T22:59:00Z",
            "generation": 900,
        },
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T23:00:00Z",
            "generation": 950,
        },
    ]

    result = build_analysis(
        actual_records=actuals,
        forecast_records=forecasts,
        cutoff_hour=23,
        cutoff_minute=0,
    )

    assert len(result["rows"]) == 1
    assert result["rows"][0]["forecast_mw"] == 950


def test_hourly_aggregation_rejects_incomplete_half_hour_pairs():
    actuals = [
        # Only the first half-hour exists for 12:00–13:00.
        {
            "startTime": "2026-01-02T12:00:00Z",
            "generation": 1000,
            "fuelType": "WIND",
        },
        # A later half-hour observation signals half-hourly source data.
        {
            "startTime": "2026-01-02T13:30:00Z",
            "generation": 1200,
            "fuelType": "WIND",
        },
    ]

    forecasts = [
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T20:00:00Z",
            "generation": 900,
        }
    ]

    result = build_analysis(actuals, forecasts)

    assert result["rows"] == []
    assert result["metrics"]["matched_periods"] == 0