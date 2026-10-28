# Enhancement roadmap: make the project distinctive

Prioritize correctness and decision usefulness over decorative UI.

## Priority 1 — Forecast decision replay

Let a user choose a decision date and cutoff time, then inspect the forecast that was actually available at that time.

Display the decision date/timezone, configured cutoff, selected forecast publication timestamp, delivery interval, actual value when available, and why later versions were excluded.

Acceptance criteria:

- Changing the decision date changes the eligible cohort.
- No forecast published after the cutoff appears.
- Tests cover multiple versions and cutoff-boundary timestamps.

## Priority 2 — Error diagnostics

Add an error heatmap by delivery date and hour, plus a top-10 absolute-error table. Include delivery timestamp, forecast, actual, signed/absolute error, publication timestamp and decision date.

Acceptance criteria:

- Rows can be sorted by absolute error.
- Error sign is consistently `forecast - actual`.
- Displayed values agree with API output.

## Priority 3 — Honest data confidence

Separate source records received, valid records, eligible forecasts, matched intervals, expected intervals, missing forecast timestamps, missing actual timestamps and future periods. Do not call coverage complete solely because constructed timestamps matched.

## Priority 4 — Exportable decision report

Add CSV export of interval rows and a summary with month, cutoff, timezone, metrics, expected/matched counts and limitations. Exported rows should reflect the current filters.

## Priority 5 — Product polish

Add accessible labels and keyboard support, loading skeletons, retry controls, responsive charts, and a short explanation of metrics. Consider code splitting to reduce the frontend bundle warning.

## Suggested order

1. Verify data semantics and tests.
2. Improve future/empty/error states.
3. Implement decision replay.
4. Add heatmap and top-error table.
5. Add CSV/report export.
6. Improve accessibility and performance.
7. Finalize documentation, deployment and demo.
