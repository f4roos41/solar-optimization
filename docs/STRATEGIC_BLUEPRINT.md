# Strategic Blueprint: Global Solar Energy Planning Platform

## Executive Summary

This document presents a comprehensive strategic blueprint for building a next-generation global solar energy planning platform that competes with and exceeds the capabilities of the Global Solar Atlas (GSA) by the World Bank Group.

### Strategic Differentiation

The Global Solar Atlas is fundamentally a **"Data Browser"** - it displays pre-computed PVOUT (Photovoltaic Power Output) data from Solargis proprietary models. Users cannot modify assumptions or customize analysis parameters.

Our platform is an **"Analysis Engine"** that empowers users to:
- Define custom suitability criteria through Multi-Criteria Decision Analysis (MCDA)
- Assign weights to economic and engineering drivers (solar irradiance, terrain slope, grid proximity)
- Create new, custom suitability maps from raw data
- Run bankable PV simulations with transparent, auditable models
- Generate investment-grade financial analysis (LCOE, IRR)

This fundamental architectural difference represents our core competitive advantage.

## Platform Architecture

### 7-Module System Design

**Module 1: AOI Definition Tool**
- Interactive polygon drawing using Mapbox GL Draw
- File import (Shapefile, GeoJSON, KML)
- Real-time area calculation using Turf.js
- Validation against maximum AOI size limits

**Module 2: Data Layer Library**
- **Tier 1 (Global Baseline):** Public datasets ensuring global coverage
  - Solar: NREL NSRDB (GHI/DNI)
  - Terrain: SRTM 90m DEM
  - Land Cover: ESA WorldCover 10m
  - Infrastructure: OpenStreetMap (roads, transmission lines)
- **Tier 2 (Premium):** Commercial APIs for bankable-grade data
  - Solargis API for high-resolution solar data
  - Solcast API for real-time irradiance forecasting

**Module 3: MCDA Workbench (Core Innovation)**
- Custom weighted overlay analysis
- User-defined factor weights (totaling 100%)
- Binary constraint toggles (slope, land use, distance thresholds)
- Real-time suitability map generation
- Transparent, reproducible analysis methodology

**Module 4: Visualization Suite**
- **2D Heatmap:** Tiled suitability rasters on Mapbox GL JS
- **3D Scene:** CesiumJS terrain visualization with texture draping
- **Shadow Analysis:** Time-of-day and seasonal shadow simulation
- **Parcel Inspector:** Point-query tool for raw data inspection

**Module 5: Export & Reporting**
- Automated PDF report generation using WeasyPrint
- GeoTIFF export for GIS analysis
- Shapefile export of high-suitability zones
- Investment-grade documentation

**Module 6: PV Simulation Engine**
- Industry-standard modeling using pvlib-python
- Transparent, open-source algorithms
- Hourly 8760 generation profiles
- Configurable system parameters
- Detailed loss modeling (soiling, shading, degradation)

