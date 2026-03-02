import asyncio
import math
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.nlp_parser import parse_query
from services.query_builder import build_query

router = APIRouter()

DEFAULT_PAGE_SIZE = 8  # Records shown per page in the frontend table

class SearchRequest(BaseModel):
    query: str
    page: int = Field(default=1, description="Which page to fetch (1-indexed)")
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, description="How many records per page")

@router.post("")
@router.post("/")
async def handle_search(request: SearchRequest):
    try:
        # Validate pagination params
        page      = max(1, request.page)
        page_size = max(1, min(request.page_size, 100))  # Cap at 100 per page
        start     = (page - 1) * page_size
        end       = start + page_size - 1  # Supabase range is inclusive
    
        # Step 1: Extract filters via LLM (blocking call — run in thread). Bypass if query empty
        if not request.query or not request.query.strip():
            filters = {}
        else:
            filters = await asyncio.to_thread(parse_query, request.query)

        # Step 2: Build & execute the primary query (with all filters)
        response = await asyncio.to_thread(
            lambda: build_query(filters).range(start, end).execute()
        )

        data        : list[dict] = response.data
        total_count : int        = response.count if response.count is not None else len(data)
        date_ignored: bool       = False

        # Step 3: Date-filter fallback
        # If the query returned 0 results AND a date filter was applied AND
        # there are other filters (name / doctor / age / gender), it likely means
        # the date range falls outside the dataset's actual data coverage.
        # In that case, re-run the same query WITHOUT the date filter so the
        # user still sees matching records and gets a clear warning.
        has_other_filters = any(k in filters for k in ("name", "doctor", "age", "gender"))
        if total_count == 0 and "date" in filters and has_other_filters:
            filters_no_date = {k: v for k, v in filters.items() if k != "date"}
            response_fallback = await asyncio.to_thread(
                lambda: build_query(filters_no_date).range(start, end).execute()
            )
            if (response_fallback.count or 0) > 0:
                data         = response_fallback.data
                total_count  = response_fallback.count or len(data)
                date_ignored = True  # Signal to the caller that date was dropped

        # Step 4: Calculate pagination metadata
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return {
            "filtersApplied": filters,
            "dateFilterIgnored": date_ignored,  # True → date range had no data
            "dateIgnoredReason": (
                "No records found within the specified date range. "
                "Results shown without the date filter."
            ) if date_ignored else None,
            "pagination": {
                "currentPage" : page,
                "pageSize"    : page_size,
                "totalPages"  : total_pages,
                "totalRecords": total_count,
                "hasNext"     : page < total_pages,
                "hasPrev"     : page > 1,
            },
            "resultCount": len(data),
            "data"       : data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
