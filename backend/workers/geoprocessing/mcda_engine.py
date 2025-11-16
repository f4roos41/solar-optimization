"""
Core MCDA (Multi-Criteria Decision Analysis) Geoprocessing Engine.

This module implements the "weighted overlay" analysis workflow described in Part 3
of the strategic blueprint.
"""

import os
import tempfile
from typing import Dict
import numpy as np
import rasterio
import rasterio.mask
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
import richdem as rd
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
import boto3

from models.project import AnalysisJob, AreaOfInterest
from api.config import settings
import logging

logger = logging.getLogger(__name__)


# Data layer catalog - maps layer names to S3 COG paths
DATA_LAYER_CATALOG = {
    "ghi": f"s3://{settings.S3_DATA_LAKE_BUCKET}/ghi.tif",
    "dni": f"s3://{settings.S3_DATA_LAKE_BUCKET}/dni.tif",
    "dem": f"s3://{settings.S3_DATA_LAKE_BUCKET}/dem.tif",
    "distance_to_grid": f"s3://{settings.S3_DATA_LAKE_BUCKET}/distance_to_grid.tif",
    "distance_to_roads": f"s3://{settings.S3_DATA_LAKE_BUCKET}/distance_to_roads.tif",
    "lulc": f"s3://{settings.S3_DATA_LAKE_BUCKET}/lulc.tif",
}


def normalize_array(arr: np.ndarray, min_val: float, max_val: float, invert: bool = False) -> np.ndarray:
    """
    Normalize a NumPy array to a 0-100 scale.

    Args:
        arr: Input array
        min_val: Minimum value for clipping
        max_val: Maximum value for clipping
        invert: If True, lower values are better (e.g., for slope, distance)

    Returns:
        Normalized array (0-100 scale)
    """
    # Replace nodata with NaN for proper handling
    arr = arr.astype(float)

    # Clip to range
    arr = np.clip(arr, min_val, max_val)

    # Normalize to 0-1
    norm_arr = (arr - min_val) / (max_val - min_val)

    # Invert if needed (for "lower is better" factors)
    if invert:
        norm_arr = 1 - norm_arr

    # Scale to 0-100
    return norm_arr * 100


def clip_raster_to_aoi(s3_path: str, aoi_geom, output_path: str = None) -> tuple:
    """
    Clip a global COG raster to an AOI using HTTP range requests.

    Args:
        s3_path: S3 path to source COG
        aoi_geom: Shapely geometry for the AOI
        output_path: Optional path to save clipped raster

    Returns:
        Tuple of (data array, transform, metadata)
    """
    with rasterio.open(s3_path) as src:
        # Clip to AOI geometry
        out_image, out_transform = rasterio.mask.mask(
            src,
            [aoi_geom],
            crop=True,
            nodata=src.nodata
        )

        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        })

        if output_path:
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)

    return out_image[0], out_transform, out_meta


def calculate_slope_from_dem(dem_array: np.ndarray, transform, nodata=-9999) -> np.ndarray:
    """
    Calculate slope in degrees from DEM using RichDEM.

    Args:
        dem_array: DEM array
        transform: Raster transform
        nodata: NoData value

    Returns:
        Slope array in degrees
    """
    # Create RichDEM array
    dem_rd = rd.rdarray(dem_array, no_data=nodata)

    # Calculate slope in degrees
    slope = rd.TerrainAttribute(dem_rd, attrib='slope_degrees')

    return np.array(slope)


