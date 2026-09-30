from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# Severity and Confidence Literals
SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW"]
FindingStatus = Literal["NEW", "VALIDATED", "NEEDS_REVIEW", "DUPLICATE", "REJECTED", "INSUFFICIENT_EVIDENCE"]
FindingCategory = Literal["CODE", "DEPENDENCY", "CONFIGURATION", "SECURITY", "TEST", "DOCUMENTATION"]

class Evidence(BaseModel):
    """Concrete, verifiable repository snippet or tool observation."""
    evidence_type: Literal[
        "SOURCE_CODE",
        "CONFIGURATION",
        "DOCUMENTATION",
        "GIT_DIFF",
        "SCANNER",
        "TEST_RESULT",
        "DEPENDENCY_MANIFEST"
    ]
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: str
    source: str = "repository"
    source_tool: Optional[str] = None
    repository_id: str
    commit_sha: Optional[str] = None

class Finding(BaseModel):
    """Canonical DeploySafe deployment readiness finding."""
    id: str = Field(description="Unique finding identifier, e.g., F-101")
    category: FindingCategory
    severity: SeverityLevel
    confidence: ConfidenceLevel
    title: str = Field(description="Short concise description of the finding")
    summary: str = Field(description="Detailed explanation of why this is a deployment risk")
    impact: str = Field(description="Potential runtime or operational impact")
    recommendation: str = Field(description="Concrete actionable remediation for the developer")
    repository_id: str
    commit_sha: Optional[str] = None
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    evidence: List[Evidence] = Field(default_factory=list)
    agent: str = Field(description="Reporting agent name")
    status: FindingStatus = "NEW"
    critic_reason: Optional[str] = None
    tool_name: Optional[str] = None
    rule_id: Optional[str] = None
    related_files: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CriticDecision(BaseModel):
    """Evaluation output produced by the Critic Agent for a single finding."""
    finding_id: str
    decision: FindingStatus
    confidence: ConfidenceLevel
    reason: str
    suggested_severity: Optional[SeverityLevel] = None

class AgentExecutionTrace(BaseModel):
    """Execution telemetry for a single agent in the analysis flow."""
    agent_name: str
    role: str
    status: Literal["WAITING", "PLANNING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED"]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    findings_count: int = 0
    tools_used: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

class AnalysisPlan(BaseModel):
    """Context-aware plan produced by the Orchestrator before dispatching agents."""
    tasks: List[str] = Field(default_factory=list)
    reasoning: str
    planned_agents: List[str] = Field(default_factory=list)
    estimated_duration_seconds: float = 5.0

class AnalysisContext(BaseModel):
    """Aggregated repository state and metadata passed to specialized agents."""
    repository_id: str
    repository_name: str
    root_path: str
    source_type: str = "local"
    branch: Optional[str] = "main"
    commit_sha: Optional[str] = None
    files: List[str] = Field(default_factory=list)
    changed_files: List[str] = Field(default_factory=list)
    is_indexed: bool = False
    categories_present: List[str] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)

class AnalysisReport(BaseModel):
    """Final deployment readiness report containing validated findings and summary."""
    run_id: str
    repository_id: str
    repository_name: str
    commit_sha: Optional[str] = None
    branch: Optional[str] = "main"
    summary: str
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    validated_count: int = 0
    needs_review_count: int = 0
    rejected_count: int = 0
    findings: List[Finding] = Field(default_factory=list)
    agents_executed: List[AgentExecutionTrace] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    status: Literal["QUEUED", "PREPARING", "PLANNING", "RUNNING_AGENTS", "AGGREGATING", "CRITIC_REVIEW", "FINALIZING", "COMPLETED", "PARTIAL", "FAILED"] = "QUEUED"
    error_message: Optional[str] = None
