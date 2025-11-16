"""Analysis service layer."""

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from models.project import AnalysisJob, JobStatus
from api.schemas.analysis import AnalysisJobCreate
from workers.tasks import run_mcda_analysis


def create_and_queue_job(
    db: Session,
    project_id: int,
    aoi_id: int,
    data: AnalysisJobCreate
) -> AnalysisJob:
    """Create a new analysis job and queue it for processing."""

    # Validate weights sum to 100
    total_weight = sum(data.weights_json.values())
    if abs(total_weight - 100) > 0.01:
        raise ValueError(f"Weights must sum to 100, got {total_weight}")

    # Create job record
    job = AnalysisJob(
        project_id=project_id,
        aoi_id=aoi_id,
        status=JobStatus.PENDING,
        weights_json=data.weights_json,
        constraints_json=data.constraints_json
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue the job for processing
    # This sends the job to RabbitMQ, where a Celery worker will pick it up
    run_mcda_analysis.delay(job.id)

    return job


def get_job_status(db: Session, job_id: int) -> Optional[dict]:
    """Get the status of an analysis job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        return None

    return {
        "job_id": job.id,
        "status": job.status,
        "progress_percent": None,  # TODO: Implement progress tracking
        "message": job.error_log if job.status == JobStatus.FAILED else None
    }


def get_job_results(db: Session, job_id: int) -> Optional[dict]:
    """Get results for a completed job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job or job.status != JobStatus.COMPLETE:
        return None

    return {
        "job_id": job.id,
        "status": job.status,
        "result_geotiff_url": job.result_url,
        "result_tiles_url": job.result_tiles_url,
        "statistics": job.stats_json,
        "report_pdf_url": None  # TODO: Implement PDF report generation
    }


def list_project_jobs(db: Session, project_id: int) -> List[AnalysisJob]:
    """List all jobs for a project."""
    return db.query(AnalysisJob)\
        .filter(AnalysisJob.project_id == project_id)\
        .order_by(AnalysisJob.created_at.desc())\
        .all()


def delete_job(db: Session, job_id: int) -> bool:
    """Delete a job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        return False

    # TODO: Cancel Celery task if running

    db.delete(job)
    db.commit()
    return True
