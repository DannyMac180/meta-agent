import sqlite3
import json
import csv
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Iterable


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

    def _query(
        self,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
    ) -> List[Dict[str, object]]:
        """Fetch records optionally filtered by ``start``/``end`` timestamps."""
        conds: List[str] = []
        params: List[str] = []
        if start is not None:
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            conds.append("timestamp >= ?")
            params.append(start.isoformat())
        if end is not None:
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            conds.append("timestamp <= ?")
            params.append(end.isoformat())

        query = "SELECT timestamp, tokens, cost, latency, guardrail_hits FROM telemetry"
        if conds:
            query += " WHERE " + " AND ".join(conds)
        query += " ORDER BY id"

        cur = self.conn.cursor()
        rows = cur.execute(query, params).fetchall()
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

    def fetch_all(
        self,
        *,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        metrics: Iterable[str] | None = None,
    ) -> List[Dict[str, object]]:
        data = self._query(start=start, end=end)
        if metrics is not None:
            allowed = set(metrics)
            for row in data:
                for key in list(row.keys()):
                    if key != "timestamp" and key not in allowed:
                        del row[key]
        return data

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

    # ------------------------------------------------------------------
    def export_json(
        self,
        path: str | Path,
        *,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        metrics: Iterable[str] | None = None,
        compress: bool | None = None,
    ) -> str:
        """Export telemetry to a JSON file with optional compression."""
        compress = compress or str(path).endswith((".gz", ".gzip"))
        data = self.fetch_all(start=start, end=end, metrics=metrics)
        open_fn = gzip.open if compress else open
        mode = "wt"
        with open_fn(path, mode, encoding="utf-8") as f:
            json.dump(data, f)
        return str(path)

    def export_csv(
        self,
        path: str | Path,
        *,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        metrics: Iterable[str] | None = None,
        compress: bool | None = None,
    ) -> str:
        """Export telemetry to a CSV file with optional compression."""
        compress = compress or str(path).endswith((".gz", ".gzip"))
        data = self.fetch_all(start=start, end=end, metrics=metrics)
        if not metrics:
            metrics = ["tokens", "cost", "latency", "guardrail_hits"]
        header = ["timestamp", *metrics]
        open_fn = gzip.open if compress else open
        mode = "wt"
        with open_fn(path, mode, encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in data:
                writer.writerow([row.get(key, "") for key in header])
        return str(path)

    def export(
        self,
        path: str | Path,
        *,
        fmt: str = "json",
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        metrics: Iterable[str] | None = None,
        compress: bool | None = None,
    ) -> str:
        """Export telemetry data in ``fmt`` ('json' or 'csv')."""
        fmt = fmt.lower()
        if fmt == "json":
            return self.export_json(
                path,
                start=start,
                end=end,
                metrics=metrics,
                compress=compress,
            )
        if fmt == "csv":
            return self.export_csv(
                path,
                start=start,
                end=end,
                metrics=metrics,
                compress=compress,
            )
        if fmt == "pdf":
            raise NotImplementedError("PDF export not implemented")
        raise ValueError(f"Unknown format: {fmt}")

    def close(self) -> None:
        self.conn.close()
