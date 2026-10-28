from typing import Optional
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import Finding


class PatchPreview(BaseModel):
    finding_id: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    original_snippet: str
    proposed_patch: str
    explanation: str
    disclaimer: str = "AI-GENERATED PROPOSAL — REQUIRES HUMAN REVIEW AND MANUAL APPROVAL BEFORE APPLICATION"


class PatchService:
    """
    Constructs unified diff patch proposals for validated findings (Phase 7 Steps 14 & 15).
    Enforces Step 16 Human Approval: proposals are never applied automatically to production repositories.
    """

    @classmethod
    def generate_patch_preview(cls, finding: Finding) -> PatchPreview:
        orig = finding.evidence or ""
        rec = finding.recommendation or "Review and remediate according to project guidelines."

        # Generate a structured unified diff representation
        lines = orig.splitlines()
        diff_lines = []
        diff_lines.append(f"--- a/{finding.file_path}")
        diff_lines.append(f"+++ b/{finding.file_path}")
        start_line = finding.line_start or 1
        diff_lines.append(f"@@ -{start_line},{max(1, len(lines))} +{start_line},{max(1, len(lines))} @@")

        # Represent remediation based on category
        if finding.category == "CONFIGURATION" and "env" in (finding.file_path or "").lower():
            diff_lines.append(f"+ # Added by developer to configure required environment variable")
            diff_lines.append(f"+ {rec.split('.')[0] if '.' in rec else rec}")
            for l in lines[:3]:
                diff_lines.append(f"  {l}")
        elif finding.category == "CONTAINERIZATION" and "root" in (finding.title or "").lower():
            for l in lines:
                if "USER root" in l:
                    diff_lines.append(f"- {l}")
                    diff_lines.append(f"+ USER appuser # Non-root security best practice")
                else:
                    diff_lines.append(f"  {l}")
        else:
            for l in lines[:4]:
                diff_lines.append(f"- {l}")
            diff_lines.append(f"+ # [REMEDIATION PROPOSAL]: {rec}")

        patch_str = "\n".join(diff_lines)

        return PatchPreview(
            finding_id=finding.id,
            file_path=finding.file_path,
            line_start=finding.line_start,
            line_end=finding.line_end,
            original_snippet=orig,
            proposed_patch=patch_str,
            explanation=f"Proposed remediation addressing '{finding.title}': {rec}"
        )
