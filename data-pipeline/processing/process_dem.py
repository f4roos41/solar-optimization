#!/usr/bin/env python3
"""
DEM processing pipeline.

Processes SRTM DEM tiles:
1. Mosaic tiles into global VRT
2. Fill voids/holes
3. Reproject to target CRS
4. Derive slope and aspect
"""

import logging
from pathlib import Path
from osgeo import gdal
import subprocess

logger = logging.getLogger(__name__)

# Enable GDAL exceptions
gdal.UseExceptions()


def mosaic_dem_tiles(input_dir: Path, output_vrt: Path):
    """
    Create a VRT mosaic from DEM tiles.

    Args:
        input_dir: Directory containing .hgt or .tif DEM tiles
        output_vrt: Output VRT file path
    """
    logger.info(f"Creating DEM mosaic from {input_dir}")

    # Find all DEM files
    dem_files = list(input_dir.glob("*.hgt")) + list(input_dir.glob("*.tif"))

    if not dem_files:
        raise FileNotFoundError(f"No DEM files found in {input_dir}")

    logger.info(f"Found {len(dem_files)} DEM tiles")

    # Build VRT
    gdal.BuildVRT(
        str(output_vrt),
        [str(f) for f in dem_files],
        options=gdal.BuildVRTOptions(
            resampleAlg='bilinear',
            addAlpha=False
        )
    )

    logger.info(f"Created VRT mosaic: {output_vrt}")


def fill_dem_voids(input_dem: Path, output_dem: Path):
    """
    Fill voids in DEM using gdal_fillnodata.

    Args:
        input_dem: Input DEM
        output_dem: Output filled DEM
    """
    logger.info(f"Filling DEM voids...")

    cmd = [
        'gdal_fillnodata.py',
        '-md', '100',  # Max distance to search for values
        '-si', '2',    # Smoothing iterations
        str(input_dem),
        str(output_dem)
    ]

    subprocess.run(cmd, check=True)
    logger.info(f"Filled DEM saved to {output_dem}")


def calculate_slope(input_dem: Path, output_slope: Path):
    """
    Calculate slope in degrees from DEM.

    Args:
        input_dem: Input DEM
        output_slope: Output slope raster
    """
    logger.info(f"Calculating slope...")

    gdal.DEMProcessing(
        str(output_slope),
        str(input_dem),
        'slope',
        computeEdges=True,
        slopeFormat='degree'
    )

    logger.info(f"Slope raster saved to {output_slope}")


def calculate_aspect(input_dem: Path, output_aspect: Path):
    """
    Calculate aspect in degrees from DEM.

    Args:
        input_dem: Input DEM
        output_aspect: Output aspect raster
    """
    logger.info(f"Calculating aspect...")

    gdal.DEMProcessing(
        str(output_aspect),
        str(input_dem),
        'aspect',
        computeEdges=True,
        zeroForFlat=True
    )

    logger.info(f"Aspect raster saved to {output_aspect}")


def process_dem_pipeline(
    input_dir: Path,
    output_dir: Path,
    target_crs: str = 'EPSG:4326',
    resolution: int = 90
):
    """
    Complete DEM processing pipeline.

    Args:
        input_dir: Directory containing source DEM tiles
        output_dir: Output directory for processed products
        target_crs: Target coordinate reference system
        resolution: Output resolution in meters
    """
    logger.info("Starting DEM processing pipeline")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Mosaic tiles
    vrt_path = output_dir / 'dem_mosaic.vrt'
    mosaic_dem_tiles(input_dir, vrt_path)

    # Step 2: Reproject and fill
    dem_path = output_dir / 'dem.tif'
    logger.info(f"Reprojecting DEM to {target_crs}...")

    gdal.Warp(
        str(dem_path),
        str(vrt_path),
        dstSRS=target_crs,
        xRes=resolution,
        yRes=resolution,
        resampleAlg='bilinear',
        creationOptions=[
            'TILED=YES',
            'COMPRESS=DEFLATE',
            'BLOCKSIZE=512'
        ]
    )

    # Step 3: Calculate slope
    slope_path = output_dir / 'slope.tif'
    calculate_slope(dem_path, slope_path)

    # Step 4: Calculate aspect
    aspect_path = output_dir / 'aspect.tif'
    calculate_aspect(dem_path, aspect_path)

    logger.info("DEM processing pipeline complete")

    return {
        'dem': dem_path,
        'slope': slope_path,
        'aspect': aspect_path
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process DEM data')
    parser.add_argument('--input', required=True, help='Input directory with DEM tiles')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--crs', default='EPSG:4326', help='Target CRS')
    parser.add_argument('--resolution', type=int, default=90, help='Resolution in meters')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    process_dem_pipeline(
        Path(args.input),
        Path(args.output),
        args.crs,
        args.resolution
    )
