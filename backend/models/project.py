"""Project and analysis models."""

from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, Text, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from .base import Base, TimestampMixin


class JobStatus(str, Enum):
    """Status of an analysis job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Project(Base, TimestampMixin):
    """Project model representing a solar analysis project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    areas_of_interest: Mapped[list["AreaOfInterest"]] = relationship(
        "AreaOfInterest",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        "AnalysisJob",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"


class AreaOfInterest(Base, TimestampMixin):
    """Area of Interest (AOI) model - user-defined polygon."""

    __tablename__ = "areas_of_interest"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Geometry stored as WGS84 (EPSG:4326) polygon
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type='POLYGON', srid=4326),
        nullable=False
    )

    # Calculated area in square kilometers
    area_km2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="areas_of_interest")

    def __repr__(self) -> str:
        return f"<AreaOfInterest(id={self.id}, name='{self.name}', area_km2={self.area_km2})>"


class AnalysisJob(Base, TimestampMixin):
    """Analysis job model tracking MCDA processing."""

    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    aoi_id: Mapped[int] = mapped_column(ForeignKey("areas_of_interest.id"), nullable=False)

    # Job status
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False
    )

    # MCDA parameters stored as JSON
    # Example: {"ghi": 40, "slope": 25, "grid_dist": 20, "road_dist": 15}
    weights_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Constraints stored as JSON
    # Example: {"slope_gt": 10, "lulc_exclude": [50, 80], "grid_dist_gt": 10000}
    constraints_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Timestamps
    started_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Results
    result_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_tiles_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Error handling
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Statistics (calculated post-processing)
    stats_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Example: {"total_area_km2": 500, "suitable_area_km2": 120, "mean_suitability": 67.5}

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="analysis_jobs")

    def __repr__(self) -> str:
        return f"<AnalysisJob(id={self.id}, status={self.status})>"
