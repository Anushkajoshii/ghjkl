# Evaluation methodology

## Purpose and data source

The application compares day-ahead wind-generation forecasts with observed wind generation for a selected decision-month cohort.

Elexon BMRS datasets:

- `WINDFOR`: forecast `startTime`, `publishTime` and `generation`.
- `FUELHH`: half-hourly generation outturn filtered to `fuelType=WIND`.

Source: https://data.elexon.co.uk/

## Decision month versus delivery date

The decision month represents the dates on which the forecast decision is considered to have been made. Those decisions concern subsequent delivery periods, so a decision-month cohort can include delivery on the first day of the following month under the application's current convention. Keep this relationship clear in the UI and evaluation rows.

## Forecast selection and cutoff

For each delivery interval, the application selects the latest forecast published at or before the configured cutoff associated with the preceding calendar day. `publishTime` represents when the forecast was published; `startTime` identifies the delivery interval.

The current default cutoff is 23:59 Europe/London. This is a **pilot assumption**, not an official market gate-closure claim unless the relevant market rules are independently verified and the application is updated accordingly.

## Actuals and interval alignment

Actual records should be filtered to WIND and matched by delivery timestamp, not merely by publication timestamp. FUELHH records are half-hourly while forecast records may be hourly. Any aggregation must be explicit and tested. For example, an hourly mean of two half-hour observations should only be produced when both expected observations are present and that definition is appropriate.

Use UTC timestamps for joins. Convert to Europe/London when deriving local decision dates or display labels. Test month boundaries and daylight-saving transitions.

## Metrics

For valid matched intervals, let forecast be \(F_i\), actual be \(A_i\), error be \(e_i = F_i - A_i\), and the number of matched intervals be \(N\).

- **Mean absolute error (MAE):** `sum(abs(e_i)) / N`
- **Root mean squared error (RMSE):** `sqrt(sum(e_i ** 2) / N)`
- **Bias:** `sum(e_i) / N`. Positive bias means over-forecasting; negative bias means under-forecasting.
- **Weighted absolute percentage error (WAPE):** `100 * sum(abs(e_i)) / sum(abs(A_i))`, provided the denominator is non-zero.

Calculate accuracy metrics only on valid matched forecast/actual pairs. Report interval counts and coverage separately. Define and test behaviour for an empty matched set and a zero WAPE denominator.

## Coverage interpretation

Expected timestamps are constructed from the selected calendar convention and evaluation frequency. Missing counts should be computed against that expected index. Zero missing expected timestamps means the received timestamps match the constructed expectation; it does **not** prove every upstream source record is complete.

Where possible, report records received, valid records after parsing/filtering, eligible forecasts, matched intervals, expected intervals, and missing expected forecast/actual timestamps. If actuals do not exist yet for a future period, return a clear future/not-yet-evaluable state rather than zero-error metrics.

## Limitations

- The cutoff is a pilot convention, not a verified official market deadline.
- Results depend on source API records and timestamp semantics.
- Hourly aggregation of half-hour actuals must be documented and tested.
- Timestamp coverage does not independently validate source completeness.
- Results are not trading advice.
