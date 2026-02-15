# Design Document: Neutrino AI Development Advisor

## Overview

Neutrino is an AI-powered repository analysis platform that transforms GitHub codebases into actionable intelligence through a sophisticated pipeline combining static analysis, parallel LLM-based code review, and RAG-enhanced trend intelligence. The system architecture follows Clean Architecture principles with clear separation between domain logic, infrastructure, and presentation layers.

### Core Design Principles

1. **Parallel-First Architecture**: All I/O-bound operations (API calls, database queries, file fetching) execute concurrently using asyncio.gather to minimize latency
2. **Connection Reuse**: Single shared httpx.AsyncClient instance eliminates TCP handshake and TLS negotiation overhead
3. **RAG-First Workflow**: Trend intelligence checks pgvector cache before expensive multi-source collection
4. **Token Optimization**: 40-60% compression of source code through strategic removal of imports, comments, and whitespace
5. **Fault Tolerance**: Multi-key rotation with model fallback ensures resilience against rate limits and API failures
6. **Ephemeral Security**: GitHub tokens never persist beyond request scope
7. **Evidence-Based Analysis**: Constraint-based prompts require LLMs to cite specific code locations

### Technology Stack

**Backend:**
- FastAPI 0.104+ (ASGI web framework with automatic OpenAPI generation)
- Python 3.11+ with asyncio for concurrent execution
- httpx 0.25+ (async HTTP client with HTTP/2 support)
- Supabase Python client (PostgreSQL + pgvector interface)
- OpenRouter API (unified LLM gateway supporting GPT-4, Claude, Gemini)

**Frontend:**
- React 19 with TypeScript 5.3+
- Vite 5.0+ (build tool with HMR)
- Tailwind CSS 3.4+ (utility-first styling)
- Framer Motion 11+ (declarative animations)
- Axios 1.6+ (HTTP client)
- react-markdown + remark-gfm (Markdown rendering)

**Infrastructure:**
- Supabase (managed PostgreSQL 15+ with pgvector extension)
- OpenRouter (LLM API aggregator)
- Serper API (Google search)
- GitHub REST API v3
- Hacker News Algolia API
- Dev.to API

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph Frontend
        UI[React UI]
        Router[React Router]
        API_Client[Axios Client]
    end
    
    subgraph Backend
        FastAPI[FastAPI Server]
        Orchestrator[Analysis Orchestrator]
        
        subgraph Analysis Pipeline
            GitHub[GitHub Client]
            Fetcher[Strategic Fetcher]
            StackDetector[Stack Detector]
            ArchDetector[Architecture Detector]
            RiskAnalyzer[Risk Analyzer]
        end
        
        subgraph Deep Review
            TokenOpt[Token Optimizer]
            FrontendAgent[Frontend Agent]
            BackendAgent[Backend Agent]
            InfraAgent[Infrastructure Agent]
        end
        
        subgraph Trend Intelligence
            RAGStore[RAG Store]
            QueryPlanner[Query Planner]
            SearchSources[Search Sources]
            SignalExtractor[Signal Extractor]
            Synthesizer[Trend Synthesizer]
        end
        
        subgraph Report Generation
            TechReport[Technical Report Agent]
            ExecReport[Executive Report Agent]
            PDFGen[PDF Generator]
        end
    end
    
    subgraph External Services
        GitHubAPI[GitHub API]
        OpenRouter[OpenRouter LLM]
        Serper[Serper API]
        HN[Hacker News API]
        DevTo[Dev.to API]
    end
    
    subgraph Data Layer
        Supabase[(Supabase PostgreSQL)]
        PGVector[(pgvector)]
    end
    
    UI --> Router
    Router --> API_Client
    API_Client --> FastAPI
    
    FastAPI --> Orchestrator
    Orchestrator --> GitHub
    GitHub --> Fetcher
    Fetcher --> StackDetector
    StackDetector --> ArchDetector
