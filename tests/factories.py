from datetime import datetime, timezone

import factory
from factory.alchemy import SQLAlchemyModelFactory
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from app.database import Link, SpeedRecord

# Jacksonville, FL area bounding box
_BASE_LON = -81.65
_BASE_LAT = 30.33
_DEFAULT_MON_AM = datetime(2024, 1, 1, 8, 30, tzinfo=timezone.utc)


def _make_linestring(offset: float = 0.0):
    """Return a simple east-west LineString near Jacksonville."""
    return from_shape(
        LineString(
            [
                (_BASE_LON + offset, _BASE_LAT + offset),
                (_BASE_LON + offset + 0.01, _BASE_LAT + offset),
            ]
        ),
        srid=4326,
    )


class LinkFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Link
        sqlalchemy_session = None  # set per test via session fixture
        sqlalchemy_session_persistence = "flush"

    link_id = factory.Sequence(lambda n: f"0_test_{n:04d}")
    road_name = factory.Sequence(lambda n: f"Test Road {n}")
    geometry = factory.LazyAttribute(lambda o: _make_linestring())


class SpeedRecordFactory(SQLAlchemyModelFactory):
    class Meta:
        model = SpeedRecord
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"

    # Default: most recent Monday at 08:30 UTC — falls in AM Peak (07:00-09:59)
    link = factory.SubFactory(LinkFactory)
    link_id = factory.LazyAttribute(lambda o: o.link.link_id)
    timestamp = factory.LazyFunction(lambda: _DEFAULT_MON_AM)
    day_of_week = factory.LazyAttribute(lambda o: o.timestamp.isoweekday())
    speed = factory.Sequence(lambda n: 40.0 + (n % 20))
