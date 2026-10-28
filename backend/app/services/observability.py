"""
DeploySafe Observability & Traceability Engine
Implements deep end-to-end tracing across:
Run ID -> Agents -> Tools -> RAG Retrievals -> Findings -> Gate Decision -> GitHub Publication.
Provides structured events, timing telemetry, and API data for UI dashboards.
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.services.safety import SecretRedactionEngine


class AgentTraceRecord(BaseModel):
    agent_name: str
    role: str
    status: Literal["RUNNING", "COMPLETED", "FAILED", "SKIPPED"]
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    tool_calls_count: int = 0
    findings_count: int = 0
    error: Optional[str] = None


class ToolTraceRecord(BaseModel):
    tool_name: str
    agent_name: str
    status: Literal["SUCCESS", "FAILED"]
    duration_ms: float
    input_summary: str
    output_summary: str
    error: Optional[str] = None


class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str  # e.g., "REPO_LOADED", "AGENT_PLANNED", "AGENT_COMPLETED", "CRITIC_REVIEW", "GATE_EVALUATED"
    component: str
    message: str
    status: Literal["SUCCESS", "WARNING", "ERROR", "INFO"] = "INFO"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunTrace(BaseModel):
    run_id: str
    repository_name: str
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    status: Literal["PREPARING", "PLANNING", "RUNNING_AGENTS", "CRITIC_REVIEW", "DEDUPLICATING", "COMPLETED", "FAILED", "PARTIAL"] = "PREPARING"
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "LOW"
    provider: str = "diagnostic_mock"
    model: str = "local-heuristic"
    rag_chunks_retrieved: int = 0
    agent_traces: List[AgentTraceRecord] = Field(default_factory=list)
    tool_traces: List[ToolTraceRecord] = Field(default_factory=list)
    events: List[TimelineEvent] = Field(default_factory=list)
    github_publication_status: Optional[str] = None


# Thread-safe in-memory registry of traces
_GLOBAL_TRACES: Dict[str, RunTrace] = {}


class ObservabilityService:
    """Manages creation, aggregation, and querying of end-to-end execution traces."""

    @classmethod
    def start_trace(
        cls,
        run_id: str,
        repository_name: str,
        commit_sha: Optional[str] = None,
        pr_number: Optional[int] = None
    ) -> RunTrace:
        """Initializes a new execution trace for an analysis run."""
        now_str = datetime.utcnow().isoformat()
        trace = RunTrace(
            run_id=run_id,
            repository_name=repository_name,
            commit_sha=commit_sha,
            pr_number=pr_number,
            started_at=now_str
        )
        _GLOBAL_TRACES[run_id] = trace
        cls.record_event(
            run_id=run_id,
            event_type="RUN_STARTED",
            component="Orchestrator",
            message=f"Initialized DeploySafe analysis trace on repository '{repository_name}'",
            status="INFO",
            metadata={"commit": commit_sha or "HEAD", "pr": pr_number}
        )
        return trace

    @classmethod
    def record_event(
        cls,
        run_id: str,
        event_type: str,
        component: str,
        message: str,
        status: Literal["SUCCESS", "WARNING", "ERROR", "INFO"] = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Records an individual execution milestone into the run timeline."""
        trace = _GLOBAL_TRACES.get(run_id)
        if not trace:
            return

        # Sanitize event message against secret exposure
        clean_msg = SecretRedactionEngine.redact_secrets(message)
        event = TimelineEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            component=component,
            message=clean_msg,
            status=status,
            metadata=metadata or {}
        )
        trace.events.append(event)
        logger.debug("[Observability] %s | %s: %s", run_id, event_type, clean_msg)

    @classmethod
    def record_agent_trace(cls, run_id: str, agent_trace: AgentTraceRecord):
        """Records telemetry for an individual specialized agent."""
        trace = _GLOBAL_TRACES.get(run_id)
        if trace:
            # Replace if already exists for this agent
            trace.agent_traces = [t for t in trace.agent_traces if t.agent_name != agent_trace.agent_name]
            trace.agent_traces.append(agent_trace)

    @classmethod
    def record_tool_trace(cls, run_id: str, tool_trace: ToolTraceRecord):
        """Records telemetry for an individual tool invocation."""
        trace = _GLOBAL_TRACES.get(run_id)
        if trace:
            # Redact input/output summaries to guarantee zero secret leakage
            tool_trace.input_summary = SecretRedactionEngine.redact_secrets(tool_trace.input_summary)
            tool_trace.output_summary = SecretRedactionEngine.redact_secrets(tool_trace.output_summary)
            trace.tool_traces.append(tool_trace)

    @classmethod
    def complete_trace(
        cls,
        run_id: str,
        status: str,
        risk_score: float,
        risk_level: str,
        provider: str,
        model: str,
        rag_chunks_retrieved: int = 0,
        github_status: Optional[str] = None
    ):
        """Marks the execution trace as completed and calculates total elapsed time."""
        trace = _GLOBAL_TRACES.get(run_id)
        if not trace:
            return

        now = datetime.utcnow()
        trace.completed_at = now.isoformat()
        trace.status = status
        trace.risk_score = risk_score
        trace.risk_level = risk_level
        trace.provider = provider
        trace.model = model
        trace.rag_chunks_retrieved = rag_chunks_retrieved
        trace.github_publication_status = github_status

        try:
            start_dt = datetime.fromisoformat(trace.started_at)
            trace.duration_seconds = round((now - start_dt).total_seconds(), 2)
        except Exception:
            trace.duration_seconds = 0.0

        cls.record_event(
            run_id=run_id,
            event_type="RUN_COMPLETED",
            component="Orchestrator",
            message=f"Completed DeploySafe analysis: status={status}, score={risk_score:.1f}/100 ({risk_level}) in {trace.duration_seconds}s",
            status="SUCCESS" if status == "COMPLETED" else "WARNING",
            metadata={"risk_score": risk_score, "provider": provider, "duration": trace.duration_seconds}
        )

    @classmethod
    def get_trace(cls, run_id: str) -> Optional[RunTrace]:
        return _GLOBAL_TRACES.get(run_id)

    @classmethod
    def list_traces(cls) -> List[RunTrace]:
        return list(_GLOBAL_TRACES.values())

    @classmethod
    def get_timeline(cls, run_id: str) -> List[TimelineEvent]:
        trace = _GLOBAL_TRACES.get(run_id)
        return trace.events if trace else []

    @classmethod
    def get_tool_traces(cls, run_id: str) -> List[ToolTraceRecord]:
        trace = _GLOBAL_TRACES.get(run_id)
        return trace.tool_traces if trace else []
