import React, { useState } from 'react';
import {
  Play,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Layers,
  Copy,
  Check,
  X,
  Code2,
  Cpu,
  PackageCheck,
  Wrench,
  BookOpen,
  Filter
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Button } from '../components/common/Button.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';

interface EvidenceItem {
  evidence_type: string;
  file_path: string;
  line_start?: number | null;
  line_end?: number | null;
  snippet: string;
  source: string;
  source_tool?: string | null;
  repository_id: string;
  commit_sha?: string | null;
}

interface Finding {
  id: string;
  category: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  summary: string;
  impact: string;
  recommendation: string;
  repository_id: string;
  commit_sha?: string | null;
  file_path: string;
  line_start?: number | null;
  line_end?: number | null;
  evidence: string;
  evidence_items?: EvidenceItem[];
  source: string;
  agent: string;
  status: 'NEW' | 'VALIDATED' | 'NEEDS_REVIEW' | 'DUPLICATE' | 'REJECTED' | 'INSUFFICIENT_EVIDENCE';
  tool_name?: string | null;
  rule_id?: string | null;
  retrieval_context?: string | null;
  related_files?: string[];
  critic_notes?: string | null;
}

interface AgentState {
  agent_name: string;
  status: 'WAITING' | 'PLANNING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds: number;
  findings_count: number;
  tools_called: string[];
  error?: string | null;
}

interface AnalysisReport {
  run_id: string;
  repository_id: string;
  repository_name: string;
  commit_sha?: string | null;
  branch?: string;
  analyzed_at: string;
  duration_seconds: number;
  status: 'COMPLETED' | 'PARTIAL' | 'FAILED';
  agents_executed: string[];
  tools_used: string[];
  risk_score?: number;
  risk_level?: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  score_breakdown?: any;
  dedup_summary?: any;
  findings: Finding[];
  validated_findings: Finding[];
  needs_review_findings: Finding[];
  rejected_findings: Finding[];
  finding_counts_by_severity: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  summary: string;
  recommendations: string[];
}

