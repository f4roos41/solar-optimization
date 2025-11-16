# Quick Start Guide

## 5-Minute Setup

This guide will get you up and running with the Solar Platform in 5 minutes.

### Prerequisites

- Docker Desktop installed and running
- Git
- 8 GB RAM minimum
- 20 GB free disk space

### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd solar-optimization
cp .env.example .env
```

### Step 2: Configure Environment

Edit `.env` and set the required variables:

```bash
# Minimum required configuration
DATABASE_URL=postgresql://solar_user:solar_password@localhost:5432/solar_platform
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
SECRET_KEY=your-secret-key-change-this

# Optional: Mapbox token for frontend
REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
```

### Step 3: Start Services

```bash
# Start infrastructure (PostgreSQL + RabbitMQ)
docker-compose up -d postgres rabbitmq

# Wait for services to be healthy (30 seconds)
docker-compose ps
```

### Step 4: Initialize Database

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
```

### Step 5: Start Application

**Terminal 1 - API Server:**
```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload
```

**Terminal 2 - Worker:**
```bash
cd backend
source venv/bin/activate
celery -A workers.celery_app worker --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Step 6: Access the Application

Open your browser to:
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **RabbitMQ Admin:** http://localhost:15672 (guest/guest)

## First Project

### Create a Project

1. Go to http://localhost:3000
2. Click "New Project"
3. Enter a name (e.g., "California Solar Site")
4. Click "Create"

### Define Area of Interest

1. Click "Draw AOI" button
2. Click on the map to define a polygon
3. Double-click to finish
4. Review calculated area

### Run Analysis

1. Click "Configure Analysis"
2. Set factor weights:
   - Solar Irradiance (GHI): 40%
   - Terrain Slope: 25%
   - Grid Proximity: 20%
   - Road Proximity: 15%
3. Set constraints:
   - Maximum slope: 10°
   - Exclude: Urban areas, Water bodies
   - Maximum distance to grid: 10 km
4. Click "Run Analysis"
5. Monitor progress (2-10 minutes)

### View Results

1. When complete, view the suitability heatmap
2. Click points on the map to inspect raw data
3. Export results as GeoTIFF or PDF report

## Sample Data

The platform ships with sample data for testing:

```
Sample AOI: 34.05°N, -118.25°W (Los Angeles area)
Sample Size: 500 km²
Expected Processing Time: 3-5 minutes
```

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# View logs
docker logs solar-platform-db
```

### RabbitMQ Connection Error

```bash
# Check RabbitMQ is running
docker ps | grep rabbitmq

# Restart if needed
docker-compose restart rabbitmq
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### GDAL Import Error (Python)

```bash
# Ubuntu
sudo apt-get install gdal-bin libgdal-dev python3-gdal

# macOS
brew install gdal
export GDAL_CONFIG=/usr/local/bin/gdal-config

# Then reinstall Python packages
pip install --no-cache-dir GDAL==3.8.1
```

### Frontend Won't Start

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Next Steps

- Read the [Architecture Documentation](ARCHITECTURE.md)
- Explore the [API Documentation](http://localhost:8000/docs)
- Learn about [Data Sources](../data-pipeline/README.md)
- Review the [Strategic Blueprint](STRATEGIC_BLUEPRINT.md)

## Production Deployment

For production deployment instructions, see:
- [Deployment Guide](DEPLOYMENT.md)
- [Infrastructure Setup](../infrastructure/README.md)

## Getting Help

- **Issues:** https://github.com/your-org/solar-optimization/issues
- **Discussions:** https://github.com/your-org/solar-optimization/discussions
- **Email:** support@solar-platform.com
