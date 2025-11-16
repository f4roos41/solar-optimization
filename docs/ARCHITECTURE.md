# Solar Platform Architecture Documentation

## System Overview

The Global Solar Energy Planning Platform is a distributed, cloud-native application designed for analyzing global solar energy potential using Multi-Criteria Decision Analysis (MCDA).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ React SPA    │  │ Mapbox GL JS │  │  CesiumJS 3D        │   │
│  │ (TypeScript) │  │ 2D Mapping   │  │  Visualization      │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/REST
┌────────────────────────────▼────────────────────────────────────┐
│                      APPLICATION TIER                            │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              FastAPI Application Server               │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │       │
│  │  │ Projects │  │ Analysis │  │  Data Query      │   │       │
│  │  │ Routes   │  │ Routes   │  │  (Parcel Insp.)  │   │       │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │       │
│  └──────────────────────────────────────────────────────┘       │
│                             │                                    │
│                   ┌─────────┴─────────┐                          │
│                   │                   │                          │
│         ┌─────────▼────────┐  ┌──────▼────────┐                │
│         │  RabbitMQ        │  │  PostgreSQL   │                 │
│         │  Message Broker  │  │  + PostGIS    │                 │
│         └─────────┬────────┘  └───────────────┘                 │
└───────────────────┼─────────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────────┐
│                    PROCESSING TIER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Celery Worker Pool (Auto-scaling)              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────────┐  │   │
│  │  │ MCDA       │  │ PV         │  │ Financial         │  │   │
│  │  │ Engine     │  │ Simulation │  │ Analysis          │  │   │
│  │  └────────────┘  └────────────┘  └───────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                         DATA TIER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Amazon S3 Data Lake                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐ │   │
│  │  │ Source   │  │ Results  │  │  Cloud-Optimized       │ │   │
│  │  │ COGs     │  │ Storage  │  │  GeoTIFFs (COGs)       │ │   │
│  │  └──────────┘  └──────────┘  └────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Tier

**Technology Stack:**
- React 18 + TypeScript
- Mapbox GL JS (2D mapping)
- CesiumJS + Resium (3D visualization)
- Zustand (state management)
- React Query (server state)

**Key Features:**
- Single Page Application (SPA)
- Interactive map-based UI
- Real-time job status polling
- Responsive design

### 2. Application Tier

**Technology Stack:**
- FastAPI (Python 3.11+)
- Pydantic (data validation)
- SQLAlchemy + GeoAlchemy2 (ORM)
- Python-JOSE (JWT auth)

**Key Responsibilities:**
- RESTful API endpoints
- Request validation
- Authentication/authorization
- Job orchestration
- Database operations

**API Design Principles:**
- Asynchronous job model (202 Accepted pattern)
- Resource-based routing
- OpenAPI/Swagger documentation
- CORS-enabled

### 3. Message Broker

**Technology:** RabbitMQ

**Purpose:**
- Decouple API from long-running processes
- Enable horizontal scaling of workers
- Provide job persistence and retry logic

**Queue Strategy:**
- Single "tasks" queue for MCDA jobs
- Separate queues for PV simulation and reporting
- Dead letter queue for failed jobs

### 4. Processing Tier

**Technology Stack:**
- Celery (task queue)
- Rasterio (raster I/O)
- GeoPandas (vector operations)
- RichDEM (terrain analysis)
- pvlib-python (PV simulation)
- PySAM (financial modeling)

**Worker Capabilities:**
- Auto-scaling based on queue depth
- Concurrent task execution
- Progress reporting
- Error recovery

**MCDA Workflow:**
```python
1. Load AOI geometry from PostGIS
2. Clip global COGs to AOI (HTTP range requests)
3. Calculate terrain derivatives (slope/aspect)
4. Create constraint mask (binary exclusions)
5. Normalize factors to 0-100 scale
6. Run weighted overlay
7. Apply constraints
8. Save result to S3
9. Generate statistics
10. Update job status
```

### 5. Data Tier

**Primary Storage:** Amazon S3

**Data Organization:**
```
s3://solar-platform-data-lake/
├── ghi.tif                    # 500 MB
├── dni.tif                    # 500 MB
├── dem.tif                    # 2.5 GB
├── slope.tif                  # 2.5 GB
├── distance_to_grid.tif       # 1 GB
├── distance_to_roads.tif      # 1 GB
├── lulc.tif                   # 10 GB
└── metadata/catalog.json      # 10 KB

s3://solar-platform-results/
└── results/
    ├── mcda_result_123.tif
    ├── mcda_result_124.tif
    └── ...
```

