"""
scripts/migrate_db.py — Jalankan migrasi skema & seeding faktual pada Database Operasional SignBridge.
Mendukung PostgreSQL 16 (DATABASE_URL) dan fallback lokal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.database import DatabaseManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrasi & Seeding Database Operasional SignBridge.")
    parser.add_argument("--url", type=str, default=None, help="Override DATABASE_URL")
    parser.add_argument("--no-seed", action="store_true", help="Hanya buat tabel tanpa seed data")
    args = parser.parse_args()

    db = DatabaseManager(database_url=args.url)
    ok = db.init_db(seed=not args.no_seed)
    summary = db.get_status_summary()
    print(json.dumps({"migration_ok": ok, **summary}, indent=2))


if __name__ == "__main__":
    main()

