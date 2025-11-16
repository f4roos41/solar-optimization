# Contributing to the Global Solar Energy Planning Platform

Thank you for your interest in contributing to this project!

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- GDAL 3.6+
- PostgreSQL 15+ with PostGIS 3.3+

### Local Development

1. **Clone the repository:**
```bash
git clone <repository-url>
cd solar-optimization
```

2. **Backend setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend setup:**
```bash
cd frontend
npm install
```

4. **Start infrastructure:**
```bash
docker-compose up -d postgres rabbitmq
```

5. **Initialize database:**
```bash
cd backend
python scripts/init_db.py
```

6. **Start services:**

Terminal 1 (API):
```bash
cd backend
uvicorn api.main:app --reload
```

Terminal 2 (Worker):
```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

Terminal 3 (Frontend):
```bash
cd frontend
npm run dev
```

## Code Style

### Python

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `black` for code formatting
- Use `ruff` for linting

```bash
black backend/
ruff check backend/
mypy backend/
```

### TypeScript

- Follow Airbnb style guide
- Use TypeScript strict mode
- Use ESLint for linting
- Use Prettier for formatting

```bash
npm run lint
npm run type-check
```

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(mcda): add support for custom normalization ranges

- Allow users to define min/max values for factor normalization
- Add UI controls for normalization parameters
- Update geoprocessing engine to handle custom ranges

Closes #123
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Write or update tests as needed
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass
```

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=api --cov=workers tests/
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Tests

```bash
# Start all services
docker-compose up -d

# Run integration tests
python tests/integration/test_mcda_workflow.py
```

## Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring style for Python
- Use JSDoc comments for TypeScript

Python example:
```python
def process_mcda_job(db: Session, job: AnalysisJob) -> Dict:
    """
    Execute MCDA analysis job.

    Args:
        db: Database session
        job: AnalysisJob instance

    Returns:
        Dictionary with result URLs and statistics

    Raises:
        ValueError: If AOI not found
        RuntimeError: If processing fails
    """
```

TypeScript example:
```typescript
/**
 * Query raw data values at a specific point.
 *
 * @param lat - Latitude in decimal degrees
 * @param lon - Longitude in decimal degrees
 * @returns Promise resolving to point data
 */
async function queryPoint(lat: number, lon: number): Promise<PointData>
```

### Architecture Documentation

When adding new features, update:
- `docs/ARCHITECTURE.md` - System architecture
- `docs/API.md` - API documentation
- `README.md` - User-facing documentation

## Adding New Features

### Backend: New API Endpoint

1. Define Pydantic schema in `backend/api/schemas/`
2. Create route in `backend/api/routes/`
3. Implement service logic in `backend/api/services/`
4. Add database model if needed in `backend/models/`
5. Write tests in `backend/tests/`

### Backend: New Celery Task

1. Define task in `backend/workers/tasks.py`
2. Implement logic in `backend/workers/geoprocessing/`
3. Update job orchestration
4. Add unit tests

### Frontend: New Module

1. Create module directory in `frontend/src/modules/`
2. Implement React components
3. Add to routing in `App.tsx`
4. Update API service layer if needed
5. Add Storybook stories

### Data Pipeline: New Dataset

1. Add source configuration to `data-pipeline/configs/`
2. Create ingestion script in `data-pipeline/ingest/`
3. Add processing logic in `data-pipeline/processing/`
4. Update data catalog
5. Document in `data-pipeline/README.md`

## Performance Optimization

### Backend

- Use async/await for I/O operations
- Implement database query optimization (indexes, query plans)
- Use caching where appropriate (Redis)
- Profile with `cProfile` and `py-spy`

### Frontend

- Lazy load components
- Memoize expensive computations
- Use virtual scrolling for large lists
- Optimize bundle size (code splitting)

### Geoprocessing

- Use COG format for all rasters
- Implement tiling for large AOIs
- Parallelize independent operations
- Use GDAL VRT for virtual mosaics

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U solar_user -d solar_platform
```

**RabbitMQ connection errors:**
```bash
# Check RabbitMQ is running
docker ps | grep rabbitmq

# View management UI
open http://localhost:15672
```

**GDAL import errors:**
```bash
# Install GDAL
# Ubuntu:
sudo apt-get install gdal-bin libgdal-dev

# macOS:
brew install gdal
```

## Release Process

1. Update version in `package.json` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Build Docker images
6. Tag release
7. Deploy to staging
8. Run smoke tests
9. Deploy to production

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the problem, not the person
- Accept feedback graciously

## Questions?

- Open an issue for bugs or feature requests
- Use GitHub Discussions for questions
- Contact maintainers for security issues

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
