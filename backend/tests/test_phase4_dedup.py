import pytest
from backend.app.models.analysis_schemas import Finding
from backend.app.services.deduplication import FindingDeduplicationService

def test_dedup_detects_same_file_overlapping_lines():
    f1 = Finding(
        id="F-101",
        category="CONFIGURATION",
        severity="HIGH",
        confidence="HIGH",
        title="Unpinned Docker Base Image",
        summary="Floating image tag used",
        impact="Build instability",
        recommendation="Pin SHA or tag",
        repository_id="test_repo",
        file_path="Dockerfile",
        line_start=1,
        line_end=1,
        evidence="FROM python:latest",
        agent="ConfigAgent",
        status="VALIDATED"
    )
    f2 = Finding(
        id="F-102",
        category="CONTAINERIZATION",
        severity="CRITICAL",
        confidence="HIGH",
        title="Unpinned Docker Image python:latest",
        summary="Container image has unpinned version",
        impact="Production deployment risk",
        recommendation="Pin explicit version",
        repository_id="test_repo",
        file_path="Dockerfile",
        line_start=1,
        line_end=2,
        evidence="FROM python:latest\nWORKDIR /app",
        agent="SecurityAgent",
        status="VALIDATED"
    )

    assert FindingDeduplicationService.are_duplicates(f1, f2) is True

    findings, summary = FindingDeduplicationService.deduplicate([f1, f2])
    assert summary["duplicates_merged"] == 1
    assert summary["unique_canonical"] == 1
    canonical = [f for f in findings if f.status != "DUPLICATE"][0]
    duplicate = [f for f in findings if f.status == "DUPLICATE"][0]

    # Verify severity was upgraded to CRITICAL from secondary duplicate
    assert canonical.severity == "CRITICAL"
    # Verify attributing agents merged
    assert "ConfigAgent" in canonical.merged_agents
    assert "SecurityAgent" in canonical.merged_agents
    # Verify duplicate linked
    assert duplicate.id in canonical.merged_finding_ids
    assert duplicate.dedup_group_id == canonical.dedup_group_id

def test_dedup_preserves_distinct_files():
    f1 = Finding(
        id="F-201",
        category="CODE",
        severity="HIGH",
        confidence="HIGH",
        title="Hardcoded Localhost in Payment",
        summary="Localhost URL used",
        impact="Network failure",
        recommendation="Use env var",
        repository_id="test_repo",
        file_path="src/payment.py",
        line_start=9,
        line_end=9,
        evidence="http://localhost:8080",
        agent="CodeAgent",
        status="VALIDATED"
    )
    f2 = Finding(
        id="F-202",
        category="CODE",
        severity="HIGH",
        confidence="HIGH",
        title="Hardcoded Localhost in Orders",
        summary="Localhost URL used",
        impact="Network failure",
        recommendation="Use env var",
        repository_id="test_repo",
        file_path="src/orders.py",
        line_start=15,
        line_end=15,
        evidence="http://localhost:8080",
        agent="CodeAgent",
        status="VALIDATED"
    )

    assert FindingDeduplicationService.are_duplicates(f1, f2) is False
    findings, summary = FindingDeduplicationService.deduplicate([f1, f2])
    assert summary["duplicates_merged"] == 0
    assert summary["unique_canonical"] == 2
