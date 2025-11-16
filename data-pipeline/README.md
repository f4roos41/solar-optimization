# Data Ingestion Pipeline

This directory contains scripts and workflows for building the global data lake that powers the solar platform.

## Overview

The data pipeline implements a one-time ETL (Extract, Transform, Load) process to:
1. Download global datasets from public sources
2. Standardize all rasters to WGS84 (EPSG:4326)
3. Convert to Cloud-Optimized GeoTIFFs (COGs)
4. Pre-calculate proximity rasters for infrastructure
5. Upload to S3 data lake

## Pipeline Architecture

```
┌──────────────┐
│   Download   │  Fetch source datasets
└──────┬───────┘
       │
┌──────▼───────┐
│  Standardize │  Reproject to WGS84, clip, resample
└──────┬───────┘
       │
┌──────▼───────┐
│   Optimize   │  Convert to COG format
└──────┬───────┘
       │
┌──────▼───────┐
│    Upload    │  Push to S3 data lake
└──────────────┘
```

## Data Sources

### Solar Irradiance
- **Source**: NREL NSRDB
- **URL**: https://nsrdb.nrel.gov/data-sets/
- **Resolution**: 4 km
- **Layers**: GHI, DNI, DHI

### Elevation
- **Source**: SRTM 90m v4.1
- **URL**: https://srtm.csi.cgiar.org/
- **Resolution**: 90 m (3 arc-seconds)
- **Coverage**: Global (60°N - 56°S)

### Land Cover
- **Source**: ESA WorldCover
- **URL**: https://esa-worldcover.org/
- **Resolution**: 10 m
- **Year**: 2021

### Infrastructure
- **Source**: OpenStreetMap
- **URL**: https://planet.openstreetmap.org/
- **Extract**: Geofabrik (https://download.geofabrik.de/)
- **Features**: Roads, transmission lines, substations

## Usage

### Prerequisites

```bash
pip install -r requirements.txt
```

Required tools:
- GDAL 3.6+
- osm2pgsql
- Python 3.11+

### Configuration

Edit `configs/global_baseline.yaml` to specify:
- Data sources
- Output paths
- Processing parameters

### Running the Pipeline

**Full pipeline:**
```bash
python ingest/run_pipeline.py --config configs/global_baseline.yaml
```

**Individual steps:**
```bash
# Download only
python ingest/download_datasets.py --config configs/global_baseline.yaml

# Process DEM and derive slope/aspect
python processing/process_dem.py --input data/raw/srtm_90m --output data/processed/

# Generate proximity rasters
python processing/generate_proximity_rasters.py

# Upload to S3
python upload/upload_to_s3.py --bucket solar-platform-data-lake
```

## Output Structure

```
S3://solar-platform-data-lake/
├── ghi.tif                    # Global Horizontal Irradiance (COG)
├── dni.tif                    # Direct Normal Irradiance (COG)
├── dhi.tif                    # Diffuse Horizontal Irradiance (COG)
├── dem.tif                    # Digital Elevation Model (COG)
├── slope.tif                  # Slope in degrees (COG)
├── aspect.tif                 # Aspect in degrees (COG)
├── lulc.tif                   # Land Use/Land Cover (COG)
├── distance_to_grid.tif       # Distance to power grid (COG)
├── distance_to_roads.tif      # Distance to roads (COG)
└── metadata/
    └── catalog.json           # Data catalog with metadata
```

## Processing Notes

### Cloud-Optimized GeoTIFFs (COGs)

All rasters are converted to COG format using:
```bash
gdal_translate -of COG \
  -co COMPRESS=DEFLATE \
  -co BLOCKSIZE=512 \
  -co OVERVIEW_RESAMPLING=AVERAGE \
  input.tif output_cog.tif
```

Benefits:
- Efficient HTTP range requests
- Progressive resolution (overviews)
- No need to download entire file

### Proximity Raster Generation

For roads and transmission lines:
1. Rasterize vector features to binary raster
2. Run distance transform using `gdal_proximity.py`
3. Output: Distance in meters to nearest feature

Example:
```bash
gdal_proximity.py roads_binary.tif distance_to_roads.tif \
  -values 1 -distunits GEO -maxdist 50000
```

## Data Catalog

After processing, a catalog is generated with metadata:

```json
{
  "layers": [
    {
      "id": "ghi",
      "name": "Global Horizontal Irradiance",
      "path": "s3://solar-platform-data-lake/ghi.tif",
      "units": "kWh/m²/year",
      "resolution": "4 km",
      "source": "NREL NSRDB",
      "crs": "EPSG:4326",
      "bounds": [-180, -90, 180, 90]
    }
  ]
}
```

## Troubleshooting

### Out of Memory

For large datasets, use GDAL's virtual rasters (VRT) and tiling:

```bash
gdalbuildvrt mosaic.vrt tiles/*.tif
gdalwarp -co TILED=YES -co BLOCKSIZE=512 mosaic.vrt output.tif
```

### S3 Upload Failures

Use multipart upload for files > 5 GB:

```python
s3_client.upload_file(
    file_path,
    bucket,
    key,
    Config=TransferConfig(multipart_threshold=1024 * 25)
)
```

## Estimated Processing Time

- SRTM DEM processing: ~2 hours
- ESA WorldCover download: ~6 hours (1 TB+)
- OSM processing: ~4 hours
- Proximity raster generation: ~3 hours
- S3 upload: ~8 hours (depends on bandwidth)

**Total**: ~24-48 hours for full global dataset

## Incremental Updates

To update a single layer:
```bash
python ingest/update_layer.py --layer ghi --year 2024
```
