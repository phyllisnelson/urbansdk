import pytest

from tests.conftest import MON_AM, MON_PM, TUE_AM
from tests.factories import LinkFactory, SpeedRecordFactory


class TestGetAggregates:
    def test_returns_average_speed_per_link(self, client, db):
        link = LinkFactory(road_name="Main St")
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=30.0)
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=50.0)
        db.flush()

        resp = client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak"})

        assert resp.status_code == 200
        data = resp.json()
        match = next(r for r in data if r["link_id"] == link.link_id)
        assert match["average_speed"] == pytest.approx(40.0, abs=0.1)
        assert match["road_name"] == "Main St"
        assert match["length_m"] > 0
        assert match["geometry"]["type"] == "LineString"

    def test_excludes_wrong_period(self, client, db):
        link = LinkFactory()
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_PM, speed=25.0)
        db.flush()

        resp = client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak"})

        assert resp.status_code == 200
        assert link.link_id not in [r["link_id"] for r in resp.json()]

    def test_excludes_wrong_day(self, client, db):
        link = LinkFactory()
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=TUE_AM, speed=25.0)
        db.flush()

        resp = client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak"})

        assert resp.status_code == 200
        assert link.link_id not in [r["link_id"] for r in resp.json()]

    def test_accepts_period_by_id(self, client, db):
        link = LinkFactory()
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=35.0)
        db.flush()

        resp = client.get("/aggregates/", params={"day": "Monday", "period": "3"})  # 3 = AM Peak

        assert resp.status_code == 200
        assert link.link_id in [r["link_id"] for r in resp.json()]

    def test_invalid_period_returns_422(self, client):
        resp = client.get("/aggregates/", params={"day": "Monday", "period": "Rush Hour"})
        assert resp.status_code == 422

    def test_invalid_day_returns_422(self, client):
        resp = client.get("/aggregates/", params={"day": "Funday", "period": "AM Peak"})
        assert resp.status_code == 422

    def test_pagination_limit(self, client, db):
        for _ in range(5):
            link = LinkFactory()
            SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=30.0)
        db.flush()

        resp = client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak", "limit": 2})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_pagination_offset(self, client, db):
        for _ in range(3):
            link = LinkFactory()
            SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=30.0)
        db.flush()

        all_ids = [
            r["link_id"]
            for r in client.get(
                "/aggregates/", params={"day": "Monday", "period": "AM Peak"}
            ).json()
        ]
        resp = client.get(
            "/aggregates/", params={"day": "Monday", "period": "AM Peak", "limit": 2, "offset": 1}
        )
        assert resp.status_code == 200
        assert [r["link_id"] for r in resp.json()] == all_ids[1:3]


class TestGetLinkAggregate:
    def test_returns_link_detail(self, client, db):
        link = LinkFactory(road_name="Oak Ave")
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=60.0)
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=40.0)
        db.flush()

        resp = client.get(
            f"/aggregates/{link.link_id}",
            params={"day": "Monday", "period": "AM Peak"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["link_id"] == link.link_id
        assert data["road_name"] == "Oak Ave"
        assert data["average_speed"] == pytest.approx(50.0, abs=0.1)
        assert data["record_count"] == 2
        assert data["length_m"] > 0
        assert data["geometry"]["type"] == "LineString"

    def test_missing_link_returns_404(self, client):
        resp = client.get(
            "/aggregates/does_not_exist",
            params={"day": "Monday", "period": "AM Peak"},
        )
        assert resp.status_code == 404

    def test_no_records_in_period_returns_404(self, client, db):
        link = LinkFactory()
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_PM, speed=30.0)
        db.flush()

        resp = client.get(
            f"/aggregates/{link.link_id}",
            params={"day": "Monday", "period": "AM Peak"},
        )

        assert resp.status_code == 404

    def test_invalid_period_returns_422(self, client, db):
        link = LinkFactory()
        db.flush()

        resp = client.get(
            f"/aggregates/{link.link_id}",
            params={"day": "Monday", "period": "NotAPeriod"},
        )

        assert resp.status_code == 422

    def test_invalid_day_returns_422(self, client, db):
        link = LinkFactory()
        db.flush()

        resp = client.get(
            f"/aggregates/{link.link_id}",
            params={"day": "NotADay", "period": "AM Peak"},
        )

        assert resp.status_code == 422
