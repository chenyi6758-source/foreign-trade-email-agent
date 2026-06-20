from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from app.db import ensure_database
from app.services.jobs import create_job, enqueue_due_follow_up_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Enqueue scheduled ExportPilot AI jobs.")
    parser.add_argument("--follow-up-limit", type=int, default=50, help="Maximum due follow-ups to enqueue.")
    parser.add_argument("--intel", action="store_true", help="Also enqueue one RSS/intel refresh job.")
    args = parser.parse_args()

    ensure_database()
    follow_up_jobs = enqueue_due_follow_up_jobs(limit=args.follow_up_limit)
    print(f"queued_follow_up_jobs={len(follow_up_jobs)}")

    if args.intel:
        job = create_job("refresh_intel", {"source": "scheduler"})
        print(f"queued_intel_job={job['id']}")


if __name__ == "__main__":
    main()
