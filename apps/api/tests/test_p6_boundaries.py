from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.domain.errors import ApiError
from app.models.project import Project
from app.observability.request_id import REQUEST_ID_HEADER
from app.repositories.workbench import WorkbenchRepository


def test_malformed_image_returns_stable_422(api_client: TestClient) -> None:
    project_id = api_client.post("/api/v1/projects", json={"name": "P6"}).json()["data"]["id"]
    case_id = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "P6-001", "title": "Boundary"},
    ).json()["data"]["id"]
    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("fake.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "IMAGE_PARSE_FAILED"
    assert response.headers[REQUEST_ID_HEADER]


def test_oversized_upload_is_rejected_before_persistence(api_client: TestClient) -> None:
    project_id = api_client.post("/api/v1/projects", json={"name": "P6"}).json()["data"]["id"]
    case_id = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "P6-002", "title": "Large boundary"},
    ).json()["data"]["id"]
    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("large.png", b"x" * (1024 * 1024 + 1), "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "UPLOAD_TOO_LARGE"


def test_repository_rolls_back_and_maps_database_failure() -> None:
    class FailingSession:
        def __init__(self) -> None:
            self.rolled_back = False

        def add(self, _: object) -> None:
            return None

        def commit(self) -> None:
            raise SQLAlchemyError("synthetic database failure")

        def rollback(self) -> None:
            self.rolled_back = True

    session = FailingSession()
    repository = WorkbenchRepository(session)  # type: ignore[arg-type]
    try:
        repository.add_project(Project(name="will rollback"))
    except ApiError as error:
        assert error.code == "PERSISTENCE_FAILED"
    else:
        raise AssertionError("expected persistence failure")
    assert session.rolled_back is True
