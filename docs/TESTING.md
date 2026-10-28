# Testing and verification guide

Run these checks before committing, deploying or submitting the project. Results below reflect the latest reported development checks, not a guarantee that every manual test has been completed on the current checkout.

## 1. Backend tests

From the repository root:

```bash
cd backend
source .venv/bin/activate
pytest -q
python -m compileall -q .
```

The latest reported local backend test run was **11 passed**. Re-run the tests after any code changes and confirm the current output.

The current suite includes checks for forecast version selection and cutoff eligibility, WIND filtering, invalid forecast values, duplicate/conflicting actual records, duplicate forecast versions, and incomplete half-hour pairs.

## 2. Frontend production build

```bash
cd frontend
npm ci
npm run build
```

A successful Vite build means compilation completed. A large-bundle warning is not a build failure, but code splitting may improve load performance.

## 3. Local API smoke tests

Start the backend in one terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

In another terminal, from any directory:

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/
curl -sS 'http://localhost:8000/api/analysis?month=2026-01' -o /tmp/wind-analysis.json
python3 -m json.tool /tmp/wind-analysis.json | head -80
curl -i 'http://localhost:8000/api/analysis?month=not-a-month'
```

Expected checks:

- `/health` returns HTTP 200 and healthy JSON.
- The analysis endpoint returns JSON with metrics, data-quality diagnostics and rows when the upstream service provides usable data.
- Invalid month input is rejected as a client error.
- The analysis request depends on Elexon availability and may take time.

## 4. Manual UI tests

Open http://localhost:5173 for Vite development or http://localhost:8080 for Docker. Verify each item and record any failures:

- [ ] Dashboard renders without a blank screen.
- [ ] January 2026 loads and displays data.
- [ ] KPI cards, chart, diagnostics and table agree with API output.
- [ ] Selecting another historical month triggers a new request and updates the screen.
- [ ] Future month shows a clear not-yet-evaluable state, not misleading zero-error metrics.
- [ ] Loading, empty-data and API-error states are understandable.
- [ ] Browser console has no uncaught errors or missing assets.
- [ ] Narrow/mobile viewport remains usable.
- [ ] Favicon loads successfully.

## 5. Docker integration

From the repository root:

```bash
docker compose -f compose.yaml up --build
```

In a second terminal:

```bash
docker compose -f compose.yaml ps
curl -i http://localhost:8000/health
curl -I http://localhost:8080/
curl -I http://localhost:8080/favicon.svg
curl -sS 'http://localhost:8000/api/analysis?month=2026-01' -o /tmp/wind-docker.json
python3 -m json.tool /tmp/wind-docker.json | head -60
```

Open http://localhost:8080 and verify the dashboard loads data. Confirm the backend is healthy and both containers are running. Rebuild after backend or frontend source changes so the containers include the latest code. Stop the stack with `Ctrl+C`, then run:

```bash
docker compose -f compose.yaml down
```

## 6. Additional tests to verify or add

The current suite already includes several selection, filtering and half-hour-completeness cases. Remaining useful coverage includes:

- [ ] Missing expected forecast and actual timestamps are counted correctly.
- [ ] Actuals are matched using delivery `startTime` rather than publication date.
- [ ] Empty and future months return meaningful status and do not imply false accuracy.
- [ ] Decision-month and delivery-month boundaries behave as documented.
- [ ] Europe/London daylight-saving transitions are handled correctly.
- [ ] Metric calculations match known expected arrays.
- [ ] WAPE handles a zero actual-value denominator safely.
- [ ] Conflicting or malformed source records produce an intentional, documented outcome.
- [ ] API and UI handle upstream timeouts, non-success responses and malformed payloads.

## 7. Production smoke tests

After deployment, repeat health and analysis requests against the public backend URL. Open the frontend in a private browser window and verify the configured API URL, CORS, future-month messaging and chart rendering. Do not mark production checks complete until they have actually been run.
