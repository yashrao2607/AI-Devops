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
  Eye
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

export const Runs: React.FC = () => {
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runSummary, setRunSummary] = useState<RunSummaryData | null>(null);
  const [agentTelemetry, setAgentTelemetry] = useState<AgentTelemetry[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showFormulaModal, setShowFormulaModal] = useState(false);

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

  const openRunDetail = async (runId: string) => {
    setSelectedRunId(runId);
    setDetailLoading(true);
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
            Historical audit records of multi-agent evaluations with deterministic risk scores and telemetry.
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
            Runs triggered from the Analyze pipeline or via API will be recorded here with complete audit trails.
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
                    onClick={() => openRunDetail(r.run_id)}
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
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Eye className="w-3.5 h-3.5" />}
                        onClick={(e) => {
                          e.stopPropagation();
                          openRunDetail(r.run_id);
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
        </Card>
      )}

      {/* Run Detail Modal / Drawer */}
      {selectedRunId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
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

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {detailLoading ? (
                <div className="py-16 text-center">
                  <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
                  <p className="text-xs text-slate-400 font-mono">Loading telemetry and audit data...</p>
                </div>
              ) : (
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

                  {/* Agent Activity Telemetry (Step 21 & Step 22) */}
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
