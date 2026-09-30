import json
from typing import Dict, Any, List
from backend.app.models.analysis_schemas import AnalysisReport, Finding
from backend.app.services.risk_engine import RiskEngine

class ReportService:
    """
    Report generation service (Phase 4, Parts 6 & 35).
    Produces structured JSON, Markdown, and self-contained HTML reports
    from finalized AnalysisReport instances.
    """

    @classmethod
    def generate_markdown(cls, report: AnalysisReport) -> str:
        """Renders an executive Markdown deployment-readiness report."""
        lines = [
            f"# DeploySafe Deployment Readiness Report",
            f"",
            f"> **Repository:** `{report.repository_name}` (`{report.repository_id}`)  ",
            f"> **Run ID:** `{report.run_id}`  ",
            f"> **Analyzed At:** `{report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`  ",
            f"> **Duration:** `{report.duration_seconds}s`  ",
            f"> **Status:** `{report.status}`",
            f"",
            f"---",
            f"",
            f"## Executive Risk Summary",
            f"",
            f"- **Deterministic Risk Score:** **{report.risk_score} / 100**",
            f"- **Deployment Risk Level:** **{report.risk_level}**",
            f"- **Total Identified Findings:** `{len(report.findings)}`",
            f"- **Critic Validated Findings:** `{len(report.validated_findings)}`",
            f"- **Findings Requiring Review:** `{len(report.needs_review_findings)}`",
            f"- **Rejected / Duplicates Merged:** `{len(report.rejected_findings)}`",
            f"",
            f"### Severity Distribution",
            f"| Severity | Count | Point Weight | Total Contributed |",
            f"| :--- | :--- | :--- | :--- |",
            f"| **CRITICAL** | {report.finding_counts_by_severity.get('CRITICAL', 0)} | 35.0 | {report.score_breakdown.get('severity_breakdown', {}).get('CRITICAL', 0.0)} pts |",
            f"| **HIGH** | {report.finding_counts_by_severity.get('HIGH', 0)} | 25.0 | {report.score_breakdown.get('severity_breakdown', {}).get('HIGH', 0.0)} pts |",
            f"| **MEDIUM** | {report.finding_counts_by_severity.get('MEDIUM', 0)} | 15.0 | {report.score_breakdown.get('severity_breakdown', {}).get('MEDIUM', 0.0)} pts |",
            f"| **LOW** | {report.finding_counts_by_severity.get('LOW', 0)} | 7.0 | {report.score_breakdown.get('severity_breakdown', {}).get('LOW', 0.0)} pts |",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"{report.summary}",
            f"",
            f"---",
            f"",
            f"## Validated Deployment Hazards",
            f""
        ]

        if not report.validated_findings:
            lines.append("No validated deployment-risk findings detected in this run.")
        else:
            for idx, f in enumerate(report.validated_findings, 1):
                loc = f"{f.file_path}"
                if f.line_start:
                    loc += f":L{f.line_start}"
                    if f.line_end and f.line_end != f.line_start:
                        loc += f"-{f.line_end}"

                lines.extend([
                    f"### {idx}. [{f.severity}] {f.title} (`{f.id}`)",
                    f"- **Location:** `{loc}`",
                    f"- **Category:** `{f.category}` | **Agent:** `{f.agent}`",
                    f"- **Score Contribution:** `+{f.score_contribution} pts`",
                    f"- **Operational Impact:** {f.impact}",
                    f"- **Actionable Fix:** {f.recommendation}",
                    f"",
                    f"```text",
                    f"{f.evidence.strip()}",
                    f"```",
                    f""
                ])

        if report.needs_review_findings:
            lines.extend([
                f"---",
                f"",
                f"## Inferred Concerns Requiring Review",
                f""
            ])
            for idx, f in enumerate(report.needs_review_findings, 1):
                lines.extend([
                    f"- **[{f.severity}] {f.title}** (`{f.file_path}`): {f.summary}",
                    f"  *Reason for Review:* {f.critic_notes or 'Requires engineer assessment'}"
                ])
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"## Recommended Remediations",
            f""
        ])
        for rec in report.recommendations:
            lines.append(f"- {rec}")

        lines.extend([
            f"",
            f"---",
            f"*Generated autonomously by DeploySafe v0.1.0 — Deterministic Risk Engine & Multi-Agent Flow*"
        ])

        return "\n".join(lines)

    @classmethod
    def generate_html(cls, report: AnalysisReport) -> str:
        """Renders a self-contained, beautifully styled HTML deployment readiness report."""
        sev_color = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f97316",
            "MODERATE": "#eab308",
            "LOW": "#10b981"
        }
        level_color = sev_color.get(report.risk_level, "#3b82f6")

        findings_html = []
        for f in report.validated_findings:
            loc = f"{f.file_path}"
            if f.line_start:
                loc += f":L{f.line_start}"
            badge_color = sev_color.get(f.severity, "#94a3b8")

            findings_html.append(f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <span style="background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}66; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; font-family: monospace;">{f.severity}</span>
                        <span style="color: #94a3b8; font-size: 12px; margin-left: 8px; font-family: monospace;">{f.category}</span>
                        <span style="color: #64748b; font-size: 11px; margin-left: 8px;">ID: {f.id}</span>
                    </div>
                    <span style="color: #38bdf8; font-family: monospace; font-size: 12px;">+{f.score_contribution} pts</span>
                </div>
                <h3 style="color: #f8fafc; margin: 4px 0 8px 0; font-size: 15px;">{f.title}</h3>
                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 10px;"><strong>Location:</strong> <code style="color: #38bdf8;">{loc}</code> &bull; <strong>Detected by:</strong> {f.agent}</div>
                <div style="background: #1e1e2e; color: #f87171; border-left: 3px solid #ef4444; padding: 8px 12px; font-size: 12px; margin-bottom: 10px;"><strong>Impact:</strong> {f.impact}</div>
                <div style="background: #064e3b33; color: #34d399; border-left: 3px solid #10b981; padding: 8px 12px; font-size: 12px; margin-bottom: 12px;"><strong>Remediation:</strong> {f.recommendation}</div>
                <pre style="background: #020617; border: 1px solid #1e293b; padding: 12px; border-radius: 6px; font-size: 11px; color: #cbd5e1; overflow-x: auto; white-space: pre-wrap;">{f.evidence.strip()}</pre>
            </div>
            """)

        recommendations_html = "".join([f"<li style='margin-bottom: 6px;'>{r}</li>" for r in report.recommendations])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DeploySafe Report - {report.repository_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #020617;
            color: #f8fafc;
            margin: 0;
            padding: 32px;
            line-height: 1.5;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px; }}
        .hero {{ background: #0b1329; border: 1px solid #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
        .score {{ font-size: 48px; font-weight: 800; font-family: monospace; color: {level_color}; }}
        .badge {{ background: {level_color}22; color: {level_color}; border: 1px solid {level_color}66; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">DeploySafe Deployment Readiness Report</h1>
            <div style="color: #64748b; font-size: 12px; margin-top: 4px; font-family: monospace;">
                Repository: {report.repository_name} &bull; Run: {report.run_id} &bull; Analyzed: {report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </div>

        <div class="hero">
            <div>
                <span class="badge">{report.risk_level} RISK</span>
                <h2 style="margin: 12px 0 4px 0; font-size: 18px;">Deployment Risk Assessment</h2>
                <div style="color: #94a3b8; font-size: 13px;">{len(report.validated_findings)} validated hazards detected across {len(report.agents_executed)} autonomous agents</div>
            </div>
            <div style="text-align: right;">
                <div class="score">{report.risk_score}<span style="font-size: 20px; color: #64748b;">/100</span></div>
                <div style="color: #64748b; font-size: 11px; font-family: monospace;">DETERMINISTIC SCORE</div>
            </div>
        </div>

        <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <h3 style="margin-top: 0; font-size: 14px; color: #38bdf8;">Executive Summary</h3>
            <p style="color: #cbd5e1; font-size: 13px; margin: 0;">{report.summary}</p>
        </div>

        <h2 style="font-size: 18px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 16px;">Validated Deployment Hazards</h2>
        {"".join(findings_html) if findings_html else "<p style='color: #64748b;'>No validated deployment hazards detected.</p>"}

        <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; margin-top: 24px;">
            <h3 style="margin-top: 0; font-size: 14px; color: #10b981;">Recommended Actions Prior to Deployment</h3>
            <ul style="color: #cbd5e1; font-size: 13px; padding-left: 20px; margin: 0;">
                {recommendations_html}
            </ul>
        </div>
    </div>
</body>
</html>
"""
        return html

    @classmethod
    def generate_json(cls, report: AnalysisReport) -> str:
        """Returns structured JSON serialization of the analysis report."""
        return report.model_dump_json(indent=2)
