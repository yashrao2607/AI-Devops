import React, { useState, useEffect } from 'react';
import { 
  Award, Play, BarChart2, RefreshCw
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge } from '../components/common/Badge.tsx';

interface EvaluationCaseResult {
  case_id: string;
  case_name: string;
  path: string;
  expected_category: string;
  expected_files: string[];
  is_clean: boolean;
  risk_score: number;
  risk_level: string;
  detected_findings_count: number;
  true_positives: number;
  false_positives: number;
  missed_risks: number;
  evidence_validity_rate: number;
  latency_seconds: number;
  status: 'PASS' | 'FAIL';
  notes?: string;
}

interface EvaluationSummary {
  timestamp: string;
  total_cases: number;
  passed_cases: number;
  detection_recall: number;
  precision: number;
  total_false_positives: number;
  average_evidence_validity: number;
  average_latency_seconds: number;
  cases: EvaluationCaseResult[];
}

export const Evaluation: React.FC = () => {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/evaluation/results');
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Error fetching evaluation results:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setRunning(true);
      const res = await fetch('/api/v1/evaluation/run', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Error running evaluation suite:', err);
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-6 h-6 text-emerald-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Evaluation Benchmark Suite</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Reproducible empirical benchmarking across controlled risk scenarios (Config Risk, Secret Leaks, Vulnerable Dependencies, Test Deficits, Clean Baseline).
          </p>
        </div>
        <button
          onClick={handleRunEvaluation}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition"
        >
          {running ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Running Benchmark (5 Scenarios)...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              Trigger Live Evaluation Suite
            </>
          )}
        </button>
      </div>

      {loading && !summary ? (
        <Card className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-400" />
          Loading benchmark results...
        </Card>
      ) : !summary ? (
        <Card className="p-8 text-center text-slate-400 space-y-3">
          <BarChart2 className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm">No benchmark evaluations recorded yet.</p>
          <button
            onClick={handleRunEvaluation}
            className="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-medium"
          >
            Run Benchmark Suite Now
          </button>
        </Card>
      ) : (
        <>
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Detection Recall</span>
              <div className="text-xl font-bold text-emerald-400 mt-1">
                {summary.detection_recall.toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                TP / (TP + FN)
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Precision</span>
              <div className="text-xl font-bold text-indigo-400 mt-1">
                {summary.precision.toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                TP / (TP + FP)
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Cases Passed</span>
              <div className="text-xl font-bold text-white mt-1">
                {summary.passed_cases} / {summary.total_cases}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                {((summary.passed_cases / summary.total_cases) * 100).toFixed(0)}% pass rate
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">False Positives</span>
              <div className="text-xl font-bold text-amber-400 mt-1">
                {summary.total_false_positives}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Non-seeded findings
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Evidence Validity</span>
              <div className="text-xl font-bold text-cyan-400 mt-1">
                {summary.average_evidence_validity.toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Line-accurate snippets
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Mean Latency</span>
              <div className="text-xl font-bold text-slate-200 mt-1">
                {summary.average_latency_seconds.toFixed(2)}s
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Per scenario
              </div>
            </Card>
          </div>

          {/* Detailed Benchmark Scenarios Table */}
          <Card className="overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase">
                Controlled Test Scenarios & Ground Truth Results
              </span>
              <span className="text-[11px] font-mono text-slate-500">
                Last Evaluated: {new Date(summary.timestamp).toLocaleString()}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900/80 text-slate-400 font-mono text-[11px]">
                  <tr>
                    <th className="px-4 py-2.5">Case ID</th>
                    <th className="px-4 py-2.5">Scenario Name</th>
                    <th className="px-4 py-2.5">Seeded Category</th>
                    <th className="px-4 py-2.5">Score</th>
                    <th className="px-4 py-2.5">Status</th>
                    <th className="px-4 py-2.5">Findings (TP / FP)</th>
                    <th className="px-4 py-2.5">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {summary.cases.map((c) => (
                    <tr key={c.case_id} className="hover:bg-slate-900/40">
                      <td className="px-4 py-3 font-semibold text-indigo-300">{c.case_id}</td>
                      <td className="px-4 py-3 text-slate-200 font-sans">
                        <div className="font-medium text-white">{c.case_name}</div>
                        {c.notes && <div className="text-[11px] text-slate-500 mt-0.5">{c.notes}</div>}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={c.is_clean ? 'success' : 'info'} size="sm">
                          {c.expected_category}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-semibold text-white">
                        {c.risk_score.toFixed(1)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={c.status === 'PASS' ? 'success' : 'critical'} size="sm">
                          {c.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {c.detected_findings_count} ({c.true_positives} TP / {c.false_positives} FP)
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {c.latency_seconds.toFixed(2)}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};
