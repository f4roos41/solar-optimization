"""Celery task definitions."""

from celery import Task
from sqlalchemy.orm import Session
import logging

from workers.celery_app import celery_app
from workers.geoprocessing.mcda_engine import process_mcda_job
from api.database import SessionLocal
from models.project import AnalysisJob, JobStatus

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""

    _db: Session = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="run_mcda_analysis")
def run_mcda_analysis(self, job_id: int):
    """
    Execute MCDA analysis job.

    This is the main worker task that processes solar site suitability analysis.
    It performs weighted overlay analysis using user-defined factors and constraints.

    Args:
        job_id: Database ID of the AnalysisJob to process
    """
    logger.info(f"Starting MCDA analysis for job {job_id}")

    db = self.db
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        # Update status to RUNNING
        job.status = JobStatus.RUNNING
        db.commit()

        # Execute the core geoprocessing workflow
        result = process_mcda_job(db, job)

        # Update job with results
        job.status = JobStatus.COMPLETE
        job.result_url = result["geotiff_url"]
        job.result_tiles_url = result["tiles_url"]
        job.stats_json = result["statistics"]
        db.commit()

        logger.info(f"Completed MCDA analysis for job {job_id}")

    except Exception as e:
        logger.exception(f"Error processing job {job_id}: {str(e)}")

        # Update job status to FAILED
        job.status = JobStatus.FAILED
        job.error_log = str(e)
        db.commit()

        raise
