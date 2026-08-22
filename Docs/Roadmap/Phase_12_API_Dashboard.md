# Phase 12: API & Dashboard

## 1. Package / Folder Structure
```text
vigil/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI Application entrypoint
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── runs.py             # Run execution & status endpoints
│   │   └── metrics.py          # Metrics & comparison queries
│   └── static/                 # Single-Page App (SPA) Dashboard
│       ├── index.html          # HTML5 layout structure
│       ├── style.css           # Premium Vanilla CSS styling (Dark mode)
│       └── app.js              # Vanilla JS API integration and rendering
└── tests/
    ├── integration/
    │   └── test_api.py         # HTTP test cases verifying API endpoints
```

---

## 2. Purpose
This phase builds the developer interface. It creates a FastAPI REST API backend to expose endpoints for querying suites, runs, results, tool call logs, anomalies, percentiles, and run comparisons. Additionally, it implements a single-page web dashboard using Vanilla HTML, CSS, and JS (statically served from the FastAPI backend) with a modern dark-mode layout to display run histories and compare agent versions.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.db.connection` (To query database tables)
- `vigil.eval.metrics` (To retrieve statistical analytics)
- `vigil.eval.comparator` (To run differential comparisons)

### 3.2 External Libraries
- **fastapi**: `0.111.0` (Web server framework)
- **uvicorn**: `^0.29.0` (ASGI server runner)
- **jinja2**: `^3.1.3` (Statically served file templates or mounts)
- **pydantic**: (To validate request and response formats)

---

## 4. Inputs
- HTTP GET/POST requests containing run IDs, date filters, or comparison parameters.
- Static client-side button clicks.

---

## 5. Outputs
- REST API JSON payloads returning execution metrics, lists, logs, and differentials.
- HTML/CSS web dashboard rendered on the developer's local browser window.

---

## 6. Public Interfaces
### 6.1 API REST Endpoints (`vigil/api/main.py`)
- `GET /api/runs`: Returns a list of all historical `eval_runs`.
- `GET /api/runs/{run_id}`: Returns detailed information for a run (status, duration, cost, and task result list).
- `GET /api/runs/{run_id}/tasks/{task_result_id}/tools`: Returns the sequence of tool calls executed during a task.
- `GET /api/runs/{run_id}/anomalies`: Returns anomalies flagged during the run.
- `GET /api/metrics/compare?run_a={id}&run_b={id}`: Returns task-by-task differentials between two runs.
- `GET /`: Serves the static dashboard page `index.html`.

---

## 7. Internal Components
- **`APIRouter`**: Handles routing of runs, metrics, and static dashboard assets.
- **`DashboardRenderer`**: Front-end javascript engine rendering run cards, progress bars, tables, and comparative charts without external frameworks.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Sample data populated**: Verify that test data runs exist in the local database.
- [ ] **Port availability**: Ensure port `8000` is free on the host.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-12.1** | Initialize FastAPI server application structure in `vigil/api/main.py`. | S | Low | TS-1.6 | None | Running web server, verified via Swagger UI. | Run `uvicorn vigil.api.main:app` and access `/docs`. | Server starts and serves the default auto-generated Swagger page. |
| **TS-12.2** | Implement runs routing (`routes/runs.py`) serving list and detail queries. | M | Low | TS-7.5, TS-12.1 | None | REST endpoints returning run models and tool execution lists. | Write API tests using `TestClient` verifying JSON payloads. | Endpoints query the database and serialize results. |
| **TS-12.3** | Implement metrics routing (`routes/metrics.py`) exposing run comparisons. | M | Low | TS-11.5, TS-12.1 | None | Endpoints returning latency stats and comparison differentials. | Test `/api/metrics/compare` with valid and invalid IDs. | Metrics endpoints return correct status codes and payloads. |
| **TS-12.4** | Design the Vanilla HTML structure for the static dashboard SPA. | S | Low | TS-12.1 | None | Semantic HTML5 dashboard skeleton containing containers for lists. | Open page, verify container elements are loaded. | Structure maps sidebar, main grid container, and comparisons. |
| **TS-12.5** | Write premium styling sheet (`static/style.css`) using Vanilla CSS. | M | Med | TS-12.4 | None | Modern dark-mode aesthetics (glassmorphism details, CSS grids). | Open page, verify rendering scales correctly on mobile and desktop. | Interface uses a cohesive theme (slate colors, vibrant indicators). |
| **TS-12.6** | Implement Vanilla JavaScript application (`static/app.js`) rendering dashboard data. | M | Med | TS-12.2, TS-12.3, TS-12.4 | None | Interactive UI displaying runs list, task details, and version comparisons. | Click through UI, check tool logs popups and comparison layouts. | UI dynamically fetches API data and renders it without layout shifts. |
| **TS-12.7** | Write integration tests verifying HTTP endpoints. | M | Low | TS-12.2, TS-12.3 | None | Pytest suite running API requests against database content. | Run `pytest tests/integration/test_api.py`. | REST endpoint requests are validated and returned correctly. |

---

## 10. Definition of Done (DoD)
- FastAPI application exposes endpoints for runs, tool calls, anomalies, and comparisons.
- Endpoint results validate and serialize to JSON correctly.
- A single-page dashboard is served statically from the backend.
- The UI is styled with responsive Vanilla CSS using a premium dark-mode aesthetic.
- The Javascript client coordinates API calls to populate run cards and comparisons.
- Integration tests cover all API endpoints.
