import os
import time
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from backend.app.models.analysis_schemas import (
    AnalysisContext,
    AnalysisRun,
    AnalysisReport,
    AnalysisPlan,
    AgentExecutionState,
    Finding,
    CriticResult
)
from backend.app.services.rag.loader import RepositorySnapshot, RepositoryLoader
from backend.app.services.rag.discovery import FileDiscoveryService
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.agents.specialized.code_agent import CodeAnalysisAgent
from backend.app.agents.specialized.dependency_agent import DependencyAnalysisAgent
from backend.app.agents.specialized.config_agent import ConfigurationAnalysisAgent
from backend.app.agents.specialized.test_agent import TestAnalysisAgent
from backend.app.agents.specialized.rag_agent import DocumentationRAGAgent
from backend.app.agents.specialized.security_agent import SecurityAnalysisAgent
from backend.app.agents.specialized.critic_agent import CriticAgent
from backend.app.agents.specialized.report_agent import ReportGenerationAgent
from backend.app.core.logging import logger

# Global in-memory registry of active and completed analysis runs for live telemetry
_ACTIVE_ANALYSIS_RUNS: Dict[str, AnalysisRun] = {}
_ACTIVE_REPORTS: Dict[str, AnalysisReport] = {}

class DeploySafeAnalysisFlow:
    """
    CrewAI-compatible Multi-Agent Analysis Flow (Step 5 of Phase 3).
    Coordinates specialized agents, enforces planning, executes parallel analysis,
    triggers Critic review, and compiles the final structured report.
    """

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"

    @classmethod
    def get_run(cls, run_id: str) -> Optional[AnalysisRun]:
        return _ACTIVE_ANALYSIS_RUNS.get(run_id)

    @classmethod
    def get_report(cls, run_id: str) -> Optional[AnalysisReport]:
        return _ACTIVE_REPORTS.get(run_id)

    def execute_flow(
        self,
        snapshot: RepositorySnapshot,
        options: Optional[dict] = None
    ) -> AnalysisReport:
        """
        Executes the complete multi-agent analysis flow on the given repository snapshot.
        Tracks real-time telemetry across all agent states.
        """
        start_time = time.time()
        logger.info("Starting DeploySafeAnalysisFlow (Run ID: %s) on repository '%s'",
                    self.run_id, snapshot.repository_name)

        # Initialize AnalysisRun
        run = AnalysisRun(
            run_id=self.run_id,
            repository_id=snapshot.repository_id,
            repository_name=snapshot.repository_name,
            branch=snapshot.branch or "main",
            commit_sha=snapshot.commit_sha,
            status="PREPARING",
            started_at=datetime.utcnow()
        )
        _ACTIVE_ANALYSIS_RUNS[self.run_id] = run

        try:
            # ------------------------------------------------------------------
            # Phase A: Prepare Context (Step 4)
            # ------------------------------------------------------------------
            run.status = "PREPARING"
            discovered_files = FileDiscoveryService.discover_files(snapshot.root_path)

            all_file_paths = [f.relative_path for f in discovered_files if f.is_indexable]
            files_by_category: Dict[str, List[str]] = {}
            for f in discovered_files:
                if f.is_indexable:
                    files_by_category.setdefault(f.category, []).append(f.relative_path)

            # Check RAG index status
            vector_store = ChromaVectorStore()
            rag_count = vector_store.count(snapshot.repository_id)

            context = AnalysisContext(
                repository_id=snapshot.repository_id,
                repository_name=snapshot.repository_name,
                source_type=snapshot.source_type,
                root_path=snapshot.root_path,
                branch=snapshot.branch,
                commit_sha=snapshot.commit_sha,
                all_files=all_file_paths,
                files_by_category=files_by_category,
                indexed_in_rag=(rag_count > 0),
                rag_chunks_count=rag_count,
                analysis_options=options or {}
            )

            # Get Git Diff
            git_diff_res = RepositoryTools.get_git_diff(context)
            context.changed_files = git_diff_res.changed_files
            context.git_diff = git_diff_res.diff_text

            # ------------------------------------------------------------------
            # Phase B: Plan Analysis (Step 6)
            # ------------------------------------------------------------------
            run.status = "PLANNING"
            plan = self._create_analysis_plan(context)
            logger.info("Orchestrator planned %d tasks: %s", len(plan.planned_tasks), plan.planned_tasks)

            # Initialize states for planned agents
            for task in plan.planned_tasks:
                run.agent_states[task] = AgentExecutionState(agent_name=task, status="WAITING")
            run.agent_states["critic"] = AgentExecutionState(agent_name="critic", status="WAITING")
            run.agent_states["report"] = AgentExecutionState(agent_name="report", status="WAITING")

            # ------------------------------------------------------------------
            # Phase C: Run Specialized Agents in Parallel (Step 43)
            # ------------------------------------------------------------------
            run.status = "RUNNING_AGENTS"
            candidate_findings: List[Finding] = []
            tools_used: List[str] = ["repo_tools", "safe_executor"]

            agents_map = {
                "code_analysis": (CodeAnalysisAgent(), ["get_file_content", "code_check"]),
                "dependency_analysis": (DependencyAnalysisAgent(), ["get_dependency_manifests"]),
                "configuration_analysis": (ConfigurationAnalysisAgent(), ["get_file_content", "docker_check"]),
                "test_analysis": (TestAnalysisAgent(), ["run_tests_safe", "get_test_files"]),
                "rag_analysis": (DocumentationRAGAgent(), ["search_repository_context"]),
                "security_analysis": (SecurityAnalysisAgent(), ["run_security_scan"])
            }

            def _run_single_agent(task_name: str):
                agent_obj, agent_tools = agents_map[task_name]
                state = run.agent_states[task_name]
                state.status = "RUNNING"
                state.started_at = datetime.utcnow()
                state.tools_called = agent_tools
                a_start = time.time()

                try:
                    f_list = agent_obj.analyze(context)
                    state.status = "COMPLETED"
                    state.findings_count = len(f_list)
                    state.duration_seconds = round(time.time() - a_start, 2)
                    state.completed_at = datetime.utcnow()
                    return f_list, agent_tools
                except Exception as ex:
                    logger.error("Agent '%s' failed during analysis: %s", task_name, str(ex))
                    state.status = "FAILED"
                    state.error = str(ex)
                    state.duration_seconds = round(time.time() - a_start, 2)
                    state.completed_at = datetime.utcnow()
                    return [], agent_tools

            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_task = {
                    executor.submit(_run_single_agent, t): t
                    for t in plan.planned_tasks
                    if t in agents_map
                }
                for future in as_completed(future_to_task):
                    f_res, t_res = future.result()
                    candidate_findings.extend(f_res)
                    for t in t_res:
                        if t not in tools_used:
                            tools_used.append(t)

            # ------------------------------------------------------------------
            # Phase D: Finding Aggregation & Correlation (Step 18)
            # ------------------------------------------------------------------
            run.status = "AGGREGATING"
            run.total_findings_count = len(candidate_findings)

            # ------------------------------------------------------------------
            # Phase E: Critic Review & Validation (Step 19)
            # ------------------------------------------------------------------
            run.status = "CRITIC_REVIEW"
            critic_state = run.agent_states["critic"]
            critic_state.status = "RUNNING"
            critic_state.started_at = datetime.utcnow()
            c_start = time.time()

            critic_agent = CriticAgent()
            reviewed_findings, decisions = critic_agent.review_findings(context, candidate_findings)

            critic_state.status = "COMPLETED"
            critic_state.duration_seconds = round(time.time() - c_start, 2)
            critic_state.completed_at = datetime.utcnow()

            # Record stats
            validated_count = sum(1 for d in decisions if d.decision == "VALIDATED")
            needs_review_count = sum(1 for d in decisions if d.decision == "NEEDS_REVIEW")
            rejected_count = sum(1 for d in decisions if d.decision in ("REJECTED", "INSUFFICIENT_EVIDENCE", "DUPLICATE"))

            run.validated_findings_count = validated_count
            run.needs_review_count = needs_review_count
            run.rejected_count = rejected_count

            # ------------------------------------------------------------------
            # Phase F: Generate Structured Report (Step 21)
            # ------------------------------------------------------------------
            run.status = "FINALIZING"
            report_state = run.agent_states["report"]
            report_state.status = "RUNNING"
            report_state.started_at = datetime.utcnow()
            r_start = time.time()

            total_duration = round(time.time() - start_time, 2)
            executed_names = [t for t in plan.planned_tasks if run.agent_states[t].status == "COMPLETED"]
            executed_names.extend(["critic", "report"])

            report = ReportGenerationAgent.generate_report(
                context=context,
                run_id=self.run_id,
                findings=reviewed_findings,
                agents_executed=executed_names,
                tools_used=tools_used,
                duration_seconds=total_duration
            )

            report_state.status = "COMPLETED"
            report_state.duration_seconds = round(time.time() - r_start, 2)
            report_state.completed_at = datetime.utcnow()

            # Finalize run
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.duration_seconds = total_duration

            _ACTIVE_REPORTS[self.run_id] = report
            logger.info("DeploySafeAnalysisFlow completed successfully for run '%s' in %.2fs",
                        self.run_id, total_duration)
            return report

        except Exception as e:
            logger.error("DeploySafeAnalysisFlow run '%s' failed: %s", self.run_id, str(e), exc_info=True)
            run.status = "FAILED"
            run.error = str(e)
            run.completed_at = datetime.utcnow()
            run.duration_seconds = round(time.time() - start_time, 2)
            raise

    def _create_analysis_plan(self, context: AnalysisContext) -> AnalysisPlan:
        """Dynamic, context-aware planning implementing Step 6."""
        tasks = []
        rationale = {}

        # 1. Code analysis
        if context.files_by_category.get("SOURCE_CODE"):
            tasks.append("code_analysis")
            rationale["code_analysis"] = f"{len(context.files_by_category['SOURCE_CODE'])} source file(s) detected."

        # 2. Dependency analysis
        manifest_files = [
            f for f in context.all_files
            if os.path.basename(f) in {"requirements.txt", "package.json", "pyproject.toml", "go.mod", "pom.xml"}
        ]
        if manifest_files:
            tasks.append("dependency_analysis")
            rationale["dependency_analysis"] = f"Manifests detected: {', '.join(manifest_files)}."

        # 3. Configuration analysis
        if context.files_by_category.get("CONFIG") or context.files_by_category.get("DOCKER") or context.files_by_category.get("CI_CD"):
            tasks.append("configuration_analysis")
            rationale["configuration_analysis"] = "Configuration, Dockerfile, or CI/CD manifests detected."

        # 4. Test analysis
        tasks.append("test_analysis")
        t_count = len(context.files_by_category.get("TEST", []))
        rationale["test_analysis"] = f"{t_count} test file(s) detected; evaluating regression test coverage."

        # 5. RAG analysis
        if context.indexed_in_rag or any("readme" in f.lower() for f in context.all_files):
            tasks.append("rag_analysis")
            rationale["rag_analysis"] = "Repository contains documentation/indexed vector knowledge for policy verification."

        # 6. Security analysis
        tasks.append("security_analysis")
        rationale["security_analysis"] = "Security inspection planned for secret exposure and dangerous configurations."

        return AnalysisPlan(
            repository_id=context.repository_id,
            planned_tasks=tasks,
            rationale=rationale
        )
