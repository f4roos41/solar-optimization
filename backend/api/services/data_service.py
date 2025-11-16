"""Data query service layer (Parcel Inspector)."""

from typing import Dict
import rasterio
from rasterio.transform import rowcol
import boto3
from api.config import settings


# TODO: Load from database or config
DATA_LAYER_CATALOG = {
    "ghi": "s3://solar-platform-data-lake/ghi.tif",
    "dni": "s3://solar-platform-data-lake/dni.tif",
    "dem": "s3://solar-platform-data-lake/dem.tif",
    "slope": "s3://solar-platform-data-lake/slope.tif",
    "aspect": "s3://solar-platform-data-lake/aspect.tif",
    "distance_to_grid": "s3://solar-platform-data-lake/distance_to_grid.tif",
    "distance_to_roads": "s3://solar-platform-data-lake/distance_to_roads.tif",
    "lulc": "s3://solar-platform-data-lake/lulc.tif",
}

# Land cover class mapping
LULC_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare/sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen"
}


async def query_point_data(lat: float, lon: float) -> Dict:
    """
    Query all data layers at a specific point.

    Uses rasterio to sample COGs on S3 via HTTP range requests.
    """
    results = {
        "coordinates": {"lat": lat, "lon": lon},
        "solar": {},
        "terrain": {},
        "infrastructure": {},
        "land_cover": {}
    }

    try:
        # Sample GHI
        with rasterio.open(DATA_LAYER_CATALOG["ghi"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            results["solar"]["ghi"] = float(value) if value != src.nodata else None

        # Sample DNI
        with rasterio.open(DATA_LAYER_CATALOG["dni"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            results["solar"]["dni"] = float(value) if value != src.nodata else None

        # Sample DEM
        with rasterio.open(DATA_LAYER_CATALOG["dem"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            results["terrain"]["elevation"] = float(value) if value != src.nodata else None

        # Sample Slope
        with rasterio.open(DATA_LAYER_CATALOG["slope"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            results["terrain"]["slope"] = float(value) if value != src.nodata else None

        # Sample Distance to Grid
        with rasterio.open(DATA_LAYER_CATALOG["distance_to_grid"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            results["infrastructure"]["distance_to_grid_km"] = float(value) / 1000 if value != src.nodata else None

        # Sample Distance to Roads
        with rasterio.open(DATA_LAYER_CATALOG["distance_to_roads"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            results["infrastructure"]["distance_to_roads_km"] = float(value) / 1000 if value != src.nodata else None

        # Sample Land Cover
        with rasterio.open(DATA_LAYER_CATALOG["lulc"]) as src:
            row, col = rowcol(src.transform, lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
            if value != src.nodata:
                results["land_cover"]["code"] = int(value)
                results["land_cover"]["class"] = LULC_CLASSES.get(int(value), "Unknown")

    except Exception as e:
        # Log error but return partial results
        print(f"Error querying point data: {e}")

    return results


def get_available_layers() -> Dict:
    """Get metadata for all available data layers."""
    return {
        "layers": [
            {
                "id": "ghi",
                "name": "Global Horizontal Irradiance",
                "units": "kWh/m²/year",
                "source": "NREL NSRDB",
                "resolution": "4 km",
                "category": "solar"
            },
            {
                "id": "dni",
                "name": "Direct Normal Irradiance",
                "units": "kWh/m²/year",
                "source": "NREL NSRDB",
                "resolution": "4 km",
                "category": "solar"
            },
            {
                "id": "dem",
                "name": "Digital Elevation Model",
                "units": "meters",
                "source": "SRTM 90m v4",
                "resolution": "90 m",
                "category": "terrain"
            },
            {
                "id": "slope",
                "name": "Slope",
                "units": "degrees",
                "source": "Derived from SRTM",
                "resolution": "90 m",
                "category": "terrain"
            },
            {
                "id": "lulc",
                "name": "Land Use / Land Cover",
                "units": "class code",
                "source": "ESA WorldCover",
                "resolution": "10 m",
                "category": "environmental"
            }
        ]
    }
