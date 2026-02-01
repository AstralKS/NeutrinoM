"""FastAPI application and endpoints.

Main API layer for the AI Development Advisor.
"""

import logging
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from advisor.analysis import AnalysisOrchestrator
from advisor.config import get_settings
from advisor.database.client import get_supabase_client
from advisor.database.models import AnalysisRecord, AnalysisRequest, AnalysisResponse
from advisor.database.repository import AnalysisRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting AI Development Advisor API")
    try:
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

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
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
async def analyze_repository(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze a GitHub repository.

    Accepts a repository URL and optional access token for private repos.
    Returns analysis results including technical and executive summaries.

    Note: Access tokens are used ephemerally and never stored.
    """
    try:
        # Create orchestrator with optional token
        orchestrator = AnalysisOrchestrator(
            github_token=request.access_token,
        )

        # Run analysis
        result = await orchestrator.analyze(request.repo_url)

        # Store in database
        try:
            client = get_supabase_client()
            repo = AnalysisRepository(client)
            saved = await repo.create(result)
            analysis_id = saved.id
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")
            analysis_id = None

        return AnalysisResponse(
            success=True,
            analysis_id=analysis_id,
            message="Analysis completed successfully",
            technical_summary=result.technical_summary,
            executive_summary=result.executive_summary,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
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


# Report endpoints
class ReportRequest(BaseModel):
    """Request for report generation."""

    format: str = Field(
        default="technical",
        description="Report format: 'technical' or 'executive'",
    )


@app.post(
    "/analysis/{analysis_id}/report",
    tags=["Reports"],
)
async def generate_report(analysis_id: UUID, request: ReportRequest):
    """Generate PDF report for an analysis.

    Reports are generated on-demand from stored analysis data.
    """
    # TODO: Implement PDF generation
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
