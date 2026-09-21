"""Scan logs from files or stdin without echoing sensitive values."""

import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "apps" / "api"))
    from app.ops.privacy_scan import main as scan_main

    scan_main()


if __name__ == "__main__":
    main()
