"""Analysis job API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobResponse,
    JobStatusResponse,
    JobResultsResponse
)
from ..services import analysis_service

router = APIRouter()


@router.post(
    "/{project_id}/run",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def run_analysis(
    project_id: int,
    aoi_id: int,
    job_data: AnalysisJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a new MCDA analysis job.

    This endpoint:
    1. Validates inputs
    2. Creates a job record with status=PENDING
    3. Pushes job to RabbitMQ queue
    4. Returns immediately with HTTP 202 Accepted

    The client should poll /analysis/{job_id}/status to monitor progress.

    **Parameters:**
    - weights_json: Dict of factor weights (e.g., {"ghi": 40, "slope": 25})
    - constraints_json: Dict of exclusion rules (e.g., {"slope_gt": 10})
    """
    job = analysis_service.create_and_queue_job(
        db, project_id, aoi_id, job_data
    )
    return job


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Poll the status of an analysis job.

    Returns current status: PENDING, RUNNING, COMPLETE, or FAILED.
    """
    status_info = analysis_service.get_job_status(db, job_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    return status_info


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get results for a completed analysis job.

    Returns S3 URLs to:
    - Suitability heatmap (GeoTIFF)
    - Tile pyramid (for web visualization)
    - Statistics JSON
    - PDF report (if generated)

    Only available when job status is COMPLETE.
    """
    results = analysis_service.get_job_results(db, job_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or not yet complete"
        )
    return results


@router.get("/{project_id}/jobs", response_model=list[AnalysisJobResponse])
async def list_project_jobs(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    List all analysis jobs for a project.
    """
    jobs = analysis_service.list_project_jobs(db, project_id)
    return jobs


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_or_delete_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a running job or delete a completed job.
    """
    success = analysis_service.delete_job(db, job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
