"""Pydantic schemas for analysis job requests/responses."""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
from models.project import JobStatus


class AnalysisJobCreate(BaseModel):
    """Schema for creating a new analysis job."""
    weights_json: Dict[str, float] = Field(
        ...,
        description="Factor weights (must sum to 100)",
        example={"ghi": 40, "slope": 25, "grid_dist": 20, "road_dist": 15}
    )
    constraints_json: Dict[str, any] = Field(
        ...,
        description="Binary constraint rules",
        example={
            "slope_gt": 10,
            "lulc_exclude": [50, 80],
            "grid_dist_gt": 10000
        }
    )


class AnalysisJobResponse(BaseModel):
    """Schema for analysis job response."""
    id: int
    project_id: int
    aoi_id: int
    status: JobStatus
    weights_json: Dict
    constraints_json: Dict
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_log: Optional[str]

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    """Schema for job status polling."""
    job_id: int
    status: JobStatus
    progress_percent: Optional[int] = None
    message: Optional[str] = None


class JobResultsResponse(BaseModel):
    """Schema for job results."""
    job_id: int
    status: JobStatus
    result_geotiff_url: Optional[str]
    result_tiles_url: Optional[str]
    statistics: Optional[Dict]
    report_pdf_url: Optional[str]
