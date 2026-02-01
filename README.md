# Neutrino - AI Development Advisor

> Transform codebases into actionable intelligence for engineers and business leaders.

## Overview

The **AI Development Advisor** is a backend system that analyzes GitHub repositories to provide:
- **Technical Summaries** for engineers (architecture, code quality, security, roadmap)
- **Executive Summaries** for business leaders (risks, opportunities, action plans)

Built with **FastAPI** (API) + **Streamlit** (UI) + **OpenRouter** (LLM) + **Supabase** (database).

---

## Quick Start

```bash
cd backend

# Install dependencies
uv sync

# Set environment variables (copy from .env.example or create .env)
# Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENROUTER_API_KEY_1

# Start API server
uv run uvicorn advisor.api.endpoints:app --reload --port 8000

# Start Streamlit UI (in another terminal)
uv run streamlit run src/advisor/ui/app.py
```

**Access:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

---

## Project Structure

```
backend/
├── src/advisor/           # Main application package
│   ├── __init__.py
│   ├── config/            # Configuration and settings
│   │   ├── __init__.py
│   │   └── settings.py    # Pydantic settings with env validation
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── client.py      # Supabase client factory
│   │   ├── models.py      # Pydantic models (AnalysisRecord, etc.)
│   │   └── repository.py  # CRUD operations
│   ├── github/            # GitHub integration
│   │   ├── __init__.py
│   │   ├── client.py      # GitHub API client (metadata, tree, content)
│   │   └── parser.py      # File tree parser and classification
│   ├── llm/               # LLM integration
│   │   ├── __init__.py
│   │   ├── client.py      # OpenRouter client with multi-key rotation
│   │   ├── models.py      # Model registry and capabilities
│   │   └── prompts.py     # Prompt templates (constraint-based)
│   ├── analysis/          # Intelligence engine
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Main analysis coordinator
│   │   ├── stack_detector.py  # Technology stack detection
│   │   ├── architecture.py    # Architecture pattern analysis
│   │   ├── risk_analyzer.py   # Risk and gap detection
│   │   └── recommendations.py # Forward-looking recommendations
│   ├── api/               # FastAPI application
│   │   ├── __init__.py
│   │   └── endpoints.py   # API routes (/analyze, /health, etc.)
│   └── ui/                # Streamlit frontend
│       ├── __init__.py
│       └── app.py         # Main UI application
├── tests/                 # Test suite (60 tests)
│   ├── conftest.py        # Pytest fixtures and mocks
│   ├── test_analysis.py   # Stack detector tests
│   ├── test_api.py        # API endpoint tests
│   ├── test_architecture.py
│   ├── test_github.py
│   ├── test_integration.py # Real repo integration tests
│   ├── test_llm.py
│   ├── test_orchestrator.py
│   ├── test_parser.py
│   ├── test_recommendations.py
│   └── test_risks.py
├── migrations/            # Database migrations
│   └── 001_create_analysis_records.sql
├── scripts/               # Utility scripts
│   └── test_analysis.py
├── pyproject.toml         # Dependencies and project config
├── uv.lock                # Lock file
└── .gitignore
```

---

## Architecture

### Flow

```
User Input (GitHub URL)
    ↓
FastAPI Endpoint (/analyze)
    ↓
AnalysisOrchestrator
    ├─→ GitHubClient (fetch metadata, tree, files)
    ├─→ RepositoryParser (classify files)
    ├─→ StackDetector (languages, frameworks, tools)
    ├─→ ArchitectureAnalyzer (patterns)
    ├─→ RiskAnalyzer (security, maintainability, etc.)
    ├─→ RecommendationEngine (priority actions)
    └─→ OpenRouterClient (generate summaries) [PARALLEL]
    ↓
AnalysisRecord (stored in Supabase)
    ↓
Response (technical + executive summaries)
```

### Key Design Decisions

