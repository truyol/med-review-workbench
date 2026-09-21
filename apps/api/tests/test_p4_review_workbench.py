from io import BytesIO

import pydicom
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid

from app.observability.request_id import REQUEST_ID_HEADER


def test_case_asset_review_closed_loop(api_client: TestClient) -> None:
    project_response = api_client.post(
        "/api/v1/projects",
        json={"name": "SHD Planning Review", "description": "Interview validation project"},
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["data"]["id"]

    case_response = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "CASE-001", "title": "TAVR pre-op asset review"},
    )
    assert case_response.status_code == 201
    case_id = case_response.json()["data"]["id"]

    upload_response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("raw_patient_name.png", _png_bytes(), "image/png")},
    )
    assert upload_response.status_code == 201
    assert upload_response.headers[REQUEST_ID_HEADER]
    asset = upload_response.json()["data"]
    assert asset["kind"] == "image"
    assert asset["status"] == "pending"
    assert asset["preview_available"] is True
    assert asset["source_label"] == "IMAGE review asset"
    assert "raw_patient_name.png" not in upload_response.text

    review_response = api_client.post(
        f"/api/v1/assets/{asset['id']}/reviews",
        json={
            "decision": "needs_changes",
            "note": "Segmentation border needs manual confirmation.",
            "reviewer_name": "engineer",
        },
    )
    assert review_response.status_code == 201
    assert review_response.json()["data"]["decision"] == "needs_changes"

    board_response = api_client.get(f"/api/v1/cases/{case_id}/review-board")
    assert board_response.status_code == 200
    board = board_response.json()["data"]
    assert board["case"]["case_code"] == "CASE-001"
    assert board["assets"][0]["asset"]["status"] == "needs_changes"
    assert board["assets"][0]["latest_review"]["decision"] == "needs_changes"


def test_case_code_conflict_returns_stable_error(api_client: TestClient) -> None:
    project_id = api_client.post("/api/v1/projects", json={"name": "Project"}).json()["data"]["id"]
    payload = {"case_code": "CASE-001", "title": "First case"}

    assert api_client.post(f"/api/v1/projects/{project_id}/cases", json=payload).status_code == 201
    response = api_client.post(f"/api/v1/projects/{project_id}/cases", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CASE_CODE_CONFLICT"
    assert response.json()["error"]["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_unsupported_upload_returns_400_with_request_id(api_client: TestClient) -> None:
    project_id = api_client.post("/api/v1/projects", json={"name": "Project"}).json()["data"]["id"]
    case_id = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "CASE-001", "title": "Case"},
    ).json()["data"]["id"]

    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("notes.txt", b"not a supported asset", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_ASSET_TYPE"
    assert response.headers[REQUEST_ID_HEADER]


def test_reviewed_asset_cannot_be_hard_deleted(api_client: TestClient) -> None:
    project_id = api_client.post("/api/v1/projects", json={"name": "Project"}).json()["data"]["id"]
    case_id = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "CASE-001", "title": "Case"},
    ).json()["data"]["id"]
    asset_id = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("image.png", _png_bytes(), "image/png")},
    ).json()["data"]["id"]
    api_client.post(
        f"/api/v1/assets/{asset_id}/reviews",
        json={"decision": "accept", "reviewer_name": "engineer"},
    )

    response = api_client.delete(f"/api/v1/assets/{asset_id}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DELETE_RESTRICTED"


def test_dicom_upload_returns_allowlist_metadata_without_identity(
    api_client: TestClient,
) -> None:
    case_id = _create_case(api_client)

    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("patient-jane-doe.dcm", _dicom_bytes(), "application/dicom")},
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["kind"] == "dicom"
    assert body["metadata_summary"]["modality"] == "CT"
    assert body["metadata_summary"]["sop_class_uid"] == str(CTImageStorage)
    assert body["preview_available"] is False
    assert "Sensitive DICOM identity tags were detected and withheld." in body["ingest_warnings"]
    assert "study_description" not in body["metadata_summary"]
    assert "series_description" not in body["metadata_summary"]
    assert "PatientName" not in response.text
    assert "Jane" not in response.text
    assert "patient-jane-doe.dcm" not in response.text


def test_stl_upload_is_validated_and_filterable(api_client: TestClient) -> None:
    case_id = _create_case(api_client)
    api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("image.png", _png_bytes(), "image/png")},
    )
    stl_response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("left-atrium.stl", _ascii_stl_bytes(), "model/stl")},
    )

    assert stl_response.status_code == 201
    stl = stl_response.json()["data"]
    assert stl["kind"] == "stl"
    assert stl["metadata_summary"] == {
        "format": "stl",
        "encoding": "ascii",
        "triangle_count": 1,
    }
    assert "left-atrium.stl" not in stl_response.text

    filtered_response = api_client.get(f"/api/v1/cases/{case_id}/assets?kind=stl&limit=100")
    assert filtered_response.status_code == 200
    filtered_assets = filtered_response.json()["data"]
    assert len(filtered_assets) == 1
    assert filtered_assets[0]["id"] == stl["id"]


