from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from app.db import ensure_database
from app.services.jobs import run_due_jobs


async def run_worker(limit: int, poll_seconds: int, once: bool) -> None:
    ensure_database()
    while True:
        result = await run_due_jobs(limit=limit)
        print(f"processed={result['count']} jobs")
        for item in result["processed"]:
            print(item)
        if once:
            break
        time.sleep(max(1, poll_seconds))


def main() -> None:
    parser = argparse.ArgumentParser(description="Process queued ExportPilot AI jobs.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum jobs to process per poll.")
    parser.add_argument("--poll-seconds", type=int, default=30, help="Seconds between polling cycles.")
    parser.add_argument("--once", action="store_true", help="Run one polling cycle and exit.")
    args = parser.parse_args()
    asyncio.run(run_worker(args.limit, args.poll_seconds, args.once))


if __name__ == "__main__":
    main()
