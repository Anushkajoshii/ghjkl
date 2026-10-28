# Architecture

## Data flow

1. The user selects a decision month in the React dashboard.
2. The frontend calls `GET /api/analysis?month=YYYY-MM`.
3. FastAPI requests forecast and actual-generation records from Elexon BMRS.
4. The analysis module parses and filters records, selects eligible forecasts, aligns intervals, and calculates metrics and coverage diagnostics.
5. The API returns metrics, data-quality information and interval-level rows.
6. The frontend renders KPI cards, a chart, diagnostics and a table.

```text
React/Vite browser
       | GET /api/analysis?month=YYYY-MM
       v
FastAPI -> Elexon BMRS WINDFOR (forecast)
       |-> Elexon BMRS FUELHH (actuals, WIND)
       v
parse -> filter -> select -> align -> evaluate -> JSON response
```

## Main modules

- `backend/main.py`: routes, request validation, CORS and error handling.
- `backend/elexon.py`: Elexon BMRS HTTP requests.
- `backend/analysis.py`: normalization, cutoff selection, interval alignment, metrics and coverage diagnostics.
- `backend/tests/test_analysis.py`: backend unit tests.
- `frontend/src/api.js`: API URL and request helper.
- `frontend/src/App.jsx`: dashboard and data loading.
- `frontend/src/index.css`: styling.

## Endpoints

- `GET /`: service information.
- `GET /health`: health check.
- `GET /api/analysis?month=2026-01`: analysis for the selected decision-month cohort.

## Configuration

- `VITE_API_URL`: frontend API base URL. Vite compiles this value into the static frontend bundle at build time.
- `FRONTEND_ORIGIN`: comma-separated allowed frontend origins for backend CORS.

For production, set `VITE_API_URL` to the deployed backend base URL and `FRONTEND_ORIGIN` to the exact deployed frontend origin. Rebuild the frontend after changing `VITE_API_URL`. Localhost defaults are for development only.