1. **Clean Architecture** - Separation of concerns with dependency injection
2. **Async Everything** - httpx + asyncio for non-blocking I/O
3. **Parallel LLM Calls** - Technical + Executive summaries generated concurrently (~40% faster)
4. **Multi-Key Rotation** - LLM client rotates through up to 4 API keys with fallback
5. **Ephemeral Credentials** - GitHub tokens never stored, used only for request
6. **Constraint-Based Prompts** - Behavioral instructions, not identity roleplay (reduces hallucination)

---

## Components Detail

### 1. Configuration (`config/settings.py`)

Pydantic-based settings with environment variable loading:

```python
class Settings(BaseSettings):
    app_name: str = "AI Development Advisor"
    supabase_url: str          # Required
    supabase_service_role_key: str  # Required
    openrouter_api_key_1: str  # Required
    openrouter_api_key_2: str | None = None
    openrouter_api_key_3: str | None = None
    openrouter_api_key_4: str | None = None
```

### 2. GitHub Client (`github/client.py`)

```python
class GitHubClient:
    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]  # Returns (owner, repo)
    
    async def get_repo_metadata(owner, repo) -> dict
    async def get_file_tree(owner, repo, branch) -> list[dict]
    async def get_file_content(owner, repo, path, branch) -> str
```

Supports private repos via optional access token (ephemeral).

### 3. Repository Parser (`github/parser.py`)

```python
class RepositoryParser:
    @staticmethod
    def parse_file_tree(tree: list) -> RepositoryStructure
    @staticmethod
    def get_files_to_analyze(structure) -> list[str]  # Priority files
```

Classifies files into: code_files, config_files, doc_files, test_files

### 4. Stack Detector (`analysis/stack_detector.py`)

Detects from file extensions and content:
- **Languages**: Python, JavaScript, TypeScript, Go, Rust, etc.
- **Frameworks**: React, FastAPI, Django, Express, etc.
- **Databases**: PostgreSQL, MongoDB, Redis, etc.
- **Tools**: Docker, GitHub Actions, ESLint, etc.

### 5. Architecture Analyzer (`analysis/architecture.py`)

Detects patterns:
- Clean Architecture (domain/application/infrastructure folders)
- MVC/MVVM (models/views/controllers)
- Microservices (multiple services, Docker Compose)
- Monolith/Simple structure

### 6. Risk Analyzer (`analysis/risk_analyzer.py`)

Identifies:
- Missing tests
- No CI/CD
- Hardcoded secrets
- No containerization
- Limited documentation
- Multi-language complexity

Severity: low, medium, high, critical

### 7. Recommendation Engine (`analysis/recommendations.py`)

Generates prioritized recommendations based on:
- Detected risks
- Missing best practices
- Tech stack opportunities

### 8. LLM Client (`llm/client.py`)

```python
class OpenRouterClient:
    async def complete(prompt, system_prompt, temperature) -> dict
```

Features:
- Multi-key rotation (up to 4 keys)
- Model fallback (primary → secondary)
- Token usage tracking
- Free model support

### 9. Prompts (`llm/prompts.py`)

Constraint-based prompts (not identity roleplay):

```python
SYSTEM_PROMPT = """You are a software architecture analyst.

CONSTRAINTS:
- Base ALL findings on actual evidence
- Return ONLY what is requested. Do not speculate beyond evidence
- Be specific - reference actual files and patterns
- No generic advice - every point must cite evidence
"""
```

### 10. API Endpoints (`api/endpoints.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyze` | POST | Analyze repository (202 Accepted) |
| `/analysis/{id}` | GET | Get stored analysis |
| `/analyses` | GET | List recent analyses |
| `/analysis/{id}/report` | POST | Generate PDF (not implemented) |

### 11. Streamlit UI (`ui/app.py`)

Features:
- Repository URL input
- Private repo token support (ephemeral)
- Tabbed view (Technical / Executive)
- **Download buttons** (Markdown reports)
- Recent analyses list
- API health indicator

---

## Database Schema

Table: `analysis_records`

