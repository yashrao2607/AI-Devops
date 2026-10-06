import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from backend.app.models.analysis_schemas import Finding, AnalysisReport, AnalysisContext
from backend.app.services.llm.factory import LLMFactory
from backend.app.core.logging import logger

class ReportGenerationAgent:
    """
    Executive Report Generation Agent (Step 21 of Phase 3 / Phase 4 Intelligence Layer).
    Synthesizes multi-agent telemetry, AST evidence, and deterministic risk scores
    into a comprehensive, professional executive deployment readiness brief using the active LLM.
    """

    @classmethod
    def generate_report(
        cls,
        context: AnalysisContext,
        run_id: str,
        findings: List[Finding],
        agents_executed: List[str],
        tools_used: List[str],
        duration_seconds: float
    ) -> AnalysisReport:
        validated = [f for f in findings if f.status == "VALIDATED"]
        needs_review = [f for f in findings if f.status == "NEEDS_REVIEW"]
        rejected = [f for f in findings if f.status in ("REJECTED", "INSUFFICIENT_EVIDENCE")]

        # Accurate counts by severity
        counts: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in validated + needs_review:
            if f.severity in counts:
                counts[f.severity] += 1

        crit_count = counts["CRITICAL"]
        high_count = counts["HIGH"]
        med_count = counts["MEDIUM"]
        low_count = counts["LOW"]

        # Detect primary tech stack from files
        tech_indicators = []
        for fp in context.all_files:
            fl = fp.lower()
            if fl.endswith(".py"):
                tech_indicators.append("Python")
            elif fl.endswith((".js", ".jsx", ".mjs")):
                tech_indicators.append("JavaScript/Node.js")
            elif fl.endswith((".ts", ".tsx")):
                tech_indicators.append("TypeScript")
            elif "dockerfile" in fl or "compose" in fl:
                tech_indicators.append("Docker")
            elif ".github/workflows" in fl:
                tech_indicators.append("GitHub Actions CI/CD")
            elif "vercel.json" in fl:
                tech_indicators.append("Vercel")
            elif "kubernetes" in fl or fl.endswith((".k8s.yaml", ".k8s.yml")):
                tech_indicators.append("Kubernetes")
        
        from collections import Counter
        top_tech = [item for item, _ in Counter(tech_indicators).most_common(5)]
        tech_str = ", ".join(top_tech) if top_tech else "Polyglot / Generic Software"

        # Build detailed findings summary for LLM synthesis
        findings_summary_lines = []
        for idx, f in enumerate(validated[:10], start=1):
            findings_summary_lines.append(
                f"{idx}. [{f.severity}] ({f.category}) {f.title} in {f.file_path or 'root'} "
                f"(L{f.line_start or 1}): {f.summary or f.evidence[:120]}"
            )
        findings_block = "\n".join(findings_summary_lines) if findings_summary_lines else "No validated deployment-blocking issues discovered."

        # Prompt Groq LLM for Executive Assessment
        system_instruction = (
            "You are the DeploySafe Principal Deployment Risk Architect. "
            "Your mission is to synthesize multi-agent findings into an articulate, executive, and technically credible "
            "deployment-readiness report. Avoid hollow fluff. Output strictly valid JSON matching the schema."
        )

        user_prompt = f"""
Repository: {context.repository_name}
Target Branch: {context.branch or 'main'}
Total Analyzed Files: {len(context.all_files)}
Detected Technology Stack: {tech_str}
Executed Autonomous Agents: {', '.join(agents_executed)}
Findings Breakdown:
- CRITICAL: {crit_count}
- HIGH: {high_count}
- MEDIUM: {med_count}
- LOW: {low_count}

Top Validated Findings:
{findings_block}

Produce an executive deployment intelligence brief.
Output strictly JSON matching this structure:
{{
  "summary": "2-3 comprehensive, well-structured executive paragraphs. Paragraph 1: Overview of the repository's architecture, detected tech stack, and deployment targets. Paragraph 2: Core deployment blockers and critical operational vulnerabilities identified by the analysis agents. Paragraph 3: Expected production failure modes and blast radius if deployed in the current state.",
  "recommendations": [
    "Prioritized, specific, actionable technical recommendation 1 referencing affected files and technologies.",
    "Prioritized, specific, actionable technical recommendation 2 referencing affected files and technologies.",
    "Prioritized, specific, actionable technical recommendation 3 referencing affected files and technologies."
  ]
}}
"""

        summary_text: Optional[str] = None
        recommendations_list: List[str] = []

        try:
            raw_out, provider = LLMFactory.generate_with_fallback(
                prompt=user_prompt,
                system_prompt=system_instruction
            )
            # Parse JSON from response
            cleaned_text = raw_out.strip()
            cleaned_text = re.sub(r'<think>.*?</think>', '', cleaned_text, flags=re.DOTALL).strip()
            s_idx = cleaned_text.find("{")
            e_idx = cleaned_text.rfind("}")
            if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                json_candidate = cleaned_text[s_idx:e_idx+1]
                parsed = json.loads(json_candidate)
            else:
                parsed = json.loads(cleaned_text)

            if isinstance(parsed, dict):
                summary_text = parsed.get("summary")
                rec_candidates = parsed.get("recommendations", [])
                if isinstance(rec_candidates, list) and rec_candidates:
                    recommendations_list = [str(r).strip() for r in rec_candidates if r]
                logger.info("ReportAgent successfully synthesized executive intelligence via %s", provider)
        except Exception as ex:
            logger.warning("ReportAgent LLM executive synthesis fallback: %s", str(ex))

        # Contextual Fallback if LLM output unavailable
        if not summary_text:
            if crit_count > 0:
                summary_text = (
                    f"DEPLOYMENT BLOCKED: Identified {crit_count} CRITICAL and {high_count} HIGH risk deployment findings "
                    f"across {len(context.all_files)} analyzed files in {context.repository_name} ({tech_str}). "
                    f"Critical vulnerabilities include hardcoded credentials or unpinned container dependencies that will "
                    f"cause immediate failure in production staging. Remediations must be verified before production promotion."
                )
            elif high_count > 0:
                summary_text = (
                    f"HIGH RISK DETECTED: Discovered {high_count} high-severity operational or configuration risks in "
                    f"{context.repository_name} ({tech_str}). While no outright runtime crashes were detected, unpinned dependencies "
                    f"or exposed tokens introduce substantial failure modes during container build or deployment steps."
                )
            elif len(validated) > 0:
                summary_text = (
                    f"MODERATE / LOW RISK: Discovered {len(validated)} validated minor findings across {len(context.all_files)} files. "
                    f"The {tech_str} architecture demonstrates baseline operational health with non-blocking maintenance recommendations."
                )
            else:
                summary_text = (
                    f"CLEAN DEPLOYMENT READINESS: All specialized analysis agents (Code, Dependencies, Config, Test, RAG, and Security) "
                    f"verified that {context.repository_name} ({tech_str}) conforms to secure deployment baselines with zero blocking issues."
                )

        if not recommendations_list:
            for f in validated[:5]:
                if f.recommendation:
                    recommendations_list.append(f"{f.title}: {f.recommendation}")
            if not recommendations_list:
                recommendations_list = [
                    "Maintain continuous automated security scans across all pull requests.",
                    "Verify lockfile synchronization before triggering CI/CD release pipelines.",
                    "Ensure all production environment variables are stored in an encrypted secrets vault."
                ]

        report = AnalysisReport(
            run_id=run_id,
            repository_id=context.repository_id,
            repository_name=context.repository_name,
            commit_sha=context.commit_sha,
            branch=context.branch,
            analyzed_at=datetime.utcnow(),
            duration_seconds=duration_seconds,
            status="COMPLETED",
            agents_executed=agents_executed,
            tools_used=tools_used,
            findings=findings,
            validated_findings=validated,
            needs_review_findings=needs_review,
            rejected_findings=rejected,
            finding_counts_by_severity=counts,
            summary=summary_text,
            recommendations=recommendations_list[:6]
        )

        logger.info(
            "ReportAgent finalized report for run '%s': %d validated findings (Crit: %d, High: %d)",
            run_id, len(validated), crit_count, high_count
        )
        return report
