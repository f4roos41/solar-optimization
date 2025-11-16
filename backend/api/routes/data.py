"""Data query API endpoints (Parcel Inspector)."""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict

from ..services import data_service

router = APIRouter()


@router.get("/point", response_model=Dict)
async def query_point(
    lat: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees")
):
    """
    Query raw data values at a specific point (Parcel Inspector).

    Samples all global data layers (GHI, DNI, DEM, slope, land cover, etc.)
    at the specified coordinates and returns the values.

    This endpoint powers the "click on map to inspect" functionality.

    **Returns:**
    ```json
    {
        "coordinates": {"lat": 34.05, "lon": -118.25},
        "solar": {
            "ghi": 2200,
            "dni": 2500,
            "dhi": 150
        },
        "terrain": {
            "elevation": 125,
            "slope": 2.3,
            "aspect": 180
        },
        "infrastructure": {
            "distance_to_grid_km": 5.2,
            "distance_to_roads_km": 1.8
        },
        "land_cover": {
            "class": "Grassland",
            "code": 30
        }
    }
    ```
    """
    try:
        data = await data_service.query_point_data(lat, lon)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying point data: {str(e)}"
        )


@router.get("/layers", response_model=Dict)
async def list_available_layers():
    """
    List all available data layers with metadata.

    Returns information about resolution, source, and coverage for each layer.
    """
    layers = data_service.get_available_layers()
    return layers
