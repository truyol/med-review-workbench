"""Create repository-safe demo copies with identifier fields removed.

This is a reproducible demo-data preparation step, not a claim of clinical-grade
DICOM de-identification. The generated CT copy is published with the repository;
original source files stay outside Git, and the optional Rubo copy is local-only.
"""

from hashlib import sha256
from pathlib import Path

from pydicom import dcmread
from pydicom.dataset import FileDataset
from pydicom.uid import generate_uid

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DICOM_ROOT = PROJECT_ROOT / "sample-data" / "dicom"

SAMPLES = (
    (DICOM_ROOT / "CT_small.dcm", DICOM_ROOT / "CT_small_anonymized.dcm"),
    (
        DICOM_ROOT / "rubo_angiogram_0002" / "0002.DCM",
        DICOM_ROOT / "rubo_angiogram_0002" / "0002_anonymized.DCM",
    ),
)

REMOVED_TAGS = (
    # Direct patient identifiers.
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientBirthTime",
    "PatientSex",
    "PatientAge",
    "PatientWeight",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "PatientMotherBirthName",
    "MedicalRecordLocator",
    "EthnicGroup",
    "Occupation",
    "MilitaryRank",
    "PatientComments",
    "AdditionalPatientHistory",
    "OtherPatientIDs",
    "OtherPatientNames",
    "OtherPatientIDsSequence",
    # Institution, device, operator and study identifiers.
    "InstitutionName",
    "InstitutionAddress",
    "InstitutionalDepartmentName",
    "StationName",
    "ReferringPhysicianName",
    "PerformingPhysicianName",
    "OperatorsName",
    "NameOfPhysiciansReadingStudy",
    "PhysiciansOfRecord",
    "RequestingPhysician",
    "AccessionNumber",
    "StudyID",
    "TimezoneOffsetFromUTC",
)


def prepare_sample(source: Path, destination: Path) -> None:
    dataset: FileDataset = dcmread(source)
    source_hash = sha256(source.read_bytes()).hexdigest()
    dataset.remove_private_tags()
    for keyword in REMOVED_TAGS:
        if keyword in dataset:
            del dataset[keyword]

    dataset.PatientIdentityRemoved = "YES"
    dataset.DeidentificationMethod = "Med Review Workbench demo header scrub v2"
    dataset.StudyInstanceUID = generate_uid(entropy_srcs=[source_hash, "study"])
    dataset.SeriesInstanceUID = generate_uid(entropy_srcs=[source_hash, "series"])
    dataset.SOPInstanceUID = generate_uid(entropy_srcs=[source_hash, "instance"])
    if dataset.file_meta is not None:
        dataset.file_meta.MediaStorageSOPInstanceUID = dataset.SOPInstanceUID
        if "SourceApplicationEntityTitle" in dataset.file_meta:
            dataset.file_meta.SourceApplicationEntityTitle = ""

    destination.parent.mkdir(parents=True, exist_ok=True)
    dataset.save_as(destination, enforce_file_format=True)
    print(f"prepared {destination.relative_to(PROJECT_ROOT)}")


def main() -> None:
    prepared_count = 0
    for source, destination in SAMPLES:
        if not source.exists():
            print(f"skipped missing optional source {source.relative_to(PROJECT_ROOT)}")
            continue
        prepare_sample(source, destination)
        prepared_count += 1

    if prepared_count == 0:
        raise FileNotFoundError(
            "no source DICOM samples found; follow README '样例数据获取与准备' first"
        )


if __name__ == "__main__":
    main()