def process_mcda_job(db: Session, job: AnalysisJob) -> Dict:
    """
    Execute the complete MCDA workflow for a job.

    This implements the step-by-step workflow from Part 3.2:
    1. Load AOI geometry
    2. Clip source rasters from S3
    3. Calculate on-the-fly derivatives (slope)
    4. Create constraint mask
    5. Normalize factors to 0-100 scale
    6. Run weighted overlay
    7. Apply constraints
    8. Save result to S3
    9. Generate tiles for visualization
    10. Calculate statistics

    Args:
        db: Database session
        job: AnalysisJob instance

    Returns:
        Dictionary with result URLs and statistics
    """
    logger.info(f"Processing MCDA job {job.id}")

    # 1. Load AOI geometry
    aoi = db.query(AreaOfInterest).filter(AreaOfInterest.id == job.aoi_id).first()
    if not aoi:
        raise ValueError(f"AOI {job.aoi_id} not found")

    aoi_geom = to_shape(aoi.geom)
    logger.info(f"AOI area: {aoi.area_km2:.2f} km²")

    # Create temporary working directory
    with tempfile.TemporaryDirectory() as tmpdir:

        # 2. Clip source rasters to AOI
        logger.info("Clipping source rasters...")

        ghi_data, transform, meta = clip_raster_to_aoi(
            DATA_LAYER_CATALOG["ghi"],
            aoi_geom
        )

        dem_data, _, _ = clip_raster_to_aoi(
            DATA_LAYER_CATALOG["dem"],
            aoi_geom
        )

        grid_dist_data, _, _ = clip_raster_to_aoi(
            DATA_LAYER_CATALOG["distance_to_grid"],
            aoi_geom
        )

        road_dist_data, _, _ = clip_raster_to_aoi(
            DATA_LAYER_CATALOG["distance_to_roads"],
            aoi_geom
        )

        lulc_data, _, _ = clip_raster_to_aoi(
            DATA_LAYER_CATALOG["lulc"],
            aoi_geom
        )

        # 3. Calculate on-the-fly derivatives
        logger.info("Calculating slope from DEM...")
        slope_data = calculate_slope_from_dem(dem_data, transform)

        # 4. Create constraint mask (binary exclusion)
        logger.info("Creating constraint mask...")
        constraints = job.constraints_json
        constraint_mask = np.zeros(ghi_data.shape, dtype=bool)

        # Exclude slopes greater than threshold
        if "slope_gt" in constraints:
            constraint_mask |= (slope_data > constraints["slope_gt"])
            logger.info(f"Excluded {np.sum(slope_data > constraints['slope_gt'])} pixels due to slope")

        # Exclude specific land cover classes
        if "lulc_exclude" in constraints:
            constraint_mask |= np.isin(lulc_data, constraints["lulc_exclude"])
            logger.info(f"Excluded {np.sum(np.isin(lulc_data, constraints['lulc_exclude']))} pixels due to land cover")

        # Exclude areas too far from grid
        if "grid_dist_gt" in constraints:
            constraint_mask |= (grid_dist_data > constraints["grid_dist_gt"])

        # 5. Normalize factors to 0-100 scale
        logger.info("Normalizing factors...")
        weights = job.weights_json

        normalized_layers = {}

        if "ghi" in weights:
            normalized_layers["ghi"] = normalize_array(ghi_data, 1000, 2500, invert=False)

        if "slope" in weights:
            normalized_layers["slope"] = normalize_array(slope_data, 0, 10, invert=True)

        if "grid_dist" in weights:
            normalized_layers["grid_dist"] = normalize_array(grid_dist_data, 0, 10000, invert=True)

        if "road_dist" in weights:
            normalized_layers["road_dist"] = normalize_array(road_dist_data, 0, 5000, invert=True)

        # 6. Run weighted overlay (MCDA)
        logger.info("Running weighted overlay...")
        final_map = np.zeros(ghi_data.shape, dtype=np.float32)

        for layer_name, weight in weights.items():
            if layer_name in normalized_layers:
                final_map += normalized_layers[layer_name] * (weight / 100.0)
                logger.info(f"Applied weight {weight}% to {layer_name}")

        # 7. Apply constraints
        nodata_val = -9999
        final_map[constraint_mask] = nodata_val
        logger.info(f"Applied constraints, excluded {np.sum(constraint_mask)} pixels")

        # 8. Save result to S3
        logger.info("Saving result to S3...")
        result_filename = f"mcda_result_{job.id}.tif"
        result_path = os.path.join(tmpdir, result_filename)

        # Update metadata for output
        meta.update({
            "dtype": "float32",
            "nodata": nodata_val,
            "compress": "lzw"
        })

        with rasterio.open(result_path, "w", **meta) as dst:
            dst.write(final_map, 1)

        # Upload to S3
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        s3_key = f"results/{result_filename}"
        s3_client.upload_file(
            result_path,
            settings.S3_RESULTS_BUCKET,
            s3_key
        )

        result_url = f"s3://{settings.S3_RESULTS_BUCKET}/{s3_key}"
        logger.info(f"Uploaded result to {result_url}")

        # 9. Calculate statistics
        valid_data = final_map[final_map != nodata_val]
        statistics = {
            "total_pixels": int(ghi_data.size),
            "valid_pixels": int(valid_data.size),
            "excluded_pixels": int(np.sum(constraint_mask)),
            "mean_suitability": float(np.mean(valid_data)) if valid_data.size > 0 else 0,
            "max_suitability": float(np.max(valid_data)) if valid_data.size > 0 else 0,
            "min_suitability": float(np.min(valid_data)) if valid_data.size > 0 else 0,
            "std_suitability": float(np.std(valid_data)) if valid_data.size > 0 else 0,
        }

        logger.info(f"Statistics: {statistics}")

        # 10. TODO: Generate tile pyramid for web visualization
        tiles_url = None  # Placeholder

        return {
            "geotiff_url": result_url,
            "tiles_url": tiles_url,
            "statistics": statistics
        }
