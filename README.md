# Neutrino - AI Development Advisor

> Transform codebases into actionable intelligence for engineers and business leaders.

## Overview

The **AI Development Advisor** is a full-stack system that analyzes GitHub repositories to provide:
- **Technical Summaries** for engineers (architecture, code quality, security, roadmap)
- **Executive Summaries** for business leaders (risks, opportunities, action plans)
- **Trend Intelligence** — version-aware market data enriched via RAG (Supabase pgvector)

### Tech Stack
- **Backend**: Python 3.12+, FastAPI, Supabase (SQL + pgvector), OpenRouter (LLM)
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS 4, Framer Motion
- **Legacy/Admin-UI**: Streamlit

---

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Install dependencies (using uv is recommended)
uv sync
# OR with pip
pip install -r requirements.txt

# Set environment variables
# Create .env and add:
# SUPABASE_URL=...
# SUPABASE_SERVICE_ROLE_KEY=...
# OPENROUTER_API_KEY_1=...
# SERPER_API_KEY=...

# Start API server
uv run uvicorn advisor.api.endpoints:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Development Server
npm run dev
```

**Access:**
- **Web App**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Legacy Streamlit UI**: http://localhost:8501 (via `uv run streamlit run src/advisor/ui/app.py`)

---

## Project Structure

```
.
├── backend/                   # Python FastAPI Backend
│   ├── src/advisor/
│   │   ├── api/               # API Endpoints
│   │   ├── analysis/          # Core Intelligence Engine
│   │   │   ├── core/          # Orchestrators & Agents
│   │   │   ├── trends/        # RAG Logic
│   │   │   └── stack_detector.py
│   │   ├── database/          # Supabase Client & Models
│   │   ├── github/            # GitHub API Client
│   │   ├── llm/               # OpenRouter/LLM Client
│   ├── tests/                 # Pytest Suite
│   ├── pyproject.toml         # Python Dependencies
│   └── ...
│
├── frontend/                  # React TypeScript Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI Components
│   │   ├── pages/             # Route Pages
│   │   ├── hooks/             # Custom Hooks
│   │   ├── services/          # API Integration
│   │   ├── App.tsx            # Main Application Component
│   │   └── main.tsx           # Entry Point
│   ├── package.json           # Node Dependencies
│   ├── vite.config.ts         # Vite Configuration
│   └── ...
│
└── README.md                  # Project Documentation
```

---

## Architecture

### System Flow
1. **User Input**: GitHub URL via React Frontend.
2. **Analysis Request**: Frontend calls `POST /analyze`.
3. **Orchestrator**: Backend coordinator triggers parallel agents.
   - **Strategic Fetcher**: Retrieves relevant files (smart 3-pass).
   - **Trend Master**: Checks RAG cache for technology trends, fetches fresh data (Serper/GitHub/HN) on miss.
   - **Deep Review**: Parallel LLM agents analyze Frontend, Backend, and Infra.
4. **Storage**: Results saved to Supabase (`analysis_records`).
5. **Presentation**: Frontend polls/retrieves results and displays interactive reports.

### Key Features
- **Parallel Execution**: `asyncio.gather` for minimal latency.
- **RAG-First Trends**: Reduces LLM hallucinations and costs by caching trend data.
- **Smart Context**: Only analyses relevant files to stay within token limits.
- **Resiliency**: Multi-key rotation for LLM API and robust error handling.

---

## Configuration

### Backend Environment Variables (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key (for backend) |
| `OPENROUTER_API_KEY_1` | Primary LLM API Key |
| `OPENROUTER_API_KEY_n` | Backup Keys (Optional) |
| `SERPER_API_KEY` | For Google Search trend data |

---

## Development

### Backend Commands
```bash
# Run Tests
uv run pytest

# Linting
uv run ruff check src/
```

### Frontend Commands
```bash
# Type Check
npm run build 

# Linting
npm run lint
```

---

## License

MIT
