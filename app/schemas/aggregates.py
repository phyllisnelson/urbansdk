from typing import Annotated, Any

from pydantic import BaseModel, Field

from app.enums import DayEnum, PeriodEnum


class LinkAggregate(BaseModel):
    link_id: str
    road_name: str | None
    average_speed: float = Field(ge=0)
    length_m: float = Field(ge=0)
    geometry: dict[str, Any]  # GeoJSON geometry


class LinkDetail(BaseModel):
    link_id: str
    road_name: str | None
    average_speed: float = Field(ge=0)
    record_count: int = Field(ge=0)
    length_m: float = Field(ge=0)
    geometry: dict[str, Any]


class SpatialFilterRequest(BaseModel):
    day: DayEnum
    period: PeriodEnum
    bbox: Annotated[list[float], Field(min_length=4, max_length=4)]
