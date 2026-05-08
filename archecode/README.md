# ArcheCode

> **AI-Powered Code Archaeology Platform** — Understand any codebase in 10 minutes.

ArcheCode automatically analyzes unfamiliar codebases to help developers quickly understand project architecture, find bugs, detect security vulnerabilities, and generate documentation — all powered by AI.

## Features

- **Project Analysis** — Upload a zip file or import from GitHub. Automatic extraction, indexing, and analysis.
- **Architecture Detection** — Identifies MVC, Clean Architecture, microservices, and other patterns.
- **Code Quality Analysis** — Detects dead code, magic numbers, long functions, duplicate blocks, empty catches, TODO/FIXME markers, and suspicious naming.
- **Security Scanning** — Finds SQL injection, XSS, eval usage, hardcoded secrets, command injection, path traversal, weak crypto, and unsafe deserialization.
- **Dependency Analysis** — Maps module imports, function relationships, class hierarchies, and circular dependencies.
- **Complexity Metrics** — Measures cyclomatic complexity, nesting depth, and file size.
- **AI Documentation** — Generates README, architecture descriptions, and refactoring suggestions using OpenAI.
- **Interactive Chat** — Ask natural-language questions about the codebase with AI-powered contextual answers.
- **Dependency Graphs** — Visualizes module dependencies and function call relationships using React Flow.
- **Health Score** — Calculates an overall project health score from 0-100 based on all findings.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, TailwindCSS, React Flow, shadcn/ui |
| Backend | Python 3.11+, FastAPI, Pydantic, uvicorn |
| AI | OpenAI API (GPT-4o), sentence-transformers, FAISS |
| Analysis | AST parsing, regex patterns, NetworkX, tree-sitter |
| DevOps | Docker, Docker Compose |

## Project Structure

```
archecode/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── core/
│   │   └── config.py        # Application configuration
│   ├── models/
│   │   ├── project.py       # Project data models
│   │   ├── analysis.py      # Analysis result models
│   │   └── chat.py          # Chat conversation models
│   ├── services/
│   │   ├── project_service.py   # Project upload & management
│   │   ├── analysis_service.py  # Analysis orchestration
│   │   └── ai_service.py       # OpenAI API integration
│   ├── analyzers/
│   │   ├── code_analyzer.py     # Code quality checks
│   │   ├── security_analyzer.py # Security vulnerability detection
│   │   ├── dependency_analyzer.py # Import & dependency analysis
│   │   └── complexity_analyzer.py # Complexity metrics
│   ├── routers/
│   │   ├── projects.py      # Project API endpoints
│   │   ├── analysis.py      # Analysis API endpoints
│   │   └── chat.py          # Chat API endpoints
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx          # Landing page with upload
│   │   ├── layout.tsx        # Root layout
│   │   ├── globals.css       # Global styles + dark theme
│   │   ├── analysis/page.tsx # Analysis dashboard
│   │   └── chat/page.tsx     # AI chat interface
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   ├── analysis/         # Analysis-specific components
│   │   └── visualization/    # React Flow graph components
│   ├── lib/
│   │   ├── api.ts            # Backend API client
│   │   ├── store.ts          # Zustand state management
│   │   └── utils.ts          # Utility functions
│   ├── types/
│   │   └── index.ts          # TypeScript type definitions
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── scripts/
    ├── start.sh              # Linux/macOS startup
    └── start.bat             # Windows startup
```

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **OpenAI API key** (for AI features)

### Quick Start

**Option 1: Docker (recommended)**

```bash
# Clone the project
git clone <repo-url>
cd archecode

# Copy and edit environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start with Docker Compose
docker-compose up --build
```

**Option 2: Manual Setup**

```bash
# Copy environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

**Option 3: Startup Script**

```bash
# Linux/macOS
chmod +x scripts/start.sh
./scripts/start.sh

# Windows
scripts\start.bat
```

### Access

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

## API Endpoints

### Projects

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/projects/upload` | Upload a zip file |
| POST | `/api/projects/import-github` | Import from GitHub URL |
| GET | `/api/projects/` | List all projects |
| GET | `/api/projects/{id}` | Get project details |
| GET | `/api/projects/{id}/tree` | Get file tree |
| GET | `/api/projects/{id}/files/{path}` | Read a file |
| DELETE | `/api/projects/{id}` | Delete a project |

### Analysis

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analysis/start` | Start project analysis |
| GET | `/api/analysis/{id}` | Get analysis result |
| GET | `/api/analysis/project/{id}` | Get project analyses |
| GET | `/api/analysis/{id}/findings` | Get findings (with filters) |
| GET | `/api/analysis/{id}/security` | Get security issues |
| GET | `/api/analysis/{id}/graph/dependencies` | Get dependency graph data |
| GET | `/api/analysis/{id}/graph/functions` | Get function graph data |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat/send` | Send a chat message |
| GET | `/api/chat/conversations/{id}` | Get conversation |
| GET | `/api/chat/suggestions/{id}` | Get suggested questions |

## Configuration

All configuration is done through environment variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | (required) | OpenAI API key for AI features |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `GITHUB_TOKEN` | (optional) | GitHub token for private repos |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Backend host |
| `PORT` | `8000` | Backend port |

## Supported Languages

| Language | Analysis Level |
|---|---|
| Python | Full (AST + regex) |
| JavaScript | Full (regex-based) |
| TypeScript | Full (regex-based) |
| Java | Partial (regex-based) |
| Go | File detection |
| Rust | File detection |
| Ruby | File detection |
| PHP | File detection |

## Architecture

ArcheCode follows a three-layer architecture:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────>│   Backend    │────>│   OpenAI API │
│  (Next.js)   │<────│  (FastAPI)   │<────│  (GPT-4o)    │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │   Analyzers  │
                     │              │
                     │  Code        │
                     │  Security    │
                     │  Dependency  │
                     │  Complexity  │
                     └──────────────┘
```

**Backend** is the core: it receives uploaded projects, extracts them, runs all analyzers in sequence, optionally calls the OpenAI API for AI-powered insights, and returns structured results.

**Frontend** provides a modern dark-themed UI with a file tree explorer, analysis dashboard, dependency graphs (React Flow), findings browser, security report, documentation viewer, and AI chat interface.

**Analyzers** are pluggable modules that each focus on a specific aspect: code quality, security, dependencies, and complexity. They produce typed findings that are aggregated into a single analysis result.

## License

MIT
