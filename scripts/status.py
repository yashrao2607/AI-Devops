#!/usr/bin/env python3
"""
DeploySafe Parallel Agent Progress Monitor
Run this at any time in terminal:
    python scripts/status.py
"""
import json
import os
import sys

def main():
    progress_file = os.path.join(os.path.dirname(__file__), "progress.json")
    if not os.path.exists(progress_file):
        print("Progress file not found.")
        sys.exit(1)

    with open(progress_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    project = data.get("project", "DeploySafe")
    phase = data.get("phase", "Phase 1")
    streams = data.get("streams", {})

    total_pct = sum(s.get("progress_pct", 0) for s in streams.values())
    overall = int(total_pct / len(streams)) if streams else 0

    print("=" * 65)
    print(f"  {project} — {phase}")
    print(f"  OVERALL COMPLETION: {overall}% [{'#' * (overall // 5)}{'.' * (20 - (overall // 5))}]")
    print("=" * 65)
    print(f"{'STREAM / AGENT':<22} | {'STATUS':<12} | {'PROGRESS':<8} | {'ROLE'}")
    print("-" * 65)

    for agent_id, info in streams.items():
        name = info.get("name", "")
        status = info.get("status", "PENDING")
        pct = info.get("progress_pct", 0)
        bar = f"{pct}%".ljust(6)
        print(f"{agent_id:<22} | {status:<12} | {bar:<8} | {name}")

    print("=" * 65)
    print("Run tests: pytest backend/tests")
    print("Run frontend: cd frontend && npm run dev")
    print("Run backend: cd backend && uvicorn app.main:app --reload")
    print("=" * 65)

if __name__ == "__main__":
    main()
