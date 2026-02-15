# Requirements Document: Neutrino AI Development Advisor

## Introduction

Neutrino is an AI-powered repository analysis platform that transforms GitHub codebases into actionable intelligence for both engineers and business leaders. The system performs deep technical analysis of repositories, enriches findings with real-time trend intelligence using RAG (Retrieval-Augmented Generation), and generates comprehensive reports tailored for different audiences. The platform emphasizes performance through parallel processing, intelligent caching, and strategic resource optimization.

## Glossary

- **System**: The Neutrino AI Development Advisor platform
- **Repository**: A GitHub codebase (public or private)
- **Analysis_Pipeline**: The orchestrated process of repository ingestion, analysis, and report generation
- **RAG_System**: Retrieval-Augmented Generation system using Supabase pgvector for trend intelligence caching
- **Review_Agent**: Specialized LLM-based code analysis agent (Frontend, Backend, or Infrastructure)
- **Trend_Intelligence**: Version-aware market and technology trend data collected from multiple sources
- **Tech_Tag**: A technology identifier (e.g., "React", "FastAPI", "PostgreSQL")
- **Strategic_Fetching**: Three-pass file prioritization algorithm that fetches ~300 most relevant files
- **Token_Optimization**: Process of compressing code by removing imports, comments, and whitespace (40-60% reduction)
- **Multi_Key_Rotation**: Load balancing across multiple OpenRouter API keys with model fallback
- **Ephemeral_Token**: Temporary GitHub access token that is never persisted
- **Executive_Brief**: Business-focused report covering ROI, risks, and opportunities
- **Technical_Deep_Dive**: Engineering-focused report covering architecture, code quality, and roadmap
- **Query_Planner**: Component that generates focused sub-queries for trend collection
- **Signal_Extraction**: Process of identifying relevant information from raw trend data
- **Version_Aware_Analysis**: Trend analysis that extracts and tracks latest_version and version_info
- **Shared_HTTP_Client**: Single httpx.AsyncClient instance reused across all LLM calls
- **Parallel_Processing**: Concurrent execution using asyncio.gather
- **Cache_Window**: 7-day period for RAG cache validity
- **Analysis_Record**: Stored repository analysis result in Supabase
- **Trend_Insight**: Cached trend intelligence entry in pgvector

## Requirements

### Requirement 1: Repository Ingestion

**User Story:** As a platform user, I want to ingest GitHub repositories through a strategic file fetching algorithm, so that I can analyze codebases efficiently without downloading entire repository trees.

#### Acceptance Criteria

1. WHEN a user provides a public GitHub repository URL matching the pattern `https://github.com/{owner}/{repo}`, THE System SHALL invoke the GitHub REST API to fetch repository contents
2. WHEN a user provides a private GitHub repository URL with an OAuth token or Personal Access Token, THE System SHALL authenticate via GitHub API Authorization header and fetch repository contents
3. WHEN fetching repository files, THE Strategic_Fetching SHALL execute a three-pass prioritization algorithm that selects approximately 300 files based on: (1) configuration files and package manifests, (2) entry points and main application files, (3) core business logic files
4. WHEN repository ingestion completes, THE System SHALL extract repository metadata including owner, name, default branch, primary language, and file tree structure
5. THE System SHALL NOT persist OAuth tokens or Personal Access Tokens to Supabase, filesystem, or application logs
6. WHEN a repository URL fails validation against GitHub URL patterns, THE System SHALL return HTTP 400 with error message specifying invalid URL format
7. WHEN GitHub API returns 404, THE System SHALL return HTTP 404 with error message indicating repository not found or access denied
8. WHEN GitHub API rate limits are exceeded, THE System SHALL return HTTP 429 with error message indicating rate limit exceeded and retry-after duration

### Requirement 2: Tech Stack Detection

**User Story:** As an engineering lead, I want automated detection of programming languages, frameworks, databases, and tooling, so that I can rapidly assess the technical foundation without manual code inspection.

#### Acceptance Criteria

