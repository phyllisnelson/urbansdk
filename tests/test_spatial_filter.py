from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from tests.conftest import MON_AM
from tests.factories import LinkFactory, SpeedRecordFactory

JACKSONVILLE_BBOX = [-81.80, 30.10, -81.60, 30.40]


class TestSpatialFilter:
    def test_returns_links_inside_bbox(self, client, db):
        link = LinkFactory(
            geometry=from_shape(LineString([(-81.70, 30.25), (-81.69, 30.25)]), srid=4326)
        )
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=45.0)
        db.flush()

        resp = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Monday", "period": "AM Peak", "bbox": JACKSONVILLE_BBOX},
        )

        assert resp.status_code == 200
        assert link.link_id in [r["link_id"] for r in resp.json()]

    def test_excludes_links_outside_bbox(self, client, db):
        link = LinkFactory(geometry=from_shape(LineString([(10.5, 50.5), (10.6, 50.5)]), srid=4326))
        SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=45.0)
        db.flush()

        resp = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Monday", "period": "AM Peak", "bbox": JACKSONVILLE_BBOX},
        )

        assert resp.status_code == 200
        assert link.link_id not in [r["link_id"] for r in resp.json()]

    def test_invalid_bbox_returns_422(self, client):
        resp = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Monday", "period": "AM Peak", "bbox": [-81.8, 30.1]},
        )
        assert resp.status_code == 422

    def test_invalid_period_returns_422(self, client):
        resp = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Monday", "period": "Rush Hour", "bbox": JACKSONVILLE_BBOX},
        )
        assert resp.status_code == 422

    def test_pagination_limit(self, client, db):
        for lon_offset in [0.0, 0.01, 0.02, 0.03]:
            link = LinkFactory(
                geometry=from_shape(
                    LineString([(-81.70 + lon_offset, 30.25), (-81.69 + lon_offset, 30.25)]),
                    srid=4326,
                )
            )
            SpeedRecordFactory(link=link, link_id=link.link_id, timestamp=MON_AM, speed=45.0)
        db.flush()

        resp = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Monday", "period": "AM Peak", "bbox": JACKSONVILLE_BBOX},
            params={"limit": 2},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2
