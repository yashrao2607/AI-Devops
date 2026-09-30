import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.rag_tools import RAGTools
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class DocumentationRAGAgent(BaseSpecializedAgent):
    """
    Documentation / RAG Agent (Step 13 of Phase 3).
    Queries the Phase-2 Chroma vector store to extract repository documentation policies
    and correlates them with actual configuration manifests.
    """

    def __init__(self):
        super().__init__(
            agent_name="RAGAgent",
            prompt_file="rag_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # 1. Semantic query to find documented environment and deployment requirements
        rag_res = RAGTools.search_repository_context(
            repository_id=context.repository_id,
            query="What required environment variables and services are documented for deployment?",
            top_k=5
        )

        if not rag_res.evidence_available or not rag_res.items:
            logger.info("RAGAgent: No indexed documentation evidence available for repository '%s'.", context.repository_id)
            return findings

        # 2. Extract documented mandatory variables (e.g. REDIS_URL, DATABASE_URL, API_KEY)
        documented_vars = []
        seen_keys = set()
        for item in rag_res.items:
            found_vars = re.findall(r"\b([A-Z][A-Z0-9_]{3,})\b", item.content)
            for v in found_vars:
                if v not in {"HTTP", "PORT", "TRUE", "FALSE", "NONE", "FROM", "COPY", "WORKDIR"}:
                    if (v, item.file_path) not in seen_keys:
                        seen_keys.add((v, item.file_path))
                        documented_vars.append((v, item))

        # 3. Check if any documented variable is missing from compose/config manifests
        compose_files = [f for f in context.all_files if "docker-compose" in f.lower() or "compose.yml" in f.lower()]
        for compose_file in compose_files:
            compose_content = RepositoryTools.get_file_content(context, compose_file)
            if not compose_content.exists or not compose_content.content:
                continue

            for var_name, evidence_item in documented_vars:
                # If documented as mandatory (e.g. REDIS_URL or CACHE_URL) but absent in compose
                if var_name in {"REDIS_URL", "CACHE_URL", "JWT_SECRET", "API_SECRET"} and var_name not in compose_content.content:
                    findings.append(Finding(
                        id=f"F-RAG-{len(findings)+1:03d}",
                        category="DOCUMENTATION",
                        severity="HIGH",
                        confidence="HIGH",
                        title=f"Documentation/Config Mismatch: Documented '{var_name}' missing from compose",
                        summary=(
                            f"Repository documentation in {evidence_item.file_path} specifies that '{var_name}' is "
                            f"required for deployment, but {compose_file} does not configure or pass this variable."
                        ),
                        impact="Application container will encounter missing environment variable exceptions upon production startup.",
                        recommendation=f"Define '{var_name}' under the environment section in {compose_file} as documented in {evidence_item.file_path}.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=compose_file,
                        line_start=compose_content.line_start,
                        line_end=min(compose_content.total_lines, 25),
                        evidence=(
                            f"Documented in {evidence_item.file_path} (L{evidence_item.line_start}-{evidence_item.line_end}):\n"
                            f"\"{evidence_item.content[:200].strip()}\"\n\n"
                            f"Missing from {compose_file} environment block."
                        ),
                        evidence_items=[
                            Evidence(
                                evidence_type="RAG_RETRIEVAL",
                                file_path=evidence_item.file_path,
                                line_start=evidence_item.line_start,
                                line_end=evidence_item.line_end,
                                snippet=evidence_item.content[:200],
                                source="chroma_rag_retrieval",
                                repository_id=context.repository_id
                            ),
                            Evidence(
                                evidence_type="CONFIGURATION",
                                file_path=compose_file,
                                line_start=1,
                                line_end=compose_content.total_lines,
                                snippet=compose_content.content[:200],
                                source="file_read",
                                repository_id=context.repository_id
                            )
                        ],
                        source="rag_correlated",
                        agent="RAGAgent",
                        status="NEW"
                    ))

        logger.info("RAGAgent completed analysis: %d findings identified.", len(findings))
        return findings