1. WHEN analyzing repository files, THE System SHALL detect programming languages by parsing file extensions and analyzing syntax patterns
2. WHEN analyzing package manifests (package.json, requirements.txt, go.mod, Cargo.toml, pom.xml), THE System SHALL extract framework and library dependencies with version constraints
3. WHEN analyzing configuration files and connection strings, THE System SHALL identify database systems (PostgreSQL, MySQL, MongoDB, Redis, etc.)
4. WHEN analyzing build configuration files (Dockerfile, docker-compose.yml, Makefile, webpack.config.js), THE System SHALL identify development tools and build systems
5. WHEN tech stack detection completes, THE System SHALL generate a normalized list of Tech_Tags with confidence scores
6. THE System SHALL store tech stack information in JSONB format conforming to schema: `{"languages": [{"name": string, "percentage": float}], "frameworks": [{"name": string, "version": string}], "databases": [string], "tools": [string]}`

### Requirement 3: Architecture Pattern Detection

**User Story:** As a software architect, I want automated detection of architectural patterns through static code analysis, so that I can assess design quality and maintainability characteristics.

#### Acceptance Criteria

1. WHEN analyzing directory structure and import graphs, THE System SHALL detect Clean Architecture patterns by identifying layers (entities, use cases, interface adapters, frameworks)
2. WHEN analyzing directory structure and file naming conventions, THE System SHALL detect MVC patterns by identifying models, views, and controllers directories
3. WHEN analyzing service boundaries and inter-service communication patterns, THE System SHALL detect Microservices architecture by identifying multiple independent services with API contracts
4. WHEN analyzing codebase structure, THE System SHALL detect Monolithic architecture by identifying single deployment unit with shared database
5. THE System SHALL store architecture patterns in JSONB format conforming to schema: `{"patterns": [{"type": string, "confidence": float, "evidence": [string]}]}`
6. WHEN multiple patterns are detected, THE System SHALL rank patterns by confidence score based on evidence strength

### Requirement 4: Risk Analysis

**User Story:** As a technical decision-maker, I want quantified risk assessment across security, maintainability, and scalability dimensions, so that I can prioritize remediation efforts and estimate technical debt.

#### Acceptance Criteria

1. WHEN performing analysis, THE System SHALL identify security risks by detecting: hardcoded credentials, SQL injection vulnerabilities, XSS vulnerabilities, insecure dependencies with known CVEs, missing authentication/authorization, and insecure cryptographic practices
2. WHEN performing analysis, THE System SHALL identify maintainability risks by calculating: cyclomatic complexity, code duplication percentage, test coverage gaps, documentation coverage, and dependency freshness
3. WHEN performing analysis, THE System SHALL identify scalability risks by detecting: N+1 query patterns, missing database indexes, synchronous blocking operations, unbounded resource allocation, and single points of failure
4. WHEN performing analysis, THE System SHALL assess technical debt by estimating remediation effort in person-hours for each identified risk
5. THE System SHALL store risks and gaps in JSONB format conforming to schema: `{"security": [{"type": string, "severity": string, "location": string, "description": string}], "maintainability": [{"metric": string, "value": float, "threshold": float}], "scalability": [{"issue": string, "impact": string, "recommendation": string}], "technical_debt_hours": float}`
6. WHEN calculating risk scores, THE System SHALL use severity weighting: critical (10), high (7), medium (4), low (1)

### Requirement 5: Feature Extraction

**User Story:** As a product manager, I want to know what features exist, so that I can understand product capabilities.

#### Acceptance Criteria

1. WHEN analyzing code, THE System SHALL detect authentication features
2. WHEN analyzing code, THE System SHALL detect payment integration features
3. WHEN analyzing code, THE System SHALL detect other significant features
4. THE System SHALL store extracted features in JSONB format

### Requirement 6: Integration Inventory

**User Story:** As a business analyst, I want to identify third-party integrations, so that I can estimate operational costs.

#### Acceptance Criteria

1. WHEN analyzing code, THE System SHALL identify third-party service integrations
2. WHEN integrations are identified, THE System SHALL provide cost estimates where applicable
3. THE System SHALL store integration inventory in JSONB format

### Requirement 7: Deep AI Code Review

**User Story:** As an engineering manager, I want parallel LLM-based code review with token optimization and fault tolerance, so that I can obtain detailed architectural and code quality analysis within acceptable latency and cost constraints.

#### Acceptance Criteria

