from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from app.config import get_settings


def sqlite_path() -> Path:
    path = get_settings().sqlite_path
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def backup_database(destination_dir: Path | None = None) -> Path:
    source = sqlite_path()
    if not source.exists():
        raise FileNotFoundError(f"SQLite database not found: {source}")

    destination_dir = destination_dir or (PROJECT_ROOT / "data" / "backups")
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    destination = destination_dir / f"{source.stem}_{timestamp}.db"

    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)

    sidecar_files = [source.with_suffix(source.suffix + "-wal"), source.with_suffix(source.suffix + "-shm")]
    for sidecar in sidecar_files:
        if sidecar.exists():
            shutil.copy2(sidecar, destination_dir / f"{destination.name}{sidecar.suffix}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a timestamped SQLite backup.")
    parser.add_argument("--dest", type=Path, default=None, help="Backup destination directory.")
    args = parser.parse_args()
    backup_path = backup_database(args.dest)
    print(f"backup_created={backup_path}")


if __name__ == "__main__":
    main()