def test_corrupt_stl_returns_model_parse_error(api_client: TestClient) -> None:
    case_id = _create_case(api_client)

    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("broken.stl", b"solid but not really a mesh", "model/stl")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MODEL_PARSE_FAILED"
    assert response.json()["error"]["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_preview_and_model_streaming_endpoints(api_client: TestClient) -> None:
    case_id = _create_case(api_client)
    image_asset_id = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("source-image.png", _png_bytes(), "image/png")},
    ).json()["data"]["id"]
    stl_content = _ascii_stl_bytes()
    stl_asset_id = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("model-source-name.stl", stl_content, "model/stl")},
    ).json()["data"]["id"]

    preview_response = api_client.get(f"/api/v1/assets/{image_asset_id}/preview")
    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"] == "image/png"
    assert b"source-image.png" not in preview_response.content

    model_response = api_client.get(f"/api/v1/assets/{stl_asset_id}/model")
    assert model_response.status_code == 200
    assert model_response.headers["content-type"] == "model/stl"
    assert model_response.content == stl_content
    assert b"model-source-name.stl" not in model_response.content


def test_preview_and_model_unavailable_errors(api_client: TestClient) -> None:
    case_id = _create_case(api_client)
    image_asset_id = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("image.png", _png_bytes(), "image/png")},
    ).json()["data"]["id"]
    stl_asset_id = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("model.stl", _ascii_stl_bytes(), "model/stl")},
    ).json()["data"]["id"]

    preview_response = api_client.get(f"/api/v1/assets/{stl_asset_id}/preview")
    assert preview_response.status_code == 409
    assert preview_response.json()["error"]["code"] == "PREVIEW_NOT_AVAILABLE"

    model_response = api_client.get(f"/api/v1/assets/{image_asset_id}/model")
    assert model_response.status_code == 409
    assert model_response.json()["error"]["code"] == "MODEL_NOT_AVAILABLE"


def test_upload_logs_do_not_include_original_filename_or_dicom_identity(
    api_client: TestClient,
    capsys: pytest.CaptureFixture[str],
) -> None:
    case_id = _create_case(api_client)

    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": ("PatientName-Jane-Doe.dcm", _dicom_bytes(), "application/dicom")},
    )

    assert response.status_code == 201
    captured = capsys.readouterr()
    logs = f"{captured.out}\n{captured.err}"
    assert "PatientName-Jane-Doe.dcm" not in logs
    assert "Jane" not in logs
    assert "DOE123" not in logs


def test_p4_boundary_errors_and_pagination_limit_are_stable(api_client: TestClient) -> None:
    missing_project = api_client.get("/api/v1/projects/not-a-real-project/cases")
    assert missing_project.status_code == 404
    assert missing_project.json()["error"]["code"] == "PROJECT_NOT_FOUND"
    assert missing_project.headers[REQUEST_ID_HEADER]

    missing_asset = api_client.get(
        "/api/v1/assets/not-a-real-asset/preview",
    )
    assert missing_asset.status_code == 404
    assert missing_asset.json()["error"]["code"] == "ASSET_NOT_FOUND"

    project_id = api_client.post(
        "/api/v1/projects",
        json={"name": "Pagination boundary"},
    ).json()["data"]["id"]
    oversized_limit = api_client.get("/api/v1/projects?limit=101")
    assert oversized_limit.status_code == 400
    assert oversized_limit.json()["error"]["code"] == "VALIDATION_ERROR"

    missing_case_board = api_client.get(
        "/api/v1/cases/not-a-real-case/review-board",
    )
    assert missing_case_board.status_code == 404
    assert missing_case_board.json()["error"]["code"] == "CASE_NOT_FOUND"
    assert project_id


def _create_case(api_client: TestClient) -> str:
    project_id = str(
        api_client.post("/api/v1/projects", json={"name": "Project"}).json()["data"]["id"],
    )
    case_id = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "CASE-001", "title": "Case"},
    ).json()["data"]["id"]
    return str(case_id)


def _png_bytes() -> bytes:
    image = Image.new("L", (16, 16), color=128)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _dicom_bytes() -> bytes:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = CTImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    dataset = FileDataset(
        "ignored.dcm",
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    dataset.SOPClassUID = CTImageStorage
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.PatientName = "Jane^Doe"
    dataset.PatientID = "DOE123"
    dataset.Modality = "CT"
    dataset.StudyDescription = "Synthetic review fixture"

    buffer = BytesIO()
    pydicom.dcmwrite(buffer, dataset, enforce_file_format=True)
    return buffer.getvalue()


def _ascii_stl_bytes() -> bytes:
    return (
        b"solid demo\n"
        b"facet normal 0 0 1\n"
        b"outer loop\n"
        b"vertex 0 0 0\n"
        b"vertex 1 0 0\n"
        b"vertex 0 1 0\n"
        b"endloop\n"
        b"endfacet\n"
        b"endsolid demo\n"
    )