1. WHEN performing deep review, THE System SHALL execute three Review_Agents concurrently using asyncio.gather: Frontend_Agent (analyzes UI components, state management, routing), Backend_Agent (analyzes API endpoints, business logic, data access), Infrastructure_Agent (analyzes deployment configs, CI/CD, monitoring)
2. WHEN preparing code for LLM analysis, THE Token_Optimization SHALL compress source code by removing: import statements, single-line and multi-line comments, leading/trailing whitespace, and blank lines, achieving 40-60% token reduction
3. WHEN calling OpenRouter API, THE System SHALL use a single Shared_HTTP_Client (httpx.AsyncClient) with connection pooling for all LLM requests to eliminate TCP handshake and TLS negotiation overhead
4. WHEN making LLM requests, THE Multi_Key_Rotation SHALL distribute requests across OPENROUTER_API_KEY_1 through OPENROUTER_API_KEY_4 using round-robin selection
5. WHEN an API key returns HTTP 429 (rate limit) or HTTP 401 (unauthorized), THE Multi_Key_Rotation SHALL immediately retry with the next available key
6. WHEN all API keys fail with rate limits, THE Multi_Key_Rotation SHALL attempt fallback to alternative models (e.g., from gpt-4 to claude-3-opus to gemini-pro)
7. THE Review_Agent prompts SHALL include constraints: "Base all findings on specific code evidence", "Do not speculate about missing code", "Cite file paths and line numbers for all claims"
8. THE Review_Agent responses SHALL be structured JSON conforming to schema: `{"findings": [{"category": string, "severity": string, "file": string, "line": int, "evidence": string, "recommendation": string}]}`
9. WHEN token optimization reduces code below 8000 tokens per file, THE System SHALL include full file content in LLM context
10. WHEN a file exceeds 8000 tokens after optimization, THE System SHALL split the file into logical chunks (by function/class boundaries) and analyze separately

### Requirement 8: Trend Intelligence Collection

**User Story:** As a technical strategist, I want version-aware market trend intelligence with RAG-based caching, so that I can contextualize technology choices against current ecosystem momentum without incurring redundant API costs.

#### Acceptance Criteria

1. WHEN Tech_Tags are identified, THE System SHALL execute parallel pgvector similarity searches for each tag using asyncio.gather with cosine similarity threshold 0.85
2. WHEN a cache hit occurs with collected_at timestamp within 7 days, THE System SHALL retrieve cached Trend_Insight and skip fresh data collection
3. WHEN a cache miss occurs, THE System SHALL invoke Query_Planner to generate 3-5 focused sub-queries per Tech_Tag optimized for each data source
4. WHEN collecting trends, THE System SHALL query Serper API with parameters: `{"q": query, "num": 10, "gl": "us"}` and extract title, snippet, link, date from results
5. WHEN collecting trends, THE System SHALL query GitHub REST API endpoints: `/search/repositories?q={tag}&sort=stars`, `/repos/{owner}/{repo}/releases/latest` and extract repository metadata, star count, release version, release date
6. WHEN collecting trends, THE System SHALL query Hacker News Algolia API with parameters: `{"query": tag, "tags": "story", "numericFilters": "created_at_i>{7_days_ago}"}` and extract story title, URL, points, comment count
7. WHEN collecting trends, THE System SHALL query Dev.to API endpoint: `/api/articles?tag={tag}&per_page=10&top=7` and extract article title, URL, published date, reaction count
8. WHEN executing multi-source collection, THE System SHALL use asyncio.gather to parallelize all API calls with 0.3 second stagger between requests to the same domain
9. WHEN processing raw trend data, THE Signal_Extraction SHALL score each item by: recency (weight 0.3), engagement metrics (weight 0.4), source authority (weight 0.3)
10. WHEN processing raw trend data, THE Signal_Extraction SHALL deduplicate items with >80% title similarity using fuzzy string matching
11. WHEN synthesizing trends via LLM, THE Version_Aware_Analysis SHALL extract latest_version using regex patterns: `v?\d+\.\d+\.\d+`, `version \d+\.\d+`, `@latest`
12. WHEN synthesizing trends via LLM, THE Version_Aware_Analysis SHALL extract version_info including: release date, breaking changes, deprecations, new features
13. WHEN LLM synthesis completes, THE System SHALL generate embedding vector using OpenAI text-embedding-ada-002 model (1536 dimensions)
14. WHEN storing to RAG_System, THE System SHALL insert Trend_Insight with pgvector embedding and GIN index on tag column
15. THE System SHALL enforce Cache_Window of 7 days by filtering: `collected_at > NOW() - INTERVAL '7 days'`
16. WHEN Serper API returns HTTP 429, THE System SHALL exponentially backoff with delays: 1s, 2s, 4s, 8s before failing
17. WHEN any single data source fails after retries, THE System SHALL continue with remaining sources and log warning

