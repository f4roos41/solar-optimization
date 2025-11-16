# Global Solar Energy Planning Platform

A next-generation geospatial analysis platform for strategic solar energy site selection, combining Multi-Criteria Decision Analysis (MCDA), advanced 3D visualization, and bankable energy simulation.

## Overview

This platform provides a comprehensive workflow from continental-scale prospecting to parcel-specific financial viability analysis, exceeding the capabilities of existing tools like the Global Solar Atlas.

### Core Capabilities

- **Multi-Criteria Decision Analysis (MCDA)**: Custom weighted overlay analysis using solar irradiance, terrain, infrastructure proximity, and land use constraints
- **Interactive 3D Visualization**: CesiumJS-powered terrain visualization with real-time shadow analysis
- **PV Simulation**: Industry-standard photovoltaic modeling using pvlib-python
- **Financial Analysis**: LCOE and IRR calculations using NREL's PySAM
- **Professional Reporting**: Automated investment-grade PDF reports and GIS data export

## Architecture

### Tech Stack

**Backend:**
- FastAPI (API server)
- Celery + RabbitMQ (asynchronous job processing)
- PostgreSQL + PostGIS (spatial database)
- Python geospatial stack (Rasterio, GeoPandas, RichDEM)
- pvlib-python (PV simulation)
- PySAM (financial modeling)

**Frontend:**
- React + TypeScript
- Mapbox GL JS (2D mapping)
- CesiumJS (3D visualization)
- Turf.js (client-side geospatial operations)

**Data Infrastructure:**
- Amazon S3 (Cloud-Optimized GeoTIFF storage)
- Cloud-based ETL pipeline (AWS Batch/Airflow)

### System Architecture

```
┌─────────────────┐
│  React Frontend │
│  (Mapbox/Cesium)│
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌─────────────────┐
│   FastAPI       │◄──────┐
│   API Server    │       │ Status Updates
└────────┬────────┘       │
         │ Job Queue      │
         ▼                │
┌─────────────────┐       │
│   RabbitMQ      │       │
│   Message Broker│       │
└────────┬────────┘       │
         │ Consume        │
         ▼                │
┌─────────────────┐       │
│  Celery Workers │───────┘
│  (Geoprocessing)│
└────────┬────────┘
         │
         ├──► PostgreSQL/PostGIS (metadata, vectors)
         └──► S3 Data Lake (COG rasters)
```

## Project Structure

```
solar-optimization/
├── backend/                    # Python backend services
│   ├── api/                   # FastAPI application
│   ├── workers/               # Celery geoprocessing workers
│   ├── models/                # Database models
│   ├── services/              # Business logic
│   └── schemas/               # Pydantic schemas
├── frontend/                  # React application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── modules/          # Feature modules
│   │   ├── services/         # API clients
│   │   └── utils/            # Utilities
├── data-pipeline/            # ETL and data ingestion
│   ├── ingest/              # Source data ingestion scripts
│   ├── processing/          # Data processing workflows
│   └── schemas/             # Data schemas
├── infrastructure/           # Infrastructure as code
│   ├── docker/              # Docker configurations
│   ├── kubernetes/          # K8s manifests
│   └── terraform/           # Cloud infrastructure
└── docs/                    # Documentation
    ├── architecture/        # Architecture documentation
    ├── api/                # API documentation
    └── user-guide/         # User guides
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with PostGIS 3.3+
- GDAL 3.6+

### Quick Start (Development)

1. **Clone and setup:**
```bash
git clone <repository-url>
cd solar-optimization
cp .env.example .env  # Configure environment variables
```

2. **Start infrastructure services:**
```bash
docker-compose up -d postgres rabbitmq
```

3. **Initialize database:**
```bash
cd backend
python scripts/init_db.py
```

4. **Start backend services:**
```bash
# Terminal 1 - API Server
uvicorn api.main:app --reload

# Terminal 2 - Celery Worker
celery -A workers.celery_app worker --loglevel=info
```

5. **Start frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Data Ingestion

The platform requires a one-time data ingestion process to build the global data lake:

```bash
cd data-pipeline
python ingest/run_pipeline.py --config configs/global_baseline.yaml
```

See [Data Pipeline Documentation](docs/data-pipeline/README.md) for details.

## Module Overview

### Module 1: AOI Definition Tool
Interactive polygon drawing, file import (Shapefile/GeoJSON/KML), area calculation

### Module 2: Data Layer Library
Global datasets:
- **Solar**: NREL NSRDB (GHI/DNI)
- **Terrain**: SRTM 90m DEM
- **Land Cover**: ESA WorldCover 10m
- **Infrastructure**: OpenStreetMap (roads/grid)

### Module 3: MCDA Workbench
Custom weighted overlay analysis with:
- Factor weighting (GHI, slope, infrastructure proximity)
- Binary constraints (land use exclusions, slope limits)
- Real-time suitability mapping

### Module 4: Visualization Suite
- **2D Heatmap**: Tiled suitability rasters on Mapbox
- **3D Scene**: CesiumJS terrain visualization
- **Shadow Analysis**: Time-of-day shadow simulation
- **Parcel Inspector**: Point-query data inspector

### Module 5: Export & Reporting
- Automated PDF reports (WeasyPrint)
- GeoTIFF export (analysis results)
- Shapefile export (vectorized high-suitability zones)

### Module 6: PV Simulation
Industry-standard modeling using pvlib-python:
- Hourly 8760 generation profiles
- Configurable system parameters
- Detailed loss modeling

### Module 7: Financial Workbench
Investment analysis using PySAM:
- LCOE (Levelized Cost of Energy)
- IRR (Internal Rate of Return)
- Customizable financial parameters

## Data Sources & Licensing

| Dataset | Source | Resolution | License | Usage |
|---------|--------|------------|---------|-------|
| Solar Irradiance | NREL NSRDB | 4km | Public | Global baseline |
| DEM | SRTM 90m v4 | 90m | Public | Terrain analysis |
| Land Cover | ESA WorldCover | 10m | CC BY 4.0 | Constraints |
| Infrastructure | OpenStreetMap | Variable | ODbL | Proximity analysis |

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

[License information to be determined]

## Acknowledgments

This platform builds upon open-source tools and public datasets from:
- National Renewable Energy Laboratory (NREL)
- European Space Agency (ESA)
- OpenStreetMap contributors
- The pvlib, PySAM, and GDAL communities
