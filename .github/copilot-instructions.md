# TerraVisu Development Instructions

TerraVisu is an interactive web application for visualizing and analyzing spatial data. It consists of a Django backend, React frontend, and React admin panel, all orchestrated with Docker Compose.

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information here is incomplete or found to be in error.**

## Core Architecture

- **Backend**: Django 4.2 with PostGIS for spatial data
- **Frontend**: React application built with Create React App (visu-front submodule)
- **Admin Panel**: React Admin application (terra-admin submodule)
- **Database**: PostgreSQL with PostGIS extension
- **Search**: Elasticsearch 7.16.2
- **Cache**: Redis
- **Task Queue**: Celery with Redis broker
- **Development**: Docker Compose environment

## Repository Structure

```
TerraVisu/
├── project/           # Django backend application
├── front/            # React frontend (git submodule)
├── admin/            # React admin panel (git submodule)
├── docs/             # Sphinx documentation
├── .docker/          # Docker configuration files
├── conf/             # Configuration files
├── public/           # Static files and frontend builds
├── Makefile          # Build automation
└── docker-compose.yml # Development environment
```

## Essential First Steps

**CRITICAL**: Always run these steps in exact order for any fresh clone:

1. **Initialize git submodules** (REQUIRED - frontend code is in submodules):
   ```bash
   git submodule init
   git submodule update
   ```

2. **Set up environment files**:
   ```bash
   cp db.env.dist db.env
   cp app.env.dist app.env
   ```

3. **Configure app.env** - Add these REQUIRED variables:
   ```bash
   echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> app.env
   echo "SECRET_KEY=your-development-secret-key-here" >> app.env
   ```

4. **Set Docker user permissions**:
   ```bash
   touch .env
   echo "UID=$UID" >> .env
   echo "GID=$(id -g)" >> .env
   ```

## Build and Development Commands

### Docker Environment Setup

**NEVER CANCEL builds or long-running commands. Set timeouts of 60+ minutes.**

1. **Pull base images** (5-10 minutes):
   ```bash
   docker compose pull
   ```

2. **Build Django backend** (15-30 minutes, NEVER CANCEL):
   ```bash
   docker compose build web
   # Timeout: 30+ minutes, network connectivity required
   ```

3. **Start services** (2-5 minutes):
   ```bash
   docker compose up -d
   ```

### Backend Development

**Database setup** (REQUIRED for first run):
```bash
# Run migrations (2-3 minutes)
docker compose run --rm web ./manage.py migrate

# Load initial data
docker compose run --rm web ./manage.py loaddata project/fixtures/initial.json

# Create superuser (interactive)
docker compose run --rm web ./manage.py createsuperuser
```

**Django management commands**:
```bash
# Run any Django command
make django [command]
# Example: make django shell
# Example: make django collectstatic
```

**Testing** (5-15 minutes, NEVER CANCEL):
```bash
# Run tests
make test
# OR detailed version:
make tests

# Run with coverage (10-20 minutes)
make coverage
```

### Frontend Development

**Build admin panel** (10-20 minutes, NEVER CANCEL):
```bash
make build_admin
# This runs: npm ci --legacy-peer-deps && npx react-scripts --openssl-legacy-provider build
# Timeout: 20+ minutes
```

**Build main frontend** (15-25 minutes, NEVER CANCEL):
```bash
make build_front  
# This runs: npm ci --production && npm run build
# Timeout: 25+ minutes
```

**Frontend development workflow**:
```bash
# For admin panel development:
cd admin
npm ci --legacy-peer-deps
npm start  # Starts dev server on default port

# For frontend development:
cd front
npm ci
cp public/env.dist.json public/env.json
cp public/settings.dist.json public/settings.json
npm start  # Starts dev server on default port
```

### Code Quality and Linting

**ALWAYS run before committing**:
```bash
# Format code
make format

# Lint code  
make lint

# Run both
make quality
```

**Manual linting** (without Docker):
```bash
# Install ruff locally first:
pip install ruff

# Check linting
ruff check project

# Check formatting
ruff format --check project
```

## Running the Application

**Full stack development**:
```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f [service-name]
```

