"""Deterministic, non-clinical fallbacks for a fresh-clone demonstration."""

from __future__ import annotations

import math
import struct
from io import BytesIO

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import UID, CTImageStorage, ExplicitVRLittleEndian


def synthetic_dicom() -> bytes:
    """Make a small CT-shaped pixel phantom with no patient identity fields."""
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = CTImageStorage
    meta.MediaStorageSOPInstanceUID = UID("1.2.826.0.1.3680043.10.543.1003")
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.10.543.1")
    dataset = FileDataset("synthetic-demo.dcm", {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = CTImageStorage
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = "1.2.826.0.1.3680043.10.543.1001"
    dataset.SeriesInstanceUID = "1.2.826.0.1.3680043.10.543.1002"
    dataset.Modality = "CT"
    dataset.BodyPartExamined = "PHANTOM"
    dataset.PatientIdentityRemoved = "YES"
    dataset.DeidentificationMethod = "Synthetic non-clinical phantom; no patient source"
    dataset.Rows = 64
    dataset.Columns = 64
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.PixelData = bytes(
        190 if (x - 32) ** 2 + (y - 32) ** 2 < 20**2 else 35
        for y in range(64)
        for x in range(64)
    )
    output = BytesIO()
    dataset.save_as(output, enforce_file_format=True)
    return output.getvalue()


def synthetic_stl() -> bytes:
    """Make a small curved tube mesh for basic 3D viewer interaction."""
    ring_count = 12
    sides = 16
    rings: list[list[tuple[float, float, float]]] = []
    for ring in range(ring_count):
        z = float(ring * 5)
        cx = 5.0 * math.sin(ring / 4)
        radius = 12.0 - ring * 0.35
        rings.append(
            [
                (
                    cx + radius * math.cos(2 * math.pi * side / sides),
                    radius * math.sin(2 * math.pi * side / sides),
                    z,
                )
                for side in range(sides)
            ],
        )

    triangles: list[tuple[tuple[float, float, float], ...]] = []
    for ring in range(ring_count - 1):
        for side in range(sides):
            next_side = (side + 1) % sides
            a, b = rings[ring][side], rings[ring][next_side]
            c, d = rings[ring + 1][side], rings[ring + 1][next_side]
            triangles.extend(((a, b, c), (b, d, c)))
    for side in range(sides):
        next_side = (side + 1) % sides
        triangles.append(((0.0, 0.0, 0.0), rings[0][next_side], rings[0][side]))
        triangles.append((rings[-1][side], rings[-1][next_side], (0.0, 0.0, 55.0)))

    output = BytesIO()
    output.write(b"Synthetic non-clinical curved tube".ljust(80, b"\0"))
    output.write(struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        normal = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        length = math.sqrt(sum(value * value for value in normal)) or 1.0
        output.write(struct.pack("<12fH", *(value / length for value in normal), *a, *b, *c, 0))
    return output.getvalue()
