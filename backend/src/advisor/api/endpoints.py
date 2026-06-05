"""FastAPI application and endpoints.

Main API layer for the AI Development Advisor.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from advisor.analysis import AnalysisOrchestrator
from advisor.api.deps import AuthenticatedUser, get_current_user, get_optional_user
from advisor.config import get_settings
from advisor.database.client import get_supabase_client
from advisor.database.models import AnalysisRecord, AnalysisRequest, AnalysisResponse
from advisor.database.repository import AnalysisRepository
from advisor.github.client import GitHubError
from advisor.reports.generator import generate_pdf
from advisor.llm.client import OpenRouterError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting AI Development Advisor API")
    try:
        # Load environment variables explicitly (local dev only)
        # On Render/production, env vars are injected by the platform
        from pathlib import Path
        from dotenv import load_dotenv

        env_loaded = False
        # Try project root first (monorepo: NeutrinoM/.env)
        project_root = Path(__file__).parent.parent.parent.parent.parent
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(env_path, override=True)
            logger.info(f"Loaded environment from {env_path}")
            env_loaded = True
        
        # Also try CWD/.env (when running from backend/)
        if not env_loaded:
            cwd_env = Path.cwd() / ".env"
            if cwd_env.exists():
                load_dotenv(cwd_env, override=True)
                logger.info(f"Loaded environment from {cwd_env}")
                env_loaded = True

        if not env_loaded:
            logger.info("No .env file found — using platform-injected environment variables")

        settings = get_settings()
        logger.info(f"Loaded settings for {settings.app_name}")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down API")


app = FastAPI(
    title="AI Development Advisor API",
    description=(
        "Intelligence and advisory system for codebase analysis. "
        "Provides technical insights for engineers and strategic guidance "
        "for non-technical leaders."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware — environment-aware origins
import os as _os

_allowed_origins_env = _os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins = (
    [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if _allowed_origins_env
    else ["*"]  # permissive in local dev only
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins if _allowed_origins_env else [],
    allow_origin_regex=".*" if not _allowed_origins_env else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Check API health status."""
    return HealthResponse()


# Analysis endpoints
@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Analysis"],
)
async def analyze_repository(
    request: AnalysisRequest,
    user: AuthenticatedUser | None = Depends(get_optional_user),
) -> AnalysisResponse:
    """Analyze a GitHub repository.

    Accepts a repository URL and optional access token for private repos.
    Returns analysis results including technical and executive summaries.

    Note: Access tokens are used ephemerally and never stored.
    If an authenticated user is making the request, the analysis is linked to them.
    """
    try:
        logger.info(f"Received analysis request for {request.repo_url}")

        # Create orchestrator with optional token
        orchestrator = AnalysisOrchestrator(
            github_token=request.access_token,
        )

        # Run analysis
        result = await orchestrator.analyze(request.repo_url)

        # Link to authenticated user if present
        if user:
            result.user_id = UUID(user.id)
            logger.info(f"Linking analysis {result.repo_name} to user {user.id}")

        # Store in database
        try:
            client = get_supabase_client()
            repo = AnalysisRepository(client)
            saved = await repo.create(result)
            analysis_id = saved.id
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")
            analysis_id = None

        # Extract per-call timings from timeline
        api_timings = []
        if result.timeline:
            for phase_data in result.timeline.get("phases", {}).values():
                api_timings.extend(phase_data.get("api_calls", []))

        return AnalysisResponse(
            success=True,
            analysis_id=analysis_id,
            message="Analysis completed successfully",
            technical_summary=result.technical_summary,
            executive_summary=result.executive_summary,
            executive_stats=result.executive_stats,
            repo_url=result.repo_url,
            model_used=result.model_used,
            timeline=result.timeline,
            api_call_timings=api_timings or None,
            trend_data=result.trend_data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except GitHubError as e:
        http_status = e.status_code or status.HTTP_502_BAD_GATEWAY
        raise HTTPException(
            status_code=http_status,
            detail=str(e),
        ) from e
    except OpenRouterError as e:
        http_status = getattr(e, "status_code", status.HTTP_502_BAD_GATEWAY) or status.HTTP_502_BAD_GATEWAY
        raise HTTPException(
            status_code=http_status,
            detail=f"LLM Provider Error: {str(e)}",
        ) from e
    except Exception as e:
        logger.exception("Analysis failed with traceback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e) or 'Unknown error'}",
        ) from e


@app.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisRecord,
    tags=["Analysis"],
)
async def get_analysis(analysis_id: UUID) -> AnalysisRecord:
    """Retrieve a stored analysis by ID."""
    try:
        client = get_supabase_client()
        repo = AnalysisRepository(client)
        result = await repo.get_by_id(analysis_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analysis: {str(e)}",
        ) from e


class AnalysisListResponse(BaseModel):
    """Response for listing analyses."""

    analyses: list[AnalysisRecord]
    count: int


@app.get(
    "/analyses",
    response_model=AnalysisListResponse,
    tags=["Analysis"],
)
async def list_analyses(limit: int = 20) -> AnalysisListResponse:
    """List recent analyses."""
    try:
        client = get_supabase_client()
        repo = AnalysisRepository(client)
        results = await repo.list_recent(limit=limit)

        return AnalysisListResponse(
            analyses=results,
            count=len(results),
        )

    except Exception as e:
        # Handle missing table gracefully - return empty list
        error_str = str(e).lower()
        if "relation" in error_str and "does not exist" in error_str:
            logger.warning("Database table not found - returning empty list")
            return AnalysisListResponse(analyses=[], count=0)
        
        logger.error(f"Failed to list analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list analyses: {str(e)}",
        ) from e


