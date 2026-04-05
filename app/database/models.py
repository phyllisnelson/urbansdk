from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Link(Base):
    __tablename__ = "links"

    link_id: Mapped[str] = mapped_column(String, primary_key=True)
    road_name: Mapped[str | None] = mapped_column(String, nullable=True)
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False
    )

    speed_records: Mapped[list["SpeedRecord"]] = relationship(back_populates="link", lazy="dynamic")


class SpeedRecord(Base):
    __tablename__ = "speed_records"
    __table_args__ = (Index("ix_speed_records_dow_link", "day_of_week", "link_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    link_id: Mapped[str] = mapped_column(ForeignKey("links.link_id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)

    link: Mapped["Link"] = relationship(back_populates="speed_records")
