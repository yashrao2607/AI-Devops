"""
Reproducible Benchmark Evaluation API Endpoints
Provides endpoints to inspect benchmark cases, run automated evaluations,
and retrieve quantitative detection metrics.
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from backend.app.services.evaluator import EvaluationEngine, EvaluationSummary

router = APIRouter()

# In-memory cache of latest evaluation report
_LATEST_EVALUATION_REPORT: Optional[EvaluationSummary] = None


@router.get("/evaluation/cases")
def get_evaluation_cases():
    """Lists all controlled benchmark cases in the evaluation suite."""
    try:
        cases = EvaluationEngine.load_cases()
        return {"total_cases": len(cases), "cases": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/results", response_model=Optional[EvaluationSummary])
def get_evaluation_results():
    """Retrieves the most recent benchmark evaluation results."""
    global _LATEST_EVALUATION_REPORT
    if _LATEST_EVALUATION_REPORT:
        return _LATEST_EVALUATION_REPORT

    # Check if report exists on disk
    report_file = "evaluation-report.json"
    if os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                import json
                data = json.load(f)
                _LATEST_EVALUATION_REPORT = EvaluationSummary.model_validate(data)
                return _LATEST_EVALUATION_REPORT
        except Exception:
            pass

    return None


@router.post("/evaluation/run", response_model=EvaluationSummary)
def run_evaluation_suite():
    """Triggers an empirical benchmark evaluation run across all 5 test scenarios."""
    global _LATEST_EVALUATION_REPORT
    try:
        summary = EvaluationEngine.run_suite()
        EvaluationEngine.save_report(summary, "evaluation-report.json")
        _LATEST_EVALUATION_REPORT = summary
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
