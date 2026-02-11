# 🧠 Neutrino - AI Development Advisor: Complete System Flow Analysis

> **Transform codebases into actionable intelligence for engineers and business leaders.**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Complete Request Flow](#complete-request-flow)
5. [Component Deep Dive](#component-deep-dive)
6. [Data Models](#data-models)
7. [API Endpoints](#api-endpoints)
8. [Analysis Pipeline](#analysis-pipeline)
9. [LLM Integration](#llm-integration)
10. [Database Layer](#database-layer)
11. [Frontend (Streamlit UI)](#frontend-streamlit-ui)
12. [Key Design Patterns](#key-design-patterns)
13. [Performance Optimizations](#performance-optimizations)

---

## 🎯 System Overview

The **AI Development Advisor** is a sophisticated backend system that analyzes GitHub repositories to provide:

| Output Type | Target Audience | Content |
|-------------|-----------------|---------|
| **Technical Summary** | Engineers | Architecture, code quality, security, technical roadmap |
| **Executive Summary** | Business Leaders | Risks, opportunities, action plans, resource estimates |

### Core Value Proposition
- **Input**: GitHub repository URL (public or private)
- **Output**: Dual-audience intelligence reports with actionable recommendations

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                      │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                     Streamlit UI (ui/app.py)                              │  │
│  │  • Repository URL input       • Private repo token support                │  │
│  │  • Tabbed view (Tech/Exec)    • Markdown report downloads                 │  │
│  │  • Recent analyses list       • API health indicator                      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼ HTTP (localhost:8000)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               API LAYER                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                  FastAPI (api/endpoints.py)                               │  │
│  │  POST /analyze      → Analyze repository (202 Accepted)                   │  │
│  │  GET  /analysis/:id → Retrieve stored analysis                            │  │
│  │  GET  /analyses     → List recent analyses                                │  │
│  │  GET  /health       → Health check                                        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                     │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │              AnalysisOrchestrator (analysis/orchestrator.py)              │  │
│  │                                                                           │  │
│  │  1. Parse repository URL                                                  │  │
│  │  2. Fetch repository data ──────────────────────────┐                     │  │
│  │  3. Run static analysis                             │                     │  │
│  │  4. Enrich with trend data (RAG + parallel search)  │                     │  │
│  │  5. Generate LLM summaries (PARALLEL)               │                     │  │
│  │  6. Return AnalysisRecord + timeline + trend_data   │                     │  │
│  └─────────────────────────────────────────────────────┼─────────────────────┘  │
└────────────────────────────────────────────────────────┼────────────────────────┘
                          │                              │
          ┌───────────────┴───────────────┐              │
          ▼                               ▼              ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   ANALYSIS LAYER    │   │    LLM LAYER        │   │   GITHUB LAYER      │
├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤
│ • StackDetector     │   │ • OpenRouterClient  │   │ • GitHubClient      │
│ • ArchitectureAnal. │   │ • Shared httpx      │   │ • StrategicFetcher  │
│ • RiskAnalyzer      │   │ • Multi-key rotation│   │ • RepositoryParser  │
│ • RecEngine         │   │ • Per-call timing   │   │                     │
│ • DeepReview        │   │ • Model fallback    │   │                     │
│ • ReportAgent (RAG) │   │ • Prompt templates  │   │                     │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
          │                         │                         │
          └─────────────┬───────────┘                         │
                        ▼                                     │
          ┌─────────────────────────┐                         │
          │    DATABASE LAYER       │                         │
          ├─────────────────────────┤                         │
          │ • Supabase Client       │                         │
          │ • AnalysisRepository    │                         │
          │ • Pydantic Models       │                         │
          └─────────────────────────┘                         │
                        │                                     │
                        ▼                                     ▼
          ┌─────────────────────────┐           ┌─────────────────────────┐
          │   Supabase (PostgreSQL) │           │      GitHub API         │
          │   (Cloud Database)      │           │   (api.github.com)      │
          └─────────────────────────┘           └─────────────────────────┘
                        │
                        │
          ┌─────────────────────────┐
          │      OpenRouter API     │
          │  (LLM Gateway - Free)   │
          └─────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Interactive web UI |
| **API** | FastAPI | REST API with async support |
| **HTTP Client** | httpx | Shared async client (reused across all LLM calls) |
| **LLM** | OpenRouter | AI model gateway (free models) |
| **Database** | Supabase (PostgreSQL) | Analysis storage |
| **Vector DB** | Supabase (pgvector) | RAG-based trend intelligence cache |
| **Search** | Serper API | Google Search for version-aware trend data |
| **Validation** | Pydantic | Data models & settings |
| **Package Manager** | uv | Fast Python package management |

### Default LLM Models (Free via OpenRouter)
| Priority | Model | Context Length | Capabilities |
|----------|-------|----------------|--------------|
| 1 (Primary) | DeepSeek R1T2 Chimera | 32K | Analysis, Reasoning, Coding |
| 2 | Moonshot Kimi K2 | 32K | Analysis, Summarization |
| 3 | Arcee Trinity Large | 16K | Analysis, Coding |
| 4 | GLM 4.5 Air | 16K | Analysis, Summarization |

---

## 🔄 Complete Request Flow

### Step-by-Step Analysis Journey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: USER INPUT                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User enters: https://github.com/owner/repo                                 │
│  (Optional: GitHub access token for private repos)                          │
│                                                                             │
│  ┌─────────────────────────────────────────┐                                │
│  │  Streamlit UI (localhost:8501)          │                                │
│  │  • Validates URL format                  │                                │
│  │  • Shows "Analyzing..." spinner          │                                │
│  │  • Timeout: 5 minutes                    │                                │
│  └─────────────────────────────────────────┘                                │
│                          │                                                  │
│                          ▼ POST /analyze                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: API ENDPOINT                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FastAPI receives AnalysisRequest:                                          │
│  {                                                                          │
│      "repo_url": "https://github.com/owner/repo",                           │
│      "access_token": null  // Optional, ephemeral                           │
│  }                                                                          │
│                                                                             │
│  → Creates AnalysisOrchestrator(github_token=access_token)                  │
│  → Calls orchestrator.analyze(repo_url)                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: URL PARSING                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GitHubClient.parse_repo_url(url)                                           │
│                                                                             │
│  Input:  "https://github.com/owner/repo"                                    │
│  Output: ("owner", "repo")                                                  │
│                                                                             │
│  Regex patterns handle:                                                     │
│  • github.com/owner/repo                                                    │
│  • github.com/owner/repo.git                                                │
│  • github.com:owner/repo.git (SSH format)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: REPOSITORY DATA FETCHING                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  _fetch_repository(owner, repo)                                             │
│                                                                             │
│  4.1 GET METADATA                                                           │
│      GET /repos/{owner}/{repo}                                              │
│      → Extracts: default_branch, size, description                          │
│                                                                             │
│  4.2 GET FILE TREE                                                          │
│      GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1               │
│      → Returns all files up to depth 5                                      │
│      → Filters: path, type (blob/tree), size                                │
│                                                                             │
│  4.3 PARSE STRUCTURE                                                        │
│      RepositoryParser.parse_file_tree(tree)                                 │
│      → Classifies files: code, config, doc, priority                        │
│      → Builds RepositoryStructure object                                    │
│                                                                             │
│  4.4 IDENTIFY PRIORITY FILES                                                │
│      RepositoryParser.get_files_to_analyze(structure, max=20)               │
│      Priority order:                                                        │
│      1. package.json, pyproject.toml, requirements.txt                      │
│      2. Cargo.toml, go.mod, pom.xml, build.gradle                           │
│      3. Dockerfile, docker-compose.yml                                      │
│      4. .github/workflows                                                   │
│      5. README.md                                                           │
│      6. Largest code files                                                  │
│                                                                             │
│  4.5 FETCH FILE CONTENTS (PARALLEL)                                         │
│      asyncio.gather(*[get_file_content(path) for path in priority_files])   │
│      → Skips files > 100KB                                                  │
│      → Skips binary files                                                   │
│      → Returns: dict[path, content]                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: STATIC ANALYSIS (In-Memory, No External Calls)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  5.1 STACK DETECTION (StackDetector)                                        │
│      ┌────────────────────────────────────────────────────────┐             │
│      │ Input: file_tree + file_contents                       │             │
│      │                                                        │             │
│      │ Detects:                                               │             │
│      │ • Languages (by extension): .py→Python, .ts→TypeScript │             │
│      │ • Frameworks (by deps): "react"→React, "fastapi"→FastAPI             │
│      │ • Databases (by keywords): "postgresql"→PostgreSQL     │             │
│      │ • Tools (by files): Dockerfile→Docker                  │             │
│      │ • Package Managers (by lock files): pnpm-lock.yaml→pnpm│             │
│      │ • Versions (from package.json)                         │             │
│      │                                                        │             │
│      │ Output: TechStackInfo                                  │             │
│      └────────────────────────────────────────────────────────┘             │
│                                                                             │
│  5.2 ARCHITECTURE ANALYSIS (ArchitectureAnalyzer)                           │
│      ┌────────────────────────────────────────────────────────┐             │
│      │ Input: file_tree + file_contents                       │             │
│      │                                                        │             │
│      │ Detects patterns:                                      │             │
│      │ • Clean Architecture: domain/, usecases/, entities/    │             │
│      │ • MVC: models/, views/, controllers/                   │             │
│      │ • Microservices: services/, api-gateway/, shared/      │             │
│      │ • Modular Monolith: modules/, packages/, libs/         │             │
│      │ • Layered: presentation/, business/, data/             │             │
│      │ • Event-Driven: events/, handlers/, subscribers/       │             │
│      │ • Serverless: functions/, lambda/, serverless.yml      │             │
│      │ • Next.js: app/, pages/, components/, lib/             │             │
│      │ • FastAPI: routers/, schemas/, crud/, core/            │             │
│      │                                                        │             │
│      │ Output: list[ArchitecturePattern] with confidence      │             │
│      └────────────────────────────────────────────────────────┘             │
│                                                                             │
│  5.3 RISK ANALYSIS (RiskAnalyzer)                                           │
│      ┌────────────────────────────────────────────────────────┐             │
│      │ Input: file_tree + file_contents + tech_stack          │             │
│      │                                                        │             │
│      │ Checks for:                                            │             │
│      │ • ❌ Missing tests (no test/, __tests__, pytest)       │             │
│      │ • ❌ No CI/CD (no .github/workflows, Jenkinsfile)      │             │
│      │ • ⚠️ Hardcoded secrets (password=, api_key=)           │             │
│      │ • ❌ No containerization (no Dockerfile)               │             │
│      │ • ❌ Limited type safety (no tsconfig, mypy)           │             │
│      │ • ❌ Limited documentation (no README.md, docs/)       │             │
│      │ • ⚠️ Multi-language complexity (>4 languages)         │             │
│      │ • ⚠️ No recognized framework                          │             │
│      │                                                        │             │
│      │ Severity levels: low, medium, high, critical          │             │
│      │ Output: list[RiskItem] sorted by severity             │             │
│      └────────────────────────────────────────────────────────┘             │
│                                                                             │
│  5.4 RECOMMENDATION GENERATION (RecommendationEngine)                       │
│      ┌────────────────────────────────────────────────────────┐             │
│      │ Input: tech_stack + architecture + risks               │             │
│      │                                                        │             │
│      │ Templates triggered by conditions:                     │             │
│      │ • add_typescript: if JavaScript in stack               │             │
│      │ • add_testing: if "Missing Test Coverage" risk         │             │
│      │ • add_ci_cd: if "No CI/CD Configuration" risk          │             │
│      │ • add_docker: if "No Containerization" risk            │             │
│      │ • add_documentation: if "Limited Documentation" risk   │             │
│      │ • modernize_react: if React in frameworks              │             │
│      │ • security_audit: if "Potential Hardcoded Secrets"     │             │
│      │                                                        │             │
│      │ Output: list[Recommendation] with effort & impact      │             │
│      └────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: LLM SUMMARY GENERATION (PARALLEL)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  _generate_summaries() runs TWO LLM calls concurrently:                     │
│                                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐   │
│  │   TECHNICAL SUMMARY             │  │   EXECUTIVE SUMMARY             │   │
│  │   (for engineers)               │  │   (for business leaders)        │   │
│  ├─────────────────────────────────┤  ├─────────────────────────────────┤   │
│  │ Prompt includes:                │  │ Prompt includes:                │   │
│  │ • repo_name                     │  │ • repo_name                     │   │
│  │ • tech_stack                    │  │ • tech_stack                    │   │
│  │ • architecture                  │  │ • architecture                  │   │
│  │ • risks                         │  │ • risks                         │   │
│  │ • recommendations               │  │ • recommendations               │   │
│  │                                 │  │                                 │   │
│  │ Structure:                      │  │ Structure:                      │   │
│  │ 1. Architecture Overview        │  │ 1. Overview                     │   │
│  │ 2. Code Quality & Tech Debt     │  │ 2. Key Findings                 │   │
│  │ 3. Security Notes               │  │    - Strengths                  │   │
│  │ 4. Prioritized Actions          │  │    - Risks (Business Impact)    │   │
│  │ 5. Quick Wins (This Week)       │  │    - Opportunities              │   │
│  │                                 │  │ 3. Recommended Actions          │   │
│  │                                 │  │    - Immediate (1-2 Weeks)      │   │
│  │                                 │  │    - Short-Term (2-4 Weeks)     │   │
│  │                                 │  │    - Strategic (1-2 Months)     │   │
│  │                                 │  │ 4. Resources                    │   │
│  │                                 │  │ 5. Bottom Line                  │   │
│  └─────────────────────────────────┘  └─────────────────────────────────┘   │
│                                                                             │
│  asyncio.gather(tech_task, exec_task) → ~40% faster than sequential         │
│                                                                             │
│  Trend Context Injection:                                                   │
│  Reports receive enriched trend data per technology:                        │
│  • latest_version + version_info                                            │
│  • Momentum direction (rising/stable/declining)                             │
│  • Key risks and opportunities                                              │
│  • Top sources with links                                                   │
│                                                                             │
│  System Prompt Constraints:                                                 │
│  • Base ALL findings on actual evidence                                     │
│  • Return ONLY what is requested                                            │
│  • Be specific - reference actual files/patterns                            │
│  • No generic advice - every point must cite evidence                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: LLM CLIENT (Multi-Key Rotation + Model Fallback)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OpenRouterClient.complete(prompt, system_prompt)                           │
│                                                                             │
│  ⚡ Shared httpx.AsyncClient:                                               │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │ Lazy-initialized, reused across ALL calls (no per-request TCP)  │        │
│  │ Per-call duration_ms tracked and reported in timeline            │        │
│  │ close() method for graceful shutdown                             │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  Fallback Strategy:                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │ For each model in [primary, fallback1, fallback2, fallback3]:   │        │
│  │   │                                                             │        │
│  │   └→ For each API key in [key1, key2, key3, key4]:              │        │
│  │        │                                                        │        │
│  │        └→ Try request                                           │        │
│  │             ├─ Success → Return result                          │        │
│  │             ├─ 429/401 → Rotate to next key                     │        │
│  │             └─ Other error → Try next model                     │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
│  Request to OpenRouter:                                                     │
│  POST https://openrouter.ai/api/v1/chat/completions                         │
│  Headers:                                                                   │
│    Authorization: Bearer {api_key}                                          │
│    HTTP-Referer: https://github.com/ai-development-advisor                  │
│    X-Title: AI Development Advisor                                          │
│  Body:                                                                      │
│    model: "tngtech/deepseek-r1t2-chimera:free"                              │
│    messages: [{role: system, content: ...}, {role: user, content: ...}]     │
│    temperature: 0.3                                                         │
│    max_tokens: 4096                                                         │
│                                                                             │
│  Token usage is tracked: _total_tokens_used                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: RESULT AGGREGATION                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AnalysisRecord created with all data:                                      │
│                                                                             │
│  {                                                                          │
│    repo_url: "https://github.com/owner/repo",                               │
│    repo_name: "owner/repo",                                                 │
│    model_used: "tngtech/deepseek-r1t2-chimera:free",                        │
│    analyzed_at: "2026-01-30T19:51:05Z",                                     │
│                                                                             │
│    tech_stack: {                                                            │
│      languages: ["Python", "TypeScript"],                                   │
│      frameworks: ["FastAPI", "React"],                                      │
│      databases: ["PostgreSQL"],                                             │
│      tools: ["Docker", "GitHub Actions"],                                   │
│      package_managers: ["Poetry", "npm"],                                   │
│      versions: {"python": "3.11", "react": "18.2"}                          │
│    },                                                                       │
│                                                                             │
│    architecture_patterns: [                                                 │
│      {pattern_name: "Clean Architecture", confidence: 0.85, evidence: [...]}│
│    ],                                                                       │
│                                                                             │
│    risks_and_gaps: [                                                        │
│      {category: "security", severity: "high", title: "...", ...}            │
│    ],                                                                       │
│                                                                             │
│    recommendations: [                                                       │
│      {category: "process", priority: "high", title: "...", ...}             │
│    ],                                                                       │
│                                                                             │
│    technical_summary: "## 1. Architecture Overview...",                     │
│    executive_summary: "## Overview...",                                     │
│                                                                             │
│    analysis_duration_ms: 45000,                                             │
│    file_count: 127,                                                         │
│    token_usage: {total: 8500},                                              │
│    timeline: {                                                              │
│      total_duration_seconds: 48.2,                                          │
│      phases: {                                                              │
│        fetch: {duration_ms: 5200, api_calls: [...]},                        │
│        detect: {duration_ms: 120},                                          │
│        trend_enrichment: {duration_ms: 8500, api_calls: [                   │
│          {name: "rag_cache_hit:React", ms: 45},                             │
│          {name: "fresh_collect:FastAPI", ms: 3200}                          │
│        ]},                                                                  │
│        deep_review: {duration_ms: 32000, api_calls: [...]},                 │
│        report: {duration_ms: 2400}                                          │
│      }                                                                      │
│    },                                                                       │
│    trend_data: {                                                            │
│      "React": {latest_version: "19.1", momentum: "rising", ...},            │
│      "FastAPI": {latest_version: "0.115", version_info: "...", ...}         │
│    }                                                                        │
│  }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 9: DATABASE STORAGE                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AnalysisRepository.create(record)                                          │
│                                                                             │
│  → record.to_db_dict() serializes to JSON                                   │
│  → INSERT INTO analysis_records (...)                                       │
│  → Supabase generates UUID                                                  │
│  → Returns saved record with ID                                             │
│                                                                             │
│  Table: analysis_records                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │ Column                  │ Type          │ Description           │        │
│  ├─────────────────────────┼───────────────┼───────────────────────┤        │
│  │ id                      │ UUID          │ Primary key           │        │
│  │ repo_url                │ TEXT          │ GitHub URL            │        │
│  │ repo_name               │ TEXT          │ owner/repo            │        │
│  │ analyzed_at             │ TIMESTAMPTZ   │ Analysis timestamp    │        │
│  │ model_used              │ TEXT          │ LLM model ID          │        │
│  │ tech_stack              │ JSONB         │ Stack detection       │        │
│  │ architecture_patterns   │ JSONB         │ Patterns found        │        │
│  │ risks_and_gaps          │ JSONB         │ Identified risks      │        │
│  │ recommendations         │ JSONB         │ Action items          │        │
│  │ technical_summary       │ TEXT          │ Engineer summary      │        │
│  │ executive_summary       │ TEXT          │ Business summary      │        │
│  │ analysis_duration_ms    │ INTEGER       │ Time taken            │        │
│  │ file_count              │ INTEGER       │ Total files           │        │
│  │ token_usage             │ JSONB         │ LLM tokens used       │        │
│  │ created_at              │ TIMESTAMPTZ   │ Record creation       │        │
│  │ updated_at              │ TIMESTAMPTZ   │ Last update           │        │
│  └─────────────────────────┴───────────────┴───────────────────────┘        │
│                                                                             │
│  Note: Database errors are caught and logged, not fatal                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 10: API RESPONSE                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HTTP 202 Accepted                                                          │
│                                                                             │
│  AnalysisResponse:                                                          │
│  {                                                                          │
│    "success": true,                                                         │
│    "analysis_id": "550e8400-e29b-41d4-a716-446655440000",                   │
│    "message": "Analysis completed successfully",                            │
│    "technical_summary": "## 1. Architecture Overview...",                   │
│    "executive_summary": "## Overview...",                                   │
│    "timeline": {"total_duration_seconds": 48.2, "phases": {...}},           │
│    "api_call_timings": [                                                    │
│      {"name": "rag_cache_hit:React", "ms": 45, "ts": "..."},               │
│      {"name": "llm:chunk_backend", "ms": 8200, "ts": "..."}                 │
│    ],                                                                       │
│    "trend_data": {                                                          │
│      "React": {"latest_version": "19.1", "momentum": "rising"},             │
│      "FastAPI": {"latest_version": "0.115", "version_info": "..."}          │
│    }                                                                        │
│  }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 11: UI DISPLAY                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Streamlit displays results:                                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  📈 Analysis Results                                            │        │
│  │  ✅ Analysis completed successfully                             │        │
│  │                                                                 │        │
│  │  ┌─────────────────┐ ┌─────────────────┐                        │        │
│  │  │ 👨‍💻 Technical  │ │ 👔 Executive   │  ← Tabbed View          │        │
│  │  └─────────────────┘ └─────────────────┘                        │        │
│  │                                                                 │        │
│  │  ## 1. Architecture Overview                                    │        │
│  │  ...rendered markdown...                                        │        │
│  │                                                                 │        │
│  │  ┌──────────────────────────────────────────┐                   │        │
│  │  │ 📥 Download Technical Report (.md)       │  ← Download       │        │
│  │  └──────────────────────────────────────────┘                   │        │
│  │                                                                 │        │
│  │  ────────────────────────────────────────────                   │        │
│  │  📋 ID: 550e8400-...  🤖 Model: deepseek...  📁 Repo: owner/repo │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Deep Dive

### 1. Configuration Layer (`config/settings.py`)

```python
class Settings(BaseSettings):
    # Required
    supabase_url: str
    supabase_service_role_key: str
    openrouter_api_key_1: str
    
    # Optional (for key rotation)
    openrouter_api_key_2: str | None
    openrouter_api_key_3: str | None
    openrouter_api_key_4: str | None
    
    @property
    def openrouter_api_keys(self) -> list[str]:
        """Returns all non-None keys for rotation."""
```

**Key Features:**
- Pydantic-based with `.env` file support
- Fail-fast validation on startup
- Cached singleton via `@lru_cache`

### 2. GitHub Integration Layer

| Component | Responsibility |
|-----------|---------------|
| `GitHubClient` | API communication, auth handling |
| `RepositoryParser` | File classification, priority selection |

**File Classification:**
```
code_files:   .py, .js, .ts, .jsx, .tsx, .java, .go, .rs, .rb, .php, .cs, .cpp...
config_files: .json, .yaml, .yml, .toml, .ini, .cfg, .conf
doc_files:    .md, .rst, .txt, LICENSE
```

### 3. Analysis Layer

| Analyzer | Input | Output |
|----------|-------|--------|
| `StackDetector` | files + contents | `TechStackInfo` |
| `ArchitectureAnalyzer` | files + contents | `list[ArchitecturePattern]` |
| `RiskAnalyzer` | files + contents + stack | `list[RiskItem]` |
| `RecommendationEngine` | stack + arch + risks | `list[Recommendation]` |

### 4. LLM Layer

| Component | Responsibility |
|-----------|---------------|
| `OpenRouterClient` | API calls, key rotation, fallback |
| `models.py` | Model registry with capabilities |
| `prompts.py` | Constraint-based prompt templates |

**Constraint-Based Prompting:**
```
CONSTRAINTS:
- Base ALL findings on actual evidence
- Return ONLY what is requested. Do not speculate beyond evidence
- Be specific - reference actual files and patterns
- No generic advice - every point must cite evidence
```

### 5. Database Layer

| Component | Responsibility |
|-----------|---------------|
| `client.py` | Supabase connection (cached) |
| `repository.py` | CRUD operations |
| `models.py` | Pydantic schemas |

---


## 🧠 Analysis Pipeline

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         ANALYSIS PIPELINE                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   repo_url                                                                 │
│      │                                                                     │
│      ▼                                                                     │
│   ┌─────────────────┐                                                      │
│   │  Parse URL      │  → (owner, repo)                                     │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐        ┌─────────────────┐                           │
│   │  Get Metadata   │───────▶│  Get File Tree  │                           │
│   │  (default branch)│        │  (recursive)    │                           │
│   └────────┬────────┘        └────────┬────────┘                           │
│            │                          │                                    │
│            │             ┌────────────┘                                    │
│            ▼             ▼                                                 │
│   ┌───────────────────────────┐                                            │
│   │    Parse File Tree        │                                            │
│   │    (classify: code/config/doc)                                         │
│   └──────────────┬────────────┘                                            │
│                  │                                                         │
│                  ▼                                                         │
│   ┌───────────────────────────┐                                            │
│   │  Get Priority Files       │  → max 20 files                            │
│   │  (parallel fetch)         │                                            │
│   └──────────────┬────────────┘                                            │
│                  │                                                         │
│      ┌───────────┴───────────┬───────────────┬───────────────┐             │
│      ▼                       ▼               ▼               ▼             │
│ ┌──────────────┐     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │StackDetector │     │ArchAnalyzer  │ │ RiskAnalyzer │ │ RecEngine    │    │
│ └──────┬───────┘     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘    │
│        │                    │                │                │            │
│        ▼                    ▼                ▼                ▼            │
│   TechStackInfo    ArchitecturePatterns   RiskItems    Recommendations     │
│        │                    │                │                │            │
│        └────────────────────┴────────────────┴────────────────┘            │
│                                    │                                       │
│                                    ▼                                       │
│                        ┌─────────────────────────┐                         │
│                        │   LLM Summary Generation │                        │
│                        │   (PARALLEL)             │                        │
│                        │   ┌────────┐ ┌────────┐  │                        │
│                        │   │TECH    │ │EXEC    │  │                        │
│                        │   │SUMMARY │ │SUMMARY │  │                        │
│                        │   └────────┘ └────────┘  │                        │
│                        └────────────┬────────────┘                         │
│                                     │                                      │
│                                     ▼                                      │
│                            ┌─────────────────┐                             │
│                            │ AnalysisRecord  │                             │
│                            │ (final output)  │                             │
│                            └─────────────────┘                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## ⚡ Performance Optimizations

| Optimization | Impact |
|--------------|--------|
| Shared `httpx.AsyncClient` | Eliminates per-request TCP/TLS overhead across all LLM calls |
| Parallel RAG lookups | All tech tag queries run concurrently via `asyncio.gather` |
| Parallel trend collection | Serper, GitHub, HN fetched in parallel per cache-missed tag |
| Parallel code review | FE, BE, and Infra agents run simultaneously |
| Parallel file fetching | `asyncio.gather` for batch GitHub file downloads |
| Parallel LLM calls | ~40% faster summary generation |
| Strategic file selection | Smart 3-pass prioritization (top ~150 files) |
| In-memory static analysis | No external calls for stack/risk/architecture detection |
| LRU cached settings | No repeated env parsing |
| LRU cached database client | Single connection per process |
| Per-API-call timing | `duration_ms` tracked for every LLM and RAG operation |
| Reduced stagger | Uncached trend tags fetched with 0.3s delay (down from 1.0s) |

**Typical Analysis Time:** 45-60 seconds (depends on repo size and LLM response time)

---

## 📁 Project Structure

```
backend/
├── src/advisor/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic settings
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py         # Supabase client
│   │   ├── models.py         # Pydantic models (AnalysisRecord, AnalysisResponse)
│   │   └── repository.py     # CRUD operations
│   ├── github/
│   │   ├── __init__.py
│   │   ├── client.py         # GitHub API client
│   │   ├── strategic_fetcher.py  # Smart 3-pass file fetching
│   │   └── parser.py         # File tree parser
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py         # OpenRouter client (shared httpx, per-call timing)
│   │   ├── models.py         # Model registry
│   │   └── prompts.py        # Prompt templates
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── core/
│   │       ├── orchestrator.py   # Main coordinator + trend enrichment
│   │       ├── deep_review.py    # Parallel LLM code review (FE/BE/Infra)
│   │       ├── report_agent.py   # RAG-enhanced report generation
│   │       ├── timeline.py       # Per-phase + per-API-call timing
│   │       └── chunk_prompts.py  # Smart chunking for code context
│   ├── trends/
│   │   ├── __init__.py
│   │   ├── trend_master.py       # Orchestrates collection + LLM summarization
│   │   ├── data_collector.py     # Serper, GitHub, HN parallel fetching
│   │   ├── aggregator.py         # HN, Dev.to, GitHub Trending aggregation
│   │   ├── matcher.py            # Stack-to-trend relevance scoring
│   │   ├── rag_manager.py        # Supabase pgvector storage/retrieval
│   │   └── models.py             # TrendInsight, TrendSourceInfo, etc.
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py      # FastAPI routes
│   └── ui/
│       ├── __init__.py
│       └── app.py            # Streamlit frontend
├── tests/                    # 60 tests total
├── migrations/               # SQL migrations
├── scripts/                  # Utility scripts
├── pyproject.toml           # Dependencies
└── uv.lock                  # Lock file
```

---

## 🚀 Quick Start Commands

```bash
# Start API server
uv run uvicorn advisor.api.endpoints:app --reload --port 8000

# Start Streamlit UI (separate terminal)
uv run streamlit run src/advisor/ui/app.py

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check src/
```

---

## 📝 TODO / Future Improvements

- [ ] PDF report generation (WeasyPrint)
- [ ] Webhook support for CI/CD integration
- [ ] Rate limiting
- [ ] User authentication
- [x] ~~Caching for repeated analyses~~ — RAG-based trend caching implemented
- [x] ~~Per-API-call timing~~ — Full timeline with `duration_ms` per call

---

*Generated by AI Development Advisor Analysis*