**Access URLs**:
- Main application: http://localhost:8080/
- Backend API: http://localhost:8000/
- Django admin: http://localhost:8000/admin/
- Frontend (development): http://localhost:3000/ (when running npm start)
- Admin panel (development): http://localhost:3001/ (when running npm start in admin/)

## Critical Timeout and Timing Information

**NEVER CANCEL these operations:**

- `docker compose build web`: 15-30 minutes (network dependent)
- `make build_admin`: 10-20 minutes  
- `make build_front`: 15-25 minutes
- `make test`: 5-15 minutes
- `make coverage`: 10-20 minutes
- `npm ci` (in frontend directories): 5-15 minutes
- Initial database migration: 2-3 minutes

**Set explicit timeouts:**
- Build commands: 30+ minutes
- Test commands: 20+ minutes
- npm install commands: 20+ minutes

## Testing and Validation

**Backend testing**:
```bash
# Quick test
make test

# Detailed test with coverage
make coverage

# Test specific app
docker compose run --rm web ./manage.py test project.visu
```

**Frontend testing**:
```bash
# Admin panel tests
cd admin
npm test

# Frontend tests  
cd front
npm test

# E2E tests (Cypress)
cd front
npm run cypress:run
```

**Manual validation scenarios** (ALWAYS test after changes):

1. **Backend API validation**:
   - Access http://localhost:8000/admin/ and log in
   - Create a test data entry
   - Verify API endpoints respond at http://localhost:8000/api/

2. **Frontend validation**:
   - Access main app at http://localhost:8080/
   - Test map functionality and data visualization
   - Check responsive design on different screen sizes

3. **Admin panel validation**:
   - Access admin interface  
   - Test CRUD operations
   - Verify user permissions

## Documentation

**Build documentation** (5-10 minutes):
```bash
make docs_build
# OR for live development:
make docs_serve  # Available at http://localhost:8800/
```

## Common Issues and Solutions

**Network connectivity issues**:
- Docker builds may fail due to PyPI timeouts
- Retry builds with: `docker compose build web --no-cache`
- Check Docker daemon status if pulls fail

**Frontend submodule issues**:
- Always run `git submodule update` after pulling changes
- If submodules are empty, re-run `git submodule init && git submodule update`

**Permission issues**:
- Ensure .env file contains correct UID/GID values
- Run: `docker compose down && docker compose up -d` after fixing permissions

**Database issues**:
- Reset database: `docker compose down -v && docker compose up -d db`
- Re-run migrations after database reset

## CI/CD Integration

**GitHub Actions workflows**:
- `.github/workflows/test.yml`: Backend testing
- `.github/workflows/lint.yml`: Code quality checks  
- `.github/workflows/doc.yml`: Documentation builds

**Pre-commit validation** (CRITICAL):
```bash
# ALWAYS run before committing:
make quality  # Runs lint + format
make test     # Runs backend tests

# For frontend changes, also run:
cd front && npm test
cd admin && npm test
```

## Key Development Files

**Backend**:
- `project/visu/`: Main application code
- `project/settings/`: Django settings
- `requirements.txt`: Python dependencies
- `pyproject.toml`: Project configuration

**Frontend**:
- `front/src/`: React frontend source
- `front/package.json`: Frontend dependencies
- `admin/src/`: Admin panel source  
- `admin/package.json`: Admin dependencies

**Configuration**:
- `docker-compose.yml`: Development environment
- `Makefile`: Build automation
- `conf/`: Nginx and other configs

## Environment Variables Reference

**Database (db.env)**:
```
POSTGRES_DB=terra-visu
POSTGRES_USER=terra-visu  
POSTGRES_PASSWORD=terra-visu
```

**Application (app.env)**:
```
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=your-secret-key
SSL_ENABLED=False
OIDC_ENABLE_LOGIN=False
# Add other OIDC settings as needed
```

**Docker (.env)**:
```
UID=1000
GID=1000
```

## Production Deployment

**Build production image**:
```bash
make build_prod
# This includes frontend builds and creates production Docker image
```

**Using install package**:
- Download from GitHub releases: install.zip
- Follow instructions in `install/README.rst`
- Use `docker compose up -d` for production deployment

Remember: TerraVisu is a complex spatial data application. Always validate changes thoroughly with real map data and user workflows.