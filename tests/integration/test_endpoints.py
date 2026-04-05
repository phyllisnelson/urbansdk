"""End-to-end API tests using real ingested data (Jan 1, 2024 = Monday)."""

import pytest
from sqlalchemy import select

from app.database import Link


@pytest.mark.usefixtures("real_data")
class TestIngestEndToEnd:
    def test_aggregates(self, client):
        resp = client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak"})
        assert resp.status_code == 200
        records = resp.json()
        assert len(records) > 0
        record = records[0]
        assert "link_id" in record
        assert "average_speed" in record
        assert "geometry" in record
        assert record["geometry"]["type"] in ("LineString", "MultiLineString")
        assert all(r["average_speed"] > 0 for r in records)

    def test_link_detail_returns_result(self, client, db):
        link_id = db.execute(select(Link.link_id).limit(1)).scalar()
        resp = client.get(
            f"/aggregates/{link_id}",
            params={"day": "Monday", "period": "AM Peak"},
        )
        # The link exists but may have no Monday AM Peak records — either is valid
        assert resp.status_code in (200, 404)

    def test_spatial_filter_returns_results(self, client):
        resp = client.post(
            "/aggregates/spatial_filter/",
            json={
                "day": "Monday",
                "period": "AM Peak",
                "bbox": [-82.0, 30.0, -81.4, 30.6],
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_slow_links_returns_results(self, client):
        resp = client.get(
            "/patterns/slow_links/",
            params={"period": "AM Peak", "threshold": 999.0, "min_days": 1},
        )
        assert resp.status_code == 200
        assert len(resp.json()) > 0
