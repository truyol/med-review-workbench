r"""Seed the local development database with repository-safe sample data.

Run from ``apps/api`` after applying migrations:
    .\.venv\Scripts\python.exe ..\..\scripts\seed-demo.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sys.path.insert(0, str(ROOT / "apps" / "api"))
    from app.ops.seed_demo import seed_demo

    project_id, case_id = seed_demo(ROOT / "sample-data")
    print(f"Demo project ready: {project_id} / {case_id}")


if __name__ == "__main__":
    main()
