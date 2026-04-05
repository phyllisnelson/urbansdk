from tests.conftest import MON_AM, THU_AM, TUE_AM, WED_AM
from tests.factories import LinkFactory, SpeedRecordFactory


class TestSlowLinks:
    def test_detects_consistently_slow_links(self, client, db):
        slow_link = LinkFactory()
        for ts in (MON_AM, TUE_AM, WED_AM):
            SpeedRecordFactory(link=slow_link, link_id=slow_link.link_id, timestamp=ts, speed=10.0)

        fast_link = LinkFactory()
        SpeedRecordFactory(link=fast_link, link_id=fast_link.link_id, timestamp=MON_AM, speed=60.0)
        db.flush()

        resp = client.get(
            "/patterns/slow_links/",
            params={"period": "AM Peak", "threshold": 20.0, "min_days": 3},
        )

        assert resp.status_code == 200
        ids = [r["link_id"] for r in resp.json()]
        assert slow_link.link_id in ids
        assert fast_link.link_id not in ids

    def test_excludes_link_below_min_days(self, client, db):
        link = LinkFactory()
        for ts in (MON_AM, TUE_AM):
            SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=ts, speed=5.0)
        db.flush()

        resp = client.get(
            "/patterns/slow_links/",
            params={"period": "AM Peak", "threshold": 20.0, "min_days": 3},
        )

        assert resp.status_code == 200
        assert link.link_id not in [r["link_id"] for r in resp.json()]

    def test_pagination_limit(self, client, db):
        for _ in range(4):
            link = LinkFactory()
            for ts in (MON_AM, TUE_AM, WED_AM):
                SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=ts, speed=5.0)
        db.flush()

        resp = client.get(
            "/patterns/slow_links/",
            params={"period": "AM Peak", "threshold": 20.0, "min_days": 3, "limit": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_response_includes_slow_days_count(self, client, db):
        link = LinkFactory()
        for ts in (MON_AM, TUE_AM, WED_AM, THU_AM):
            SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=ts, speed=5.0)
        db.flush()

        resp = client.get(
            "/patterns/slow_links/",
            params={"period": "AM Peak", "threshold": 20.0, "min_days": 3},
        )

        assert resp.status_code == 200
        match = next(r for r in resp.json() if r["link_id"] == link.link_id)
        assert match["slow_days"] == 4

    def test_invalid_period_returns_422(self, client):
        resp = client.get(
            "/patterns/slow_links/",
            params={"period": "Rush Hour", "threshold": 20.0, "min_days": 3},
        )
        assert resp.status_code == 422
