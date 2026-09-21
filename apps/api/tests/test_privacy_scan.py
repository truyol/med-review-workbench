from app.ops.privacy_scan import scan_lines


def test_privacy_scan_accepts_structured_access_log() -> None:
    count, findings = scan_lines(
        ['{"request_id":"safe","path":"/api/v1/assets","status":201}'],
    )
    assert count == 1
    assert findings == []


def test_privacy_scan_flags_identity_keys_without_echoing_values() -> None:
    count, findings = scan_lines(
        ["safe line", "PatientName must never appear", "patient_id=hidden"],
    )
    assert count == 3
    assert [(item.line_number, item.rule) for item in findings] == [
        (2, "dicom_identity_keyword"),
        (3, "normalized_identity_key"),
    ]
