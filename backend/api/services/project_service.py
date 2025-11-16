"""Project service layer."""

from sqlalchemy.orm import Session
from typing import List, Optional
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
import json

from models.project import Project, AreaOfInterest
from api.schemas.project import ProjectCreate, ProjectUpdate, AOICreate


def create_project(db: Session, user_id: int, data: ProjectCreate) -> Project:
    """Create a new project."""
    project = Project(
        user_id=user_id,
        name=data.name,
        description=data.description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """Get a project by ID."""
    return db.query(Project).filter(Project.id == project_id).first()


def list_projects(db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Project]:
    """List projects, optionally filtered by user."""
    query = db.query(Project)
    if user_id:
        query = query.filter(Project.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def update_project(db: Session, project_id: int, data: ProjectUpdate) -> Optional[Project]:
    """Update a project."""
    project = get_project(db, project_id)
    if not project:
        return None

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    """Delete a project."""
    project = get_project(db, project_id)
    if not project:
        return False

    db.delete(project)
    db.commit()
    return True


def create_or_update_aoi(db: Session, project_id: int, data: AOICreate) -> AreaOfInterest:
    """Create or update an Area of Interest."""
    # Convert GeoJSON to Shapely geometry
    geom = shape(data.geojson)

    # Calculate area in km²
    # Note: This is a simple approximation. For accurate area, use projected coordinates
    area_km2 = geom.area * 111.32 * 111.32  # Rough conversion from degrees² to km²

    # Check if AOI already exists for this project
    existing_aoi = db.query(AreaOfInterest).filter(
        AreaOfInterest.project_id == project_id,
        AreaOfInterest.name == data.name
    ).first()

    if existing_aoi:
        # Update existing
        existing_aoi.geom = from_shape(geom, srid=4326)
        existing_aoi.area_km2 = area_km2
        db.commit()
        db.refresh(existing_aoi)
        return existing_aoi
    else:
        # Create new
        aoi = AreaOfInterest(
            project_id=project_id,
            name=data.name,
            geom=from_shape(geom, srid=4326),
            area_km2=area_km2
        )
        db.add(aoi)
        db.commit()
        db.refresh(aoi)
        return aoi


def get_project_aois(db: Session, project_id: int) -> List[AreaOfInterest]:
    """Get all AOIs for a project."""
    return db.query(AreaOfInterest).filter(AreaOfInterest.project_id == project_id).all()
