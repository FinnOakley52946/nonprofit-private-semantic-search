from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from content_visibility import SearchContext
from nonprofit_search import InfraiClient, InfraiError, NonprofitSearch


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    donor_id: str | None = Field(default=None, max_length=100)
    program_id: str | None = Field(default=None, max_length=100)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResponse(BaseModel):
    matches: list[dict[str, Any]]


app = FastAPI(title="Nonprofit content search")


@app.post("/search", response_model=SearchResponse)
def search_content(request: SearchRequest) -> SearchResponse:
    try:
        search = NonprofitSearch(InfraiClient())
        matches = search.search(
            request.query,
            SearchContext(donor_id=request.donor_id, program_id=request.program_id),
            request.top_k,
        )
        return SearchResponse(matches=matches)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
