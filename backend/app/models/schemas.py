from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Finding(BaseModel):
    id: str = Field(description="Unique finding identifier, e.g., F-101")
    category: Literal["CODE", "DEPENDENCY", "CONFIGURATION", "SECURITY", "TEST", "DOCUMENTATION"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    title: str = Field(description="Short concise description of the finding")
    summary: str = Field(description="Detailed explanation of the risk")
    repository: Optional[str] = Field(default=None)
    commit_sha: Optional[str] = Field(default=None)
    file_path: str = Field(description="Exact file path in repository")
    line_start: Optional[int] = Field(default=None)
    line_end: Optional[int] = Field(default=None)
    evidence: str = Field(description="Concrete snippet or rationale from repository")
    impact: str = Field(description="Potential runtime or deployment impact")
    recommendation: str = Field(description="Actionable fix for the developer")
    source_type: Literal["deterministic", "agentic", "deterministic+agent"] = "agentic"
    agent: str = Field(description="Name of the reporting agent")
    status: Literal["new", "validated", "needs_review", "false_positive", "dismissed"] = "validated"

class ReadinessAssessmentResult(BaseModel):
    repository_name: str
    target_branch: str = "main"
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    overall_risk_level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"] = "LOW"
    risk_score: int = Field(ge=0, le=100, default=0)
    findings: List[Finding] = Field(default_factory=list)
    agent_trace: List[dict] = Field(default_factory=list)
    summary: str = Field(description="Executive summary of the deployment readiness")

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    active_llm_provider: str
    gemini_configured: bool
    groq_configured: bool
    github_configured: bool = False
    database_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LLMDiagnosticRequest(BaseModel):
    prompt: str = Field(default="Analyze deployment safety for this release.")
    provider: Optional[Literal["gemini", "groq"]] = None

class LLMDiagnosticResponse(BaseModel):
    provider_used: str
    model_used: str
    success: bool
    content: str
    latency_ms: float
    error: Optional[str] = None
