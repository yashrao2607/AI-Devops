import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.rag_tools import RAGTools
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class DocumentationRAGAgent(BaseSpecializedAgent):
    """
    Documentation / RAG Agent (Step 13 of Phase 3 / Phase 4 Intelligence Layer).
    Queries the Chroma vector store to extract repository documentation policies,
    prerequisites, and mandatory environment variables, correlating them with actual
    CI/CD workflows, Docker configs, and deployment manifests.
    """

    COMMON_NOISE_TOKENS = {
        "HTTP", "HTTPS", "PORT", "TRUE", "FALSE", "NONE", "FROM", "COPY",
        "WORKDIR", "RUN", "CMD", "ENTRYPOINT", "ENV", "EXPOSE", "ADD", "USER",
        "JSON", "HTML", "POST", "GET", "PUT", "DELETE", "HEAD", "OPTIONS"
    }

    def __init__(self):
        super().__init__(
            agent_name="RAGAgent",
            prompt_file="rag_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # 1. Semantic RAG queries across indexed documentation and configs
        rag_queries = [
            "What required environment variables and services are documented for deployment?",
            "What database, queue, or external service dependencies are documented?",
        ]

        documented_vars = []
        seen_keys = set()

        for q in rag_queries:
            rag_res = RAGTools.search_repository_context(
                repository_id=context.repository_id,
                query=q,
                top_k=5
            )
            if not rag_res.evidence_available or not rag_res.items:
                continue

            # Extract variable names from RAG hits
            for item in rag_res.items:
                found_vars = re.findall(r"\b([A-Z][A-Z0-9_]{3,})\b", item.content)
                for v in found_vars:
                    if v not in self.COMMON_NOISE_TOKENS and not v.startswith("GITHUB_"):
                        if (v, item.file_path) not in seen_keys:
                            seen_keys.add((v, item.file_path))
                            documented_vars.append((v, item))

        if not documented_vars:
            logger.info("RAGAgent: No mandatory environment variables extracted from documentation for '%s'.", context.repository_id)
            return findings

        # 2. Check deployment manifests (compose, github workflows, vercel.json)
        deploy_manifests = [
            f for f in context.all_files
            if any(term in f.lower() for term in ["compose", "workflow", "vercel.json", "netlify.toml", "fly.toml"])
        ]

        for dep_file in deploy_manifests:
            dep_res = RepositoryTools.get_file_content(context, dep_file)
            if not dep_res.exists or not dep_res.content:
                continue

            content_text = dep_res.content
            for var_name, evidence_item in documented_vars:
                # Check critical infrastructure variables
                is_critical_var = any(term in var_name for term in ["DATABASE", "POSTGRES", "REDIS", "SECRET", "TOKEN", "MONGO", "API_KEY", "PASSWORD", "AUTH"])
                if is_critical_var and var_name not in content_text:
                    findings.append(Finding(
                        id=f"F-RAG-{len(findings)+1:03d}",
                        category="DOCUMENTATION",
                        severity="HIGH",
                        confidence="HIGH",
                        title=f"Documentation/Config Mismatch: Documented '{var_name}' missing from {dep_file}",
                        summary=(
                            f"Repository documentation in '{evidence_item.file_path}' specifies that '{var_name}' is "
                            f"required for operation, but deployment configuration '{dep_file}' does not configure or pass this variable."
                        ),
                        impact="Application containers or serverless functions will encounter missing configuration exceptions upon production initialization.",
                        recommendation=f"Define '{var_name}' under the environment or secrets block in '{dep_file}' as specified in '{evidence_item.file_path}'.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=dep_file,
                        line_start=1,
                        line_end=min(dep_res.total_lines, 25),
                        evidence=(
                            f"Documented in {evidence_item.file_path} (L{evidence_item.line_start}-{evidence_item.line_end}):\n"
                            f"\"{evidence_item.content[:200].strip()}\"\n\n"
                            f"Missing from '{dep_file}' deployment configuration."
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
                                file_path=dep_file,
                                line_start=1,
                                line_end=dep_res.total_lines,
                                snippet=content_text[:200],
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
