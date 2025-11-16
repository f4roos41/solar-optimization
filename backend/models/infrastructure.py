"""Infrastructure models for OSM data."""

from typing import Optional
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from .base import Base


class InfrastructureOSM(Base):
    """OpenStreetMap infrastructure features (roads, power grid)."""

    __tablename__ = "infrastructure_osm"

    id: Mapped[int] = mapped_column(primary_key=True)
    osm_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    # Type: 'road', 'transmission_line', 'substation'
    type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # Subtype: 'primary', 'secondary', 'motorway' for roads
    # or voltage level for power lines
    subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Data source: 'osm', 'commercial', etc.
    source: Mapped[str] = mapped_column(String(50), default='osm', nullable=False)

    # Geometry (can be LineString for roads/lines or Point for substations)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type='GEOMETRY', srid=4326),
        nullable=False
    )

    # Additional attributes as JSON
    tags: Mapped[Optional[dict]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<InfrastructureOSM(id={self.id}, type='{self.type}')>"
