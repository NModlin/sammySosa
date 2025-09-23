# Legacy (Deprecated) Phase Scripts

This folder contains the original Phase 1 and Phase 2 scripts preserved for reference.
They are no longer used at runtime. The unified application is `govcon_suite.py` (run via `Apollo_GovCon.py`).

- Phase 1: `sam_gov_scraper_phase1.py` (deprecated)
- Phase 2: `sam_dashboard_phase_2.py` (deprecated)

Use the unified app instead:

- Local: `streamlit run Apollo_GovCon.py`
- Docker Compose: `docker compose up --build`

Configuration is environment-driven via `.env` and docker-compose.yml.

