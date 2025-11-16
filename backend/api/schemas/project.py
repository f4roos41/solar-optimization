"""Pydantic schemas for project-related API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AOICreate(BaseModel):
    """Schema for creating/updating an Area of Interest."""
    name: str = Field(..., min_length=1, max_length=255)
    geojson: dict = Field(..., description="GeoJSON polygon geometry")


class AOIResponse(BaseModel):
    """Schema for AOI response."""
    id: int
    project_id: int
    name: str
    area_km2: Optional[float]
    geojson: dict
    created_at: datetime

    class Config:
        from_attributes = True
