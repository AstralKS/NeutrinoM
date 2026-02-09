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
import re
from dataclasses import dataclass
from typing import Any

from advisor.analysis.core.token_optimizer import TokenOptimizer, CompressionStats
from advisor.llm.client import OpenRouterClient
from advisor.llm.models import AvailableModels
from advisor.trends.trend_master import TrendMaster
from advisor.trends.version_checker import VersionChecker, PackageInfo

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

    def __init__(
        self,
        trend_master: TrendMaster | None = None,
        version_checker: VersionChecker | None = None,
    ) -> None:
        """Initialize with LLM client, token optimizer, and trend/version services."""
        self._llm = OpenRouterClient()
        self._optimizer = TokenOptimizer(
            max_file_chars=15000,  # Aggressive truncation
            max_total_chars=600000,  # ~150K tokens for all 3 chunks
        )
        self._trend_master = trend_master or TrendMaster()
        self._version_checker = version_checker or VersionChecker()

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

        # Step 4: Aggregate into final reports with trend/version context
        technical, executive, model = await self._aggregate_reports(
            repo_name, frontend_result, backend_result, infra_result, file_contents
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
        file_contents: dict[str, str] | None = None,
    ) -> tuple[str, str, str]:
        """Aggregate 3 chunk analyses into final reports with trend and version context."""
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

        # Fetch trend and version context
        trend_context = "No trend data available."
        version_context = "No version data available."
        
        if file_contents:
            try:
                # Extract tech tags and fetch trend context
                tech_tags = self._extract_tech_tags(file_contents)
                if tech_tags:
                    trends = await self._trend_master.get_batch_trends(list(tech_tags)[:10])
                    trend_context = self._trend_master.format_for_analysis(trends)
                
                # Extract packages and fetch version context
                packages = self._extract_packages(file_contents)
                if packages:
                    versions = await self._version_checker.get_batch_versions(packages[:20])
                    version_context = self._version_checker.format_for_analysis(versions)
            except Exception as e:
                logger.warning(f"Could not fetch trend/version context: {e}")

        # Generate final technical report with context
        tech_result = await self._llm.complete(
            prompt=self._build_technical_aggregation_prompt(
                repo_name, combined_findings, trend_context, version_context
            ),
            system_prompt="You are a senior technical architect. Synthesize code review findings into a comprehensive technical report. Use the trend and version context to inform upgrade recommendations. Only include findings that have evidence.",
            temperature=0.2,
            max_tokens=8000,
        )

        # Generate final executive report with context
        exec_result = await self._llm.complete(
            prompt=self._build_executive_aggregation_prompt(
                repo_name, combined_findings, trend_context, version_context
            ),
            system_prompt="You are a technology strategist. Translate technical findings into business-focused insights. Use trend data to highlight market opportunities. Focus on impact, not technical details. Only include findings with evidence.",
            temperature=0.2,
            max_tokens=6000,
        )

        return tech_result["content"], exec_result["content"], tech_result["model"]

    def _extract_tech_tags(self, file_contents: dict[str, str]) -> set[str]:
        """Extract technology tags from file contents for trend lookup."""
        tags: set[str] = set()
        all_content = " ".join(file_contents.values()).lower()
        
        # Map patterns to tag names
        tech_patterns = {
            r"\breact\b": "react",
            r"\bnext\.?js\b|next/": "nextjs",
            r"\bvue\b": "vue",
            r"\bangular\b": "angular",
            r"\bsvelte\b": "svelte",
            r"\bfastapi\b": "fastapi",
            r"\bdjango\b": "django",
            r"\bflask\b": "flask",
            r"\bexpress\b": "express",
            r"\bnestjs\b": "nestjs",
            r"\bpostgres|postgresql\b": "postgresql",
            r"\bmongodb\b": "mongodb",
            r"\bredis\b": "redis",
            r"\bsupabase\b": "supabase",
            r"\bprisma\b": "prisma",
            r"\btailwind\b": "tailwindcss",
            r"\btypescript\b": "typescript",
            r"\bpython\b": "python",
            r"\brust\b": "rust",
            r"\bgo\b": "golang",
            r"\bdocker\b": "docker",
            r"\bkubernetes|k8s\b": "kubernetes",
        }
        
        for pattern, tag in tech_patterns.items():
            if re.search(pattern, all_content):
                tags.add(tag)
        
        return tags

    def _extract_packages(self, file_contents: dict[str, str]) -> list[PackageInfo]:
        """Extract package names and versions from package files."""
        packages: list[PackageInfo] = []
        
        for path, content in file_contents.items():
            path_lower = path.lower()
            
            # Parse package.json
            if path_lower.endswith("package.json"):
                try:
                    import json
                    data = json.loads(content)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for name, version in deps.items():
                        # Clean version string (remove ^, ~, etc.)
                        clean_version = re.sub(r"^[\^~>=<]+", "", str(version))
                        packages.append(PackageInfo(
                            name=name,
                            current_version=clean_version if clean_version else None,
                            registry="npm",
                        ))
                except Exception:
                    pass
            
            # Parse requirements.txt
            elif path_lower.endswith("requirements.txt"):
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse: package==version or package>=version
                        match = re.match(r"^([a-zA-Z0-9_-]+)\s*([=<>!]+)?\s*([\d\.]+)?", line)
                        if match:
                            packages.append(PackageInfo(
                                name=match.group(1),
                                current_version=match.group(3),
                                registry="pypi",
                            ))
            
            # Parse pyproject.toml dependencies
            elif path_lower.endswith("pyproject.toml"):
                # Simple regex extraction for common patterns
                for match in re.finditer(r'"([a-zA-Z0-9_-]+)\s*([<>=!]+)?\s*([\d\.]+)?"', content):
                    packages.append(PackageInfo(
                        name=match.group(1),
                        current_version=match.group(3),
                        registry="pypi",
                    ))
        
        return packages

    def _build_technical_aggregation_prompt(
        self,
        repo_name: str,
        findings: str,
        trend_context: str = "",
        version_context: str = "",
    ) -> str:
        """Build comprehensive technical report prompt with trend and version context."""
        from advisor.llm.prompts import AGGREGATED_TECHNICAL_PROMPT
        
        # Now prompts.py has placeholders, so we format them directly
        return AGGREGATED_TECHNICAL_PROMPT.format(
            repo_name=repo_name,
            findings=findings,
            trend_context=trend_context,
            version_context=version_context,
        )

    def _build_executive_aggregation_prompt(
        self,
        repo_name: str,
        findings: str,
        trend_context: str = "",
        version_context: str = "",
    ) -> str:
        """Build executive report prompt with trend and version context."""
        from advisor.llm.prompts import AGGREGATED_EXECUTIVE_PROMPT
        
        return AGGREGATED_EXECUTIVE_PROMPT.format(
            repo_name=repo_name,
            findings=findings,
            trend_context=trend_context,
            version_context=version_context,
        )