**Secondary Storage:** PostgreSQL + PostGIS

**Schema:**
- `users` - User accounts
- `projects` - Project metadata
- `areas_of_interest` - User-defined polygons (geometry)
- `analysis_jobs` - Job tracking (status, params, results)
- `infrastructure_osm` - Vector infrastructure (roads, grid)

## Data Flow

### Example: MCDA Analysis

**Step 1: User Initiates Analysis**
```
User draws polygon on map → React app
                           ↓
POST /analysis/{project_id}/run
{
  "weights_json": {"ghi": 40, "slope": 25, ...},
  "constraints_json": {"slope_gt": 10, ...}
}
                           ↓
FastAPI creates AnalysisJob (status=PENDING)
                           ↓
Pushes job to RabbitMQ → Returns 202 Accepted
```

**Step 2: Background Processing**
```
Celery Worker picks up job from queue
                ↓
Updates status to RUNNING
                ↓
Executes MCDA workflow:
  - Clips COGs from S3
  - Performs geoprocessing
  - Saves result to S3
                ↓
Updates status to COMPLETE
```

**Step 3: Results Retrieval**
```
React app polls GET /analysis/{job_id}/status
                ↓
Receives status=COMPLETE
                ↓
Calls GET /analysis/{job_id}/results
                ↓
Receives S3 URLs for result GeoTIFF and tiles
                ↓
Displays results on map
```

## Scalability

### Horizontal Scaling

**API Tier:**
- Stateless design allows multiple FastAPI instances
- Load balancer (AWS ALB) distributes requests
- Target: 1000 concurrent users

**Worker Tier:**
- Auto-scaling group based on queue depth
- Each worker handles 4 concurrent jobs
- Target: 50 concurrent analyses

**Database:**
- PostgreSQL read replicas for read-heavy operations
- Connection pooling (pgBouncer)

### Vertical Scaling

**Worker Instance Types:**
- MCDA jobs: c5.2xlarge (8 vCPU, 16 GB RAM)
- PV simulation: c5.4xlarge (16 vCPU, 32 GB RAM)

### Data Lake Optimization

**Cloud-Optimized GeoTIFFs:**
- Tiled structure (512x512 blocks)
- Internal overviews (pyramids)
- HTTP range request support
- Result: 95% reduction in data transfer

## Security

### Authentication
- JWT-based authentication
- Token expiration: 30 minutes
- Refresh token mechanism

### Authorization
- Role-based access control (RBAC)
- Project-level permissions
- Premium tier features

### Data Security
- S3 bucket encryption (AES-256)
- Presigned URLs for file access (1-hour expiration)
- VPC isolation for database

### API Security
- Rate limiting (100 req/min per user)
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

## Monitoring & Observability

### Metrics (Prometheus)
- API response times
- Job completion times
- Worker utilization
- S3 request rates

### Logging (ELK Stack)
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized aggregation

### Tracing (Jaeger)
- Distributed tracing across services
- Job execution timeline

### Alerts
- Job failures (>5% failure rate)
- API errors (>1% error rate)
- Worker health

## Disaster Recovery

### Backup Strategy
- Database: Daily full backup + WAL archiving
- S3: Cross-region replication
- Configuration: Version-controlled (Git)

### RTO/RPO
- Recovery Time Objective: 4 hours
- Recovery Point Objective: 1 hour

## Cost Optimization

**Data Transfer:**
- COG format reduces transfer by 95%
- CloudFront CDN for static tiles

**Compute:**
- Spot instances for workers (70% cost reduction)
- Auto-scaling based on demand

**Storage:**
- S3 Intelligent-Tiering
- Lifecycle policies (delete old results after 30 days)

**Estimated Monthly Cost (1000 analyses/month):**
- EC2 (workers): $500
- RDS (PostgreSQL): $200
- S3 (storage + transfer): $300
- **Total: ~$1000/month**

## Future Enhancements

1. **Real-time Collaboration:** WebSocket-based multi-user editing
2. **ML Integration:** Automated site ranking using trained models
3. **Edge Computing:** Local processing for data-constrained regions
4. **Blockchain:** Immutable audit trail for regulatory compliance
