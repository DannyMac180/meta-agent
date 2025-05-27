import json
import gzip
import csv
from datetime import datetime, timedelta

from meta_agent.telemetry_db import TelemetryDB
from meta_agent.telemetry import TelemetryCollector


def test_record_and_fetch(tmp_path):
    db_path = tmp_path / "tele.db"
    db = TelemetryDB(db_path, retention_days=1)
    db.record(10, 0.1, 0.5, 0)
    rows = db.fetch_all()
    assert len(rows) == 1
    assert rows[0]["tokens"] == 10
    assert db.verify()
    db.close()


def test_purge_old(tmp_path):
    db_path = tmp_path / "tele.db"
    db = TelemetryDB(db_path, retention_days=1)
    db.record(1, 0.01, 0.1, 0)
    # update timestamp to old date
    old_ts = "2000-01-01T00:00:00"
    db.conn.execute("UPDATE telemetry SET timestamp=?", (old_ts,))
    db.conn.commit()
    db.purge_old()
    assert db.fetch_all() == []
    db.close()


def test_archive(tmp_path):
    db = TelemetryDB(tmp_path / "tele.db")
    db.record(5, 0.02, 0.3, 1)
    archive_path = db.archive(tmp_path / "out.gz")
    with gzip.open(archive_path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["guardrail_hits"] == 1
    db.close()


def test_export_json_and_csv(tmp_path):
    db_path = tmp_path / "tele.db"
    db = TelemetryDB(db_path)
    # Create two records with known timestamps
    now = datetime.utcnow()
    db.record(5, 0.02, 0.3, 1)
    db.conn.execute(
        "UPDATE telemetry SET timestamp=? WHERE id=1",
        ((now - timedelta(days=1)).isoformat(),),
    )
    db.record(10, 0.05, 0.6, 2)

    json_path = tmp_path / "export.json"
    csv_path = tmp_path / "export.csv"

    db.export_json(json_path, start=now.isoformat())
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["tokens"] == 10

    db.export_csv(csv_path, metrics=["tokens"], start=now.isoformat())
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert rows[0] == ["timestamp", "tokens"]
    assert len(rows) == 2
    db.close()


def test_collector_with_db(tmp_path):
    db = TelemetryDB(tmp_path / "tele.db")
    collector = TelemetryCollector(db=db, include_sensitive=False)
    collector.start_timer()
    collector.stop_timer()
    line = collector.summary_line()
    assert "<redacted>" in line
    assert db.fetch_all()
    db.close()
