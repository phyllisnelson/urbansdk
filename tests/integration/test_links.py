from sqlalchemy import func, select

from app.database import Link


class TestLoadLinks:
    def test_links_are_inserted(self, real_data, db, expected_link_count):
        count = db.execute(select(func.count()).select_from(Link)).scalar()
        assert count == expected_link_count

    def test_links_have_link_id(self, real_data, db):
        null_ids = db.execute(
            select(func.count()).select_from(Link).where(Link.link_id == None)  # noqa: E711
        ).scalar()
        assert null_ids == 0

    def test_links_have_geometry(self, real_data, db):
        null_geom = db.execute(
            select(func.count()).select_from(Link).where(Link.geometry == None)  # noqa: E711
        ).scalar()
        assert null_geom == 0
