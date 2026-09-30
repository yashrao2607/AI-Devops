import uuid
from typing import List, Tuple, Dict, Any, Optional
from backend.app.models.analysis_schemas import Finding
from backend.app.core.logging import logger

class FindingDeduplicationService:
    """
    Dedicated finding deduplication service (Phase 4, Step 4 & Part 4).
    Compares candidate findings across multiple specialized agents using:
      1. Repository and file path identity
      2. Overlapping line ranges (e.g. line_start to line_end)
      3. Category and rule/issue similarity
      4. Evidence snippet overlap
    Preserves all evidence citations and attributing agents without data loss.
    """

    @staticmethod
    def _lines_overlap(start1: Optional[int], end1: Optional[int],
                       start2: Optional[int], end2: Optional[int]) -> bool:
        """Determines if two line ranges overlap or are within a 3-line vicinity."""
        if start1 is None or start2 is None:
            return True  # If line numbers are not specified, consider whole file context
        
        e1 = end1 if end1 is not None else start1
        e2 = end2 if end2 is not None else start2
        
        # Overlap or nearby (within 3 lines)
        return not (e1 + 3 < start2 or e2 + 3 < start1)

    @classmethod
    def are_duplicates(cls, f1: Finding, f2: Finding) -> bool:
        """Determines if two findings represent substantially the same issue."""
        if f1.id == f2.id:
            return False
        
        # 1. Repository must match
        if f1.repository_id != f2.repository_id:
            return False
            
        # 2. File path must match
        norm_file1 = f1.file_path.strip().replace("\\", "/").lower()
        norm_file2 = f2.file_path.strip().replace("\\", "/").lower()
        if norm_file1 != norm_file2:
            return False

        # 3. Category must match or be closely related
        if f1.category != f2.category:
            # Allow container/config cross-categorization
            compatible = {
                ("CONFIGURATION", "CONTAINERIZATION"),
                ("CONTAINERIZATION", "CONFIGURATION"),
                ("CONFIGURATION", "ENVIRONMENT"),
                ("ENVIRONMENT", "CONFIGURATION"),
                ("DOCUMENTATION", "CONFIGURATION"),
                ("CONFIGURATION", "DOCUMENTATION")
            }
            if (f1.category, f2.category) not in compatible:
                return False

        # 4. Check line range overlap
        if not cls._lines_overlap(f1.line_start, f1.line_end, f2.line_start, f2.line_end):
            return False

        # 5. Check semantic/title/rule resemblance
        # If identical rule_id or tool_name
        if f1.rule_id and f2.rule_id and f1.rule_id == f2.rule_id:
            return True

        # Check title token overlap
        tokens1 = set(f1.title.lower().split())
        tokens2 = set(f2.title.lower().split())
        overlap = len(tokens1.intersection(tokens2)) / max(len(tokens1), len(tokens2), 1)
        if overlap >= 0.5:
            return True

        # Check evidence snippet overlap if available
        if f1.evidence and f2.evidence:
            s1 = f1.evidence.strip()[:60].lower()
            s2 = f2.evidence.strip()[:60].lower()
            if s1 in s2 or s2 in s1:
                return True

        return False

    @classmethod
    def deduplicate(cls, findings: List[Finding]) -> Tuple[List[Finding], Dict[str, Any]]:
        """
        Deduplicates candidate findings.
        Returns:
          - all_findings: List with canonical findings updated and duplicates marked with status='DUPLICATE'
          - summary: Deduplication metrics and cluster information
        """
        if not findings:
            return [], {
                "total_input": 0,
                "unique_canonical": 0,
                "duplicates_merged": 0,
                "groups_formed": 0
            }

        canonical_list: List[Finding] = []
        duplicate_list: List[Finding] = []
        groups: Dict[str, List[str]] = {}

        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        for finding in findings:
            matched_canonical: Optional[Finding] = None

            for canonical in canonical_list:
                if cls.are_duplicates(finding, canonical):
                    matched_canonical = canonical
                    break

            if matched_canonical is None:
                # Initialize new canonical finding
                finding.merged_agents = [finding.agent]
                finding.merged_finding_ids = []
                canonical_list.append(finding)
            else:
                # Merge into existing canonical finding
                group_id = matched_canonical.dedup_group_id or f"DEDUP-{uuid.uuid4().hex[:8].upper()}"
                matched_canonical.dedup_group_id = group_id
                finding.dedup_group_id = group_id
                finding.status = "DUPLICATE"
                finding.critic_notes = f"Duplicate of primary finding {matched_canonical.id} ({matched_canonical.title})"

                # Maintain attributing agents without duplication
                if finding.agent not in matched_canonical.merged_agents:
                    matched_canonical.merged_agents.append(finding.agent)
                if finding.id not in matched_canonical.merged_finding_ids:
                    matched_canonical.merged_finding_ids.append(finding.id)

                # Merge structured evidence items
                for ev in finding.evidence_items:
                    if ev not in matched_canonical.evidence_items:
                        matched_canonical.evidence_items.append(ev)

                # Upgrade severity if secondary duplicate has higher severity
                if severity_rank.get(finding.severity, 0) > severity_rank.get(matched_canonical.severity, 0):
                    matched_canonical.severity = finding.severity

                groups.setdefault(group_id, [matched_canonical.id]).append(finding.id)
                duplicate_list.append(finding)

        logger.info(
            "Deduplication completed: %d total input -> %d canonical, %d duplicate merged in %d groups",
            len(findings), len(canonical_list), len(duplicate_list), len(groups)
        )

        all_findings = canonical_list + duplicate_list
        summary = {
            "total_input": len(findings),
            "unique_canonical": len(canonical_list),
            "duplicates_merged": len(duplicate_list),
            "groups_formed": len(groups),
            "groups": groups
        }
        return all_findings, summary
