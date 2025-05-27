import sqlite3
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


class TelemetryDB:
    """SQLite-backed storage for telemetry events."""

    def __init__(
        self, path: str | Path = "telemetry.db", retention_days: int = 30
    ) -> None:
        self.path = Path(path)
        self.retention_days = retention_days
        self.conn = sqlite3.connect(self.path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tokens INTEGER,
                cost REAL,
                latency REAL,
                guardrail_hits INTEGER
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    def record(
        self, tokens: int, cost: float, latency: float, guardrail_hits: int
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO telemetry (timestamp, tokens, cost, latency, guardrail_hits) VALUES (?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), tokens, cost, latency, guardrail_hits),
        )
        self.conn.commit()
        self.purge_old()

    def purge_old(self) -> None:
        """Remove records older than ``retention_days``."""
        if self.retention_days <= 0:
            return
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        cur = self.conn.cursor()
        cur.execute("DELETE FROM telemetry WHERE timestamp < ?", (cutoff.isoformat(),))
        self.conn.commit()

    def fetch_all(self) -> List[Dict[str, object]]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT timestamp, tokens, cost, latency, guardrail_hits FROM telemetry ORDER BY id"
        ).fetchall()
        return [
            {
                "timestamp": ts,
                "tokens": tokens,
                "cost": cost,
                "latency": latency,
                "guardrail_hits": hits,
            }
            for ts, tokens, cost, latency, hits in rows
        ]

    def verify(self) -> bool:
        cur = self.conn.cursor()
        res = cur.execute("PRAGMA integrity_check").fetchone()
        return res[0] == "ok"

    def archive(self, path: Optional[str] = None) -> str:
        """Export all telemetry records to a gzipped JSON file."""
        data = self.fetch_all()
        if path is None:
            name = datetime.utcnow().isoformat().replace(":", "").replace(".", "")
            path = f"telemetry_{name}.json.gz"
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def close(self) -> None:
        self.conn.close()
