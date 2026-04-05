from typing import Any

from pydantic import BaseModel


class SlowLink(BaseModel):
    link_id: str
    road_name: str | None
    average_speed: float
    slow_days: int
    geometry: dict[str, Any]
