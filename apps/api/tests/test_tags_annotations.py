from io import BytesIO
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from app.observability.request_id import REQUEST_ID_HEADER


def _png_bytes() -> bytes:
    image = Image.new("L", (16, 16), color=128)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _create_case(api_client: TestClient) -> str:
    project_id = api_client.post(
        "/api/v1/projects",
        json={"name": "P9 tags project"},
    ).json()["data"]["id"]
    case_id = api_client.post(
        f"/api/v1/projects/{project_id}/cases",
        json={"case_code": "TAG-001", "title": "Tag and annotation case"},
    ).json()["data"]["id"]
    return str(case_id)


def _upload_image(api_client: TestClient, case_id: str, name: str = "image.png") -> dict[str, Any]:
    response = api_client.post(
        f"/api/v1/cases/{case_id}/assets",
        files={"file": (name, _png_bytes(), "image/png")},
    )
    assert response.status_code == 201
    payload: dict[str, Any] = response.json()["data"]
    return payload


def test_asset_tags_and_note_can_be_updated_and_filtered(api_client: TestClient) -> None:
    case_id = _create_case(api_client)
    first = _upload_image(api_client, case_id, "first.png")
    second = _upload_image(api_client, case_id, "second.png")

    assert first["tags"] == []
    assert first["note"] is None

    update = api_client.patch(
        f"/api/v1/assets/{first['id']}",
        json={"tags": ["瓣膜", "待补图"], "note": "需要补充标注图"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["tags"] == ["瓣膜", "待补图"]
    assert update.json()["data"]["note"] == "需要补充标注图"

    filtered = api_client.get(f"/api/v1/cases/{case_id}/assets", params={"tag": "瓣膜"})
    assert filtered.status_code == 200
    ids = [item["id"] for item in filtered.json()["data"]]
    assert ids == [first["id"]]

    no_match = api_client.get(f"/api/v1/cases/{case_id}/assets", params={"tag": "不存在"})
    assert no_match.json()["data"] == []
    assert second["id"] != first["id"]


def test_annotation_crud_round_trip(api_client: TestClient) -> None:
    case_id = _create_case(api_client)
    asset = _upload_image(api_client, case_id)

    created = api_client.post(
        f"/api/v1/assets/{asset['id']}/annotations",
        json={"label": "主动脉瓣环", "data": {"x": 1.5, "y": -2.0, "z": 3.25}, "note": "标记点"},
    )
    assert created.status_code == 201
    annotation = created.json()["data"]
    assert annotation["label"] == "主动脉瓣环"
    assert annotation["data"] == {"x": 1.5, "y": -2.0, "z": 3.25}

    listed = api_client.get(f"/api/v1/assets/{asset['id']}/annotations")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [annotation["id"]]

    deleted = api_client.delete(f"/api/v1/annotations/{annotation['id']}")
    assert deleted.status_code == 204

    after = api_client.get(f"/api/v1/assets/{asset['id']}/annotations")
    assert after.json()["data"] == []


def test_annotation_missing_returns_stable_error(api_client: TestClient) -> None:
    response = api_client.delete("/api/v1/annotations/not-a-real-annotation")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ANNOTATION_NOT_FOUND"
    assert response.json()["error"]["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_asset_update_missing_returns_stable_error(api_client: TestClient) -> None:
    response = api_client.patch(
        "/api/v1/assets/not-a-real-asset",
        json={"tags": ["x"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ASSET_NOT_FOUND"
