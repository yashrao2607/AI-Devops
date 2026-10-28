from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# Evidence Schema (Step 16)
# ------------------------------------------------------------------------------
class Evidence(BaseModel):
    evidence_type: Literal[
        "SOURCE_CODE",
        "CONFIGURATION",
        "DOCUMENTATION",
        "GIT_DIFF",
        "SCANNER",
        "TEST_RESULT",
        "DEPENDENCY_MANIFEST",
        "RAG_RETRIEVAL"
    ]
    file_path: str = Field(description="Exact file path in repository")
    line_start: Optional[int] = Field(default=None, description="1-indexed starting line")
    line_end: Optional[int] = Field(default=None, description="1-indexed ending line")
    snippet: str = Field(description="Actual snippet or ground-truth evidence text")
    source: str = Field(description="Source mechanism, e.g. git_diff, file_read, scanner, rag")
    source_tool: Optional[str] = Field(default=None, description="Tool that produced the evidence")
    repository_id: str = Field(description="Target repository identifier")
    commit_sha: Optional[str] = Field(default=None, description="Commit SHA if available")

# ------------------------------------------------------------------------------
# Canonical Finding Schema (Step 15)
# ------------------------------------------------------------------------------
class Finding(BaseModel):
    id: str = Field(description="Unique finding identifier, e.g., F-101")
    category: Literal[
        "CODE",
        "DEPENDENCY",
        "CONFIGURATION",
        "SECURITY",
        "TEST",
        "DOCUMENTATION",
        "ENVIRONMENT",
        "CONTAINERIZATION",
        "CI_CD"
    ]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    title: str = Field(description="Concise description of the deployment risk")
    summary: str = Field(description="Detailed explanation of the risk mechanism")
    impact: str = Field(description="Potential runtime, operational, or deployment failure impact")
    recommendation: str = Field(description="Actionable remediation instructions")
    repository_id: str = Field(description="Target repository ID")
    commit_sha: Optional[str] = Field(default=None, description="Target commit SHA")
    file_path: str = Field(description="Primary affected file path")
    line_start: Optional[int] = Field(default=None, description="Starting line")
    line_end: Optional[int] = Field(default=None, description="Ending line")
    evidence: str = Field(description="Primary evidence snippet or factual justification")
    evidence_items: List[Evidence] = Field(default_factory=list, description="Structured evidence items")
    source: Literal["deterministic", "agentic", "deterministic+agent", "rag_correlated"] = "agentic"
    agent: str = Field(description="Specialized agent name that detected the issue")
    status: Literal[
        "NEW",
        "VALIDATED",
        "NEEDS_REVIEW",
        "DUPLICATE",
        "REJECTED",
        "INSUFFICIENT_EVIDENCE",
        "DISMISSED"
    ] = "NEW"
    tool_name: Optional[str] = Field(default=None, description="Deterministic tool name if applicable")
    rule_id: Optional[str] = Field(default=None, description="Linter or scanner rule ID if applicable")
    retrieval_context: Optional[str] = Field(default=None, description="RAG retrieved context if used")
    related_files: List[str] = Field(default_factory=list, description="Related correlated files")
    critic_notes: Optional[str] = Field(default=None, description="Review remarks from Critic Agent")
    dedup_group_id: Optional[str] = Field(default=None, description="Group ID linking duplicate findings")
    merged_finding_ids: List[str] = Field(default_factory=list, description="IDs of duplicate findings merged into this one")
    merged_agents: List[str] = Field(default_factory=list, description="All agents that discovered this issue")
    validation_reason: Optional[str] = Field(default=None, description="Audit justification for validation status")
    score_contribution: float = Field(default=0.0, description="Points contributed by this finding to overall risk score")
    impact_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(default="HIGH", description="Operational blast radius")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ------------------------------------------------------------------------------