# ──────────────────────────────────────────────
# User-authenticated endpoints
# ──────────────────────────────────────────────

class UserHistoryResponse(BaseModel):
    """Response for user analysis history."""

    analyses: list[AnalysisRecord]
    count: int


@app.get(
    "/user/history",
    response_model=UserHistoryResponse,
    tags=["User"],
)
async def get_user_history(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = 50,
) -> UserHistoryResponse:
    """Fetch all analysis records for the authenticated user."""
    try:
        client = get_supabase_client()
        repo = AnalysisRepository(client)
        results = await repo.get_by_user_id(UUID(user.id), limit=limit)

        return UserHistoryResponse(
            analyses=results,
            count=len(results),
        )

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if "relation" in error_str and "does not exist" in error_str:
            logger.warning("Database table not found - returning empty history")
            return UserHistoryResponse(analyses=[], count=0)

        logger.error(f"Failed to fetch user history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user history: {str(e)}",
        ) from e


class GitHubRepoItem(BaseModel):
    """Simplified GitHub repository info."""

    id: int
    name: str
    full_name: str
    html_url: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    updated_at: str | None = None
    private: bool = False


class GitHubReposResponse(BaseModel):
    """Response for listing user GitHub repos."""

    repos: list[GitHubRepoItem]
    count: int


@app.get(
    "/user/github/repos",
    response_model=GitHubReposResponse,
    tags=["User"],
)
async def get_user_github_repos(
    user: AuthenticatedUser = Depends(get_current_user),
    x_github_token: Annotated[str | None, Header()] = None,
    page: int = 1,
    per_page: int = 30,
) -> GitHubReposResponse:
    """Fetch the authenticated user's GitHub repositories.

    Uses the GitHub provider token. Prioritizes the X-GitHub-Token header
    (passed from frontend session), then falls back to Supabase identities.
    """
    try:
        github_token = x_github_token

        # If not provided in header, try to fetch from Supabase
        if not github_token:
            # try to find it in the user identities if needed, but header is preferred
            # (skipping complex Supabase admin logic for now as header is more reliable)
            pass

        if not github_token:
            # One last try: check if we can get it from Supabase /user endpoint
            # This is a fallback
            try:
                settings = get_settings()
                async with httpx.AsyncClient() as http_client:
                    resp = await http_client.get(
                        f"{settings.supabase_url}/auth/v1/user",
                        headers={
                            "Authorization": f"Bearer {user.access_token}",
                            "apikey": settings.supabase_service_role_key,
                        },
                    )
                    if resp.status_code == 200:
                        user_data = resp.json()
                        for identity in user_data.get("identities", []):
                            if identity.get("provider") == "github":
                                github_token = identity.get("access_token")
                                break
            except Exception as e:
                logger.warning(f"Failed to fetch GitHub token from Supabase: {e}")

        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub provider token not found. Please sign in with GitHub.",
            )

        # Fetch repos from GitHub API
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                params={
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": per_page,
                    "page": page,
                    "type": "owner",
                },
            )

            if resp.status_code != 200:
                logger.error(f"GitHub API Error: {resp.status_code} {resp.text}")
                msg = "Failed to fetch repositories from GitHub."
                if resp.status_code == 401:
                    msg = "GitHub token expired or invalid. Please sign out and sign in again."
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=msg,
                )

            repos_data = resp.json()
            repos = [
                GitHubRepoItem(
                    id=r["id"],
                    name=r["name"],
                    full_name=r["full_name"],
                    html_url=r["html_url"],
                    description=r.get("description"),
                    language=r.get("language"),
                    stargazers_count=r.get("stargazers_count", 0),
                    updated_at=r.get("updated_at"),
                    private=r.get("private", False),
                )
                for r in repos_data
            ]

            return GitHubReposResponse(repos=repos, count=len(repos))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user repos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user repos: {str(e)}",
        ) from e


# Report endpoints
class ReportRequest(BaseModel):
    """Request for report generation."""

    format: str = Field(
        default="technical",
        description="Report format: 'technical' or 'executive'",
    )


class ReportPdfRequest(BaseModel):
    """Request body for generating a PDF report from content."""

    report_type: str = Field(
        ...,
        description="Report type: 'technical' or 'executive'",
    )
    repo_url: str = Field(..., description="Repository URL for the report header")
    content: str = Field(..., description="Report body in markdown")
    model_used: str | None = Field(default=None, description="Model name for the header")


@app.post(
    "/report/pdf",
    tags=["Reports"],
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF file"}},
)
async def create_report_pdf(request: ReportPdfRequest) -> Response:
    """Generate a PDF report from markdown content.

    Accepts report type, repo URL, and markdown content; returns a PDF file.
    Used by the frontend after analysis to download technical or executive reports.
    """
    if request.report_type not in ("technical", "executive"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="report_type must be 'technical' or 'executive'",
        )
    try:
        pdf_bytes = await asyncio.to_thread(
            generate_pdf,
            report_type=request.report_type,
            repo_url=request.repo_url,
            content_markdown=request.content,
            model_used=request.model_used,
        )
    except Exception as e:
        logger.exception("PDF generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}",
        ) from e
    filename = f"{request.report_type}_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@app.post(
    "/analysis/{analysis_id}/report",
    tags=["Reports"],
)
async def generate_report(analysis_id: UUID, request: ReportRequest):
    """Generate PDF report for an analysis.

    Reports are generated on-demand from stored analysis data.
    """
    # TODO: Implement PDF generation from stored analysis
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="PDF generation not yet implemented",
    )


# Entry point for uvicorn
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "advisor.api.endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
