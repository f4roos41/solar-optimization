#!/usr/bin/env python3
"""
Main data ingestion pipeline orchestrator.

This script coordinates the end-to-end ETL process for building
the global solar platform data lake.
"""

import argparse
import logging
import yaml
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates the complete data ingestion pipeline."""

    def __init__(self, config_path: str):
        """Initialize pipeline with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.raw_dir = Path(self.config['paths']['raw'])
        self.processed_dir = Path(self.config['paths']['processed'])
        self.cog_dir = Path(self.config['paths']['cog'])

        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.cog_dir.mkdir(parents=True, exist_ok=True)

    def run(self, steps: list = None):
        """
        Run the pipeline.

        Args:
            steps: List of steps to run. If None, run all steps.
                   Options: ['download', 'process_dem', 'process_lulc',
                            'process_osm', 'proximity', 'cog', 'upload']
        """
        all_steps = [
            ('download', self.download_datasets),
            ('process_dem', self.process_dem),
            ('process_lulc', self.process_land_cover),
            ('process_osm', self.process_osm_data),
            ('proximity', self.generate_proximity_rasters),
            ('cog', self.convert_to_cog),
            ('upload', self.upload_to_s3)
        ]

        if steps is None:
            steps_to_run = all_steps
        else:
            steps_to_run = [(name, func) for name, func in all_steps if name in steps]

        logger.info(f"Running pipeline with steps: {[name for name, _ in steps_to_run]}")

        for step_name, step_func in steps_to_run:
            logger.info(f"{'='*60}")
            logger.info(f"Starting step: {step_name}")
            logger.info(f"{'='*60}")

            try:
                step_func()
                logger.info(f"Completed step: {step_name}")
            except Exception as e:
                logger.exception(f"Error in step {step_name}: {str(e)}")
                if self.config.get('stop_on_error', True):
                    raise
                else:
                    logger.warning(f"Continuing despite error in {step_name}")

    def download_datasets(self):
        """Download all source datasets."""
        logger.info("Downloading datasets...")

        # Download SRTM DEM
        if self.config['datasets']['srtm']['enabled']:
            logger.info("Downloading SRTM DEM...")
            # TODO: Implement SRTM download
            # from download_datasets import download_srtm
            # download_srtm(self.raw_dir / 'srtm')

        # Download ESA WorldCover
        if self.config['datasets']['esa_worldcover']['enabled']:
            logger.info("Downloading ESA WorldCover...")
            # TODO: Implement ESA WorldCover download
            # from download_datasets import download_worldcover
            # download_worldcover(self.raw_dir / 'worldcover')

        # Download NREL NSRDB
        if self.config['datasets']['nrel_nsrdb']['enabled']:
            logger.info("Downloading NREL NSRDB...")
            # TODO: Implement NSRDB download
            # Requires API key and specific time period

        # Download OSM data
        if self.config['datasets']['osm']['enabled']:
            logger.info("Downloading OSM data...")
            # Download from Geofabrik
            # from download_datasets import download_osm
            # download_osm(self.raw_dir / 'osm')

        logger.info("Dataset download complete")

    def process_dem(self):
        """Process DEM: mosaic, fill, derive slope/aspect."""
        logger.info("Processing DEM...")

        from processing.process_dem import process_dem_pipeline

        process_dem_pipeline(
            input_dir=self.raw_dir / 'srtm',
            output_dir=self.processed_dir,
            target_crs='EPSG:4326',
            resolution=90
        )

        logger.info("DEM processing complete")

    def process_land_cover(self):
        """Process land cover data."""
        logger.info("Processing land cover...")

        from processing.process_lulc import process_worldcover

        process_worldcover(
            input_dir=self.raw_dir / 'worldcover',
            output_path=self.processed_dir / 'lulc.tif',
            target_crs='EPSG:4326'
        )

        logger.info("Land cover processing complete")

    def process_osm_data(self):
        """Import OSM data to PostGIS."""
        logger.info("Processing OSM data...")

        from processing.process_osm import import_osm_to_postgis

        import_osm_to_postgis(
            osm_file=self.raw_dir / 'osm' / 'planet-latest.osm.pbf',
            database_url=self.config['database_url']
        )

        logger.info("OSM processing complete")

    def generate_proximity_rasters(self):
        """Generate proximity rasters from vector infrastructure."""
        logger.info("Generating proximity rasters...")

        from processing.generate_proximity_rasters import generate_all_proximity_rasters

        generate_all_proximity_rasters(
            database_url=self.config['database_url'],
            output_dir=self.processed_dir,
            resolution=1000,  # 1 km resolution
            max_distance=50000  # 50 km max distance
        )

        logger.info("Proximity raster generation complete")

    def convert_to_cog(self):
        """Convert all rasters to Cloud-Optimized GeoTIFF."""
        logger.info("Converting rasters to COG format...")

        from processing.convert_to_cog import convert_directory_to_cog

        convert_directory_to_cog(
            input_dir=self.processed_dir,
            output_dir=self.cog_dir,
            compression='DEFLATE',
            blocksize=512
        )

        logger.info("COG conversion complete")

    def upload_to_s3(self):
        """Upload all COGs to S3 data lake."""
        logger.info("Uploading to S3...")

        from upload.upload_to_s3 import upload_directory

        upload_directory(
            local_dir=self.cog_dir,
            bucket=self.config['s3']['bucket'],
            prefix=self.config['s3']['prefix'],
            aws_access_key_id=self.config['s3']['access_key_id'],
            aws_secret_access_key=self.config['s3']['secret_access_key'],
            region=self.config['s3']['region']
        )

        logger.info("S3 upload complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Solar Platform Data Ingestion Pipeline'
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to configuration YAML file'
    )
    parser.add_argument(
        '--steps',
        nargs='+',
        help='Specific steps to run (default: all)',
        choices=['download', 'process_dem', 'process_lulc', 'process_osm',
                 'proximity', 'cog', 'upload']
    )

    args = parser.parse_args()

    pipeline = DataPipeline(args.config)
    pipeline.run(steps=args.steps)

    logger.info("Pipeline execution complete!")


if __name__ == '__main__':
    main()
