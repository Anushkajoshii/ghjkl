# Requirements and submission checklist

This checklist records known development progress. It is not a substitute for comparing the implementation against the original assignment prompt or rerunning checks before submission. Only mark an item complete after verifying it on the current checkout.

## Core application

- [x] React dashboard with KPI cards, chart, data-quality panel and evaluation table implemented.
- [x] FastAPI health and analysis endpoints implemented.
- [x] Elexon BMRS integration using `WINDFOR` and `FUELHH` implemented.
- [x] MAE, RMSE, bias and WAPE implemented.
- [ ] Verify the month selector across multiple historical months.
- [ ] Verify loading, API-error, empty-data and future-period states.
- [ ] Confirm chart and table agree with API output.

## Data quality and methodology

- [x] Latest reported local backend test run: 11 tests passed.
- [x] Tests cover several forecast-selection, filtering, duplicate-handling and half-hour-completeness cases.
- [ ] Verify delivery-time matching and cutoff logic against the intended source semantics.
- [ ] Verify hourly/half-hourly alignment on realistic source data.
- [ ] Test missing timestamps, month boundaries and daylight-saving transitions.
- [ ] Distinguish timestamp coverage from upstream source completeness in UI and documentation.
- [x] Document the default cutoff as a pilot assumption, not an official market deadline.

## Engineering and local verification

- [x] Frontend production build reported successful.
- [x] Backend Dockerfile exists.
- [x] Frontend Dockerfile and root Compose configuration exist.
- [x] Docker containers previously started and backend reported healthy.
- [x] `.gitignore` rules were checked for virtual environments, caches, `node_modules`, build output and environment files.
- [ ] Rebuild Docker images after the latest source edits and re-run integration checks.
- [ ] Confirm dashboard data loads and controls work at http://localhost:8080.
- [ ] Run `git diff --check`, backend tests and frontend build before commit.
- [ ] Review repository status to ensure no secrets, generated files or unrelated files are staged.

## Submission

- [ ] README and docs reviewed against the actual implementation and original assignment.
- [ ] Public GitHub repository pushed and checked.
- [ ] Frontend and backend deployed; public URLs smoke-tested.
- [ ] Short unlisted demo video recorded if required by the assignment.
- [ ] Submission form completed with verified links.
- [ ] Appropriate license selected and added before public release.

## Final quality gate

Do not mark the project complete until local tests, Docker integration checks, UI checks, production checks and required submission artifacts have been verified. Do not claim a public deployment or source completeness unless it has been independently confirmed.