export const Analyze: React.FC = () => {
  const [repoPath, setRepoPath] = useState('demo-repos/deploysafe-analysis-demo');
  const [branch, setBranch] = useState('main');
  const [commitSha, setCommitSha] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [agentStates, setAgentStates] = useState<Record<string, AgentState>>({});
  const [runStatus, setRunStatus] = useState<string>('IDLE');
  const [error, setError] = useState<string | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Pre-seed demo repository metadata
  const handleSelectDemoPreset = () => {
    setRepoPath('demo-repos/deploysafe-analysis-demo');
    setBranch('main');
    setCommitSha('HEAD');
  };

  const getSeverityBadgeVariant = (sev: string): BadgeVariant => {
    switch (sev.toUpperCase()) {
      case 'CRITICAL':
        return 'critical';
      case 'HIGH':
        return 'high';
      case 'MEDIUM':
      case 'MODERATE':
        return 'moderate';
      case 'LOW':
        return 'low';
      default:
        return 'neutral';
    }
  };

  const getStatusBadgeVariant = (st: string): BadgeVariant => {
    switch (st.toUpperCase()) {
      case 'VALIDATED':
        return 'success';
      case 'NEEDS_REVIEW':
        return 'moderate';
      case 'DUPLICATE':
        return 'neutral';
      case 'REJECTED':
      case 'INSUFFICIENT_EVIDENCE':
        return 'critical';
      default:
        return 'info';
    }
  };

  const getAgentFriendlyName = (name: string): string => {
    const map: Record<string, string> = {
      code_analysis: 'Code Analysis Agent',
      dependency_analysis: 'Dependency Agent',
      configuration_analysis: 'Configuration Agent',
      test_analysis: 'Test Agent',
      rag_analysis: 'Documentation / RAG Agent',
      security_analysis: 'Security Analysis Agent',
      critic: 'Critic Validation Agent',
      report: 'Report Synthesis Agent',
      orchestrator: 'Orchestrator'
    };
    return map[name] || name;
  };

  const getAgentIcon = (name: string) => {
    switch (name) {
      case 'code_analysis':
        return <Code2 className="w-4 h-4 text-cyan-400" />;
      case 'dependency_analysis':
        return <PackageCheck className="w-4 h-4 text-amber-400" />;
      case 'configuration_analysis':
        return <Wrench className="w-4 h-4 text-blue-400" />;
      case 'test_analysis':
        return <CheckCircle2 className="w-4 h-4 text-purple-400" />;
      case 'rag_analysis':
        return <BookOpen className="w-4 h-4 text-emerald-400" />;
      case 'security_analysis':
        return <ShieldAlert className="w-4 h-4 text-rose-400" />;
      case 'critic':
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
      default:
        return <Cpu className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    setError(null);
    setSelectedFinding(null);
    setRunStatus('PREPARING');

    try {
      // Step 1: Ensure demo repository is ingested and indexed if pointing to demo-repos
      const targetRepoId = repoPath.trim().replace(/^demo-repos\//, '');

      // Attempt ingestion if not already registered
      try {
        await fetch('/api/v1/repositories/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_type: 'local',
            target: repoPath.trim(),
            repository_id: targetRepoId,
            branch: branch || 'main'
          })
        });

        // Trigger indexing to ensure RAG has embeddings
        await fetch(`/api/v1/repositories/${encodeURIComponent(targetRepoId)}/index`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (ingestErr) {
        // Fallback: Continue directly to analysis run
        console.warn('Repository pre-ingest notice:', ingestErr);
      }

      setRunStatus('RUNNING_AGENTS');

      // Step 2: Trigger Multi-Agent Deployment Analysis
      const runRes = await fetch('/api/v1/analysis/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repository_id: targetRepoId,
          branch: branch || 'main',
          options: { commit_sha: commitSha || undefined }
        })
      });

      if (!runRes.ok) {
        const errData = await runRes.json();
        throw new Error(errData.detail || `Analysis trigger returned HTTP ${runRes.status}`);
      }

      const repData: AnalysisReport = await runRes.json();
      setActiveRunId(repData.run_id);
      setReport(repData);
      setRunStatus(repData.status);

      // Fetch live agent states
      const agentsRes = await fetch(`/api/v1/analysis/${repData.run_id}/agents`);
      if (agentsRes.ok) {
        const agentList: AgentState[] = await agentsRes.json();
        const map: Record<string, AgentState> = {};
        agentList.forEach((a) => {
          map[a.agent_name] = a;
        });
        setAgentStates(map);
      }
    } catch (err: any) {
      setError(err.message || 'Multi-agent analysis execution failed.');
      setRunStatus('FAILED');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopySnippet = (snippet: string) => {
    navigator.clipboard.writeText(snippet);
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  // Filtered findings
  const filteredFindings = report?.findings.filter((f) => {
    const matchSev = severityFilter === 'ALL' || f.severity === severityFilter;
    const matchStatus = statusFilter === 'ALL' || f.status === statusFilter;
    return matchSev && matchStatus;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Multi-Agent Deployment Analysis
            <span className="text-xs px-2.5 py-0.5 rounded font-mono font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
              Phase 3 Live
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Specialized autonomous agents collaborating with deterministic tools, RAG context, and Critic verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectDemoPreset}
            className="text-xs font-mono"
          >
            Load Demo Repo
          </Button>
          <Button
            variant="primary"
            size="md"
            icon={<Play className="w-4 h-4 fill-current" />}
            isLoading={isAnalyzing}
            onClick={handleRunAnalysis}
          >
            {isAnalyzing ? 'Executing Agent Flow...' : 'Run Deployment Analysis'}
          </Button>
        </div>
      </div>

      {/* Target Repository Input & Scope Card */}
      <Card title="Repository & Analysis Scope" subtitle="Configure target repository path, branch, and execution scope.">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-mono text-slate-400 block mb-1.5">Repository Path or ID</label>
            <input
              type="text"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              placeholder="e.g. demo-repos/deploysafe-analysis-demo"
              className="w-full rounded-md bg-dark-950 border border-slate-800 px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs font-mono text-slate-400 block mb-1.5">Target Branch</label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full rounded-md bg-dark-950 border border-slate-800 px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs font-mono text-slate-400 block mb-1.5">Commit SHA (Optional)</label>
            <input
              type="text"
              value={commitSha}
              onChange={(e) => setCommitSha(e.target.value)}
              placeholder="e.g. 5e6cc9a"
              className="w-full rounded-md bg-dark-950 border border-slate-800 px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              Scope: Code, Dependencies, Config, Tests, RAG, Secrets
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              Critic Review: Enforced
            </span>
          </div>
          <div className="flex items-center gap-3 font-mono">
            {runStatus !== 'IDLE' && (
              <span className="text-slate-400">
                Flow Status: <span className="text-emerald-400 font-semibold">{runStatus}</span>
              </span>
            )}
            {activeRunId && (
              <span className="text-slate-400">
                Active Run ID: <span className="text-emerald-400 font-semibold">{activeRunId}</span>
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">
            <div className="font-semibold text-rose-200">Analysis Execution Error</div>
            <div className="mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* Live Agent Activity Timeline (Step 26) */}
      <Card
        title="Autonomous Agent Activity & Telemetry"
        subtitle="Real-time execution status, runtime duration, invoked tools, and individual agent discoveries."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            'code_analysis',
            'dependency_analysis',
            'configuration_analysis',
            'test_analysis',
            'rag_analysis',
            'security_analysis',
            'critic',
            'report'
          ].map((agentKey) => {
            const st = agentStates[agentKey];
            const isCompleted = st?.status === 'COMPLETED';
            const isRunning = st?.status === 'RUNNING' || (isAnalyzing && !st);
            const isFailed = st?.status === 'FAILED';

            return (
              <div
                key={agentKey}
                className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getAgentIcon(agentKey)}
                    <span className="text-xs font-semibold text-slate-200">
                      {getAgentFriendlyName(agentKey)}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                      isCompleted
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                        : isRunning
                        ? 'bg-blue-950 text-blue-400 border border-blue-800/60 animate-pulse'
                        : isFailed
                        ? 'bg-rose-950 text-rose-400 border border-rose-800/60'
                        : 'bg-slate-950 text-slate-500 border border-slate-800'
                    }`}
                  >
                    {st?.status || (isAnalyzing ? 'WAITING' : 'IDLE')}
                  </span>
                </div>

                <div className="space-y-1 text-[11px] font-mono text-slate-400">
                  <div className="flex items-center justify-between">
                    <span>Duration:</span>
                    <span className="text-slate-200">
                      {st?.duration_seconds !== undefined ? `${st.duration_seconds}s` : '--'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Findings:</span>
                    <span className="text-emerald-400 font-semibold">
                      {st?.findings_count !== undefined ? st.findings_count : '--'}
                    </span>
                  </div>
                  {st?.tools_called && st.tools_called.length > 0 && (
                    <div className="pt-1 text-[10px] text-slate-500 truncate" title={st.tools_called.join(', ')}>
                      Tools: {st.tools_called.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Phase 4 Deterministic Risk Score Banner */}
      {report && report.risk_score !== undefined && (
        <Card className="border-emerald-500/30 bg-slate-950/80">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center font-mono">
                <span className="text-xl font-bold text-white">{report.risk_score}</span>
                <span className="text-[9px] text-slate-400">/ 100</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white font-mono">
                    Deterministic Risk Score
                  </h3>
                  <Badge
                    variant={
                      report.risk_level === 'CRITICAL'
                        ? 'critical'
                        : report.risk_level === 'HIGH'
                        ? 'high'
                        : report.risk_level === 'MODERATE'
                        ? 'moderate'
                        : 'low'
                    }
                    size="sm"
                  >
                    {report.risk_level} RISK
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Audited by Critic Agent & computed deterministically via Phase 4 RiskEngine.
                </p>
              </div>
            </div>

            {/* Deduplication & Export Shortcuts */}
            <div className="flex items-center gap-3 font-mono text-xs">
              {report.dedup_summary && (
                <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
                  <span className="text-emerald-400 font-semibold">
                    {report.dedup_summary.canonical_count}
                  </span>{' '}
                  canonical findings ({report.dedup_summary.duplicate_count} merged duplicates)
                </div>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(`/api/v1/runs/${report.run_id}/report?format=html`, '_blank')}
              >
                Export Report
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Analysis Severity Summary Cards (Step 21 & Step 27) */}
      {report && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-red-900/40 bg-red-950/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-red-400 uppercase tracking-wider">Critical Severity</span>
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
            </div>
            <div className="text-3xl font-bold font-mono text-red-400 mt-2">
              {report.finding_counts_by_severity.CRITICAL}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">High deployment risk blockers</div>
          </Card>

          <Card className="border-orange-900/40 bg-orange-950/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-orange-400 uppercase tracking-wider">High Severity</span>
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
            </div>
            <div className="text-3xl font-bold font-mono text-orange-400 mt-2">
              {report.finding_counts_by_severity.HIGH}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Significant drift / vulnerability</div>
          </Card>

          <Card className="border-yellow-900/40 bg-yellow-950/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-yellow-400 uppercase tracking-wider">Medium Severity</span>
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span>
            </div>
            <div className="text-3xl font-bold font-mono text-yellow-400 mt-2">
              {report.finding_counts_by_severity.MEDIUM}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Configuration drift warnings</div>
          </Card>

          <Card className="border-emerald-900/40 bg-emerald-950/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider">Critic Validated</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-3xl font-bold font-mono text-emerald-400 mt-2">
              {report.validated_findings.length}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Grounded in repo evidence</div>
          </Card>
        </div>
      )}

      {/* Findings Table Section (Step 27) */}
      {report && (
        <Card
          title={`Identified Findings (${report.findings.length} Total)`}
          subtitle="Deployment hazards detected by specialized agents and audited by the Critic Agent."
        >
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-mono text-slate-400">Severity:</span>
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSeverityFilter(sev)}
                  className={`text-xs px-2 py-0.5 rounded font-mono transition-colors ${
                    severityFilter === sev
                      ? 'bg-slate-700 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400">Status:</span>
              {['ALL', 'VALIDATED', 'NEEDS_REVIEW', 'DUPLICATE', 'REJECTED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`text-xs px-2 py-0.5 rounded font-mono transition-colors ${
                    statusFilter === st
                      ? 'bg-slate-700 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Table */}
          {filteredFindings.length === 0 ? (
            <div className="text-center py-8 text-xs font-mono text-slate-500">
              No findings match the selected filters.
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
                    <th className="py-2.5 px-3">Critic Status</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredFindings.map((finding) => (
                    <tr
                      key={finding.id}
                      onClick={() => setSelectedFinding(finding)}
                      className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                        selectedFinding?.id === finding.id ? 'bg-slate-800/60' : ''
                      }`}
                    >
                      <td className="py-3 px-3">
                        <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                          {finding.severity}
                        </Badge>
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-200">{finding.title}</div>
                        <div className="text-[11px] font-mono text-slate-400 mt-0.5 flex items-center gap-1">
                          <FileCode className="w-3 h-3 text-cyan-400" />
                          <span>{finding.file_path}</span>
                          {finding.line_start !== null && finding.line_start !== undefined && (
                            <span className="text-cyan-300">
                              :L{finding.line_start}
                              {finding.line_end ? `-${finding.line_end}` : ''}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-slate-800 text-slate-300 border border-slate-700">
                          {finding.category}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-mono text-slate-300 text-xs flex items-center gap-1.5">
                          {getAgentIcon(finding.agent.toLowerCase().replace('agent', '_analysis'))}
                          {finding.agent}
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant={getStatusBadgeVariant(finding.status)}>
                          {finding.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedFinding(finding);
                          }}
                        >
                          View Evidence
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Finding Detail & Evidence Viewer Modal / Drawer (Step 28 & 29) */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-start justify-between sticky top-0 bg-slate-900/95 backdrop-blur z-10">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <Badge variant={getSeverityBadgeVariant(selectedFinding.severity)}>
                    {selectedFinding.severity}
                  </Badge>
                  <Badge variant={getStatusBadgeVariant(selectedFinding.status)}>
                    {selectedFinding.status}
                  </Badge>
                  <span className="text-xs font-mono text-slate-400">
                    ID: {selectedFinding.id}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white tracking-tight">
                  {selectedFinding.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Summary & Impact */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3.5 rounded-lg bg-dark-950 border border-slate-800">
                  <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
                    Risk Mechanism & Summary
                  </div>
                  <div className="text-xs text-slate-300 leading-relaxed">
                    {selectedFinding.summary}
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/40">
                  <div className="text-xs font-mono text-rose-400 uppercase tracking-wider mb-1">
                    Deployment Impact
                  </div>
                  <div className="text-xs text-rose-200/90 leading-relaxed">
                    {selectedFinding.impact}
                  </div>
                </div>
              </div>

              {/* Recommendation */}
              <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-900/40">
                <div className="text-xs font-mono text-emerald-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Actionable Recommendation
                </div>
                <div className="text-xs text-emerald-200 leading-relaxed">
                  {selectedFinding.recommendation}
                </div>
              </div>

              {/* Agent Attribution & Critic Audit */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Detected By Agent:</span>
                  <div className="flex items-center gap-2 text-slate-200 font-semibold">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    {selectedFinding.agent} ({selectedFinding.source})
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Critic Agent Audit:</span>
                  <div className="text-slate-200">
                    {selectedFinding.critic_notes || 'Validated against repository ground truth.'}
                  </div>
                </div>
              </div>

              {/* Step 29: Concrete Code Evidence Viewer */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-mono font-semibold text-slate-200">
                      {selectedFinding.file_path}
                    </span>
                    {selectedFinding.line_start !== null && selectedFinding.line_start !== undefined && (
                      <span className="text-xs font-mono text-cyan-400">
                        (Lines {selectedFinding.line_start} - {selectedFinding.line_end || selectedFinding.line_start})
                      </span>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    icon={copiedSnippet ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    onClick={() => handleCopySnippet(selectedFinding.evidence)}
                  >
                    {copiedSnippet ? 'Copied' : 'Copy Snippet'}
                  </Button>
                </div>

                <div className="relative rounded-lg bg-dark-950 border border-slate-800 p-4 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                  {selectedFinding.evidence}
                </div>
              </div>

              {/* Structured Evidence Items if available */}
              {selectedFinding.evidence_items && selectedFinding.evidence_items.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                    Structured Evidence Chains ({selectedFinding.evidence_items.length})
                  </div>
                  <div className="space-y-2">
                    {selectedFinding.evidence_items.map((ev, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-slate-950/80 border border-slate-800 text-xs font-mono">
                        <div className="flex items-center justify-between text-slate-400 mb-1">
                          <span className="text-cyan-400">{ev.evidence_type}</span>
                          <span>{ev.file_path}:{ev.line_start || 1}</span>
                        </div>
                        <div className="text-slate-300 text-[11px] truncate">
                          {ev.snippet}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setSelectedFinding(null)}>
                Close Viewer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
