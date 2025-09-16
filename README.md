# MetaAgent v2.0

MetaAgent is a Mastra-based platform for building, testing, and deploying AI agents. Create agents through a guided interview process, then deploy them locally or to the cloud.

## Quick Start

### Prerequisites

- Node.js 20+ and pnpm
- Docker and Docker Compose (or Podman with `podman compose`)  
- Git

### Development Setup

1. **Clone and install dependencies**:
   ```bash
   git clone <repo-url>
   cd meta-agent
   pnpm i
   ```

2. **Start infrastructure**:
   ```bash
   # Start PostgreSQL, Redis, and MinIO
   pnpm db:up   # or: pnpm db:up:podman
   
   # Initialize MinIO bucket (requires mc client)
   brew install minio/stable/mc  # macOS
   ./infra/scripts/minio-init.sh
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Build and start services**:
   ```bash
   # Build all packages
   pnpm -w build
   
   # Start all services in development mode
   pnpm -w dev
   ```

5. **Access the application**:
   - Web UI: http://localhost:3000
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

## Architecture

MetaAgent follows a microservices architecture:

- **Web App (Remix)**: User interface for agent creation and management
- **Builder Service**: Processes agent specifications and generates projects  
- **Runner Service**: Executes agents in controlled environments
- **Queue System**: BullMQ with Redis for background job processing
- **Database**: PostgreSQL with RLS for multi-tenant data isolation
- **Object Storage**: S3-compatible storage (MinIO) for artifacts

## Key Features

- **Template-based Agent Creation**: Choose from chatbot, web automation, or API copilot templates
- **Interactive Interview Process**: Guided questions to build agent specifications
- **Real-time Spec Validation**: Live validation with JSON Schema and Monaco editor
- **Project Scaffolding**: Generate complete, deployable Mastra projects
- **Background Processing**: Async job processing with queue management
- **Multi-tenant Architecture**: User isolation with row-level security

## Environment Variables

Core configuration (see `.env.example` for complete list):

```env
# Database  
DATABASE_URL=postgresql://user@localhost:5432/metaagent
REDIS_URL=redis://localhost:6379

# Object Storage (MinIO/S3)
S3_ENDPOINT=http://localhost:9000
S3_KEY=minioadmin
S3_SECRET=minioadmin
BUILDER_BUCKET=metaagent-artifacts

# Security - Egress Allow-List
ALLOW_HTTP_HOSTS=["api.openai.com","google.serper.dev"]

# Services
PORT=3000
BUILDER_PORT=3101  
RUNNER_PORT=3102
```

## Development Commands

```bash
# Build all packages
pnpm -w build

# Run all services  
pnpm -w dev

# Run tests
pnpm -w test

# Run specific service
pnpm --filter @metaagent/web dev
pnpm --filter @metaagent/builder dev

# Database migrations
# (TBD - migrations system pending)
```

## Project Structure

```
├── apps/
│   ├── desktop/          # Electron app (Week 7)
│   └── web/              # Remix web application
├── services/
│   ├── builder/          # Agent building and scaffolding service
│   └── runner/           # Agent execution service  
├── packages/
│   ├── db/               # Database schema and utilities
│   ├── templates/        # Agent templates and metadata
│   ├── spec/             # Specification types and validation
│   ├── queue/            # BullMQ job queue utilities
│   ├── object-storage/   # S3/MinIO storage utilities
│   └── ...               # Additional shared packages
├── infra/
│   ├── docker-compose.yml # Local development infrastructure
│   └── scripts/          # Setup and deployment scripts
└── docs/                 # Documentation and specifications
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Security](docs/security.md)
- [Project Scaffolder](docs/scaffolder.md)
- [Development Decisions](docs/decisions.md)
- [Delivery Plan](docs/delivery_plan.md)
- [Complete Docs Index](docs/README.md)

## Contributing

1. Follow the [feature PR checklist](docs/checklists.md#feature-pr-checklist)
2. Ensure tests pass: `pnpm -w test` 
3. Build successfully: `pnpm -w build`
4. Update documentation as needed

## Amp Toolbox: codex-code-review

A toolbox tool is provided to run OpenAI Codex CLI to review a GitHub PR.

Setup:
- Install Codex CLI: `npm i -g @openai/codex` (or `brew install codex`)
- Export toolbox path: `export AMP_TOOLBOX="$(pwd)/toolboxes"`
- Optional: set `GITHUB_TOKEN` for private repos and higher rate limits

Usage in Amp:
- Tool name: `codex-code-review`
- Required param: `pr_url` (e.g., `https://github.com/owner/repo/pull/123`)
- Optional params: `model` (default `GPT-5-Codex`), `github_token`, `max_diff_bytes`

Example invocation:
- pr_url: https://github.com/openai/codex/pull/1
- model: GPT-5-Codex

The tool fetches the PR diff via GitHub API and invokes `codex exec` with a structured review prompt.

## License

[License TBD]
