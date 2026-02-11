"""Chunk prompt builders and signature extraction for deep review.

Handles:
- Extracting lightweight signatures (imports + function names) from code
- Building tailored prompts for backend (full code) vs frontend/infra (signatures)
- Combining frontend+infra into a single prompt when small enough
"""

import logging

logger = logging.getLogger(__name__)


def extract_signatures(files: dict[str, str]) -> dict[str, str]:
    """Extract only imports + function/class signatures from code.

    Used for frontend and infra files to keep them lightweight
    while still giving the AI enough context to analyze architecture.
    """
    extracted: dict[str, str] = {}
    for path, content in files.items():
        lines = content.split("\n")
        sig_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Keep imports
            if stripped.startswith((
                "import ", "from ", "require(", "const ", "export ",
                "module.exports",
            )):
                sig_lines.append(line)
            # Keep function/class/interface declarations
            elif stripped.startswith((
                "def ", "class ", "async def ", "function ",
                "async function ", "interface ", "type ", "enum ",
            )):
                sig_lines.append(line)
            # Keep decorators
            elif stripped.startswith("@"):
                sig_lines.append(line)
            # Keep export declarations
            elif stripped.startswith((
                "export default", "export const",
                "export function", "export class",
            )):
                sig_lines.append(line)
            # Keep route/endpoint definitions
            elif any(kw in stripped.lower() for kw in (
                "router.", "app.get", "app.post", "app.put",
                "app.delete", "app.patch", "@app.", "@router.",
            )):
                sig_lines.append(line)
            # Keep config files fully
            elif path.endswith((".yaml", ".yml", ".json", ".toml")):
                sig_lines.append(line)

        if sig_lines:
            extracted[path] = "\n".join(sig_lines)
        else:
            # Fallback: first 50 lines for unparseable files
            extracted[path] = "\n".join(lines[:50])

    return extracted


def build_backend_prompt(
    files: dict[str, str], repo_name: str,
) -> str:
    """Build prompt for backend: includes FULL logic + imports."""
    if not files:
        return "No backend files found in this repository."

    file_sections = [
        f"=== FILE: {path} ===\n{content}"
        for path, content in files.items()
    ]
    code_content = "\n\n".join(file_sections)

    return f"""DEEP CODE REVIEW: BACKEND - Repository: {repo_name}

You are a senior backend engineer. You have FULL source code below.
Analyze the main logic, data flow, security, and architecture.

## CRITICAL RULES
1. ONLY report findings you can PROVE with code references below
2. Every claim must include: file path + module/function reference
3. DO NOT provide code fix suggestions — reference files/modules only
4. Use MAXIMUM detail — the user wants comprehensive analysis

---

## REVIEW SECTIONS

### 1. STACK & VERSIONS
### 2. ARCHITECTURE ANALYSIS
### 3. CORE BUSINESS LOGIC
| Feature | Files/Modules | What it Does | Maturity |
|---------|--------------|-------------|----------|
### 4. CODE QUALITY
| File | Module/Function | Observation | Severity |
|------|----------------|-------------|----------|
### 5. SECURITY FINDINGS
| File | Section | Vulnerability | Risk |
|------|---------|---------------|------|
### 6. DATABASE/DATA MODELS
### 7. API SURFACE
| Method | Path | Handler | Auth |
|--------|------|---------|------|
### 8. IMPROVEMENT AREAS (no code fixes)
### 9. STRENGTHS

---
## CODE TO ANALYZE ({len(files)} files, FULL source):

{code_content}

---
END INSTRUCTIONS. Be extremely thorough. Begin your analysis."""


def build_lightweight_prompt(
    chunk_type: str, files: dict[str, str], repo_name: str,
) -> str:
    """Build prompt for frontend/infra: function names + imports only."""
    if not files:
        return f"No {chunk_type} files found in this repository."

    file_sections = [
        f"=== FILE: {path} ===\n{content}"
        for path, content in files.items()
    ]
    code_content = "\n\n".join(file_sections)

    return f"""ARCHITECTURE REVIEW: {chunk_type.upper()} - Repository: {repo_name}

You are a senior {chunk_type} engineer. Below are FUNCTION SIGNATURES,
IMPORTS, and KEY DECLARATIONS (not full source).
Analyze architecture, dependencies, and patterns.

## CRITICAL RULES
1. Analyze architecture and structure from signatures and imports
2. Every claim must reference specific files
3. DO NOT provide code fix suggestions
4. Focus on: tech stack, patterns, component structure, dependencies

---

### 1. TECHNOLOGY STACK
### 2. ARCHITECTURE & PATTERNS
### 3. COMPONENT INVENTORY
| Component/Module | File | Purpose | Dependencies |
|-----------------|------|---------|-------------|
### 4. OBSERVATIONS
| File | Item | Observation | Severity |
|------|------|-------------|----------|
### 5. IMPROVEMENT AREAS
### 6. STRENGTHS

---
## {chunk_type.upper()} SIGNATURES ({len(files)} files):

{code_content}

---
END. Analyze thoroughly based on available signatures."""


def build_combined_frontend_infra_prompt(
    frontend_files: dict[str, str],
    infra_files: dict[str, str],
    repo_name: str,
) -> str:
    """Build combined prompt for frontend + infra (saves an AI call)."""
    frontend_sections = [
        f"=== FILE: {p} ===\n{c}" for p, c in frontend_files.items()
    ]
    infra_sections = [
        f"=== FILE: {p} ===\n{c}" for p, c in infra_files.items()
    ]

    frontend_content = "\n\n".join(frontend_sections) or "No frontend files."
    infra_content = "\n\n".join(infra_sections) or "No infrastructure files."

    return f"""ARCHITECTURE REVIEW: FRONTEND + INFRASTRUCTURE - Repository: {repo_name}

You are a senior full-stack engineer. Below are FUNCTION SIGNATURES,
IMPORTS, and KEY DECLARATIONS from both frontend and infrastructure code.

## CRITICAL RULES
1. Analyze BOTH frontend and infrastructure
2. Every claim must reference specific files
3. DO NOT provide code fix suggestions

---

## PART A: FRONTEND ANALYSIS
### A1. Frontend Tech Stack
### A2. Frontend Architecture
### A3. Frontend Component Inventory
| Component | File | Purpose |
|-----------|------|---------|
### A4. Frontend Observations & Improvements
| File | Observation | Severity |
|------|-------------|----------|

---

## PART B: INFRASTRUCTURE ANALYSIS
### B1. Infrastructure Stack
### B2. Infrastructure Setup
### B3. Infrastructure Observations & Improvements
| File | Observation | Severity |
|------|-------------|----------|

---
## FRONTEND SIGNATURES ({len(frontend_files)} files):
{frontend_content}

---
## INFRASTRUCTURE SIGNATURES ({len(infra_files)} files):
{infra_content}

---
END. Analyze both areas thoroughly."""
