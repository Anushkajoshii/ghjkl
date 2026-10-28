# Deployment guide

## Local Docker Compose

Ensure Docker Desktop is running, then execute from the repository root:

```bash
docker compose -f compose.yaml up --build
```

- Frontend: http://localhost:8080
- Backend health: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

Stop the stack with `Ctrl+C`, then run:

```bash
docker compose -f compose.yaml down
```

## Production architecture

Deploy the frontend and backend as separate services unless the selected platform explicitly supports the existing multi-container setup.

1. Deploy FastAPI using the `backend` directory or its Dockerfile.
2. Confirm the platform's port configuration. The Dockerfile uses `PORT` if supplied.
3. Set `FRONTEND_ORIGIN` to the exact deployed frontend origin.
4. Deploy the frontend from `frontend`.
5. Set `VITE_API_URL` to the deployed backend base URL before building the frontend.
6. Rebuild and redeploy after changing `VITE_API_URL`; Vite variables are compiled into static assets at build time.
7. Verify `/health`, `/api/analysis?month=2026-01`, and the public frontend.

Exact platform settings depend on the chosen hosting provider; verify its current requirements before deploying.

## CORS and secrets

The backend reads comma-separated origins from `FRONTEND_ORIGIN`. Include the scheme and hostname, without a path. Do not rely on localhost defaults in production.

Do not commit `.env` files, API keys, secrets, virtual environments, caches, `node_modules` or build output. Keep `frontend/.env.example` as an example configuration only; it should not contain secrets.

## Production checklist

- [ ] Backend health returns HTTP 200.
- [ ] Analysis endpoint returns valid JSON for a historical month.
- [ ] Frontend API URL points to the production backend.
- [ ] Browser console has no CORS or network errors.
- [ ] Future periods show a not-yet-evaluable state.
- [ ] Logs contain no secrets.
- [ ] README includes only verified public URLs.
- [ ] Public URLs have been tested from a separate browser/session.

## Troubleshooting

- **Backend startup failure:** inspect service logs, dependency installation and port configuration.
- **Frontend loads but has no data:** check `VITE_API_URL`, backend health, browser console and CORS.
- **Old API URL remains after a configuration change:** rebuild and redeploy the frontend.
- **Docker daemon error:** start Docker Desktop and wait for the engine.
- **Local and Docker results differ:** rebuild the relevant image and rerun the same API request against both environments.
