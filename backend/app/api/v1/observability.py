"""
Observability and Traceability API Endpoints
Provides endpoints for run execution traces, timeline events, tool telemetry,
and LLM provider fallback metrics.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.services.observability import (
    ObservabilityService,
    RunTrace,
    TimelineEvent,
    ToolTraceRecord
)
from backend.app.services.llm.factory import LLMFactory

router = APIRouter()


@router.get("/runs/{run_id}/trace", response_model=RunTrace)
def get_run_trace(run_id: str):
    """Retrieves deep end-to-end execution trace for an analysis run."""
    trace = ObservabilityService.get_trace(run_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"No execution trace found for run '{run_id}'")
    return trace


@router.get("/runs/{run_id}/timeline", response_model=List[TimelineEvent])
def get_run_timeline(run_id: str):
    """Retrieves milestone events in chronological order for the specified run."""
    trace = ObservabilityService.get_trace(run_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"No execution trace found for run '{run_id}'")
    return trace.events


@router.get("/runs/{run_id}/tools", response_model=List[ToolTraceRecord])
def get_run_tools(run_id: str):
    """Retrieves tool executions recorded during the specified run."""
    trace = ObservabilityService.get_trace(run_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"No execution trace found for run '{run_id}'")
    return trace.tool_traces


@router.get("/observability/traces", response_model=List[RunTrace])
def list_run_traces():
    """Lists all available run traces with high-level metrics."""
    return ObservabilityService.list_traces()


@router.get("/observability/telemetry")
def get_provider_telemetry():
    """Returns recent LLM provider latency, fallback switches, and success metrics."""
    return {
        "telemetry_events": LLMFactory.get_telemetry(),
        "active_provider": "gemini" if "gemini" in LLMFactory.get_provider().provider_name else "groq"
    }
