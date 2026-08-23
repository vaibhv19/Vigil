import pytest
from fastapi.testclient import TestClient

from vigil.api.main import app
from vigil.db.connection import get_session
from vigil.db.repository import VigilRepository
from vigil.eval.task_models import TaskDefinition


client = TestClient(app)


def _seed_test_data():
    """Seeds a suite, run, task, tool call, and anomaly for API testing."""
    with get_session() as session:
        suite = VigilRepository.get_or_create_suite(session, "api-test-suite", "v1.0.0")
        run = VigilRepository.create_eval_run(session, suite.id, {"test": True})

        task_def = TaskDefinition(
            task_id="api-test-task",
            description="API test task",
            input_prompt="test",
            category="api",
            expected_output={"assertions": []},
        )
        task = VigilRepository.get_or_create_task(session, task_def)
        VigilRepository.associate_task_with_suite(session, suite.id, task.id, 1)

        result = VigilRepository.create_task_result(
            session=session,
            run_id=run.id,
            task_id=task.id,
            status="PASS",
            steps_taken=2,
            final_output="task completed",
        )

        VigilRepository.create_tool_call(
            session=session,
            task_result_id=result.id,
            sequence_number=1,
            tool_name="bash",
            input_args={"cmd": "echo hello"},
            stdout_capture="hello",
            exit_code=0,
            duration_ms=150,
        )

        VigilRepository.update_eval_run(session, run.id, "COMPLETED", 3000)

        return str(run.id), str(result.id)


# Seed once at module level
_run_id, _result_id = _seed_test_data()


class TestRunsAPI:
    def test_list_runs(self):
        response = client.get("/api/runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_run_detail(self):
        response = client.get(f"/api/runs/{_run_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == _run_id
        assert data["status"] == "COMPLETED"
        assert "task_results" in data
        assert len(data["task_results"]) > 0

    def test_get_run_detail_not_found(self):
        response = client.get("/api/runs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_get_run_detail_invalid_id(self):
        response = client.get("/api/runs/not-a-uuid")
        assert response.status_code == 400

    def test_get_tool_calls(self):
        response = client.get(f"/api/runs/{_run_id}/tasks/{_result_id}/tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["tool_name"] == "bash"
        assert data[0]["exit_code"] == 0

    def test_get_anomalies(self):
        response = client.get(f"/api/runs/{_run_id}/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_anomalies_invalid_id(self):
        response = client.get("/api/runs/bad-id/anomalies")
        assert response.status_code == 400


class TestMetricsAPI:
    def test_get_run_summary(self):
        response = client.get(f"/api/metrics/runs/{_run_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == _run_id
        assert "pass_rate" in data
        assert "p50_latency_ms" in data
        assert "total_tool_calls" in data

    def test_get_run_summary_not_found(self):
        response = client.get("/api/metrics/runs/00000000-0000-0000-0000-000000000000/summary")
        assert response.status_code == 404

    def test_compare_runs_missing_params(self):
        response = client.get("/api/metrics/compare")
        assert response.status_code == 422  # FastAPI validation error


class TestDashboard:
    def test_serve_index_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Vigil" in response.text
        assert "text/html" in response.headers["content-type"]

    def test_serve_static_css(self):
        response = client.get("/static/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_serve_static_js(self):
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
