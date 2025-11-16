"""Project management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    AOICreate,
    AOIResponse
)
from ..services import project_service

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)  # TODO: Add auth
):
    """
    Create a new solar analysis project.

    Returns the created project with generated ID.
    """
    # For now, use a dummy user_id
    user_id = 1
    project = project_service.create_project(db, user_id, project_data)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific project by ID.

    Returns full project details including associated AOIs and jobs.
    """
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all projects for the current user.

    Supports pagination with skip and limit parameters.
    """
    # TODO: Filter by current_user
    projects = project_service.list_projects(db, skip=skip, limit=limit)
    return projects


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update project details (name, description).
    """
    project = project_service.update_project(db, project_id, project_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a project and all associated data.

    This cascades to delete all AOIs and analysis jobs.
    """
    success = project_service.delete_project(db, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )


@router.post("/{project_id}/aoi", response_model=AOIResponse, status_code=status.HTTP_201_CREATED)
async def create_aoi(
    project_id: int,
    aoi_data: AOICreate,
    db: Session = Depends(get_db)
):
    """
    Create or update the Area of Interest for a project.

    Accepts GeoJSON polygon geometry.
    """
    aoi = project_service.create_or_update_aoi(db, project_id, aoi_data)
    return aoi


@router.get("/{project_id}/aoi", response_model=List[AOIResponse])
async def get_project_aois(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all Areas of Interest for a project.
    """
    aois = project_service.get_project_aois(db, project_id)
    return aois
