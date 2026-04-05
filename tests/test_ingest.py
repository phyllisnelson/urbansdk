import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app import ingest


class _GeomObj:
    __geo_interface__ = {
        "type": "LineString",
        "coordinates": [[-81.7, 30.2], [-81.6, 30.3]],
    }


def _make_db_with_cursor():
    cursor = MagicMock()
    db = MagicMock()
    db.connection.return_value.connection.dbapi_connection.cursor.return_value = cursor
    return db, cursor


def test_copy_speed_records_uses_copy_expert_and_closes_cursor():
    df = pd.DataFrame(
        {
            "link_id": ["A1"],
            "timestamp": [pd.Timestamp("2024-01-01T08:00:00Z")],
            "day_of_week": [1],
            "speed": [35.0],
        }
    )
    db, cursor = _make_db_with_cursor()

    ingest._copy_speed_records(df, db)

    cursor.copy_expert.assert_called_once()
    query, buffer = cursor.copy_expert.call_args.args
    assert "COPY speed_records" in query
    assert isinstance(buffer, io.StringIO)
    cursor.close.assert_called_once()


def test_load_links_raises_when_required_columns_missing():
    df = pd.DataFrame({"road_name": ["Main St"]})
    db, _ = _make_db_with_cursor()

    with pytest.raises(RuntimeError, match="Cannot identify id/geometry"):
        ingest.Ingester().load_links(df, db)


def test_load_links_stages_and_upserts_rows():
    geojson_text = json.dumps({"type": "LineString", "coordinates": [[-81.8, 30.1], [-81.7, 30.2]]})
    wkt_text = "LINESTRING (-81.8 30.1, -81.7 30.2)"
    df = pd.DataFrame(
        {
            "ID": [101, 102, 103],
            "Road Name": ["Main", None, "Elm"],
            "WKT": [geojson_text, wkt_text, _GeomObj()],
        }
    )
    db, cursor = _make_db_with_cursor()

    ingest.Ingester().load_links(df, db)

    assert cursor.execute.call_count == 2
    assert cursor.copy_expert.call_count == 1
    db.commit.assert_called_once()
    cursor.close.assert_called_once()


def test_load_speed_records_raises_when_columns_missing():
    df = pd.DataFrame({"id": ["A1"], "speed": [22.0]})
    db, _ = _make_db_with_cursor()

    with pytest.raises(RuntimeError, match="Cannot identify required columns"):
        ingest.Ingester().load_speed_records(df, db)


def test_load_speed_records_normalizes_and_commits(monkeypatch):
    captured = {}

    def fake_copy(df, _db):
        captured["df"] = df.copy()

    monkeypatch.setattr(ingest, "_copy_speed_records", fake_copy)
    df = pd.DataFrame(
        {
            "ID": [1, 2],
            "Timestamp": ["2024-01-01T08:00:00Z", "2024-01-02T08:00:00Z"],
            "avg_speed": [20.5, 22.0],
        }
    )
    db, _ = _make_db_with_cursor()

    ingest.Ingester().load_speed_records(df, db)

    out = captured["df"]
    assert list(out.columns) == ["link_id", "timestamp", "day_of_week", "speed"]
    assert out["link_id"].tolist() == ["1", "2"]
    assert out["day_of_week"].tolist() == [1, 2]
    db.commit.assert_called_once()


def test_ingester_properties_read_from_settings(monkeypatch):
    monkeypatch.setattr(ingest.settings, "data_dir", Path("/tmp"))
    monkeypatch.setattr(ingest.settings, "link_info_filename", "links.parquet.gz")
    monkeypatch.setattr(ingest.settings, "speed_data_filename", "speed.parquet.gz")
    i = ingest.Ingester()

    assert i.link_info_file == Path("/tmp/links.parquet.gz")
    assert i.speed_data_file == Path("/tmp/speed.parquet.gz")


def test_run_reads_files_loads_and_closes_db(monkeypatch):
    db = MagicMock()
    link_df = pd.DataFrame({"id": [1], "wkt": ["LINESTRING (0 0, 1 1)"]})
    speed_df = pd.DataFrame({"id": [1], "timestamp": ["2024-01-01T08:00:00Z"], "speed": [20.0]})

    monkeypatch.setattr(ingest, "SessionLocal", lambda: db)
    monkeypatch.setattr(ingest.settings, "data_dir", Path("/tmp"))
    monkeypatch.setattr(ingest.settings, "link_info_filename", "links.parquet.gz")
    monkeypatch.setattr(ingest.settings, "speed_data_filename", "speed.parquet.gz")

    def fake_read_parquet(path):
        if path == Path("/tmp/links.parquet.gz"):
            return link_df
        if path == Path("/tmp/speed.parquet.gz"):
            return speed_df
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(ingest.pd, "read_parquet", fake_read_parquet)

    called = {"links": 0, "speed": 0}

    def fake_load_links(self, df, got_db):
        called["links"] += 1
        assert got_db is db
        assert df.equals(link_df)

    def fake_load_speed(self, df, got_db):
        called["speed"] += 1
        assert got_db is db
        assert df.equals(speed_df)

    monkeypatch.setattr(ingest.Ingester, "load_links", fake_load_links)
    monkeypatch.setattr(ingest.Ingester, "load_speed_records", fake_load_speed)

    ingest.Ingester().run()

    assert called == {"links": 1, "speed": 1}
    db.close.assert_called_once()