```sql
CREATE TABLE analysis_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_url TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    model_used TEXT NOT NULL,
    tech_stack JSONB NOT NULL,
    architecture_patterns JSONB DEFAULT '[]',
    risks_and_gaps JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    technical_summary TEXT NOT NULL,
    executive_summary TEXT NOT NULL,
    analysis_duration_ms INTEGER,
    file_count INTEGER,
    token_usage JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Run migration:** Copy `migrations/001_create_analysis_records.sql` into Supabase SQL Editor.

---

## Environment Variables

Create `.env` in root:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Required (at least one)
OPENROUTER_API_KEY_1=sk-or-v1-xxx
OPENROUTER_API_KEY_2=sk-or-v1-xxx  # Optional
OPENROUTER_API_KEY_3=sk-or-v1-xxx  # Optional
OPENROUTER_API_KEY_4=sk-or-v1-xxx  # Optional
```

---

## Testing

```bash
cd backend

# Run all unit tests (fast, no network)
uv run pytest tests/ --ignore=tests/test_integration.py -v

# Run integration tests (uses real GitHub + LLM)
uv run pytest tests/test_integration.py -v -s

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=advisor --cov-report=html
```

**Test counts:** 49 unit tests + 11 integration tests = **60 total**

---

## Performance Optimizations

1. **Parallel file fetching** - Uses `asyncio.gather` to fetch multiple files concurrently
2. **Parallel LLM calls** - Technical and Executive summaries generated concurrently
3. **Minimal file fetching** - Only fetches priority files (configs, key code files)
4. **Efficient parsing** - Static analysis runs in-memory without external calls

**Typical analysis time:** ~45-60 seconds (depends on repo size and LLM response time)

---

## Models Used

Default free models via OpenRouter:
- Primary: `tngtech/deepseek-r1t-chimera:free`
- Fallback: `google/gemma-3-27b-it:free`

Configurable in `llm/models.py`.

---

## Pydantic Models

### AnalysisRecord (main output)
```python
class AnalysisRecord(BaseModel):
    id: UUID | None
    repo_url: str
    repo_name: str
    analyzed_at: datetime
    model_used: str
    tech_stack: TechStackInfo
    architecture_patterns: list[ArchitecturePattern]
    risks_and_gaps: list[RiskItem]
    recommendations: list[Recommendation]
    technical_summary: str
    executive_summary: str
    analysis_duration_ms: int | None
    file_count: int | None
    token_usage: dict[str, int]
```

### TechStackInfo
```python
class TechStackInfo(BaseModel):
    languages: list[str]
    frameworks: list[str]
    databases: list[str]
    tools: list[str]
    package_managers: list[str]
    versions: dict[str, str]
```

### RiskItem
```python
class RiskItem(BaseModel):
    category: str  # security, maintainability, scalability, debt, practices
    severity: str  # low, medium, high, critical
    title: str
    description: str
    impact: str
    recommendation: str
```

### Recommendation
```python
class Recommendation(BaseModel):
    category: str
    priority: str  # low, medium, high
    title: str
    description: str
    effort_estimate: str  # small, medium, large
    business_impact: str
    technical_steps: list[str]
```

---

## Commands Reference

```bash
# Start API
uv run uvicorn advisor.api.endpoints:app --reload --port 8000

# Start UI
uv run streamlit run src/advisor/ui/app.py

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

---

## TODO

- [ ] PDF report generation (WeasyPrint)
- [ ] Webhook support for CI/CD integration
- [ ] Caching for repeated analyses
- [ ] Rate limiting
- [ ] User authentication

---

## Tested With

- **Repository:** `https://github.com/AstralKS/LSTM_FROM_SCRATCH`
- **Results:**
  - Languages: Python
  - Risks: No CI/CD, Limited Type Safety, Limited Documentation
  - Recommendations: Set Up CI/CD, Containerize, Improve Documentation
  - Duration: ~78s (before optimization), ~45-50s (after parallel LLM)

---

## License

MIT
