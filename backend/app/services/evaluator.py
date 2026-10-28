"""
DeploySafe Reproducible Evaluation Framework.
Executes empirical benchmark evaluations on controlled risk scenarios and clean baselines.
Calculates deterministic metrics: Detection Recall, Precision, False Positive Rate,
Evidence Validity, and Execution Latency without manual fabrication.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

from backend.app.core.logging import logger
from backend.app.services.rag.loader import RepositoryLoader
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow


class EvaluationCaseResult(BaseModel):
    case_id: str
    case_name: str
    path: str
    expected_category: str
    expected_files: List[str]
    is_clean: bool
    risk_score: float
    risk_level: str
    detected_findings_count: int
    true_positives: int
    false_positives: int
    missed_risks: int
    evidence_validity_rate: float
    latency_seconds: float
    status: Literal["PASS", "FAIL"]
    notes: Optional[str] = None


class EvaluationSummary(BaseModel):
    timestamp: str
    total_cases: int
    passed_cases: int
    detection_recall: float
    precision: float
    total_false_positives: int
    average_evidence_validity: float
    average_latency_seconds: float
    cases: List[EvaluationCaseResult]


class EvaluationEngine:
    """Automated benchmark evaluator for DeploySafe multi-agent detectors."""

    DEFAULT_CASES_FILE = os.path.join("evaluation", "cases.json")

    @classmethod
    def load_cases(cls, cases_file: Optional[str] = None) -> List[Dict[str, Any]]:
        target_path = cases_file or cls.DEFAULT_CASES_FILE
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Evaluation benchmark file not found: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def evaluate_case(cls, case_spec: Dict[str, Any]) -> EvaluationCaseResult:
        """Executes DeploySafe analysis on a single benchmark repository fixture."""
        case_id = case_spec["case_id"]
        case_name = case_spec["name"]
        rel_path = case_spec["path"]
        is_clean = case_spec.get("is_clean", False)
        expected_cat = case_spec.get("expected_category", "")
        expected_files = case_spec.get("expected_files", [])

        abs_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Evaluation fixture path does not exist: {abs_path}")

        t0 = time.time()
        snapshot = RepositoryLoader.load_local(abs_path, repository_id=f"eval_{case_id.lower()}")
        flow = DeploySafeAnalysisFlow()
        report = flow.execute_flow(snapshot, options={"evaluation_mode": True})
        elapsed = round(time.time() - t0, 2)

        # Inspect detected findings
        findings = report.findings
        total_findings = len(findings)

        # Evidence validity check: Does each finding contain non-empty evidence snippet?
        valid_evidence_count = sum(1 for f in findings if f.evidence and len(f.evidence.strip()) > 0)
        evidence_rate = round((valid_evidence_count / total_findings * 100.0) if total_findings > 0 else 100.0, 1)

        tp = 0
        fp = 0
        fn = 0

        if is_clean:
            # For clean baseline: Any CRITICAL or HIGH finding is a false positive
            crit_or_high = sum(1 for f in findings if f.severity in ("CRITICAL", "HIGH"))
            fp = crit_or_high
            tp = 1 if crit_or_high == 0 else 0
            fn = 0
            status: Literal["PASS", "FAIL"] = "PASS" if crit_or_high == 0 else "FAIL"
        else:
            # For risk scenarios: Check if expected category or file was flagged
            matched_flag = False
            for f in findings:
                cat_match = (f.category.upper() == expected_cat.upper()) if expected_cat else False
                file_match = any(exp_f in f.file_path for exp_f in expected_files) if expected_files else False
                if cat_match or file_match:
                    matched_flag = True
                    break

            if matched_flag:
                tp = 1
                fn = 0
                fp = max(0, total_findings - 1)
                status = "PASS"
            else:
                tp = 0
                fn = 1
                fp = total_findings
                status = "FAIL"

        return EvaluationCaseResult(
            case_id=case_id,
            case_name=case_name,
            path=rel_path,
            expected_category=expected_cat,
            expected_files=expected_files,
            is_clean=is_clean,
            risk_score=report.risk_score,
            risk_level=report.risk_level,
            detected_findings_count=total_findings,
            true_positives=tp,
            false_positives=fp,
            missed_risks=fn,
            evidence_validity_rate=evidence_rate,
            latency_seconds=elapsed,
            status=status,
            notes=case_spec.get("notes")
        )

    @classmethod
    def run_suite(cls, cases_file: Optional[str] = None) -> EvaluationSummary:
        """Executes all benchmark cases and aggregates mathematical metrics."""
        cases = cls.load_cases(cases_file)
        results: List[EvaluationCaseResult] = []

        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_lat = 0.0
        total_evid = 0.0

        logger.info("Starting DeploySafe Benchmark Evaluation Suite (%d cases)...", len(cases))
        for c in cases:
            res = cls.evaluate_case(c)
            results.append(res)
            total_tp += res.true_positives
            total_fp += res.false_positives
            total_fn += res.missed_risks
            total_lat += res.latency_seconds
            total_evid += res.evidence_validity_rate

        total_cases = len(results)
        passed_cases = sum(1 for r in results if r.status == "PASS")

        # Deterministic metric calculations
        recall = round((total_tp / (total_tp + total_fn) * 100.0) if (total_tp + total_fn) > 0 else 0.0, 1)
        precision = round((total_tp / (total_tp + total_fp) * 100.0) if (total_tp + total_fp) > 0 else 0.0, 1)
        avg_lat = round(total_lat / total_cases if total_cases > 0 else 0.0, 2)
        avg_evid = round(total_evid / total_cases if total_cases > 0 else 0.0, 1)

        summary = EvaluationSummary(
            timestamp=datetime.utcnow().isoformat(),
            total_cases=total_cases,
            passed_cases=passed_cases,
            detection_recall=recall,
            precision=precision,
            total_false_positives=total_fp,
            average_evidence_validity=avg_evid,
            average_latency_seconds=avg_lat,
            cases=results
        )

        logger.info("Benchmark complete: %d/%d cases passed. Recall: %.1f%%, Precision: %.1f%%, Avg Latency: %.2fs",
                    passed_cases, total_cases, recall, precision, avg_lat)
        return summary

    @classmethod
    def save_report(cls, summary: EvaluationSummary, output_path: str = "evaluation-report.json"):
        """Saves evaluation report to JSON file."""
        abs_out = os.path.abspath(output_path)
        with open(abs_out, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(mode="json"), f, indent=2)
        logger.info("Saved evaluation benchmark report to: %s", abs_out)