# Critic Decision Schema (Step 19)
# ------------------------------------------------------------------------------
class CriticResult(BaseModel):
    finding_id: str
    decision: Literal["VALIDATED", "NEEDS_REVIEW", "DUPLICATE", "REJECTED", "INSUFFICIENT_EVIDENCE"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    reason: str
    duplicate_of_id: Optional[str] = None
    severity_adjustment: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = None

# ------------------------------------------------------------------------------
# Analysis Context Schema (Step 4)
# ------------------------------------------------------------------------------
class AnalysisContext(BaseModel):
    repository_id: str
    repository_name: str
    source_type: str = "local"
    root_path: str
    branch: Optional[str] = "main"
    commit_sha: Optional[str] = None
    changed_files: List[str] = Field(default_factory=list)
    git_diff: Optional[str] = None
    all_files: List[str] = Field(default_factory=list)
    files_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    indexed_in_rag: bool = False
    rag_chunks_count: int = 0
    analysis_options: Dict[str, Any] = Field(default_factory=dict)

# ------------------------------------------------------------------------------
# Analysis Plan Schema (Step 6)
# ------------------------------------------------------------------------------
class AnalysisPlan(BaseModel):
    repository_id: str
    planned_tasks: List[str] = Field(
        description="Tasks planned based on repository structure: code, dependency, config, test, rag, security"
    )
    rationale: Dict[str, str] = Field(default_factory=dict)

# ------------------------------------------------------------------------------
# Agent Execution State (Step 23 & 24)
# ------------------------------------------------------------------------------
class AgentExecutionState(BaseModel):
    agent_name: str
    status: Literal["WAITING", "PLANNING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED"] = "WAITING"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    findings_count: int = 0
    tools_called: List[str] = Field(default_factory=list)
    error: Optional[str] = None

# ------------------------------------------------------------------------------
# Analysis Run Schema (Step 22 & 23)
# ------------------------------------------------------------------------------
class AnalysisRun(BaseModel):
    run_id: str
    repository_id: str
    repository_name: str
    branch: Optional[str] = "main"
    commit_sha: Optional[str] = None
    status: Literal[
        "QUEUED",
        "PREPARING",
        "PLANNING",
        "RUNNING_AGENTS",
        "AGGREGATING",
        "CRITIC_REVIEW",
        "FINALIZING",
        "COMPLETED",
        "PARTIAL",
        "FAILED"
    ] = "QUEUED"
    agent_states: Dict[str, AgentExecutionState] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    total_findings_count: int = 0
    validated_findings_count: int = 0
    needs_review_count: int = 0
    rejected_count: int = 0
    risk_score: float = Field(default=0.0, description="Normalized deterministic risk score (0-100)")
    risk_level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"] = Field(default="LOW", description="Risk level tier")
    score_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Score explanation by severity")
    error: Optional[str] = None

# ------------------------------------------------------------------------------
# Final Analysis Report Schema (Step 21 & Phase 4)
# ------------------------------------------------------------------------------
class AnalysisReport(BaseModel):
    run_id: str
    repository_id: str
    repository_name: str
    commit_sha: Optional[str] = None
    branch: Optional[str] = "main"
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0
    status: Literal["COMPLETED", "PARTIAL", "FAILED"] = "COMPLETED"
    agents_executed: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    risk_score: float = Field(default=0.0, description="Deterministic risk score (0-100)")
    risk_level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"] = Field(default="LOW", description="Risk tier")
    score_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Itemized score contributors")
    dedup_summary: Dict[str, Any] = Field(default_factory=dict, description="Deduplication statistics")
    findings: List[Finding] = Field(default_factory=list)
    validated_findings: List[Finding] = Field(default_factory=list)
    needs_review_findings: List[Finding] = Field(default_factory=list)
    rejected_findings: List[Finding] = Field(default_factory=list)
    finding_counts_by_severity: Dict[str, int] = Field(
        default_factory=lambda: {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    )
    summary: str = Field(description="Executive deployment-readiness intelligence summary")
    recommendations: List[str] = Field(default_factory=list)

# ------------------------------------------------------------------------------
# Phase 4 Deterministic Risk Engine Models (Parts 6 - 10)
# ------------------------------------------------------------------------------
class ScoreContributor(BaseModel):
    finding_id: str
    title: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    impact_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    points: float
    file_path: str
    line_start: Optional[int] = None

class RiskEvaluation(BaseModel):
    risk_score: float = Field(ge=0.0, le=100.0, description="Normalized score bounded between 0 and 100")
    risk_level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]
    raw_score: float
    contributors: List[ScoreContributor] = Field(default_factory=list)
    excluded_findings: List[Dict[str, str]] = Field(default_factory=list)
    severity_breakdown: Dict[str, float] = Field(default_factory=dict)
    formula_explanation: str = Field(
        default="Score = min(100, round(sum(severity_weight * confidence_factor * impact_factor)))"
    )

# ------------------------------------------------------------------------------
# Phase 4 Dashboard Summary Model (Part 11 & 14)
# ------------------------------------------------------------------------------
class DashboardSummary(BaseModel):
    total_runs: int = 0
    latest_run_id: Optional[str] = None
    latest_repository_id: Optional[str] = None
    latest_risk_score: float = 0.0
    latest_risk_level: str = "LOW"
    total_findings_detected: int = 0
    validated_findings_count: int = 0
    severity_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    )
    status_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "VALIDATED": 0,
            "NEEDS_REVIEW": 0,
            "DUPLICATE": 0,
            "REJECTED": 0,
            "DISMISSED": 0
        }
    )
    recent_runs: List[Dict[str, Any]] = Field(default_factory=list)
    top_findings: List[Finding] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# Phase 6 Run Comparison Models (Steps 13 & 14)
# ------------------------------------------------------------------------------
class ComparisonFindingItem(BaseModel):
    fingerprint: str
    finding_id: str
    title: str
    file_path: str
    line_start: Optional[int] = None
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    category: str
    status: str
    score_contribution: float = 0.0


class RunComparisonResult(BaseModel):
    has_baseline: bool
    base_run_id: Optional[str] = None
    target_run_id: str
    repository_id: str
    repository_name: str
    base_score: Optional[float] = None
    target_score: float
    score_delta: Optional[float] = None
    risk_trend: Literal["IMPROVED", "DEGRADED", "UNCHANGED", "INITIAL_BASELINE"]
    base_findings_count: int = 0
    target_findings_count: int = 0
    resolved_count: int = 0
    new_count: int = 0
    persistent_count: int = 0
    changed_count: int = 0
    resolved_findings: List[ComparisonFindingItem] = Field(default_factory=list)
    new_findings: List[ComparisonFindingItem] = Field(default_factory=list)
    persistent_findings: List[ComparisonFindingItem] = Field(default_factory=list)
    changed_findings: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None

