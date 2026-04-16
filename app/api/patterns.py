import json

from fastapi import APIRouter, Depends, Query
from geoalchemy2.functions import ST_AsGeoJSON
from sqlalchemy import Time, cast, func, select
from sqlalchemy.orm import Session

from app.database import Link, SpeedRecord, get_db
from app.enums import PeriodEnum
from app.schemas import SlowLink

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("/slow_links/", response_model=list[SlowLink])
def slow_links(
    period: PeriodEnum,
    threshold: float = Query(..., ge=0),
    min_days: int = Query(3, ge=1, le=7),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Returns road segments with average speeds below `threshold`
    for at least `min_days` days in a week.

    - `threshold` — speed in mph below which a link is considered slow
    - `min_days` — minimum number of days (1–7) the link must be slow to be included
    """

    start, end = period.times

    # Per-day average speed per link — group by day_of_week so the composite
    # index ix_speed_records_dow_link is used for the time-window scan.
    per_day = (
        select(
            SpeedRecord.link_id,
            SpeedRecord.day_of_week,
            func.avg(SpeedRecord.speed).label("day_avg"),
        )
        .where(
            cast(SpeedRecord.timestamp, Time) >= start,
            cast(SpeedRecord.timestamp, Time) <= end,
        )
        .group_by(SpeedRecord.link_id, SpeedRecord.day_of_week)
        .subquery()
    )

    # Count days where the link was slow (below threshold)
    slow_days_sq = (
        select(
            per_day.c.link_id,
            func.count().label("slow_days"),
            func.avg(per_day.c.day_avg).label("average_speed"),
        )
        .where(per_day.c.day_avg < threshold)
        .group_by(per_day.c.link_id)
        .having(func.count() >= min_days)
        .subquery()
    )

    rows = db.execute(
        select(
            Link.link_id,
            Link.road_name,
            slow_days_sq.c.average_speed,
            slow_days_sq.c.slow_days,
            ST_AsGeoJSON(Link.geometry).label("geometry"),
        )
        .join(slow_days_sq, slow_days_sq.c.link_id == Link.link_id)
        .order_by(Link.link_id)
        .limit(limit)
        .offset(offset)
    ).all()

    return [
        SlowLink(
            link_id=r.link_id,
            road_name=r.road_name,
            average_speed=round(r.average_speed, 2),
            slow_days=r.slow_days,
            geometry=json.loads(r.geometry),
        )
        for r in rows
    ]