### Requirement 9: Report Generation

**User Story:** As a platform user, I want LLM-generated reports tailored for technical and executive audiences with trend enrichment and source citations, so that I can communicate findings effectively to stakeholders with different priorities.

#### Acceptance Criteria

1. WHEN analysis completes, THE System SHALL generate a Technical_Deep_Dive report by invoking LLM with context: repository analysis, code review findings, trend intelligence, and prompt template for engineering audience
2. WHEN analysis completes, THE System SHALL generate an Executive_Brief report by invoking LLM with context: business model analysis, risk assessment, opportunity identification, and prompt template for business stakeholders
3. WHEN generating reports, THE System SHALL inject Trend_Intelligence into LLM context with structure: `{"tag": string, "momentum": string, "latest_version": string, "key_points": [string], "sources": [{"title": string, "url": string, "date": string}]}`
4. THE Technical_Deep_Dive SHALL include sections: Executive Summary, Architecture Analysis (patterns, strengths, weaknesses), Code Quality Assessment (maintainability metrics, test coverage, documentation), Security Findings (vulnerabilities by severity, remediation priority), Performance Considerations (bottlenecks, optimization opportunities), Technical Roadmap (recommended improvements with effort estimates)
5. THE Executive_Brief SHALL include sections: Business Context, ROI Analysis (development velocity, maintenance cost, scalability cost), Risk Assessment (technical risks with business impact, mitigation strategies), Market Opportunities (competitive advantages, technology trends alignment), Action Plan (prioritized recommendations with timeline and resource requirements)
6. THE System SHALL format reports in GitHub Flavored Markdown with: headers (##, ###), bullet lists, code blocks with syntax highlighting, tables for structured data, emphasis (*italic*, **bold**)
7. THE System SHALL include source citations in format: `[Source Title](URL) - Date` for all trend intelligence references
8. WHEN a user requests PDF format via POST /report/pdf, THE System SHALL convert Markdown to PDF using a rendering library (e.g., WeasyPrint, Puppeteer) with: A4 page size, 1-inch margins, table of contents, page numbers, header with report title and date
9. WHEN PDF generation completes, THE System SHALL return PDF as binary stream with Content-Type: application/pdf and Content-Disposition: attachment; filename="analysis_{repo_name}_{timestamp}.pdf"

### Requirement 10: Performance Optimization

**User Story:** As a system operator, I want sub-60-second analysis latency through parallel processing and connection reuse, so that users receive timely results and infrastructure costs remain bounded.

#### Acceptance Criteria

1. THE System SHALL use asyncio.gather to execute parallel RAG cache lookups with concurrency limit of 10 simultaneous pgvector queries
2. THE System SHALL use asyncio.gather to execute parallel trend data collection with concurrency: Serper (3 concurrent), GitHub (5 concurrent), HN (unlimited), Dev.to (unlimited)
3. THE System SHALL use asyncio.gather to execute three Review_Agents concurrently without artificial delays
4. THE System SHALL use asyncio.gather to fetch repository files in batches of 20 concurrent requests
5. THE System SHALL instantiate a single Shared_HTTP_Client (httpx.AsyncClient) at application startup with configuration: `{"timeout": 30.0, "limits": {"max_connections": 100, "max_keepalive_connections": 20}, "http2": True}`
6. THE System SHALL reuse Shared_HTTP_Client for all outbound HTTP requests (OpenRouter, Serper, GitHub, HN, Dev.to) to eliminate TCP handshake (50-100ms) and TLS negotiation (100-200ms) per request
7. THE System SHALL perform static analysis (tech stack detection, architecture pattern detection) in-memory without writing intermediate files to disk
8. THE System SHALL record start and end timestamps for each API call and store in timeline JSONB with structure: `{"phase": string, "api_calls": [{"service": string, "endpoint": string, "duration_ms": int, "status": int}]}`
9. THE System SHALL implement 0.3 second asyncio.sleep stagger between uncached trend requests to the same domain to avoid rate limiting
10. THE System SHALL store total analysis_duration_ms in Analysis_Record calculated from first API call to final database write
11. WHEN analysis completes in under 60 seconds, THE System SHALL log success metric
12. WHEN analysis exceeds 60 seconds, THE System SHALL log warning with breakdown of slowest phases

### Requirement 11: Data Persistence

**User Story:** As a platform user, I want persistent storage of analysis results with structured JSONB schemas, so that I can retrieve historical analyses and perform aggregate queries across multiple repositories.

#### Acceptance Criteria

1. WHEN analysis completes, THE System SHALL insert an Analysis_Record into Supabase table `analysis_records` with UUID primary key generated via gen_random_uuid()
2. THE Analysis_Record SHALL include repo_url (TEXT NOT NULL) and repo_name (TEXT NOT NULL) extracted from GitHub repository metadata
3. THE Analysis_Record SHALL include analyzed_at (TIMESTAMPTZ NOT NULL DEFAULT NOW()) and model_used (TEXT NOT NULL) indicating primary LLM model
4. THE Analysis_Record SHALL include tech_stack (JSONB NOT NULL) conforming to schema: `{"languages": [{"name": string, "percentage": float}], "frameworks": [{"name": string, "version": string}], "databases": [string], "tools": [string]}`
5. THE Analysis_Record SHALL include architecture_patterns (JSONB NOT NULL) conforming to schema: `{"patterns": [{"type": string, "confidence": float, "evidence": [string]}]}`
6. THE Analysis_Record SHALL include risks_and_gaps (JSONB NOT NULL) conforming to schema: `{"security": [{"type": string, "severity": string, "location": string}], "maintainability": [{"metric": string, "value": float}], "scalability": [{"issue": string, "impact": string}], "technical_debt_hours": float}`
7. THE Analysis_Record SHALL include recommendations (JSONB NOT NULL) as array of objects: `[{"category": string, "priority": string, "effort_hours": float, "description": string}]`
8. THE Analysis_Record SHALL include features (JSONB NOT NULL) as array of detected features: `[{"name": string, "confidence": float, "files": [string]}]`
9. THE Analysis_Record SHALL include business_model (JSONB) with structure: `{"revenue_streams": [string], "cost_drivers": [string], "scalability_model": string}`
10. THE Analysis_Record SHALL include integrations (JSONB NOT NULL) as array: `[{"service": string, "purpose": string, "estimated_monthly_cost_usd": float}]`
11. THE Analysis_Record SHALL include technical_summary (TEXT NOT NULL) containing full Technical_Deep_Dive report in Markdown format
12. THE Analysis_Record SHALL include executive_summary (TEXT NOT NULL) containing full Executive_Brief report in Markdown format
13. THE Analysis_Record SHALL include analysis_duration_ms (INTEGER NOT NULL) representing total wall-clock time from request start to database commit
14. THE Analysis_Record SHALL include file_count (INTEGER NOT NULL) representing total files in repository and files_analyzed (INTEGER NOT NULL) representing files actually processed
15. THE Analysis_Record SHALL include token_usage (JSONB NOT NULL) with structure: `{"total_input_tokens": int, "total_output_tokens": int, "by_agent": [{"agent": string, "input_tokens": int, "output_tokens": int}]}`
16. THE Analysis_Record SHALL include timeline (JSONB NOT NULL) with structure: `{"phases": [{"name": string, "duration_ms": int, "api_calls": [{"service": string, "endpoint": string, "duration_ms": int, "status": int}]}]}`
17. THE Analysis_Record SHALL include trend_data (JSONB) as array of enriched trends: `[{"tag": string, "momentum": string, "latest_version": string, "key_points": [string], "sources_count": int}]`
18. WHEN storing Trend_Insight to table `trend_insights`, THE System SHALL include: id (TEXT PRIMARY KEY as hash of tag), tag (TEXT NOT NULL with GIN index), key_points (JSONB), momentum (TEXT), risks (JSONB), opportunities (JSONB), direction (TEXT), latest_version (TEXT), version_info (TEXT), sources (JSONB as array of source objects), sources_count (INTEGER), collected_at (TIMESTAMPTZ NOT NULL), embedding (VECTOR(1536) with ivfflat index)
19. THE System SHALL create GIN index on analysis_records(repo_name) for fast repository name lookups
20. THE System SHALL create BTREE index on analysis_records(analyzed_at DESC) for chronological queries

### Requirement 12: API Endpoints

**User Story:** As a frontend developer, I want RESTful API endpoints with OpenAPI specification, so that I can integrate analysis functionality with type-safe client code generation.

#### Acceptance Criteria

1. THE System SHALL expose POST /analyze endpoint accepting JSON body: `{"repo_url": string, "github_token": string | null}` and returning HTTP 202 with JSON: `{"analysis_id": string, "status": "queued"}`
2. THE System SHALL expose GET /analysis/{id} endpoint accepting UUID path parameter and returning HTTP 200 with full Analysis_Record as JSON, or HTTP 404 if analysis_id not found
3. THE System SHALL expose GET /analyses endpoint accepting query parameters: `?limit=int&offset=int&repo_name=string` and returning HTTP 200 with JSON: `{"analyses": [Analysis_Record], "total": int, "limit": int, "offset": int}`
4. THE System SHALL expose POST /report/pdf endpoint accepting JSON body: `{"analysis_id": string}` and returning HTTP 200 with Content-Type: application/pdf binary stream, or HTTP 404 if analysis_id not found
5. THE System SHALL expose GET /health endpoint returning HTTP 200 with JSON: `{"status": "healthy", "database": "connected", "llm_service": "available"}` or HTTP 503 if critical dependencies unavailable
6. WHEN POST /analyze receives invalid repo_url format, THE System SHALL return HTTP 400 with JSON: `{"error": "invalid_url", "message": "Repository URL must match pattern https://github.com/{owner}/{repo}"}`
7. WHEN POST /analyze encounters GitHub API authentication failure, THE System SHALL return HTTP 401 with JSON: `{"error": "github_auth_failed", "message": "Invalid or expired GitHub token"}`
8. WHEN POST /analyze encounters GitHub API rate limiting, THE System SHALL return HTTP 429 with JSON: `{"error": "rate_limited", "message": "GitHub API rate limit exceeded", "retry_after_seconds": int}`
9. WHEN any endpoint encounters internal server error, THE System SHALL return HTTP 500 with JSON: `{"error": "internal_error", "message": string, "request_id": string}` and log full stack trace with request_id for debugging
10. THE System SHALL include CORS headers: `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: GET, POST, OPTIONS`, `Access-Control-Allow-Headers: Content-Type, Authorization`
11. THE System SHALL generate OpenAPI 3.0 specification available at GET /openapi.json with complete schema definitions for all request/response types

### Requirement 13: Frontend User Interface

**User Story:** As a platform user, I want a responsive React-based interface with real-time status updates, so that I can initiate analyses and view results without page refreshes.

#### Acceptance Criteria

1. THE System SHALL render a landing page at route "/" with sections: hero (value proposition, CTA button), features overview (3-column grid with icons), dashboard preview (screenshot or demo), footer (links, contact)
2. THE System SHALL render a dashboard at route "/dashboard" with: repository URL input field (validated against GitHub URL pattern), optional GitHub token input field (type="password"), analyze button (disabled until valid URL entered), recent analyses list (last 10 analyses with repo name, date, status)
3. WHEN a user enters repository URL, THE System SHALL validate format using regex: `^https:\/\/github\.com\/[\w-]+\/[\w-]+$` and display inline error message if invalid
4. WHEN a user clicks analyze button, THE System SHALL POST to /analyze endpoint and display loading spinner with text "Analyzing repository..."
5. WHEN analysis is in progress, THE System SHALL poll GET /analysis/{id} endpoint every 2 seconds and display status updates: "Fetching files...", "Running code review...", "Collecting trends...", "Generating reports..."
6. WHEN analysis completes, THE System SHALL render tabbed interface with tabs: Technical (displays technical_summary Markdown), Executive (displays executive_summary Markdown), Timeline (displays timeline as interactive chart), Trends (displays trend_data as cards with momentum indicators)
7. THE System SHALL render Markdown content using react-markdown library with syntax highlighting via react-syntax-highlighter for code blocks
8. THE System SHALL provide "Download PDF" button that POSTs to /report/pdf and triggers browser download with filename from Content-Disposition header
9. WHEN GET /health returns HTTP 503, THE System SHALL display banner: "Service temporarily unavailable. Please try again later."
10. WHEN any API call returns HTTP 4xx or 5xx, THE System SHALL display toast notification with error message from response JSON
11. THE System SHALL implement responsive design with breakpoints: mobile (<640px), tablet (640-1024px), desktop (>1024px) using Tailwind CSS utility classes
12. THE System SHALL use Framer Motion for page transitions (fade in/out, 200ms duration) and button hover animations (scale 1.05, 100ms duration)

### Requirement 14: Security and Privacy

**User Story:** As a security-conscious user, I want ephemeral credential handling with zero persistence, so that my private repository access tokens cannot be compromised through database breaches or log analysis.

#### Acceptance Criteria

1. THE System SHALL accept github_token parameter in POST /analyze request body as optional string field
2. THE System SHALL use github_token exclusively in Authorization header for GitHub API requests: `Authorization: token {github_token}`
3. THE System SHALL NOT write github_token to Supabase database tables (analysis_records, trend_insights, or any other table)
4. THE System SHALL NOT write github_token to application logs (stdout, stderr, file logs, or structured logging systems)
5. THE System SHALL NOT write github_token to temporary files, cache files, or any filesystem location
6. THE System SHALL store github_token only in request-scoped memory (function parameter, local variable) with lifetime limited to single analysis request
7. WHEN analysis request completes (success or failure), THE System SHALL allow github_token to be garbage collected without explicit zeroing
8. THE System SHALL enforce HTTPS for all API endpoints by redirecting HTTP requests to HTTPS with HTTP 301
9. THE System SHALL include security headers in all responses: `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'self'`
10. THE System SHALL validate all user inputs (repo_url, github_token) against injection patterns before using in API calls or database queries
11. WHEN storing Analysis_Record, THE System SHALL sanitize all text fields to prevent XSS by escaping HTML entities in user-controlled content

### Requirement 15: Error Handling and Resilience

**User Story:** As a system operator, I want graceful degradation with detailed error context, so that partial failures do not cascade and debugging is efficient.

#### Acceptance Criteria

1. WHEN GitHub API returns HTTP 404, THE System SHALL return HTTP 404 to client with JSON: `{"error": "repo_not_found", "message": "Repository not found or access denied", "repo_url": string}`
2. WHEN GitHub API returns HTTP 403 (rate limit), THE System SHALL return HTTP 429 to client with JSON: `{"error": "github_rate_limited", "message": "GitHub API rate limit exceeded", "reset_at": ISO8601_timestamp}`
3. WHEN GitHub API returns HTTP 5xx, THE System SHALL retry up to 3 times with exponential backoff (1s, 2s, 4s) before returning HTTP 502 with JSON: `{"error": "github_unavailable", "message": "GitHub API temporarily unavailable"}`
4. WHEN OpenRouter API returns HTTP 429 for a specific key, THE Multi_Key_Rotation SHALL immediately switch to next key without counting as retry
5. WHEN all OpenRouter API keys return HTTP 429, THE System SHALL attempt model fallback in order: gpt-4-turbo → claude-3-opus → gemini-1.5-pro → gpt-3.5-turbo
6. WHEN all OpenRouter API keys and models fail, THE System SHALL return HTTP 503 with JSON: `{"error": "llm_unavailable", "message": "AI service temporarily unavailable. All API keys exhausted."}`
7. WHEN Serper API returns HTTP 429 or HTTP 5xx, THE System SHALL continue analysis with remaining trend sources (GitHub, HN, Dev.to) and log warning: `"Serper API unavailable, continuing with {N} remaining sources"`
8. WHEN GitHub trending API fails, THE System SHALL continue with remaining trend sources and log warning
9. WHEN Hacker News API fails, THE System SHALL continue with remaining trend sources and log warning
10. WHEN Dev.to API fails, THE System SHALL continue with remaining trend sources and log warning
11. WHEN all trend sources fail for a specific Tech_Tag, THE System SHALL continue analysis without trend enrichment for that tag and include note in report: "Trend data unavailable for {tag}"
12. WHEN Supabase connection fails during Analysis_Record insert, THE System SHALL retry up to 3 times with 1 second delay, then return HTTP 503 with JSON: `{"error": "database_unavailable", "message": "Unable to store analysis results"}`
13. WHEN pgvector query fails during RAG lookup, THE System SHALL treat as cache miss and proceed with fresh trend collection
14. THE System SHALL log all errors with structured format: `{"timestamp": ISO8601, "level": "ERROR", "request_id": UUID, "error_type": string, "message": string, "stack_trace": string, "context": object}`
15. THE System SHALL generate unique request_id (UUID v4) for each API request and include in all log entries and error responses for correlation

### Requirement 16: Configuration Management

**User Story:** As a system administrator, I want environment-based configuration with validation, so that I can deploy across development, staging, and production environments with appropriate credentials.

#### Acceptance Criteria

1. THE System SHALL read SUPABASE_URL from environment variable and validate format matches: `https://{project_id}.supabase.co`
2. THE System SHALL read SUPABASE_SERVICE_ROLE_KEY from environment variable and validate format matches JWT pattern: `^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$`
3. THE System SHALL read OPENROUTER_API_KEY_1, OPENROUTER_API_KEY_2, OPENROUTER_API_KEY_3, OPENROUTER_API_KEY_4 from environment variables and validate format matches: `^sk-or-v1-[a-f0-9]{64}$`
4. THE System SHALL read SERPER_API_KEY from environment variable and validate non-empty string
5. THE System SHALL read optional GITHUB_API_BASE_URL from environment variable with default: `https://api.github.com`
6. THE System SHALL read optional OPENROUTER_API_BASE_URL from environment variable with default: `https://openrouter.ai/api/v1`
7. THE System SHALL read optional MAX_CONCURRENT_FILES from environment variable with default: 20
8. THE System SHALL read optional ANALYSIS_TIMEOUT_SECONDS from environment variable with default: 300
9. THE System SHALL read optional RAG_CACHE_DAYS from environment variable with default: 7
10. WHEN SUPABASE_URL is missing or invalid, THE System SHALL exit with code 1 and error message: "Invalid or missing SUPABASE_URL environment variable"
11. WHEN SUPABASE_SERVICE_ROLE_KEY is missing or invalid, THE System SHALL exit with code 1 and error message: "Invalid or missing SUPABASE_SERVICE_ROLE_KEY environment variable"
12. WHEN all OPENROUTER_API_KEY_* variables are missing, THE System SHALL exit with code 1 and error message: "At least one OPENROUTER_API_KEY_N must be configured"
13. WHEN SERPER_API_KEY is missing, THE System SHALL log warning and continue with trend collection disabled: "SERPER_API_KEY not configured, Serper trend source disabled"
14. THE System SHALL load environment variables from .env file in development mode using python-dotenv library
15. THE System SHALL NOT load .env file in production mode (rely on system environment variables)

### Requirement 17: Testing and Quality Assurance

**User Story:** As a developer, I want comprehensive test coverage with both unit and integration tests, so that I can refactor confidently and catch regressions early.

#### Acceptance Criteria

1. THE System SHALL include unit tests for Strategic_Fetching algorithm verifying: prioritization logic, file count limits, three-pass execution order
2. THE System SHALL include unit tests for Token_Optimization verifying: 40-60% compression ratio, preservation of code semantics, removal of imports/comments/whitespace
3. THE System SHALL include unit tests for Multi_Key_Rotation verifying: round-robin distribution, automatic failover on HTTP 429, model fallback sequence
4. THE System SHALL include unit tests for Query_Planner verifying: sub-query generation, source-specific optimization, query deduplication
5. THE System SHALL include unit tests for Signal_Extraction verifying: relevance scoring algorithm, deduplication threshold (80% similarity), ranking correctness
6. THE System SHALL include unit tests for Version_Aware_Analysis verifying: version regex extraction, version_info parsing, handling of missing version data
7. THE System SHALL include integration tests for GitHub API interaction verifying: public repository fetch, private repository fetch with token, error handling for 404/403/429
8. THE System SHALL include integration tests for OpenRouter API interaction verifying: successful LLM completion, token counting, error handling for rate limits
9. THE System SHALL include integration tests for Supabase operations verifying: Analysis_Record insertion, Trend_Insight insertion with pgvector, query performance
10. THE System SHALL include integration tests for RAG cache workflow verifying: cache hit within 7 days, cache miss triggers fresh collection, embedding generation and storage
11. THE System SHALL include integration tests for end-to-end analysis workflow verifying: complete analysis from repo URL to stored Analysis_Record, report generation, PDF export
12. THE System SHALL maintain minimum 60 total tests (49 unit tests + 11 integration tests)
13. THE System SHALL use pytest framework with fixtures for: mock GitHub API, mock OpenRouter API, test Supabase instance, mock httpx client
14. THE System SHALL use pytest-asyncio for testing async functions with asyncio.gather
15. THE System SHALL use pytest-cov to measure code coverage and fail CI pipeline if coverage drops below 70%
16. THE System SHALL use pytest markers to separate: `@pytest.mark.unit` for unit tests (no external dependencies), `@pytest.mark.integration` for integration tests (require API keys), `@pytest.mark.slow` for tests exceeding 5 seconds
17. THE System SHALL mock external API calls in unit tests using respx library for httpx
18. THE System SHALL use VCR.py (pytest-vcr) to record/replay HTTP interactions in integration tests for deterministic results
