# Development Setup Guide

Complete guide for setting up MetaAgent v2.0 for local development.

## Prerequisites

### Required Software

- **Node.js 20+** with pnpm package manager
- **Docker** and **Docker Compose** (or **Podman** with `podman compose`) for infrastructure
- **Git** for version control

### Optional Tools

- **MinIO Client (mc)** for object storage management
- **PostgreSQL client** for database inspection
- **Redis CLI** for queue debugging

## Infrastructure Setup

### 1. Start Core Services

MetaAgent uses docker-compose for local infrastructure (Podman users: use `podman compose`):

```bash
# Start PostgreSQL, Redis, and MinIO
cd infra
docker-compose up -d   # or: podman compose up -d

# Verify services are running
docker-compose ps   # or: podman compose ps
```

Services started:
- **PostgreSQL**: localhost:5432 (metaagent/postgres/devpassword)
- **Redis**: localhost:6379 (no auth)  
- **MinIO**: localhost:9000 (minioadmin/minioadmin)
- **MinIO Console**: localhost:9001 (web UI)

### 2. Initialize MinIO

Create the required storage bucket:

```bash
# Install MinIO client (macOS)
brew install minio/stable/mc

# Or download binary for other platforms:
# https://min.io/docs/minio/linux/reference/minio-mc.html

# Run initialization script
chmod +x infra/scripts/minio-init.sh
./infra/scripts/minio-init.sh
```

This creates the `metaagent-artifacts` bucket used for storing generated project files.

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your local settings (defaults should work)
# Key variables:
# - DATABASE_URL: PostgreSQL connection  
# - REDIS_URL: Redis connection
# - S3_*: MinIO connection settings
# - *_PORT: Service port configurations
```

## Application Setup

### 1. Install Dependencies

```bash
# Install all workspace dependencies
pnpm install

# This installs dependencies for:
# - Root workspace 
# - All apps/* packages
# - All services/* packages  
# - All packages/* packages
```

### 2. Build Packages

```bash
# Build all packages in dependency order
pnpm -w build

# This compiles TypeScript and prepares:
# - Shared packages (db, queue, templates, etc.)
# - Services (builder, runner)
# - Apps (web, desktop)
```

### 3. Database Setup

```bash
# Database migrations are handled automatically by Drizzle
# Schema files are in packages/db/migrations/

# To inspect the database:
psql postgresql://postgres:devpassword@localhost:5432/metaagent

# Key tables:
# - app_users: User accounts
# - spec_drafts: Agent specifications  
# - builder_artifacts: Generated project files
```

## Running Services

### Development Mode (All Services)

```bash
# Start all services in watch mode
pnpm -w dev

# This starts:
# - Web app (port 3000)
# - Builder service (port 3101) 
# - Runner service (port 3102)
```

### Individual Services

```bash
# Web application only
pnpm --filter @metaagent/web dev

# Builder service only  
pnpm --filter @metaagent/builder dev

# Runner service only
pnpm --filter @metaagent/runner dev
```

### Production Mode

```bash
# Build for production
pnpm -w build

# Start services
pnpm --filter @metaagent/web start
pnpm --filter @metaagent/builder start  
pnpm --filter @metaagent/runner start
```

## Testing

### Unit Tests

```bash
# Run all tests
pnpm -w test

# Test specific package
pnpm --filter @metaagent/builder test
pnpm --filter @metaagent/templates test

# Watch mode
pnpm --filter @metaagent/builder test --watch
```

### Integration Tests  

```bash
# Integration tests require Docker/Podman
pnpm --filter @metaagent/builder test:integration

# These tests:
# - Start MinIO container
# - Test full scaffold workflow
# - Validate generated projects
```

## Verification

### Health Checks

```bash
# Check service health
curl http://localhost:3000/healthz      # Web app
curl http://localhost:3101/healthz     # Builder service  
curl http://localhost:3102/healthz     # Runner service
```

### Test Scaffold Generation

```bash
# Generate a test project  
pnpm --filter @metaagent/builder build
pnpm --filter @metaagent/builder scaffold:tpl chatbot

# This creates a ZIP file in services/builder/dist/tmp-scaffold/
```

### Packaging Outputs
- Packaged zips are uploaded as builder artifact step `package:zip` and stored under `scaffolds/{user}/{draft}/{build}/project.zip` in object storage.
- Docker packaging (when enabled) exports an OCI tarball to `services/builder/dist/tmp-scaffold/docker-packaging/` for temporary staging before upload.
- Set `MOCK_DOCKER_BUILD=1` when running unit tests without Docker installed; packaging tests respect this flag.

### MinIO Browser

Visit http://localhost:9001 and log in with `minioadmin/minioadmin` to browse stored artifacts.

## Troubleshooting

### Common Issues

**Docker services not starting:**
```bash
# Check for port conflicts
docker-compose -f infra/docker-compose.yml down   # or: podman compose -f infra/docker-compose.yml down
docker-compose -f infra/docker-compose.yml up -d   # or: podman compose -f infra/docker-compose.yml up -d

# Check logs
docker-compose -f infra/docker-compose.yml logs
```

**Build failures:**
```bash
# Clean and rebuild
rm -rf node_modules
rm -rf packages/*/node_modules  
rm -rf services/*/node_modules
rm -rf apps/*/node_modules

pnpm install
pnpm -w build
```

**Database connection issues:**
```bash
# Verify PostgreSQL is running
docker-compose -f infra/docker-compose.yml ps

# Test connection
psql postgresql://postgres:devpassword@localhost:5432/metaagent -c "SELECT 1"
```

**MinIO bucket errors:**
```bash
# Recreate bucket
mc rm -r --force local/metaagent-artifacts
mc mb local/metaagent-artifacts
```

### Logs and Debugging

```bash
# View service logs
pnpm --filter @metaagent/builder dev  # Shows builder logs
pnpm --filter @metaagent/web dev      # Shows web app logs

# View infrastructure logs  
docker-compose -f infra/docker-compose.yml logs -f postgres
docker-compose -f infra/docker-compose.yml logs -f redis
docker-compose -f infra/docker-compose.yml logs -f minio

# View BullMQ job queue (Redis)
redis-cli -p 6379
KEYS *                    # Show all keys
LLEN bull:builder-scaffold:waiting  # Check queue length
```

### Port Conflicts

Default ports used:
- 3000: Web app
- 3101: Builder service  
- 3102: Runner service
- 5432: PostgreSQL
- 6379: Redis
- 9000: MinIO API
- 9001: MinIO Console

Change ports in `.env` if conflicts occur.

## IDE Setup

### VS Code

Recommended extensions:
- TypeScript and JavaScript Language Features
- Prettier
- ESLint  
- Docker
- PostgreSQL

### Environment Configuration

Create `.vscode/settings.json`:
```json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

## Next Steps

After setup is complete:
1. Visit http://localhost:3000 to access the web UI
2. Create a test agent specification
3. Try the scaffold generation workflow
4. Review the [Architecture Guide](architecture.md) to understand the system
5. Check the [Delivery Plan](delivery_plan.md) for current development status
