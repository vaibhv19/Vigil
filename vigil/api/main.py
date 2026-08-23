from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from vigil.api.routes import runs, metrics

app = FastAPI(
    title="Vigil Evaluation Dashboard",
    description="REST API and Dashboard for the Vigil AI Agent Evaluation Harness",
    version="1.0.0",
)

# Register API routers
app.include_router(runs.router, prefix="/api", tags=["Runs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])

# Mount static files for the dashboard SPA
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serves the single-page dashboard HTML."""
    return FileResponse(os.path.join(static_dir, "index.html"))
