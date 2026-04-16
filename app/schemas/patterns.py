from typing import Any

from pydantic import BaseModel, Field


class SlowLink(BaseModel):
    link_id: str
    road_name: str | None
    average_speed: float = Field(ge=0)
    slow_days: int = Field(ge=0)
    geometry: dict[str, Any]
