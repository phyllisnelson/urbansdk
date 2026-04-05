from sqlalchemy import func, select

from app.database import Link, SpeedRecord


class TestLoadSpeedRecords:
    def test_speed_records_are_inserted(self, real_data, db, expected_speed_record_count):
        count = db.execute(select(func.count()).select_from(SpeedRecord)).scalar()
        assert count == expected_speed_record_count

    def test_speed_records_have_positive_speed(self, real_data, db):
        non_positive = db.execute(
            select(func.count()).select_from(SpeedRecord).where(SpeedRecord.speed <= 0)
        ).scalar()
        assert non_positive == 0

    def test_speed_records_have_timestamps(self, real_data, db):
        null_ts = db.execute(
            select(func.count())
            .select_from(SpeedRecord)
            .where(SpeedRecord.timestamp == None)  # noqa: E711
        ).scalar()
        assert null_ts == 0

    def test_speed_records_are_linked(self, real_data, db):
        """Every speed record references a link that exists."""
        orphaned = db.execute(
            select(func.count())
            .select_from(SpeedRecord)
            .outerjoin(Link, SpeedRecord.link_id == Link.link_id)
            .where(Link.link_id == None)  # noqa: E711
        ).scalar()
        assert orphaned == 0
