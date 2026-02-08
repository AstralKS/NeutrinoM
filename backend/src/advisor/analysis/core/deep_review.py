"""Deep AI Review Orchestrator - Multi-AI parallel code analysis.

Architecture:
1. Fetch entire repo (up to 300K tokens)
2. OPTIMIZE: Strip comments, boilerplate, compress whitespace
3. Partition into 3 meaningful chunks (frontend, backend, infra)
4. Send each chunk to parallel AI for DEEP code review
5. Aggregate findings into concrete, evidence-based report

Each AI gets up to 100K tokens and does ACTUAL code analysis.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from advisor.analysis.core.token_optimizer import TokenOptimizer, CompressionStats
from advisor.llm.client import OpenRouterClient
from advisor.llm.models import AvailableModels

logger = logging.getLogger(__name__)

# Token limits per chunk (100K each, 300K total)
MAX_TOKENS_PER_CHUNK = 100_000
CHARS_PER_TOKEN = 4  # Approximate


@dataclass
class ChunkAnalysis:
    """Analysis result from one AI chunk."""

    chunk_name: str
    files_analyzed: list[str]
    token_count: int
    findings: str  # Raw AI response
    error: str | None = None


@dataclass 
class DeepReviewResult:
    """Complete deep review result from all AIs."""

    total_files: int
    total_tokens: int
    compression_stats: CompressionStats | None
    frontend_analysis: ChunkAnalysis | None
    backend_analysis: ChunkAnalysis | None
    infra_analysis: ChunkAnalysis | None
    aggregated_technical: str
    aggregated_executive: str
    model_used: str


# File classification patterns
FRONTEND_PATTERNS = [
    "src/app", "src/pages", "src/components", "src/hooks", "src/lib",
    "app/", "pages/", "components/", "hooks/", "styles/", "public/",
    ".tsx", ".jsx", ".vue", ".svelte", "tailwind", "next.config",
    "vite.config", "nuxt.config", "package.json", "tsconfig",
]

BACKEND_PATTERNS = [
    "api/", "server/", "backend/", "src/advisor/", "routes/",
    "controllers/", "services/", "models/", "middleware/",
    "handlers/", "endpoints/", "main.py", "app.py", "server.",
    "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml",
]

INFRA_PATTERNS = [
    "docker", "kubernetes", "k8s", ".github/", "ci/", "cd/",
    "terraform", "pulumi", "ansible", "helm", "deploy",
    ".env", "config/", "scripts/", "makefile", "readme",
    "license", "changelog", ".yaml", ".yml", "nginx", "caddy",
]


class DeepReviewOrchestrator:
    """Orchestrates multi-AI deep code review."""

    def __init__(self) -> None:
        """Initialize with LLM client and token optimizer."""
        self._llm = OpenRouterClient()
        self._optimizer = TokenOptimizer(
            max_file_chars=15000,  # Aggressive truncation
            max_total_chars=600000,  # ~150K tokens for all 3 chunks
        )

    async def review(
        self,
        repo_name: str,
        file_contents: dict[str, str],
    ) -> DeepReviewResult:
        """Run deep AI review on repository.

        Args:
            repo_name: Name of the repository.
            file_contents: Dict of file paths to content.

        Returns:
            Complete deep review results from 3 parallel AIs.
        """
        logger.info(f"Starting deep review of {repo_name} with {len(file_contents)} files")

        # Step 0: OPTIMIZE - Strip comments, boilerplate, compress
        optimized_contents, compression_stats = self._optimizer.optimize(file_contents)
        
        logger.info(
            f"Token optimization: {compression_stats.original_chars:,} -> {compression_stats.compressed_chars:,} chars "
            f"({compression_stats.savings_percent:.1f}% saved)"
        )

        # Step 1: Partition optimized files into 3 chunks
        frontend, backend, infra = self._partition_files(optimized_contents)

        logger.info(f"Partitioned: Frontend={len(frontend)} Backend={len(backend)} Infra={len(infra)}")

        # Step 2: Prepare prompts with actual code
        frontend_prompt = self._build_chunk_prompt("frontend", frontend, repo_name)
        backend_prompt = self._build_chunk_prompt("backend", backend, repo_name)
        infra_prompt = self._build_chunk_prompt("infrastructure", infra, repo_name)

        # Step 3: Run all 3 AI calls in parallel
        results = await asyncio.gather(
            self._analyze_chunk("frontend", frontend_prompt, list(frontend.keys())),
            self._analyze_chunk("backend", backend_prompt, list(backend.keys())),
            self._analyze_chunk("infrastructure", infra_prompt, list(infra.keys())),
            return_exceptions=True,
        )

        # Process results
        frontend_result = results[0] if not isinstance(results[0], Exception) else ChunkAnalysis(
            chunk_name="frontend", files_analyzed=[], token_count=0, findings="", error=str(results[0])
        )
        backend_result = results[1] if not isinstance(results[1], Exception) else ChunkAnalysis(
            chunk_name="backend", files_analyzed=[], token_count=0, findings="", error=str(results[1])
        )
        infra_result = results[2] if not isinstance(results[2], Exception) else ChunkAnalysis(
            chunk_name="infrastructure", files_analyzed=[], token_count=0, findings="", error=str(results[2])
        )

        # Step 4: Aggregate into final reports
        technical, executive, model = await self._aggregate_reports(
            repo_name, frontend_result, backend_result, infra_result
        )

        total_tokens = (
            frontend_result.token_count + 
            backend_result.token_count + 
            infra_result.token_count
        )

        return DeepReviewResult(
            total_files=len(file_contents),
            total_tokens=total_tokens,
            compression_stats=compression_stats,
            frontend_analysis=frontend_result,
            backend_analysis=backend_result,
            infra_analysis=infra_result,
            aggregated_technical=technical,
            aggregated_executive=executive,
            model_used=model,
        )

    def _partition_files(
        self,
        file_contents: dict[str, str],
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Partition files into frontend, backend, and infra chunks."""
        frontend: dict[str, str] = {}
        backend: dict[str, str] = {}
        infra: dict[str, str] = {}

        frontend_chars = 0
        backend_chars = 0
        infra_chars = 0

        max_chars = MAX_TOKENS_PER_CHUNK * CHARS_PER_TOKEN

        for path, content in file_contents.items():
            path_lower = path.lower()
            content_len = len(content)

            # Classify and add to appropriate bucket (if within limit)
            if any(p in path_lower for p in FRONTEND_PATTERNS):
                if frontend_chars + content_len < max_chars:
                    frontend[path] = content
                    frontend_chars += content_len
            elif any(p in path_lower for p in BACKEND_PATTERNS):
                if backend_chars + content_len < max_chars:
                    backend[path] = content
                    backend_chars += content_len
            elif any(p in path_lower for p in INFRA_PATTERNS):
                if infra_chars + content_len < max_chars:
                    infra[path] = content
                    infra_chars += content_len
            else:
                # Default: add to smallest bucket
                sizes = [
                    (frontend_chars, frontend, "frontend"),
                    (backend_chars, backend, "backend"),
                    (infra_chars, infra, "infra"),
                ]
                smallest = min(sizes, key=lambda x: x[0])
                if smallest[0] + content_len < max_chars:
                    smallest[1][path] = content
                    if smallest[2] == "frontend":
                        frontend_chars += content_len
                    elif smallest[2] == "backend":
                        backend_chars += content_len
                    else:
                        infra_chars += content_len

        return frontend, backend, infra

    def _build_chunk_prompt(
        self,
        chunk_type: str,
        files: dict[str, str],
        repo_name: str,
    ) -> str:
        """Build detailed analysis prompt for a chunk."""
        if not files:
            return f"No {chunk_type} files found in this repository."

        # Build file content section (already optimized)
        file_sections = []
        for path, content in files.items():
            file_sections.append(f"=== FILE: {path} ===\n{content}")

        code_content = "\n\n".join(file_sections)

        return f"""DEEP CODE REVIEW: {chunk_type.upper()} - Repository: {repo_name}

You are an expert {chunk_type} engineer conducting a thorough code review.

## CRITICAL RULES
1. ONLY report findings you can PROVE with code snippets below
2. Every claim must include: file path + line quote
3. If you don't see something, say "Not found" - DO NOT guess
4. Zero tolerance for speculation or generic advice

---

## REVIEW SECTIONS

### 1. STACK & VERSIONS
What technologies are used? (List only what you see)
- Frameworks detected (quote the import/config)
- Libraries used
- Database/ORM if visible

### 2. ARCHITECTURE ANALYSIS
How is this code organized?
- File organization pattern
- Module dependencies (what imports what)
- Data flow (how data moves through the code)
- State management approach

### 3. CODE QUALITY ISSUES
List specific problems found:

| File | Line | Issue | Severity |
|------|------|-------|----------|
| path | "code snippet" | Description | High/Med/Low |

Focus on:
- Error handling gaps (try/except, .catch)
- Type safety issues
- Code duplication
- Complex functions (high cyclomatic complexity)
- Missing validation

### 4. SECURITY FINDINGS
⚠️ ONLY report if you find actual evidence:

| File | Line | Vulnerability | Risk |
|------|------|---------------|------|

Look for:
- Hardcoded secrets/keys/passwords
- SQL injection risks
- XSS vulnerabilities  
- Missing auth checks
- Insecure configurations

If no security issues found: "No security vulnerabilities identified in analyzed code."

### 5. API/ENDPOINTS DETECTED
List all routes/endpoints found:

| Method | Path | Handler | Auth Required |
|--------|------|---------|---------------|

### 6. DATABASE/DATA MODELS
If present, document:
- Tables/Collections
- Key relationships
- Validation rules

### 7. CONCRETE IMPROVEMENTS
Top 5 specific changes to make:

**1. [Title]**
- File: exact/path.ts
- Current: `problematic code snippet`
- Better: `improved code snippet`
- Why: explanation

**2. [Title]**
[same format]

### 8. WHAT'S DONE WELL
Strengths with evidence:
- [Strength 1]: "code snippet showing good practice"
- [Strength 2]: evidence

---
## CODE TO ANALYZE ({len(files)} files):

{code_content}

---
END INSTRUCTIONS. Begin your analysis."""

    async def _analyze_chunk(
        self,
        chunk_name: str,
        prompt: str,
        files: list[str],
    ) -> ChunkAnalysis:
        """Send chunk to AI for analysis."""
        if not prompt or "No " in prompt[:50]:
            return ChunkAnalysis(
                chunk_name=chunk_name,
                files_analyzed=[],
                token_count=0,
                findings=f"No {chunk_name} files to analyze.",
            )

        token_estimate = len(prompt) // CHARS_PER_TOKEN
        logger.info(f"Analyzing {chunk_name}: ~{token_estimate} tokens, {len(files)} files")

        try:
            result = await self._llm.complete(
                prompt=prompt,
                system_prompt="You are an expert code reviewer. Analyze code thoroughly and cite specific evidence for all findings.",
                temperature=0.2,
                max_tokens=8000,  # Allow detailed response
            )

            return ChunkAnalysis(
                chunk_name=chunk_name,
                files_analyzed=files,
                token_count=token_estimate,
                findings=result["content"],
            )

        except Exception as e:
            logger.error(f"Error analyzing {chunk_name}: {e}")
            return ChunkAnalysis(
                chunk_name=chunk_name,
                files_analyzed=files,
                token_count=token_estimate,
                findings="",
                error=str(e),
            )

    async def _aggregate_reports(
        self,
        repo_name: str,
        frontend: ChunkAnalysis,
        backend: ChunkAnalysis,
        infra: ChunkAnalysis,
    ) -> tuple[str, str, str]:
        """Aggregate 3 chunk analyses into final reports."""
        # Combine all findings
        combined_findings = f"""
# FRONTEND ANALYSIS
Files analyzed: {len(frontend.files_analyzed)}
{frontend.findings if frontend.findings else 'No frontend files or error occurred.'}

# BACKEND ANALYSIS  
Files analyzed: {len(backend.files_analyzed)}
{backend.findings if backend.findings else 'No backend files or error occurred.'}

# INFRASTRUCTURE ANALYSIS
Files analyzed: {len(infra.files_analyzed)}
{infra.findings if infra.findings else 'No infrastructure files or error occurred.'}
"""

        # Generate final technical report
        tech_result = await self._llm.complete(
            prompt=self._build_technical_aggregation_prompt(repo_name, combined_findings),
            system_prompt="You are a senior technical architect. Synthesize code review findings into a comprehensive technical report. Only include findings that have evidence.",
            temperature=0.2,
            max_tokens=8000,
        )

        # Generate final executive report
        exec_result = await self._llm.complete(
            prompt=self._build_executive_aggregation_prompt(repo_name, combined_findings),
            system_prompt="You are a technology strategist. Translate technical findings into business-focused insights. Focus on impact, not technical details. Only include findings with evidence.",
            temperature=0.2,
            max_tokens=6000,
        )

        return tech_result["content"], exec_result["content"], tech_result["model"]

    def _build_technical_aggregation_prompt(
        self,
        repo_name: str,
        findings: str,
    ) -> str:
        """Build comprehensive technical report prompt."""
        from advisor.llm.prompts import AGGREGATED_TECHNICAL_PROMPT
        return AGGREGATED_TECHNICAL_PROMPT.format(repo_name=repo_name, findings=findings)


    def _build_executive_aggregation_prompt(
        self,
        repo_name: str,
        findings: str,
    ) -> str:
        """Build executive report prompt."""
        from advisor.llm.prompts import AGGREGATED_EXECUTIVE_PROMPT
        return AGGREGATED_EXECUTIVE_PROMPT.format(repo_name=repo_name, findings=findings)

