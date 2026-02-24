from typing import Any, Dict

from fastapi.testclient import TestClient

import main
import main_cloud
from database.connection import get_db


class StubOrchestrator:
    def __init__(self):
        self._history = [{"id": "wf-1"}]
        self._cleared = False

    def get_system_status(self):
        return {
            "system_status": {
                "agent1_ready": True,
                "agent2_ready": True,
                "system_ready": True,
            }
        }

    def validate_specific_element(self, file_content, element_type, filename=None):
        return {
            "success": True,
            "element_type": element_type,
            "filename": filename,
            "size": len(file_content),
        }

    def generate_compliance_report(self, validation_results: Dict[str, Any]):
        return {"generated": True, "input": validation_results}

    def get_workflow_history(self):
        return self._history

    def get_current_workflow_status(self):
        return {"status": "idle"}

    def clear_workflow_history(self):
        self._cleared = True
        self._history = []


class StubPdfGenerator:
    def generate_report(self, validation_data, image_data=None):
        return b"%PDF-1.4\n%stub\n"


def _disable_lifespan(app):
    app.router.on_startup = []
    app.router.on_shutdown = []


def _override_get_db():
    yield object()


async def _authorized_user():
    return {"id": "u-1", "email": "user@example.com"}


def _main_client(authenticated: bool) -> TestClient:
    _disable_lifespan(main.app)
    main.orchestrator = StubOrchestrator()
    main.optimized_validator = object()
    main.pdf_generator = StubPdfGenerator()

    main.app.dependency_overrides = {get_db: _override_get_db}
    if authenticated:
        main.app.dependency_overrides[main.require_auth] = _authorized_user

    return TestClient(main.app)


def _main_cloud_client(authenticated: bool) -> TestClient:
    _disable_lifespan(main_cloud.app)
    main_cloud.orchestrator = object()
    main_cloud.optimized_validator = object()
    main_cloud.pdf_generator = StubPdfGenerator()

    main_cloud.app.dependency_overrides = {get_db: _override_get_db}
    if authenticated:
        main_cloud.app.dependency_overrides[main_cloud.require_auth] = _authorized_user

    return TestClient(main_cloud.app)


def test_main_sensitive_endpoints_return_401_without_auth():
    client = _main_client(authenticated=False)

    unauthorized_calls = [
        lambda: client.get("/api/system/status"),
        lambda: client.post(
            "/api/validation/validate-element",
            files={"file": ("roof.png", b"img-bytes", "image/png")},
        ),
        lambda: client.post("/api/reports/compliance", json={"validation": "data"}),
        lambda: client.get("/api/workflow/history"),
        lambda: client.get("/api/workflow/current"),
        lambda: client.delete("/api/workflow/history"),
        lambda: client.get("/api/agents/test"),
        lambda: client.post("/generate-pdf-report", json={"validation_data": {}}),
    ]

    for request_call in unauthorized_calls:
        response = request_call()
        assert response.status_code == 401


def test_main_sensitive_endpoints_work_for_authenticated_users():
    client = _main_client(authenticated=True)

    assert client.get("/api/system/status").status_code == 200

    validate_element = client.post(
        "/api/validation/validate-element",
        data={"element_type": "sheathing"},
        files={"file": ("roof.png", b"img-bytes", "image/png")},
    )
    assert validate_element.status_code == 200
    assert validate_element.json()["success"] is True

    report = client.post("/api/reports/compliance", json={"validation": "data"})
    assert report.status_code == 200
    assert report.json()["generated"] is True

    history = client.get("/api/workflow/history")
    assert history.status_code == 200
    assert history.json()["total_workflows"] == 1

    current = client.get("/api/workflow/current")
    assert current.status_code == 200
    assert current.json()["current_workflow"]["status"] == "idle"

    cleared = client.delete("/api/workflow/history")
    assert cleared.status_code == 200
    assert cleared.json()["message"] == "Workflow history cleared"

    agents = client.get("/api/agents/test")
    assert agents.status_code == 200
    assert agents.json()["system_ready"] is True

    pdf = client.post("/generate-pdf-report", json={"validation_data": {}})
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"


def test_main_cloud_sensitive_endpoints_return_401_without_auth():
    client = _main_cloud_client(authenticated=False)

    status = client.get("/api/system/status")
    assert status.status_code == 401

    pdf = client.post("/generate-pdf-report", json={"validation_data": {}})
    assert pdf.status_code == 401


def test_main_cloud_sensitive_endpoints_work_for_authenticated_users():
    client = _main_cloud_client(authenticated=True)

    status = client.get("/api/system/status")
    assert status.status_code == 200
    assert status.json()["status"] == "operational"

    pdf = client.post("/generate-pdf-report", json={"validation_data": {}})
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
