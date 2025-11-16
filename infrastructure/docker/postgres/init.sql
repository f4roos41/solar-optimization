-- Database initialization script
-- This script is automatically executed when the PostgreSQL container starts

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS infrastructure;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO solar_user;
GRANT ALL PRIVILEGES ON SCHEMA infrastructure TO solar_user;

-- Note: Database tables will be created by SQLAlchemy/Alembic migrations
-- This script only sets up the initial database structure and extensions