**Module 7: Financial Workbench**
- LCOE (Levelized Cost of Energy) calculation
- IRR (Internal Rate of Return) modeling
- PySAM integration (NREL's System Advisor Model)
- Customizable financial parameters (CAPEX, OPEX, discount rates)
- Pro-forma cash flow analysis

## Technical Stack

### Backend (Python)
```
FastAPI          → High-performance async API server
Celery + RabbitMQ → Asynchronous job processing
PostgreSQL + PostGIS → Spatial database
Rasterio         → Raster I/O and manipulation
GeoPandas        → Vector operations
RichDEM          → Fast terrain analysis
pvlib-python     → PV simulation
PySAM            → Financial modeling
```

### Frontend (TypeScript)
```
React 18         → UI framework
Mapbox GL JS     → 2D mapping
CesiumJS         → 3D visualization
Turf.js          → Client-side geospatial operations
Zustand          → State management
React Query      → Server state management
```

### Data Infrastructure
```
Amazon S3        → Data lake storage
Cloud-Optimized GeoTIFFs (COGs) → Efficient raster access
AWS Batch / Airflow → ETL pipeline orchestration
```

## Data Architecture: The Dual-Source Pipeline

### Architectural Principle

All core MCDA functionality operates on **Tier 1 (public)** data, ensuring:
- Zero licensing costs for basic operations
- Global coverage without gaps
- Legal compliance (CC BY 4.0, ODbL licenses)

A **data abstraction layer** allows seamless swapping to **Tier 2 (premium)** APIs for specific AOIs, providing:
- Higher resolution for project developers
- Bankable-grade data for investment decisions
- Clear upgrade path for high-value customers

### Data Lake Structure

```
S3://solar-platform-data-lake/
├── ghi.tif                    # Global Horizontal Irradiance (NREL NSRDB, 4km)
├── dni.tif                    # Direct Normal Irradiance (NREL NSRDB, 4km)
├── dem.tif                    # Digital Elevation Model (SRTM 90m, hole-filled)
├── slope.tif                  # Slope in degrees (derived from DEM)
├── aspect.tif                 # Aspect in degrees (derived from DEM)
├── lulc.tif                   # Land Use/Land Cover (ESA WorldCover 10m)
├── distance_to_grid.tif       # Pre-calculated proximity raster (1km resolution)
├── distance_to_roads.tif      # Pre-calculated proximity raster (1km resolution)
└── metadata/catalog.json      # Data catalog with metadata
```

### Critical Optimization: Pre-Calculated Proximity Rasters

**Problem:** On-the-fly proximity calculations over large AOIs are computationally prohibitive (10-30 minutes per layer).

**Solution:** Treat proximity maps as **source data**, not derived data.

**Implementation:**
1. During ETL, rasterize OSM vectors (roads, transmission lines) to binary rasters
2. Run global distance transform using `gdal_proximity.py`
3. Store results as COGs in the data lake
4. During analysis, proximity is a simple raster clip operation (< 5 seconds)

**Result:** 95% reduction in processing time for infrastructure proximity analysis.

## MCDA Geoprocessing Workflow

The core analytical workflow implements a **weighted overlay** analysis:

```python
1. Load AOI Geometry
   └─→ Query PostGIS for user-defined polygon

2. Clip Global COGs to AOI
   └─→ HTTP range requests to S3 (only download AOI extent)

3. Calculate Terrain Derivatives
   └─→ RichDEM: slope and aspect from DEM

4. Create Constraint Mask
   └─→ Binary exclusions:
       • Slope > threshold
       • Land cover in excluded classes (urban, water)
       • Distance to grid > max distance

5. Normalize Factors to 0-100 Scale
   └─→ Linear scaling with min/max clipping
       • Higher values = better (GHI)
       • Lower values = better (slope, distance) → inverted

6. Run Weighted Overlay
   └─→ final_map = Σ (normalized_factor × weight / 100)

7. Apply Constraints
   └─→ Set excluded pixels to NoData

8. Save Result to S3
   └─→ Upload GeoTIFF with compression

9. Generate Statistics
   └─→ Mean, max, min suitability; excluded area

10. Update Job Status
    └─→ PostGIS: status = COMPLETE
```

## Asynchronous Job Architecture

### The Problem
Synchronous API calls for long-running analyses (5-15 minutes) cause HTTP timeouts and poor UX.

### The Solution: Job Queue Pattern

```
┌─────────┐                ┌──────────┐
│  User   │   POST /run    │ FastAPI  │
│ (React) │───────────────→│   API    │
└─────────┘                └────┬─────┘
     ▲                          │
     │                          │ 1. Create Job (status=PENDING)
     │                          │ 2. Push to RabbitMQ
     │                          │ 3. Return 202 Accepted
     │                          ▼
     │                     ┌──────────┐
     │   Poll /status      │ RabbitMQ │
     │◄─────(every 5s)     │  Queue   │
     │                     └────┬─────┘
     │                          │
     │                          │ Consume
     │                          ▼
     │                     ┌──────────┐
     │                     │  Celery  │
     │                     │  Worker  │
     │                     └────┬─────┘
     │                          │
     │                          │ 1. Update: status=RUNNING
     │                          │ 2. Execute MCDA workflow
     │                          │ 3. Update: status=COMPLETE
     │                          │
     └──────────────────────────┘
```

### Benefits
- API remains responsive (< 500ms response)
- Horizontal scaling of workers
- Job persistence and retry logic
- Progress tracking
- Graceful error handling

## Competitive Analysis: GSA vs. Our Platform

| Feature | Global Solar Atlas | Our Platform | Strategic Advantage |
|---------|-------------------|--------------|---------------------|
| **Analysis Type** | Data Browser (pre-computed) | Analysis Engine (on-demand) | ✓ User customization |
| **MCDA Capability** | ✗ None | ✓ Full custom weighting | ✓ Flexible suitability criteria |
| **Constraints** | ✗ Fixed | ✓ User-defined toggles | ✓ Site-specific exclusions |
| **PV Simulation** | Solargis (black box) | pvlib (open-source) | ✓ Transparent & auditable |
| **Financial Analysis** | ✗ None | ✓ LCOE/IRR with PySAM | ✓ Investment-grade analysis |
| **3D Visualization** | ✗ None | ✓ CesiumJS with shadows | ✓ Virtual site inspection |
| **Data Export** | Regional GeoTIFF | GeoTIFF + Shapefile + PDF | ✓ Professional deliverables |
| **Global Coverage** | ✓ Yes (Solargis data) | ✓ Yes (NREL/ESA/OSM) | ✓ No vendor lock-in |
| **Premium Data** | ✗ N/A | ✓ API integration layer | ✓ Upgrade path |

## Data Licensing & Legal Compliance

All Tier 1 data sources are legally licensed for commercial use:

| Dataset | Source | License | Commercial Use | Attribution Required |
|---------|--------|---------|----------------|---------------------|
| NREL NSRDB | U.S. Government | Public Domain | ✓ Yes | Recommended |
| SRTM 90m | CGIAR-CSI | Public Domain | ✓ Yes | No |
| ESA WorldCover | European Space Agency | CC BY 4.0 | ✓ Yes | ✓ Yes |
| OpenStreetMap | OSM Contributors | ODbL | ✓ Yes | ✓ Yes |

**GSA Data:** The World Bank's Global Solar Atlas provides downloadable GeoTIFFs under CC BY 4.0, which can be legally ingested as a validation/calibration dataset.

## Scalability & Performance

### Horizontal Scaling
- **API:** Stateless FastAPI instances behind load balancer
- **Workers:** Auto-scaling Celery worker pool (EC2 Auto Scaling Group)
- **Database:** PostgreSQL read replicas for read-heavy operations

### Performance Targets
- **AOI Definition:** < 500ms to save polygon to PostGIS
- **MCDA Job Submission:** < 1s to validate and queue job
- **MCDA Execution:** 2-10 minutes for typical AOI (1000-5000 km²)
- **Point Query (Parcel Inspector):** < 2s to sample all layers

### Cost Optimization
- **COG Format:** 95% reduction in data transfer vs. full raster download
- **Spot Instances:** 70% cost reduction for worker fleet
- **S3 Intelligent-Tiering:** Automatic cost optimization for infrequently accessed data

## Security Architecture

### Authentication & Authorization
- JWT-based authentication with 30-minute expiration
- Role-based access control (RBAC): Free tier, Professional, Enterprise
- Project-level permissions

### Data Security
- S3 bucket encryption (AES-256)
- Presigned URLs for file access (1-hour expiration)
- VPC isolation for database

### API Security
- Rate limiting (100 requests/minute per user)
- Input validation (Pydantic schemas)
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration

## Implementation Roadmap

### Phase 1: MVP (Months 1-3)
- ✓ Backend infrastructure (FastAPI, Celery, PostgreSQL)
- ✓ MCDA core engine
- ✓ Data ingestion pipeline for SRTM + NREL
- ✓ Basic React frontend with Mapbox
- ✓ AOI definition tool
- ✓ 2D suitability map visualization

### Phase 2: Enhanced Analysis (Months 4-6)
- 3D visualization with CesiumJS
- Shadow analysis implementation
- Parcel Inspector (point query tool)
- PV simulation integration (pvlib)
- PDF report generation

### Phase 3: Financial Platform (Months 7-9)
- PySAM integration for LCOE/IRR
- Financial parameter UI
- Investment-grade reporting
- Export functionality (Shapefile, GeoTIFF)

### Phase 4: Scale & Optimize (Months 10-12)
- Premium data source integrations (Solargis, Solcast APIs)
- Advanced user management
- Collaboration features
- Performance optimization
- Production deployment

## Market Positioning

### Target Customer Segments

**1. Project Developers ($500-2000/month)**
- Primary use case: Site selection for utility-scale solar
- Value proposition: MCDA + 3D visualization + bankable PV simulation

**2. Investment Banks & Funds ($2000-10000/month)**
- Primary use case: Portfolio screening and due diligence
- Value proposition: LCOE/IRR analysis + automated reporting + premium data

**3. Government & NGOs (Custom pricing)**
- Primary use case: National renewable energy planning
- Value proposition: Global coverage + transparent methodology + data sovereignty

**4. Researchers & Universities (Free tier)**
- Primary use case: Academic research
- Value proposition: Open-source tools + reproducible analysis + data access

### Pricing Strategy

**Free Tier:**
- 5 projects
- Public data only (Tier 1)
- Basic MCDA (3 factors)
- 2D visualization only

**Professional ($99/month):**
- Unlimited projects
- Full MCDA (all factors)
- 3D + shadow analysis
- PV simulation
- PDF reports

**Enterprise (Custom):**
- Premium data sources (Tier 2 APIs)
- LCOE/IRR financial analysis
- Priority processing
- Dedicated support
- White-label option

## Technical Risks & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **Data Lake Size** (>2 TB) | High | High | Use COG format, S3 Intelligent-Tiering, delete old results |
| **Processing Time** (>15 min for large AOI) | Medium | Medium | Implement tiling, show progress bar, optimize algorithms |
| **OSM Data Quality** (gaps in grid data) | Medium | Medium | Provide premium data upgrade, crowdsource corrections |
| **AWS Costs** (>$5000/month) | High | Low | Spot instances, auto-scaling, cost alerts |
| **Solargis API Costs** | Medium | Medium | Cache results, implement usage quotas per tier |

## Success Metrics

### Technical KPIs
- MCDA job completion time: < 10 minutes (p95)
- API uptime: > 99.5%
- Error rate: < 1%
- Data transfer costs: < $0.10 per analysis

### Business KPIs
- Monthly Active Users: 1000 (Year 1)
- Conversion rate (Free → Professional): > 5%
- Customer retention: > 80%
- Net Promoter Score (NPS): > 50

## Conclusion

This platform represents a fundamental architectural shift from "data browsing" to "data analysis." By empowering users with transparent, customizable MCDA workflows, industry-standard PV simulation, and investment-grade financial modeling, we deliver a superior value proposition to project developers, investors, and researchers worldwide.

The strategic use of public datasets for global baseline coverage, combined with a premium tier for high-resolution commercial data, ensures both accessibility and scalability. The asynchronous job architecture and Cloud-Optimized GeoTIFF data lake provide the technical foundation for a performant, cost-effective platform capable of handling thousands of concurrent analyses.

**This is not a clone of the Global Solar Atlas. This is the next generation.**
