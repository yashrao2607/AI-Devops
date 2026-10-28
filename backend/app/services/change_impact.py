from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ComponentImpact(BaseModel):
    changed_file: str
    primary_component: str
    affected_components: List[str]
    risk_radius: str  # "HIGH", "MEDIUM", "LOW"
    rationale: str
    recommended_checks: List[str]


class ChangeImpactReport(BaseModel):
    """
    Deterministic Change Impact Analysis implementing Phase 7 Step 7.
    Grounds architectural blast radius directly in actual git diff files.
    """
    repository_id: str
    total_changed_files: int
    impacted_components: List[str]
    highest_risk_radius: str
    details: List[ComponentImpact]
    summary: str


class ChangeImpactService:
    """
    Analyzes changed files from a git diff and deterministically derives
    the architectural blast radius across system components.
    """

    @classmethod
    def analyze_impact(cls, repository_id: str, changed_files: List[str]) -> ChangeImpactReport:
        if not changed_files:
            return ChangeImpactReport(
                repository_id=repository_id,
                total_changed_files=0,
                impacted_components=[],
                highest_risk_radius="LOW",
                details=[],
                summary="No files changed in this analysis context."
            )

        details: List[ComponentImpact] = []
        impacted_set = set()
        has_high = False
        has_med = False

        for fpath in changed_files:
            low = fpath.lower().replace("\\", "/")
            fname = low.split("/")[-1]

            # 1. Configuration & Secrets
            if "env" in fname or "config" in fname or "settings" in fname:
                affected = ["CONTAINER_RUNTIME", "ENVIRONMENT_INITIALIZATION", "API_SERVICES"]
                details.append(ComponentImpact(
                    changed_file=fpath,
                    primary_component="CONFIGURATION",
                    affected_components=affected,
                    risk_radius="HIGH",
                    rationale="Configuration changes alter environment variables and downstream service initialization.",
                    recommended_checks=["configuration_analysis", "docker_check"]
                ))
                impacted_set.update(affected)
                impacted_set.add("CONFIGURATION")
                has_high = True

            # 2. Containerization & Orchestration
            elif "dockerfile" in fname or "docker-compose" in fname or low.endswith((".dockerfile", ".compose.yml", ".compose.yaml")):
                affected = ["DEPLOYMENT_CONTAINERS", "PORT_BINDINGS", "HOST_SECURITY"]
                details.append(ComponentImpact(
                    changed_file=fpath,
                    primary_component="CONTAINERIZATION",
                    affected_components=affected,
                    risk_radius="HIGH",
                    rationale="Container specs modify execution privileges, port exposure, and build artifacts.",
                    recommended_checks=["configuration_analysis", "security_analysis"]
                ))
                impacted_set.update(affected)
                impacted_set.add("CONTAINERIZATION")
                has_high = True

            # 3. Dependencies
            elif fname in ["requirements.txt", "package.json", "package-lock.json", "pipfile", "pyproject.toml", "go.mod"]:
                affected = ["SUPPLY_CHAIN", "RUNTIME_LIBRARIES", "SECURITY_SCAN"]
                details.append(ComponentImpact(
                    changed_file=fpath,
                    primary_component="DEPENDENCIES",
                    affected_components=affected,
                    risk_radius="HIGH",
                    rationale="Dependency manifest modifications risk introducing CVEs or breaking library versions.",
                    recommended_checks=["dependency_analysis"]
                ))
                impacted_set.update(affected)
                impacted_set.add("DEPENDENCIES")
                has_high = True

            # 4. Test Files
            elif "test" in low or "spec" in low:
                affected = ["REGRESSION_SAFETY", "CI_GATING"]
                details.append(ComponentImpact(
                    changed_file=fpath,
                    primary_component="TEST_SUITE",
                    affected_components=affected,
                    risk_radius="MEDIUM",
                    rationale="Modifying tests impacts regression verification and test coverage validity.",
                    recommended_checks=["test_analysis"]
                ))
                impacted_set.update(affected)
                impacted_set.add("TEST_SUITE")
                has_med = True

            # 5. Core Source Code
            elif low.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java")):
                affected = ["API_ENDPOINTS", "BUSINESS_LOGIC"]
                details.append(ComponentImpact(
                    changed_file=fpath,
                    primary_component="SOURCE_CODE",
                    affected_components=affected,
                    risk_radius="MEDIUM",
                    rationale="Source code modifications alter application logic and require error propagation analysis.",
                    recommended_checks=["code_analysis"]
                ))
                impacted_set.update(affected)
                impacted_set.add("SOURCE_CODE")
                has_med = True

            # 6. Documentation
            elif low.endswith((".md", ".txt", ".rst")) or "docs/" in low:
                affected = ["RAG_CONTEXT", "DEPLOYMENT_RUNBOOKS"]
                details.append(ComponentImpact(
                    changed_file=fpath,
                    primary_component="DOCUMENTATION",
                    affected_components=affected,
                    risk_radius="LOW",
                    rationale="Documentation updates influence developer runbooks and vector retrieval.",
                    recommended_checks=["rag_analysis"]
                ))
                impacted_set.update(affected)
                impacted_set.add("DOCUMENTATION")

        highest = "HIGH" if has_high else ("MEDIUM" if has_med else "LOW")

        summary = (
            f"Analyzed {len(changed_files)} changed file(s). "
            f"Detected blast radius spanning {len(impacted_set)} architectural component(s) "
            f"with highest risk tier '{highest}'."
        )

        return ChangeImpactReport(
            repository_id=repository_id,
            total_changed_files=len(changed_files),
            impacted_components=sorted(list(impacted_set)),
            highest_risk_radius=highest,
            details=details,
            summary=summary
        )
