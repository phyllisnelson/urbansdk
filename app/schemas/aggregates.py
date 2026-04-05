from typing import Any

from pydantic import BaseModel


class LinkAggregate(BaseModel):
    link_id: str
    road_name: str | None
    average_speed: float
    length_m: float
    geometry: dict[str, Any]  # GeoJSON geometry


class LinkDetail(BaseModel):
    link_id: str
    road_name: str | None
    average_speed: float
    record_count: int
    length_m: float
    geometry: dict[str, Any]


class SpatialFilterRequest(BaseModel):
    day: str
    period: str
    bbox: list[float]  # [min_lon, min_lat, max_lon, max_lat]
