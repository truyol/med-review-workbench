from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

RULES = {
    "dicom_identity_keyword": re.compile(r"\bPatient(?:Name|ID)\b", re.IGNORECASE),
    "normalized_identity_key": re.compile(r"\bpatient_(?:name|id)\b", re.IGNORECASE),
    "dicom_identity_tag": re.compile(r"\(0010,\s*00(?:10|20)\)", re.IGNORECASE),
    "multipart_filename": re.compile(r"content-disposition:.*filename=", re.IGNORECASE),
}


@dataclass(frozen=True)
class Finding:
    line_number: int
    rule: str


def scan_lines(lines: Iterable[str]) -> tuple[int, list[Finding]]:
    findings: list[Finding] = []
    count = 0
    for count, line in enumerate(lines, start=1):
        for rule, pattern in RULES.items():
            if pattern.search(line):
                findings.append(Finding(line_number=count, rule=rule))
    return count, findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan runtime logs for forbidden privacy fields.")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()

    if args.paths:
        lines: list[str] = []
        for path in args.paths:
            lines.extend(path.read_text(encoding="utf-8", errors="replace").splitlines())
    else:
        lines = sys.stdin.read().splitlines()

    count, findings = scan_lines(lines)
    if findings:
        for finding in findings:
            print(f"Privacy finding: line={finding.line_number} rule={finding.rule}")
        raise SystemExit(1)
    print(f"Privacy scan passed: scanned_lines={count} findings=0")


if __name__ == "__main__":
    main()
