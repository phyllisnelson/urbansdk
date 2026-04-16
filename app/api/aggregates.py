import json

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.functions import ST_AsGeoJSON, ST_Intersects, ST_Length, ST_MakeEnvelope
from sqlalchemy import Time, cast, func, select
from sqlalchemy.orm import Session

from app.database import Link, SpeedRecord, get_db
from app.enums import DayEnum, PeriodEnum
from app.schemas import LinkAggregate, LinkDetail, SpatialFilterRequest

router = APIRouter(prefix="/aggregates", tags=["aggregates"])


def _time_filter(dow: int, start, end):
    """Build SQLAlchemy filter conditions for day-of-week and time window."""

    return [
        SpeedRecord.day_of_week == dow,
        cast(SpeedRecord.timestamp, Time) >= start,
        cast(SpeedRecord.timestamp, Time) <= end,
    ]


@router.get("/", response_model=list[LinkAggregate])
def get_aggregates(
    day: DayEnum,
    period: PeriodEnum,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Aggregated average speed per link for the given day and time period."""

    start, end = period.times
    dow = day.iso_weekday

    # Join links with their speed records filtered by day and time, then aggregate.
    rows = db.execute(
        select(
            Link.link_id,
            Link.road_name,
            func.avg(SpeedRecord.speed).label("average_speed"),
            ST_Length(func.ST_Transform(Link.geometry, 4326), True).label("length_m"),
            ST_AsGeoJSON(Link.geometry).label("geometry"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(*_time_filter(dow, start, end))
        .group_by(Link.link_id, Link.road_name, Link.geometry)
        .order_by(Link.link_id)
        .limit(limit)
        .offset(offset)
    ).all()

    return [
        LinkAggregate(
            link_id=r.link_id,
            road_name=r.road_name,
            average_speed=round(r.average_speed, 2),
            length_m=round(r.length_m, 1),
            geometry=json.loads(r.geometry),
        )
        for r in rows
    ]


@router.get("/{link_id}", response_model=LinkDetail)
def get_link_aggregate(
    link_id: str,
    day: DayEnum,
    period: PeriodEnum,
    db: Session = Depends(get_db),
):
    """Speed and metadata for a single road segment."""

    start, end = period.times
    dow = day.iso_weekday

    # Query for the link with aggregated average speed and record count, filtered by day and time.
    row = db.execute(
        select(
            Link.link_id,
            Link.road_name,
            func.avg(SpeedRecord.speed).label("average_speed"),
            func.count(SpeedRecord.id).label("record_count"),
            ST_Length(func.ST_Transform(Link.geometry, 4326), True).label("length_m"),
            ST_AsGeoJSON(Link.geometry).label("geometry"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(Link.link_id == link_id, *_time_filter(dow, start, end))
        .group_by(Link.link_id, Link.road_name, Link.geometry)
    ).one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found")

    return LinkDetail(
        link_id=row.link_id,
        road_name=row.road_name,
        average_speed=round(row.average_speed, 2),
        record_count=row.record_count,
        length_m=round(row.length_m, 1),
        geometry=json.loads(row.geometry),
    )


@router.post("/spatial_filter/", response_model=list[LinkAggregate])
def spatial_filter(
    body: SpatialFilterRequest,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Road segments intersecting the bounding box for the given day and period."""

    start, end = body.period.times
    dow = body.day.iso_weekday
    min_lon, min_lat, max_lon, max_lat = body.bbox

    # ST_MakeEnvelope creates a rectangular polygon from the bounding box coordinates,
    # which we can use to filter links by spatial intersection.
    envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

    # Join links with their speed records filtered by day, time, and spatial intersection,
    # then aggregate.
    rows = db.execute(
        select(
            Link.link_id,
            Link.road_name,
            func.avg(SpeedRecord.speed).label("average_speed"),
            ST_Length(func.ST_Transform(Link.geometry, 4326), True).label("length_m"),
            ST_AsGeoJSON(Link.geometry).label("geometry"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(
            ST_Intersects(Link.geometry, envelope),
            *_time_filter(dow, start, end),
        )
        .group_by(Link.link_id, Link.road_name, Link.geometry)
        .order_by(Link.link_id)
        .limit(limit)
        .offset(offset)
    ).all()

    return [
        LinkAggregate(
            link_id=r.link_id,
            road_name=r.road_name,
            average_speed=round(r.average_speed, 2),
            length_m=round(r.length_m, 1),
            geometry=json.loads(r.geometry),
        )
        for r in rows
    ]
