from __future__ import annotations

import hashlib
import struct
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pydicom
from PIL import Image, UnidentifiedImageError
from pydicom.errors import InvalidDicomError

from app.domain.errors import (
    ApiError,
    image_parse_failed,
    model_parse_failed,
    unsupported_asset_type,
    upload_too_large,
)
from app.models.asset import AssetKind
from app.settings import Settings

DICOM_METADATA_ALLOWLIST = {
    "Modality": "modality",
    "BodyPartExamined": "body_part_examined",
    "SOPClassUID": "sop_class_uid",
    "Rows": "rows",
    "Columns": "columns",
    "NumberOfFrames": "number_of_frames",
}

DENIED_DICOM_TAGS = {"PatientName", "PatientID"}


class PreparedAsset:
    def __init__(
        self,
        *,
        kind: AssetKind,
        source_label: str,
        content_type: str | None,
        size_bytes: int,
        sha256: str,
        storage_path: str,
        preview_path: str | None,
        metadata_summary: dict[str, object],
        ingest_warnings: list[str],
    ) -> None:
        self.kind = kind
        self.source_label = source_label
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.sha256 = sha256
        self.storage_path = storage_path
        self.preview_path = preview_path
        self.metadata_summary = metadata_summary
        self.ingest_warnings = ingest_warnings


def prepare_asset_upload(
    *,
    content: bytes,
    filename: str | None,
    content_type: str | None,
    settings: Settings,
) -> PreparedAsset:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise upload_too_large()

    suffix = _suffix(filename)
    kind = _detect_kind(content=content, suffix=suffix, content_type=content_type)
    sha256 = hashlib.sha256(content).hexdigest()
    storage_path = _write_bytes(settings.storage_root, suffix or f".{kind.value}", content)
    metadata: dict[str, object] = {}
    warnings: list[str] = []
    preview_path: str | None = None

    try:
        if kind == AssetKind.DICOM:
            metadata, warnings, preview_path = _inspect_dicom(content, settings)
        elif kind == AssetKind.IMAGE:
            preview_path = _make_image_preview(content, settings)
            metadata = _inspect_image(content)
        elif kind == AssetKind.STL:
            metadata = _inspect_stl(content)
    except ApiError:
        storage_path.unlink(missing_ok=True)
        if preview_path:
            Path(preview_path).unlink(missing_ok=True)
        raise

    return PreparedAsset(
        kind=kind,
        source_label=f"{kind.value.upper()} review asset",
        content_type=content_type,
        size_bytes=len(content),
        sha256=sha256,
        storage_path=str(storage_path),
        preview_path=str(preview_path) if preview_path else None,
        metadata_summary=metadata,
        ingest_warnings=warnings,
    )


def _suffix(filename: str | None) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def _detect_kind(*, content: bytes, suffix: str, content_type: str | None) -> AssetKind:
    lowered_content_type = (content_type or "").lower()
    if suffix in {".dcm", ".dicom"} or content[128:132] == b"DICM":
        return AssetKind.DICOM
    if suffix == ".stl":
        return AssetKind.STL
    if suffix in {".png", ".jpg", ".jpeg"} or lowered_content_type in {
        "image/png",
        "image/jpeg",
    }:
        return AssetKind.IMAGE
    raise unsupported_asset_type()


def _write_bytes(root: Path, suffix: str, content: bytes) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{uuid4()}{suffix}"
    destination.write_bytes(content)
    return destination


def _inspect_dicom(
    content: bytes,
    settings: Settings,
) -> tuple[dict[str, object], list[str], str | None]:
    warnings: list[str] = []
    metadata: dict[str, object] = {}
    try:
        dataset = pydicom.dcmread(BytesIO(content), stop_before_pixels=False, force=False)
    except InvalidDicomError as exc:
        raise unsupported_asset_type() from exc

    for tag_name, label in DICOM_METADATA_ALLOWLIST.items():
        if hasattr(dataset, tag_name):
            value = getattr(dataset, tag_name)
            metadata[label] = str(value)

    leaked = sorted(tag for tag in DENIED_DICOM_TAGS if hasattr(dataset, tag))
    if leaked:
        warnings.append("Sensitive DICOM identity tags were detected and withheld.")

    preview_path: str | None = None
    if "PixelData" not in dataset:
        warnings.append(
            "DICOM pixel data is unavailable; metadata is usable but preview is unavailable.",
        )
    else:
        try:
            pixel_array = dataset.pixel_array
            if getattr(pixel_array, "ndim", 0) == 3:
                pixel_array = pixel_array[0]
            preview_path = _save_grayscale_preview(pixel_array, settings)
        except Exception:
            warnings.append(
                "DICOM pixel data could not be decoded; metadata is usable but "
                "preview is unavailable.",
            )

    return metadata, warnings, preview_path


def _inspect_image(content: bytes) -> dict[str, object]:
    try:
        with Image.open(BytesIO(content)) as image:
            return {"format": image.format or "image", "width": image.width, "height": image.height}
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise image_parse_failed() from exc


def _inspect_stl(content: bytes) -> dict[str, object]:
    if len(content) < 15:
        raise model_parse_failed()

    if len(content) >= 84:
        triangle_count = struct.unpack("<I", content[80:84])[0]
        expected_size = 84 + triangle_count * 50
        if expected_size == len(content):
            return {"format": "stl", "encoding": "binary", "triangle_count": triangle_count}

    prefix = content[:512].lstrip().lower()
    if prefix.startswith(b"solid") and b"facet normal" in content.lower():
        triangle_count = content.lower().count(b"facet normal")
        return {"format": "stl", "encoding": "ascii", "triangle_count": triangle_count}

    raise model_parse_failed()


def _make_image_preview(content: bytes, settings: Settings) -> str:
    try:
        with Image.open(BytesIO(content)) as image:
            image.thumbnail((512, 512))
            destination = settings.preview_root / f"{uuid4()}.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.convert("RGB").save(destination)
            return str(destination)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise image_parse_failed() from exc


def _save_grayscale_preview(pixel_array: object, settings: Settings) -> str:
    import numpy as np

    pixels = np.asarray(pixel_array, dtype=np.float32)
    pixels = pixels - pixels.min()
    max_value = float(pixels.max())
    if max_value > 0:
        pixels = pixels / max_value
    pixels = (pixels * 255).clip(0, 255).astype("uint8")
    image = Image.fromarray(pixels)
    image.thumbnail((512, 512))
    destination = settings.preview_root / f"{uuid4()}.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    return str(destination)
