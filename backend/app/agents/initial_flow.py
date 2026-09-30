import os
import time
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from backend.app.models.schemas import Finding, ReadinessAssessmentResult
from backend.app.services.llm.factory import LLMFactory
from backend.app.core.logging import logger

class RepositoryReadinessFlow:
    """
    CrewAI-compatible flow that executes the initial Phase-1 deployment readiness check.
    Evaluates repository structure, configuration files, and dependencies to produce
    a typed Pydantic ReadinessAssessmentResult.
    """

    def __init__(self, repository_path: Optional[str] = None):
        self.repository_path = repository_path or os.getcwd()
        self.flow_name = "Phase1ReadinessFlow"

    def execute(self, target_branch: str = "main") -> ReadinessAssessmentResult:
        """
        Executes the initial readiness inspection workflow.
        Returns a structured ReadinessAssessmentResult.
        """
        start_time = time.time()
        logger.info("Executing %s on repository path: %s", self.flow_name, self.repository_path)

        # 1. Inspect repository foundation deterministically
        findings: List[Finding] = []
        repo_files = []
        try:
            for root, _, files in os.walk(self.repository_path):
                # Skip ignore directories
                if any(ignored in root for ignored in [".git", "node_modules", ".venv", "__pycache__"]):
                    continue
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), self.repository_path)
                    repo_files.append(rel_path)
        except Exception as e:
            logger.warning("Could not list local files: %s", str(e))

        # Check for essential deployment artifacts
        has_readme = any("readme" in f.lower() for f in repo_files)
        has_docker = any("docker" in f.lower() for f in repo_files)
        has_env_example = any(".env.example" in f for f in repo_files)

        trace = [
            {"step": "file_discovery", "status": "completed", "files_found": len(repo_files)},
            {"step": "initial_inspection", "status": "completed", "has_readme": has_readme, "has_docker": has_docker}
        ]

        if not has_docker:
            findings.append(Finding(
                id="F-101",
                category="CONFIGURATION",
                severity="LOW",
                confidence=0.95,
                title="Container configuration missing",
                summary="No Dockerfile or docker-compose file detected in repository root.",
                file_path="Dockerfile",
                evidence="Inspected repository root files; Dockerfile not located.",
                impact="Automated container builds may fail or require manual configuration.",
                recommendation="Add a standard Dockerfile tailored to the application runtime.",
                source_type="deterministic",
                agent="RepositoryReadinessAgent",
                status="validated"
            ))

        # 2. Invoke LLM provider via factory for reasoning summary
        prompt = (
            f"Repository: {os.path.basename(self.repository_path)}\n"
            f"Files analyzed: {len(repo_files)}\n"
            f"Findings detected: {len(findings)}\n"
            f"Summarize deployment readiness in 2 concise sentences."
        )

        try:
            summary_text, provider_used = LLMFactory.generate_with_fallback(
                prompt=prompt,
                system_prompt="You are the DeploySafe Orchestrator Agent. Give concise technical summaries."
            )
            trace.append({"step": "llm_readiness_summary", "provider": provider_used, "status": "completed"})
        except Exception as e:
            summary_text = "Repository structure inspected. Baseline deployment readiness established."
            trace.append({"step": "llm_readiness_summary", "error": str(e), "status": "degraded"})

        duration = round(time.time() - start_time, 2)
        trace.append({"step": "completed", "duration_seconds": duration})

        # Calculate preliminary risk score based on findings
        severity_weights = {"CRITICAL": 35, "HIGH": 25, "MEDIUM": 15, "LOW": 7}
        raw_score = sum(severity_weights.get(f.severity, 0) for f in findings)
        risk_score = min(raw_score, 100)

        risk_level = "LOW"
        if risk_score >= 75:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MODERATE"

        return ReadinessAssessmentResult(
            repository_name=os.path.basename(self.repository_path) or "DeploySafe",
            target_branch=target_branch,
            analyzed_at=datetime.utcnow(),
            overall_risk_level=risk_level,
            risk_score=risk_score,
            findings=findings,
            agent_trace=trace,
            summary=summary_text
        )
