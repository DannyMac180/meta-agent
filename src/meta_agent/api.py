"""REST API endpoints for meta-agent template functionality."""

from __future__ import annotations

from typing import List, Dict, Any, Optional, cast
from datetime import datetime

try:
    from fastapi import FastAPI, Query, HTTPException
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - optional dependency missing
    # Graceful fallback types when FastAPI or Pydantic are absent.
    FastAPI = cast(Any, None)
    Query = cast(Any, None)
    HTTPException = cast(Any, None)
    BaseModel = cast(Any, object)

from .template_registry import TemplateRegistry
from .template_search import TemplateSearchEngine


class TemplateSearchRequest(BaseModel):
    """Request model for template search."""
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    limit: int = 5


class TemplateSearchResponse(BaseModel):
    """Response model for template search."""
    matches: List[Dict[str, Any]]
    total_found: int
    query_time_ms: float


class TemplateListResponse(BaseModel):
    """Response model for template listing."""
    templates: List[Dict[str, Any]]
    total_count: int


def create_app() -> FastAPI:
    """Create FastAPI application with template endpoints."""
    if FastAPI is None:
        raise ImportError("FastAPI is required for the REST API. Install with: pip install fastapi uvicorn")
    
    app = FastAPI(
        title="Meta-Agent Template API",
        description="REST API for managing and searching meta-agent templates",
        version="0.1.0"
    )
    
    # Initialize template services
    registry = TemplateRegistry()
    search_engine = TemplateSearchEngine(registry)
    search_engine.build_index()
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    @app.get("/api/v1/templates", response_model=TemplateListResponse)
    async def list_templates():
        """List all available templates."""
        templates = registry.list_templates()
        return TemplateListResponse(
            templates=templates,
            total_count=len(templates)
        )
    
    @app.get("/api/v1/templates/search", response_model=TemplateSearchResponse)
    async def search_templates(
        query: str = Query(..., description="Search query string"),
        category: Optional[str] = Query(None, description="Filter by category"),
        tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
        capabilities: Optional[str] = Query(None, description="Comma-separated list of required capabilities"),
        limit: int = Query(5, ge=1, le=50, description="Maximum number of results")
    ):
        """Search templates by query and optional filters."""
        start_time = datetime.utcnow()
        
        # Parse comma-separated parameters
        tags_list = [t.strip() for t in tags.split(",")] if tags else None
        capabilities_list = [c.strip() for c in capabilities.split(",")] if capabilities else None
        
        matches = search_engine.search(
            query=query,
            category=category,
            tags=tags_list,
            capabilities=capabilities_list,
            limit=limit
        )
        
        end_time = datetime.utcnow()
        query_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Convert matches to dict format
        matches_dict = []
        for match in matches:
            matches_dict.append({
                "slug": match.slug,
                "version": match.version,
                "score": match.score,
                "preview": match.preview,
                "metadata": match.metadata
            })
        
        return TemplateSearchResponse(
            matches=matches_dict,
            total_found=len(matches),
            query_time_ms=query_time_ms
        )
    
    @app.post("/api/v1/templates/search", response_model=TemplateSearchResponse)
    async def search_templates_post(request: TemplateSearchRequest):
        """Search templates using POST request with JSON body."""
        start_time = datetime.utcnow()
        
        matches = search_engine.search(
            query=request.query,
            category=request.category,
            tags=request.tags,
            capabilities=request.capabilities,
            limit=request.limit
        )
        
        end_time = datetime.utcnow()
        query_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Convert matches to dict format
        matches_dict = []
        for match in matches:
            matches_dict.append({
                "slug": match.slug,
                "version": match.version,
                "score": match.score,
                "preview": match.preview,
                "metadata": match.metadata
            })
        
        return TemplateSearchResponse(
            matches=matches_dict,
            total_found=len(matches),
            query_time_ms=query_time_ms
        )
    
    @app.get("/api/v1/templates/{slug}")
    async def get_template(slug: str, version: str = Query("latest", description="Template version")):
        """Get a specific template by slug and version."""
        template_content = registry.load_template(slug, version)
        if not template_content:
            raise HTTPException(status_code=404, detail=f"Template '{slug}' version '{version}' not found")
        
        # Get metadata
        templates = registry.list_templates()
        template_info = next((t for t in templates if t["slug"] == slug.replace(" ", "_").lower()), None)
        if not template_info:
            raise HTTPException(status_code=404, detail=f"Template '{slug}' not found")
        
        return {
            "slug": slug,
            "version": version,
            "content": template_content,
            "metadata": template_info
        }
    
    return app


# Global app instance for easy import by the CLI and tests.
app = None
try:
    app = create_app()
except ImportError:
    # FastAPI isn't installed; keep ``app`` as ``None`` so other
    # parts of the codebase can handle the missing dependency gracefully.
    pass
