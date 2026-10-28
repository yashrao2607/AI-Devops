import React, { useState, useEffect } from 'react';
import {
  History,
  ShieldAlert,
  CheckCircle2,
  Clock,
  RefreshCw,
  X,
  FileText,
  Download,
  Cpu,
  HelpCircle,
  Eye,
  GitCompare,
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  AlertTriangle,
  FileCode
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';
import { Button } from '../components/common/Button.tsx';

interface RunItem {
  run_id: string;
  repository_id: string;
  repository_name: string;
  branch: string;
  commit_sha: string;
  risk_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  findings_count: number;
  validated_count: number;
  needs_review_count: number;
  rejected_count: number;
  status: string;
  duration_seconds: number;
  analyzed_at: string;
}

interface RunSummaryData {
  run_id: string;
  repository_id: string;
  repository_name: string;
  risk_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  summary: string;
  score_breakdown: {
    raw_score: number;
    risk_score: number;
    risk_level: string;
    contributors: Array<{
      finding_id: string;
      title: string;
      severity: string;
      confidence: string;
      impact_level: string;
      points: number;
      file_path: string;
    }>;
    excluded_findings: Array<{
      finding_id: string;
      reason: string;
    }>;
    formula_explanation: string;
  };
  dedup_summary: {
    input_count: number;
    canonical_count: number;
    duplicate_count: number;
    groups_formed: number;
  };
  severity_counts: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  recommendations: string[];
}

interface AgentTelemetry {
  agent_name: string;
  status: string;
  duration_seconds: number;
  findings_count: number;
  tools_called: string[];
  error?: string | null;
}

interface ComparisonFindingItem {
  fingerprint: string;
  finding_id: string;
  title: string;
  file_path: string;
  line_start?: number | null;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  status: string;
  score_contribution: number;
}

interface RunComparisonResult {
  has_baseline: boolean;
  base_run_id?: string | null;
  target_run_id: string;
  repository_id: string;
  repository_name: string;
  base_score?: number | null;
  target_score: number;
  score_delta?: number | null;
  risk_trend: 'IMPROVED' | 'DEGRADED' | 'UNCHANGED' | 'INITIAL_BASELINE';
  base_findings_count: number;
  target_findings_count: number;
  resolved_count: number;
  new_count: number;
  persistent_count: number;
  changed_count: number;
  resolved_findings: ComparisonFindingItem[];
  new_findings: ComparisonFindingItem[];
  persistent_findings: ComparisonFindingItem[];
  changed_findings: Array<{
    fingerprint: string;
    finding_id: string;
    title: string;
    file_path: string;
    line_start?: number | null;
    category: string;
    base_severity: string;
    target_severity: string;
    base_status: string;
    target_status: string;
    base_score_contribution: number;
    target_score_contribution: number;
  }>;
  message?: string | null;
}

export const Runs: React.FC = () => {
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [modalTab, setModalTab] = useState<'details' | 'compare'>('details');
  const [runSummary, setRunSummary] = useState<RunSummaryData | null>(null);
  const [agentTelemetry, setAgentTelemetry] = useState<AgentTelemetry[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showFormulaModal, setShowFormulaModal] = useState(false);

  // Comparison State
  const [comparison, setComparison] = useState<RunComparisonResult | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [selectedBaseRunId, setSelectedBaseRunId] = useState<string>('');

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/runs');
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
      }
    } catch (e) {
      console.error('Failed to fetch runs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const fetchComparisonData = async (targetRunId: string, baseRunId?: string) => {
    setCompareLoading(true);
    try {
      const url = baseRunId
        ? `/api/v1/runs/${targetRunId}/compare?base_run_id=${encodeURIComponent(baseRunId)}`
        : `/api/v1/runs/${targetRunId}/compare`;
      const res = await fetch(url);
      if (res.ok) {
        const data: RunComparisonResult = await res.json();
        setComparison(data);
        if (data.base_run_id) {
          setSelectedBaseRunId(data.base_run_id);
        }
      }
    } catch (e) {
      console.error('Failed to load run comparison:', e);
    } finally {
      setCompareLoading(false);
    }
  };

  const openRunDetail = async (runId: string, initialTab: 'details' | 'compare' = 'details') => {
    setSelectedRunId(runId);
    setModalTab(initialTab);
    setDetailLoading(true);
    setComparison(null);
    setSelectedBaseRunId('');

    try {
      const [sumRes, detailRes] = await Promise.all([
        fetch(`/api/v1/runs/${runId}/summary`),
        fetch(`/api/v1/runs/${runId}`)
      ]);

      if (sumRes.ok) {
        const sumData = await sumRes.json();
        setRunSummary(sumData);
      }

      if (detailRes.ok) {
        const detailData = await detailRes.json();
        if (detailData.agent_states) {
          const agents: AgentTelemetry[] = Object.values(detailData.agent_states);
          setAgentTelemetry(agents);
        }
      }

      // Also prefetch comparison
      fetchComparisonData(runId);
    } catch (e) {
      console.error('Failed to load run details:', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const getRiskLevelBadgeVariant = (lvl: string): BadgeVariant => {
    switch (lvl?.toUpperCase()) {
      case 'CRITICAL':
        return 'critical';
      case 'HIGH':
        return 'high';
      case 'MODERATE':
      case 'MEDIUM':
        return 'moderate';
      case 'LOW':
        return 'low';
      default:
        return 'neutral';
    }
  };

  // Other candidate runs for the same repository to compare against
  const eligibleBaseRuns = runs.filter(
    (r) => r.run_id !== selectedRunId && r.repository_id === runSummary?.repository_id
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <History className="w-6 h-6 text-emerald-400" />
            Analysis Run History
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Historical audit records of multi-agent evaluations with deterministic risk scores, telemetry, and before/after comparisons.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          onClick={fetchRuns}
        >
          Refresh Runs
        </Button>
      </div>

      {/* Runs Table or Empty State */}
      {runs.length === 0 && !loading ? (
        <Card className="border-dashed border-slate-800/90 py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
            <History className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-white">No Stored Historical Runs</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            Runs triggered from the Analyze pipeline or via CLI will be recorded here with complete audit trails.
          </p>
        </Card>
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-mono">
                  <th className="py-3 px-4">Run ID & Target</th>
                  <th className="py-3 px-4">Deterministic Risk</th>
                  <th className="py-3 px-4">Findings Breakdown</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Analyzed At</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {runs.map((r) => (
                  <tr
                    key={r.run_id}
                    className="hover:bg-slate-900/40 transition-colors group cursor-pointer"
                    onClick={() => openRunDetail(r.run_id, 'details')}
                  >
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                        {r.run_id}
                      </div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                        <span>{r.repository_name || r.repository_id}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-500">{r.branch}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-500">{r.commit_sha?.substring(0, 7)}</span>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-white">
                          {r.risk_score}
                          <span className="text-[10px] text-slate-500 font-normal">/100</span>
                        </span>
                        <Badge variant={getRiskLevelBadgeVariant(r.risk_level)} size="sm">
                          {r.risk_level}
                        </Badge>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                          {r.findings_count} total
                        </span>
                        <span className="text-emerald-400 text-[11px]">
                          {r.validated_count} validated
                        </span>
                        {r.needs_review_count > 0 && (
                          <span className="text-amber-400 text-[11px]">
                            {r.needs_review_count} review
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>{r.duration_seconds}s</span>
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-400">
                      {new Date(r.analyzed_at).toLocaleString()}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<GitCompare className="w-3.5 h-3.5 text-indigo-400" />}
                          onClick={(e) => {
                            e.stopPropagation();
                            openRunDetail(r.run_id, 'compare');
                          }}
                        >
                          Compare
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Eye className="w-3.5 h-3.5" />}
                          onClick={(e) => {
                            e.stopPropagation();
                            openRunDetail(r.run_id, 'details');
                          }}
                        >
                          Inspect
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Run Detail & Comparison Modal */}
      {selectedRunId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-emerald-950/60 border border-emerald-800/80 flex items-center justify-center text-emerald-400">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-white font-mono">{selectedRunId}</h2>
                    {runSummary && (
                      <Badge variant={getRiskLevelBadgeVariant(runSummary.risk_level)} size="sm">
                        {runSummary.risk_level} RISK
                      </Badge>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">
                    {runSummary?.repository_name} ({runSummary?.repository_id})
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  icon={<FileText className="w-3.5 h-3.5" />}
                  onClick={() => window.open(`/api/v1/runs/${selectedRunId}/report?format=html`, '_blank')}
                >
                  HTML Report
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<Download className="w-3.5 h-3.5" />}
                  onClick={() => window.open(`/api/v1/runs/${selectedRunId}/report?format=markdown`, '_blank')}
                >
                  Markdown
                </Button>
                <button
                  onClick={() => setSelectedRunId(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-2"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Navigation Tabs (Details vs Compare) */}
            <div className="flex border-b border-slate-800 bg-slate-950 px-6 font-mono text-xs">
              <button
                onClick={() => setModalTab('details')}
                className={`py-3 px-4 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                  modalTab === 'details'
                    ? 'border-emerald-400 text-emerald-400 bg-emerald-950/20'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                Telemetry & Score
              </button>
              <button
                onClick={() => {
                  setModalTab('compare');
                  if (!comparison && selectedRunId) {
                    fetchComparisonData(selectedRunId);
                  }
                }}
                className={`py-3 px-4 font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                  modalTab === 'compare'
                    ? 'border-indigo-400 text-indigo-400 bg-indigo-950/20'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" />
                Before / After Comparison
                {comparison && comparison.has_baseline && (
                  <span
                    className={`ml-1 text-[10px] px-1.5 py-0.2 rounded font-bold ${
                      (comparison.score_delta ?? 0) < 0
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/80'
                        : (comparison.score_delta ?? 0) > 0
                        ? 'bg-rose-950 text-rose-400 border border-rose-800/80'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {(comparison.score_delta ?? 0) > 0 ? `+${comparison.score_delta}` : comparison.score_delta}
                  </span>
                )}
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {detailLoading ? (
                <div className="py-16 text-center">
                  <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
                  <p className="text-xs text-slate-400 font-mono">Loading telemetry and audit data...</p>
                </div>
              ) : modalTab === 'details' ? (
                <>
                  {/* Risk Engine Score Card */}
                  {runSummary && (
                    <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
                        <div>
                          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                            Deterministic Risk Score
                            <button
                              onClick={() => setShowFormulaModal(true)}
                              className="text-slate-500 hover:text-slate-300"
                              title="Formula Explainability"
                            >
                              <HelpCircle className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          <div className="text-3xl font-bold font-mono text-white mt-1 flex items-baseline gap-2">
                            <span>{runSummary.risk_score}</span>
                            <span className="text-sm font-normal text-slate-500">/ 100</span>
                            <span className="text-xs font-mono text-slate-400 ml-2">
                              (Raw: {runSummary.score_breakdown?.raw_score} pts)
                            </span>
                          </div>
                        </div>

                        {/* Deduplication Summary Badges */}
                        {runSummary.dedup_summary && (
                          <div className="flex items-center gap-2 font-mono text-xs">
                            <div className="p-2 rounded bg-slate-900 border border-slate-800 text-center">
                              <div className="text-slate-400 text-[10px]">Total Detected</div>
                              <div className="text-white font-semibold">{runSummary.dedup_summary.input_count}</div>
                            </div>
                            <div className="p-2 rounded bg-slate-900 border border-slate-800 text-center">
                              <div className="text-emerald-400 text-[10px]">Canonical</div>
                              <div className="text-emerald-400 font-semibold">{runSummary.dedup_summary.canonical_count}</div>
                            </div>
                            <div className="p-2 rounded bg-slate-900 border border-slate-800 text-center">
                              <div className="text-amber-400 text-[10px]">Duplicates Merged</div>
                              <div className="text-amber-400 font-semibold">{runSummary.dedup_summary.duplicate_count}</div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Formula & Contributors */}
                      <div className="mt-4 space-y-3 font-mono text-xs">
                        <div className="text-slate-300 font-semibold">Active Score Contributors:</div>
                        <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                          {runSummary.score_breakdown?.contributors?.map((c) => (
                            <div
                              key={c.finding_id}
                              className="p-2.5 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs"
                            >
                              <div className="flex items-center gap-2 truncate">
                                <Badge variant={getRiskLevelBadgeVariant(c.severity)} size="sm">
                                  {c.severity}
                                </Badge>
                                <span className="font-semibold text-slate-200 truncate">{c.title}</span>
                                <span className="text-slate-500 text-[11px] truncate">({c.file_path})</span>
                              </div>
                              <span className="text-emerald-400 font-bold shrink-0 ml-2">
                                +{c.points} pts
                              </span>
                            </div>
                          ))}
                        </div>

                        {/* Excluded Findings */}
                        {runSummary.score_breakdown?.excluded_findings?.length > 0 && (
                          <div className="pt-2">
                            <div className="text-slate-400 text-[11px] mb-1">
                              Excluded from Score Calculation ({runSummary.score_breakdown.excluded_findings.length} findings):
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {runSummary.score_breakdown.excluded_findings.map((ef) => (
                                <span
                                  key={ef.finding_id}
                                  className="px-2 py-0.5 rounded bg-slate-900 text-slate-500 border border-slate-800 text-[10px]"
                                  title={ef.reason}
                                >
                                  {ef.finding_id}: {ef.reason}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Agent Activity Telemetry */}
                  <div>
                    <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-emerald-400" />
                      Agent Execution Telemetry
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
                      {agentTelemetry.map((agent) => (
                        <div
                          key={agent.agent_name}
                          className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-200 capitalize">
                              {agent.agent_name.replace('_', ' ')}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                              {agent.status}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center justify-between">
                            <span>Duration:</span>
                            <span className="text-white">{agent.duration_seconds}s</span>
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center justify-between">
                            <span>Findings:</span>
                            <span className="text-emerald-400 font-bold">{agent.findings_count}</span>
                          </div>
                          {agent.tools_called?.length > 0 && (
                            <div className="text-[10px] text-slate-500 truncate" title={agent.tools_called.join(', ')}>
                              Tools: {agent.tools_called.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  {runSummary && runSummary.recommendations?.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        Remediation Action Plan
                      </h3>
                      <div className="space-y-2">
                        {runSummary.recommendations.map((rec, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5"
                          >
                            <span className="text-emerald-400 font-mono font-bold shrink-0">{idx + 1}.</span>
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Before / After Comparison Tab (Steps 13 & 14) */
                <div className="space-y-6">
                  {/* Baseline Selection Control */}
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold text-slate-200">Comparison Baseline</div>
                      <div className="text-[11px] text-slate-400">
                        Compare current run against immediate previous run or pick a historical baseline.
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <select
                        value={selectedBaseRunId}
                        onChange={(e) => {
                          const val = e.target.value;
                          setSelectedBaseRunId(val);
                          if (selectedRunId) {
                            fetchComparisonData(selectedRunId, val);
                          }
                        }}
                        className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="">Auto (Immediate Prior Run)</option>
                        {eligibleBaseRuns.map((r) => (
                          <option key={r.run_id} value={r.run_id}>
                            {r.run_id} ({r.risk_score} pts • {new Date(r.analyzed_at).toLocaleDateString()})
                          </option>
                        ))}
                      </select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (selectedRunId) fetchComparisonData(selectedRunId, selectedBaseRunId);
                        }}
                        icon={<RefreshCw className={`w-3.5 h-3.5 ${compareLoading ? 'animate-spin' : ''}`} />}
                      >
                        Compare
                      </Button>
                    </div>
                  </div>

                  {compareLoading ? (
                    <div className="py-16 text-center">
                      <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
                      <p className="text-xs text-slate-400 font-mono">Computing finding fingerprints and delta...</p>
                    </div>
                  ) : !comparison?.has_baseline ? (
                    <Card className="border-dashed border-slate-800 py-12 text-center">
                      <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
                        <History className="w-6 h-6" />
                      </div>
                      <h3 className="text-sm font-semibold text-white">No Previous Analysis Available</h3>
                      <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-2">
                        This run represents the initial baseline for repository <span className="text-slate-200 font-mono font-semibold">{comparison?.repository_name}</span>.
                      </p>
                      <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                        Subsequent analyses on this repository will automatically calculate score improvements, newly introduced vulnerabilities, and resolved findings.
                      </p>
                    </Card>
                  ) : (
                    <>
                      {/* Before / After Top Score Comparison Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* BEFORE CARD */}
                        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 relative">
                          <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                              BEFORE (Baseline)
                            </span>
                            <span className="text-[10px] font-mono text-slate-500">{comparison.base_run_id}</span>
                          </div>
                          <div className="mt-3 flex items-baseline justify-between">
                            <div>
                              <div className="text-3xl font-extrabold font-mono text-white">
                                {comparison.base_score}
                                <span className="text-xs text-slate-500 font-normal ml-1">/ 100</span>
                              </div>
                              <div className="text-[11px] text-slate-400 mt-1">
                                {comparison.base_findings_count} finding(s) detected
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* AFTER CARD */}
                        <div className="p-4 rounded-xl bg-slate-950 border border-indigo-900/50 relative">
                          <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                            <span className="text-[11px] font-mono uppercase tracking-wider text-indigo-400 font-bold">
                              AFTER (Current Run)
                            </span>
                            <span className="text-[10px] font-mono text-slate-500">{comparison.target_run_id}</span>
                          </div>
                          <div className="mt-3 flex items-baseline justify-between">
                            <div>
                              <div className="text-3xl font-extrabold font-mono text-white">
                                {comparison.target_score}
                                <span className="text-xs text-slate-500 font-normal ml-1">/ 100</span>
                              </div>
                              <div className="text-[11px] text-slate-400 mt-1">
                                {comparison.target_findings_count} finding(s) detected
                              </div>
                            </div>

                            {/* Score Delta Badge */}
                            <div>
                              {typeof comparison.score_delta === 'number' && (
                                <div
                                  className={`px-3 py-1.5 rounded-lg border font-mono text-xs font-bold flex items-center gap-1.5 ${
                                    comparison.score_delta < 0
                                      ? 'bg-emerald-950/80 border-emerald-800 text-emerald-400'
                                      : comparison.score_delta > 0
                                      ? 'bg-rose-950/80 border-rose-800 text-rose-400'
                                      : 'bg-slate-900 border-slate-800 text-slate-400'
                                  }`}
                                >
                                  {comparison.score_delta < 0 ? (
                                    <>
                                      <ArrowDownRight className="w-4 h-4" />
                                      {comparison.score_delta} pts (IMPROVED)
                                    </>
                                  ) : comparison.score_delta > 0 ? (
                                    <>
                                      <ArrowUpRight className="w-4 h-4" />
                                      +{comparison.score_delta} pts (DEGRADED)
                                    </>
                                  ) : (
                                    <>
                                      <Minus className="w-4 h-4" />
                                      0.0 pts (UNCHANGED)
                                    </>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* 4-Column Transition Counters */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                        <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800/60 text-center">
                          <div className="text-emerald-400 text-[10px] font-semibold uppercase">Resolved</div>
                          <div className="text-2xl font-bold text-emerald-400 mt-0.5">{comparison.resolved_count}</div>
                          <div className="text-[10px] text-emerald-500/80 mt-0.5">Fixed since baseline</div>
                        </div>
                        <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-800/60 text-center">
                          <div className="text-rose-400 text-[10px] font-semibold uppercase">New</div>
                          <div className="text-2xl font-bold text-rose-400 mt-0.5">{comparison.new_count}</div>
                          <div className="text-[10px] text-rose-500/80 mt-0.5">Newly introduced</div>
                        </div>
                        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
                          <div className="text-slate-400 text-[10px] font-semibold uppercase">Persistent</div>
                          <div className="text-2xl font-bold text-slate-300 mt-0.5">{comparison.persistent_count}</div>
                          <div className="text-[10px] text-slate-500 mt-0.5">Still present</div>
                        </div>
                        <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-800/60 text-center">
                          <div className="text-indigo-400 text-[10px] font-semibold uppercase">Changed</div>
                          <div className="text-2xl font-bold text-indigo-400 mt-0.5">{comparison.changed_count}</div>
                          <div className="text-[10px] text-indigo-500/80 mt-0.5">Severity shifted</div>
                        </div>
                      </div>

                      {/* Resolved Findings List */}
                      {comparison.resolved_findings.length > 0 && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                            <CheckCircle2 className="w-4 h-4" />
                            Resolved Findings ({comparison.resolved_findings.length})
                          </div>
                          <div className="space-y-1.5 font-mono text-xs">
                            {comparison.resolved_findings.map((rf) => (
                              <div
                                key={rf.fingerprint}
                                className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-900/60 flex items-center justify-between text-xs"
                              >
                                <div className="flex items-center gap-2 truncate">
                                  <Badge variant="low" size="sm">
                                    RESOLVED
                                  </Badge>
                                  <span className="text-slate-200 line-through truncate">{rf.title}</span>
                                  <span className="text-slate-500 text-[11px] truncate">
                                    ({rf.file_path}{rf.line_start ? `:${rf.line_start}` : ''})
                                  </span>
                                </div>
                                <span className="text-emerald-400 font-bold shrink-0 ml-2">
                                  -{rf.score_contribution} pts
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* New Findings List */}
                      {comparison.new_findings.length > 0 && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs font-semibold text-rose-400">
                            <AlertTriangle className="w-4 h-4" />
                            Newly Introduced Findings ({comparison.new_findings.length})
                          </div>
                          <div className="space-y-1.5 font-mono text-xs">
                            {comparison.new_findings.map((nf) => (
                              <div
                                key={nf.fingerprint}
                                className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/60 flex items-center justify-between text-xs"
                              >
                                <div className="flex items-center gap-2 truncate">
                                  <Badge variant={getRiskLevelBadgeVariant(nf.severity)} size="sm">
                                    {nf.severity}
                                  </Badge>
                                  <span className="text-slate-200 font-semibold truncate">{nf.title}</span>
                                  <span className="text-slate-500 text-[11px] truncate">
                                    ({nf.file_path}{nf.line_start ? `:${nf.line_start}` : ''})
                                  </span>
                                </div>
                                <span className="text-rose-400 font-bold shrink-0 ml-2">
                                  +{nf.score_contribution} pts
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Persistent Findings List */}
                      {comparison.persistent_findings.length > 0 && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
                            <FileCode className="w-4 h-4" />
                            Persistent Unresolved Findings ({comparison.persistent_findings.length})
                          </div>
                          <div className="space-y-1.5 font-mono text-xs max-h-40 overflow-y-auto pr-1">
                            {comparison.persistent_findings.map((pf) => (
                              <div
                                key={pf.fingerprint}
                                className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                              >
                                <div className="flex items-center gap-2 truncate">
                                  <Badge variant={getRiskLevelBadgeVariant(pf.severity)} size="sm">
                                    {pf.severity}
                                  </Badge>
                                  <span className="text-slate-300 truncate">{pf.title}</span>
                                  <span className="text-slate-500 text-[11px] truncate">
                                    ({pf.file_path}{pf.line_start ? `:${pf.line_start}` : ''})
                                  </span>
                                </div>
                                <span className="text-slate-400 font-bold shrink-0 ml-2">
                                  +{pf.score_contribution} pts
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Formula Modal */}
      {showFormulaModal && (
        <div className="fixed inset-0 z-60 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-emerald-400" />
                Deterministic Risk Formula
              </h3>
              <button
                onClick={() => setShowFormulaModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-300 font-mono">
              <p>
                DeploySafe computes risk scores through a strictly deterministic algorithm governed by
                project-defined severity weights and confidence multipliers:
              </p>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-emerald-300">
                Score = min(100, round(∑ (SeverityWeight × ConfidenceMultiplier × ImpactMultiplier)))
              </div>

              <div className="space-y-1 text-slate-400">
                <div>• CRITICAL = 35 pts (High=1.0, Med=0.8, Low=0.6)</div>
                <div>• HIGH = 25 pts (High=1.0, Med=0.8, Low=0.6)</div>
                <div>• MEDIUM = 15 pts (High=1.0, Med=0.8, Low=0.6)</div>
                <div>• LOW = 7 pts (High=1.0, Med=0.8, Low=0.6)</div>
              </div>

              <div className="pt-2 border-t border-slate-800 text-slate-400 text-[11px]">
                Note: Inactive, duplicate, or rejected findings contribute 0 points.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
