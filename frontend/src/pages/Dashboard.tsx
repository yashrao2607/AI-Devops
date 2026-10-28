import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  FileCode,
  Info,
  X,
  Play,
  RefreshCw,
  TrendingUp
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Button } from '../components/common/Button.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';

interface Finding {
  id: string;
  category: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  summary: string;
  impact: string;
  recommendation: string;
  file_path: string;
  line_start?: number | null;
  line_end?: number | null;
  evidence: string;
  agent: string;
  status: string;
  score_contribution: number;
  critic_notes?: string | null;
}

interface RecentRun {
  run_id: string;
  repository_id: string;
  repository_name: string;
  branch: string;
  commit_sha: string;
  risk_score: number;
  risk_level: string;
  findings_count: number;
  validated_count: number;
  status: string;
  analyzed_at: string;
  duration_seconds: number;
}

interface DashboardSummary {
  total_runs: number;
  latest_run_id: string | null;
  latest_repository_id: string | null;
  latest_risk_score: number;
  latest_risk_level: string;
  total_findings_detected: number;
  validated_findings_count: number;
  severity_distribution: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  status_distribution: {
    VALIDATED: number;
    NEEDS_REVIEW: number;
    DUPLICATE: number;
    REJECTED: number;
    DISMISSED: number;
  };
  recent_runs: RecentRun[];
  top_findings: Finding[];
}

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFormulaModal, setShowFormulaModal] = useState(false);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // First ensure demo repo has at least one run if no runs exist
      const res = await fetch('/api/v1/dashboard/summary');
      if (!res.ok) {
        throw new Error(`Failed to load dashboard summary (HTTP ${res.status})`);
      }
      const summary: DashboardSummary = await res.json();

      // If zero runs exist, trigger one on demo repo automatically
      if (summary.total_runs === 0) {
        await fetch('/api/v1/analysis/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repository_id: 'deploysafe-analysis-demo' })
        });
        const refetch = await fetch('/api/v1/dashboard/summary');
        const updated = await refetch.json();
        setData(updated);
      } else {
        setData(summary);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const getRiskColor = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return { text: 'text-red-400', bg: 'bg-red-950/40', border: 'border-red-800/80', badge: 'critical' as BadgeVariant };
      case 'HIGH':
        return { text: 'text-orange-400', bg: 'bg-orange-950/40', border: 'border-orange-800/80', badge: 'high' as BadgeVariant };
      case 'MODERATE':
        return { text: 'text-yellow-400', bg: 'bg-yellow-950/40', border: 'border-yellow-800/80', badge: 'moderate' as BadgeVariant };
      case 'LOW':
      default:
        return { text: 'text-emerald-400', bg: 'bg-emerald-950/40', border: 'border-emerald-800/80', badge: 'success' as BadgeVariant };
    }
  };

  const getSeverityBadgeVariant = (sev: string): BadgeVariant => {
    switch (sev.toUpperCase()) {
      case 'CRITICAL':
        return 'critical';
      case 'HIGH':
        return 'high';
      case 'MEDIUM':
        return 'moderate';
      case 'LOW':
        return 'low';
      default:
        return 'neutral';
    }
  };

  const handleCopySnippet = (snippet: string) => {
    navigator.clipboard.writeText(snippet);
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  if (loading && !data) {
    return (
      <div className="py-20 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <div className="text-sm font-mono text-slate-400">Loading Deployment Readiness Dashboard...</div>
      </div>
    );
  }

  const riskMeta = getRiskColor(data?.latest_risk_level || 'LOW');

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Deployment Readiness Dashboard
            <span className="text-xs px-2.5 py-0.5 rounded font-mono font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
              Production v1.0
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic risk scoring, multi-agent finding aggregation, and deployment hazard intelligence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
            onClick={fetchDashboardData}
          >
            Refresh Metrics
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<Play className="w-3.5 h-3.5 fill-current" />}
            onClick={() => {
              window.location.hash = '#analyze';
              window.dispatchEvent(new CustomEvent('deploysafe-navigate'));
            }}
          >
            Run New Analysis
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">{error}</div>
        </div>
      )}

      {/* Hero Section: Primary Risk Assessment & Score (Part 15 & 16) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Big Risk Score Gauge Card */}
        <div className={`p-6 rounded-xl border ${riskMeta.border} ${riskMeta.bg} flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
                Deployment Risk Score
              </span>
              <Badge variant={riskMeta.badge}>
                {data?.latest_risk_level} RISK
              </Badge>
            </div>

            <div className="flex items-baseline gap-2 mt-2">
              <span className={`text-6xl font-extrabold font-mono tracking-tight ${riskMeta.text}`}>
                {data?.latest_risk_score}
              </span>
              <span className="text-xl font-mono text-slate-500 font-semibold">/ 100</span>
            </div>

            <p className="text-xs text-slate-300 mt-3 leading-relaxed">
              Calculated deterministically from {data?.validated_findings_count} Critic-validated findings. Zero LLM hallucination in mathematical scoring.
            </p>
          </div>

          <div className="pt-4 mt-6 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <button
              onClick={() => setShowFormulaModal(true)}
              className="inline-flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 font-mono transition-colors"
            >
              <Info className="w-3.5 h-3.5" />
              How is this calculated?
            </button>
            <span className="font-mono text-slate-400 text-[11px]">
              Run: {data?.latest_run_id || '--'}
            </span>
          </div>
        </div>

        {/* Center: Severity Counts Breakdown (Part 17) */}
        <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-red-900/40 bg-red-950/15 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-red-400 uppercase tracking-wider font-semibold">Critical</span>
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
              </div>
              <div className="text-4xl font-extrabold font-mono text-red-400 mt-3">
                {data?.severity_distribution.CRITICAL || 0}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Weight: 35.0 pts each</p>
            </div>
            <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60 mt-3">
              Direct release blockers
            </div>
          </Card>

          <Card className="border-orange-900/40 bg-orange-950/15 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-orange-400 uppercase tracking-wider font-semibold">High</span>
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
              </div>
              <div className="text-4xl font-extrabold font-mono text-orange-400 mt-3">
                {data?.severity_distribution.HIGH || 0}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Weight: 25.0 pts each</p>
            </div>
            <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60 mt-3">
              Severe drift & unpinned deps
            </div>
          </Card>

          <Card className="border-yellow-900/40 bg-yellow-950/15 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-yellow-400 uppercase tracking-wider font-semibold">Medium</span>
                <span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span>
              </div>
              <div className="text-4xl font-extrabold font-mono text-yellow-400 mt-3">
                {data?.severity_distribution.MEDIUM || 0}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Weight: 15.0 pts each</p>
            </div>
            <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60 mt-3">
              Moderate config warnings
            </div>
          </Card>

          <Card className="border-blue-900/40 bg-blue-950/15 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-blue-400 uppercase tracking-wider font-semibold">Low</span>
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              </div>
              <div className="text-4xl font-extrabold font-mono text-blue-400 mt-3">
                {data?.severity_distribution.LOW || 0}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Weight: 7.0 pts each</p>
            </div>
            <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60 mt-3">
              Minor operational notes
            </div>
          </Card>
        </div>
      </div>

      {/* Audit Pipeline Health Bar */}
      {data && (
        <Card title="Finding Audit & Deduplication Health" subtitle="Breakdown of candidate issues evaluated by Critic Agent and Deduplication Service.">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-900/40">
              <span className="text-slate-400 block mb-1">Critic Validated</span>
              <span className="text-lg font-bold text-emerald-400">{data.status_distribution.VALIDATED}</span>
              <span className="text-[11px] text-slate-500 block">Ground-truth verified</span>
            </div>
            <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-900/40">
              <span className="text-slate-400 block mb-1">Needs Review</span>
              <span className="text-lg font-bold text-amber-400">{data.status_distribution.NEEDS_REVIEW}</span>
              <span className="text-[11px] text-slate-500 block">Inferred concerns</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400 block mb-1">Duplicates Merged</span>
              <span className="text-lg font-bold text-slate-300">{data.status_distribution.DUPLICATE}</span>
              <span className="text-[11px] text-slate-500 block">0 duplicate points</span>
            </div>
            <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-900/40">
              <span className="text-slate-400 block mb-1">Rejected / Insufficient</span>
              <span className="text-lg font-bold text-rose-400">{data.status_distribution.REJECTED}</span>
              <span className="text-[11px] text-slate-500 block">Filtered hallucinations</span>
            </div>
          </div>
        </Card>
      )}

      {/* Top Priority Findings Table (Part 18) */}
      <Card
        title="Top Priority Deployment Hazards"
        subtitle="Highest impact validated findings actively contributing to the deployment risk score."
      >
        {(!data?.top_findings || data.top_findings.length === 0) ? (
          <div className="text-center py-8 text-xs font-mono text-slate-500">
            No validated findings currently detected.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Finding Title & Location</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Score Contribution</th>
                  <th className="py-2.5 px-3 text-right">Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.top_findings.map((f) => (
                  <tr
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-3">
                      <Badge variant={getSeverityBadgeVariant(f.severity)}>{f.severity}</Badge>
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-200">{f.title}</div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5 flex items-center gap-1">
                        <FileCode className="w-3 h-3 text-cyan-400" />
                        <span>{f.file_path}</span>
                        {f.line_start !== null && <span>:L{f.line_start}</span>}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-slate-800 text-slate-300 border border-slate-700">
                        {f.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {f.agent}
                    </td>
                    <td className="py-3 px-3 font-mono text-cyan-400 font-semibold">
                      +{f.score_contribution} pts
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFinding(f);
                        }}
                      >
                        Inspect
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Recent Analysis Runs (Part 19) */}
      <Card
        title="Recent Repository Analysis Runs"
        subtitle="Historical multi-agent evaluations with deterministic risk scoring audit records."
      >
        {(!data?.recent_runs || data.recent_runs.length === 0) ? (
          <div className="text-center py-8 text-xs font-mono text-slate-500">
            No historical runs recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="py-2.5 px-3">Run ID</th>
                  <th className="py-2.5 px-3">Repository</th>
                  <th className="py-2.5 px-3">Commit</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Findings</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.recent_runs.map((r) => {
                  const rMeta = getRiskColor(r.risk_level);
                  return (
                    <tr key={r.run_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-3 text-cyan-400 font-semibold">{r.run_id}</td>
                      <td className="py-3 px-3 text-slate-200">{r.repository_name}</td>
                      <td className="py-3 px-3 text-slate-400">{r.commit_sha}</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded font-bold ${rMeta.text} ${rMeta.bg} border ${rMeta.border}`}>
                          {r.risk_score} / 100 ({r.risk_level})
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {r.validated_count} validated / {r.findings_count} total
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-emerald-400 font-semibold">{r.status}</span>
                      </td>
                      <td className="py-3 px-3 text-right text-slate-500">
                        {new Date(r.analyzed_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* "How is this calculated?" Mathematical Explanation Modal (Part 9) */}
      {showFormulaModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-2xl w-full p-6 space-y-5">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-cyan-400" />
                  Deterministic Risk Score Calculation
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  DeploySafe Risk Engine formula specification (PRD §10).
                </p>
              </div>
              <button
                onClick={() => setShowFormulaModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
              <div className="p-3.5 rounded-lg bg-dark-950 border border-slate-800 text-cyan-300">
                Score = min(100.0, round(&sum; (Severity Weight &times; Confidence Multiplier &times; Impact Multiplier)))
              </div>

              <div>
                <span className="text-white font-semibold block mb-2 font-sans">1. Base Severity Weights:</span>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-red-400 font-bold block">CRITICAL</span>
                    <span className="text-slate-200">35.0 pts</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-orange-400 font-bold block">HIGH</span>
                    <span className="text-slate-200">25.0 pts</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-yellow-400 font-bold block">MEDIUM</span>
                    <span className="text-slate-200">15.0 pts</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-blue-400 font-bold block">LOW</span>
                    <span className="text-slate-200">7.0 pts</span>
                  </div>
                </div>
              </div>

              <div>
                <span className="text-white font-semibold block mb-2 font-sans">2. Multipliers & Exclusion Rules:</span>
                <ul className="list-disc pl-5 space-y-1 text-slate-400">
                  <li><strong>Confidence:</strong> HIGH = 1.0, MEDIUM = 0.8, LOW = 0.6</li>
                  <li><strong>Impact:</strong> HIGH/CRITICAL = 1.0, MEDIUM = 0.8, LOW = 0.6</li>
                  <li><strong>Duplicates:</strong> 0.0 pts (automatically merged into canonical issue)</li>
                  <li><strong>Rejected / Hallucinations:</strong> 0.0 pts (filtered by Critic Agent)</li>
                  <li><strong>Needs Review:</strong> 0.0 pts (inferred concerns held for human verification)</li>
                </ul>
              </div>

              <div>
                <span className="text-white font-semibold block mb-2 font-sans">3. Project-Defined Risk Levels:</span>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800 text-emerald-400">0–24: LOW</div>
                  <div className="p-2 rounded bg-yellow-950/40 border border-yellow-800 text-yellow-400">25–49: MODERATE</div>
                  <div className="p-2 rounded bg-orange-950/40 border border-orange-800 text-orange-400">50–74: HIGH</div>
                  <div className="p-2 rounded bg-red-950/40 border border-red-800 text-red-400">75–100: CRITICAL</div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setShowFormulaModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Finding Detail Modal / Drawer (Part 24 & 25) */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
            <div className="p-4 border-b border-slate-800 flex items-start justify-between sticky top-0 bg-slate-900/95 backdrop-blur z-10">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <Badge variant={getSeverityBadgeVariant(selectedFinding.severity)}>
                    {selectedFinding.severity}
                  </Badge>
                  <span className="text-xs font-mono text-cyan-400 font-semibold">
                    +{selectedFinding.score_contribution} pts
                  </span>
                  <span className="text-xs font-mono text-slate-500">ID: {selectedFinding.id}</span>
                </div>
                <h2 className="text-base font-bold text-white">{selectedFinding.title}</h2>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-dark-950 border border-slate-800">
                  <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-1">
                    Risk Mechanism
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">{selectedFinding.summary}</p>
                </div>
                <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/40">
                  <span className="text-xs font-mono text-rose-400 uppercase tracking-wider block mb-1">
                    Deployment Impact
                  </span>
                  <p className="text-xs text-rose-200/90 leading-relaxed">{selectedFinding.impact}</p>
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40">
                <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block mb-1">
                  Actionable Remediation
                </span>
                <p className="text-xs text-emerald-200 leading-relaxed">{selectedFinding.recommendation}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block mb-0.5">Attributing Agent:</span>
                  <span className="text-slate-200 font-semibold">{selectedFinding.agent}</span>
                </div>
                <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block mb-0.5">Critic Verification:</span>
                  <span className="text-emerald-400">{selectedFinding.critic_notes || 'Validated against repository ground truth'}</span>
                </div>
              </div>

              {/* Concrete Code Evidence */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-300 font-semibold">
                    <FileCode className="w-4 h-4 text-cyan-400" />
                    <span>{selectedFinding.file_path}</span>
                    {selectedFinding.line_start !== null && (
                      <span className="text-cyan-400">:L{selectedFinding.line_start}</span>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopySnippet(selectedFinding.evidence)}
                  >
                    {copiedSnippet ? 'Copied' : 'Copy Snippet'}
                  </Button>
                </div>
                <pre className="p-4 rounded-lg bg-dark-950 border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                  {selectedFinding.evidence}
                </pre>
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setSelectedFinding(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
