# Wind Forecast Intelligence

A decision-support dashboard for reviewing UK wind-generation forecasts against observed generation using Elexon BMRS data.

## Features

- Forecast-versus-actual time-series chart
- MAE, RMSE, signed bias and WAPE
- Data-coverage diagnostics and interval-level evaluation rows
- React/Vite frontend and Python/FastAPI backend
- Docker Compose local execution

## Technology stack

- **Frontend:** React, Vite, Recharts, Lucide
- **Backend:** Python, FastAPI, Pandas, NumPy, HTTPX
- **Data source:** Elexon BMRS `WINDFOR` forecasts and `FUELHH` actuals filtered to `fuelType=WIND`

Source: https://data.elexon.co.uk/

## Run locally

### Backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Useful URLs:

- Health check: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

### Frontend

Open a second terminal from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173.

### Docker Compose

From the repository root:

```bash
docker compose -f compose.yaml up --build
```

Open the dashboard at http://localhost:8080. The backend health endpoint is http://localhost:8000/health. Stop the stack with `Ctrl+C`, then run:

```bash
docker compose -f compose.yaml down
```

## Tests and build

Backend tests:

```bash
cd backend
source .venv/bin/activate
pytest -q
```

The latest reported local backend test run was **11 passed**. Re-run the tests against the current checkout before committing or submitting.

Frontend production build:

```bash
cd frontend
npm ci
npm run build
```

A successful Vite build may still report a large-bundle warning. This is a performance improvement opportunity, not necessarily a build failure.

## API

- `GET /` — service information
- `GET /health` — health check
- `GET /api/analysis?month=2026-01` — analysis for a decision month

## Interpretation and limitations

- A decision-month cohort can include delivery periods in the following calendar month under the application's current convention. See the methodology documentation.
- Future periods cannot have final accuracy metrics until actual generation is available.
- The default 23:59 Europe/London previous-calendar-day cutoff is a **pilot assumption**, not a claim about an official market deadline.
- Matching expected timestamps does not prove the upstream source is complete.
- Accuracy metrics should be calculated only from valid, aligned forecast/actual pairs.
- Results are not trading advice.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Methodology](docs/METHODOLOGY.md)
- [Testing guide](docs/TESTING.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Requirements checklist](docs/REQUIREMENTS_CHECKLIST.md)
- [Enhancement roadmap](docs/ENHANCEMENT_ROADMAP.md)

Before submission, add only verified public deployment, repository and demo-video URLs. Add an appropriate license before publishing the repository.
