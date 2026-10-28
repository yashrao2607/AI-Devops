import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  FileCode,
  RefreshCw,
  Search,
  X,
  Copy,
  Check,
  Wrench
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';
import { Button } from '../components/common/Button.tsx';

interface PatchPreviewData {
  finding_id: string;
  file_path: string;
  line_start?: number | null;
  line_end?: number | null;
  original_snippet: string;
  proposed_patch: string;
  explanation: string;
  disclaimer: string;
}

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
  impact_level?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
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
  status: 'NEW' | 'VALIDATED' | 'NEEDS_REVIEW' | 'DUPLICATE' | 'REJECTED' | 'INSUFFICIENT_EVIDENCE' | 'DISMISSED';
  tool_name?: string | null;
  rule_id?: string | null;
  retrieval_context?: string | null;
  related_files?: string[];
  critic_notes?: string | null;
  validation_reason?: string | null;
  dedup_group_id?: string | null;
  merged_finding_ids?: string[];
  merged_agents?: string[];
  score_contribution?: number;
}

export const Findings: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [agentFilter, setAgentFilter] = useState<string>('ALL');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [patchData, setPatchData] = useState<PatchPreviewData | null>(null);
  const [patchLoading, setPatchLoading] = useState(false);
  const [showPatch, setShowPatch] = useState(false);

  const fetchPatch = async (findingId: string) => {
    setPatchLoading(true);
    try {
      const res = await fetch(`/api/v1/findings/${findingId}/patch`);
      if (res.ok) {
        const data = await res.json();
        setPatchData(data);
        setShowPatch(true);
      }
    } catch (e) {
      console.error('Failed to load patch preview:', e);
    } finally {
      setPatchLoading(false);
    }
  };

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/findings');
      if (res.ok) {
        const data = await res.json();
        setFindings(data);
      }
    } catch (e) {
      console.error('Error fetching findings:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, []);

  const handleStatusUpdate = async (findingId: string, newStatus: string) => {
    setUpdatingStatus(true);
    try {
      const res = await fetch(`/api/v1/findings/${findingId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          reason: `Manual triage update from Findings Directory to ${newStatus}`
        })
      });

      if (res.ok) {
        const updatedFinding = await res.json();
        setFindings((prev) => prev.map((f) => (f.id === findingId ? updatedFinding : f)));
        if (selectedFinding?.id === findingId) {
          setSelectedFinding(updatedFinding);
        }
      }
    } catch (e) {
      console.error('Failed to update status:', e);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getSeverityBadgeVariant = (sev: string): BadgeVariant => {
    switch (sev?.toUpperCase()) {
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
    switch (st?.toUpperCase()) {
      case 'VALIDATED':
        return 'success';
      case 'NEEDS_REVIEW':
        return 'warning';
      case 'DUPLICATE':
        return 'neutral';
      case 'DISMISSED':
        return 'neutral';
      case 'REJECTED':
      case 'INSUFFICIENT_EVIDENCE':
        return 'critical';
      default:
        return 'info';
    }
  };

  // Distinct agent list
  const availableAgents = Array.from(new Set(findings.map((f) => f.agent).filter(Boolean)));

  // Filter findings
  const filteredFindings = findings.filter((f) => {
    if (severityFilter !== 'ALL' && f.severity !== severityFilter) return false;
    if (statusFilter !== 'ALL' && f.status !== statusFilter) return false;
    if (agentFilter !== 'ALL' && f.agent !== agentFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        f.title.toLowerCase().includes(q) ||
        f.summary.toLowerCase().includes(q) ||
        f.file_path.toLowerCase().includes(q) ||
        f.id.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-amber-400" />
            Findings & Vulnerabilities Directory
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Global catalog of detected deployment hazards, anti-hallucination Critic audits, and risk score contributions.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          onClick={fetchFindings}
        >
          Refresh Findings
        </Button>
      </div>

      {/* Filter Toolbar */}
      <Card noPadding className="p-4 bg-slate-900/40 border-slate-800">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search findings by ID, title, summary, or file path..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/80 font-mono"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
            {/* Severity */}
            <div className="flex items-center gap-1.5 bg-slate-950 px-2 py-1 rounded-lg border border-slate-800">
              <span className="text-slate-500">Sev:</span>
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((s) => (
                <button
                  key={s}
                  onClick={() => setSeverityFilter(s)}
                  className={`px-1.5 py-0.5 rounded text-[11px] transition-colors ${
                    severityFilter === s
                      ? 'bg-slate-700 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            {/* Status */}
            <div className="flex items-center gap-1.5 bg-slate-950 px-2 py-1 rounded-lg border border-slate-800">
              <span className="text-slate-500">Status:</span>
              {['ALL', 'VALIDATED', 'NEEDS_REVIEW', 'DUPLICATE', 'DISMISSED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-1.5 py-0.5 rounded text-[11px] transition-colors ${
                    statusFilter === st
                      ? 'bg-slate-700 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            {/* Agent Select */}
            {availableAgents.length > 0 && (
              <select
                value={agentFilter}
                onChange={(e) => setAgentFilter(e.target.value)}
                className="bg-slate-950 text-slate-300 border border-slate-800 rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Agents</option>
                {availableAgents.map((ag) => (
                  <option key={ag} value={ag}>
                    {ag}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </Card>

      {/* Findings Table */}
      {filteredFindings.length === 0 && !loading ? (
        <Card className="border-dashed border-slate-800/90 py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
          </div>
          <h3 className="text-sm font-semibold text-white">No Matching Findings</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            Try adjusting search terms or clear filters to view discovered findings.
          </p>
        </Card>
      ) : (
        <Card noPadding>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-mono">
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Finding & Location</th>
                  <th className="py-3 px-4">Audited Status</th>
                  <th className="py-3 px-4">Agent Source</th>
                  <th className="py-3 px-4">Risk Contribution</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredFindings.map((f) => (
                  <tr
                    key={f.id}
                    className="hover:bg-slate-900/40 transition-colors group cursor-pointer"
                    onClick={() => setSelectedFinding(f)}
                  >
                    <td className="py-3 px-4">
                      <Badge variant={getSeverityBadgeVariant(f.severity)} size="sm">
                        {f.severity}
                      </Badge>
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                        {f.title}
                      </div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <FileCode className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="font-mono text-slate-300">{f.file_path}</span>
                        {f.line_start && (
                          <span className="text-slate-500 font-mono">
                            :{f.line_start}{f.line_end ? `-${f.line_end}` : ''}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <Badge variant={getStatusBadgeVariant(f.status)} size="sm">
                        {f.status}
                      </Badge>
                    </td>

                    <td className="py-3 px-4 text-slate-300 capitalize">
                      {f.agent}
                      {f.merged_agents && f.merged_agents.length > 0 && (
                        <div className="text-[10px] text-slate-500">
                          +{f.merged_agents.length} merged
                        </div>
                      )}
                    </td>

                    <td className="py-3 px-4 font-bold">
                      {f.status === 'VALIDATED' && (f.score_contribution ?? 0) > 0 ? (
                        <span className="text-emerald-400">+{f.score_contribution} pts</span>
                      ) : (
                        <span className="text-slate-600 font-normal">0 pts (excluded)</span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
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
        </Card>
      )}

      {/* Inspect Finding Modal */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 font-mono">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <Badge variant={getSeverityBadgeVariant(selectedFinding.severity)} size="md">
                  {selectedFinding.severity}
                </Badge>
                <div>
                  <h2 className="text-sm font-bold text-white">{selectedFinding.title}</h2>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    ID: {selectedFinding.id} • Category: {selectedFinding.category}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSelectedFinding(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {/* Status & Score Contribution Banner */}
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div>
                    <span className="text-slate-500 text-[10px] block">AUDIT STATUS</span>
                    <Badge variant={getStatusBadgeVariant(selectedFinding.status)} size="sm">
                      {selectedFinding.status}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">CONFIDENCE</span>
                    <span className="text-white font-semibold">{selectedFinding.confidence}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">CONTRIBUTION</span>
                    <span className="text-emerald-400 font-bold">
                      {selectedFinding.status === 'VALIDATED'
                        ? `+${selectedFinding.score_contribution || 0} pts`
                        : '0 pts (Inactive)'}
                    </span>
                  </div>
                </div>

                {/* Status Triage Controls */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500">Triage:</span>
                  <button
                    disabled={updatingStatus || selectedFinding.status === 'VALIDATED'}
                    onClick={() => handleStatusUpdate(selectedFinding.id, 'VALIDATED')}
                    className="px-2 py-1 rounded bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-[11px] transition-colors disabled:opacity-50"
                  >
                    Validate
                  </button>
                  <button
                    disabled={updatingStatus || selectedFinding.status === 'NEEDS_REVIEW'}
                    onClick={() => handleStatusUpdate(selectedFinding.id, 'NEEDS_REVIEW')}
                    className="px-2 py-1 rounded bg-amber-950/80 hover:bg-amber-900 border border-amber-800 text-amber-300 text-[11px] transition-colors disabled:opacity-50"
                  >
                    Flag Review
                  </button>
                  <button
                    disabled={updatingStatus || selectedFinding.status === 'DISMISSED'}
                    onClick={() => handleStatusUpdate(selectedFinding.id, 'DISMISSED')}
                    className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[11px] transition-colors disabled:opacity-50"
                  >
                    Dismiss
                  </button>
                </div>
              </div>

              {/* What / Summary */}
              <div>
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] block mb-1">
                  What: Analysis Summary
                </span>
                <p className="text-slate-200 leading-relaxed bg-slate-950/50 p-3 rounded border border-slate-800/80">
                  {selectedFinding.summary}
                </p>
              </div>

              {/* Why & Impact */}
              <div>
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] block mb-1">
                  Why This Matters & Deployment Impact
                </span>
                <p className="text-rose-300 leading-relaxed bg-rose-950/20 p-3 rounded border border-rose-900/30">
                  {selectedFinding.impact}
                </p>
              </div>

              {/* Where: File Location & Evidence Snippet */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                    Where: Verified File & Code Evidence
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(selectedFinding.evidence);
                      setCopiedSnippet(true);
                      setTimeout(() => setCopiedSnippet(false), 2000);
                    }}
                    className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-white"
                  >
                    {copiedSnippet ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    {copiedSnippet ? 'Copied' : 'Copy Snippet'}
                  </button>
                </div>

                <div className="rounded-lg bg-slate-950 border border-slate-800 overflow-hidden">
                  <div className="px-3 py-1.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="text-emerald-400 font-bold">{selectedFinding.file_path}</span>
                    <span>
                      {selectedFinding.line_start
                        ? `Lines ${selectedFinding.line_start}–${selectedFinding.line_end || selectedFinding.line_start}`
                        : 'Entire File Context'}
                    </span>
                  </div>
                  <pre className="p-3 text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                    {selectedFinding.evidence || '// No code snippet evidence captured'}
                  </pre>
                </div>
              </div>

              {/* Actionable Remediation */}
              <div>
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] block mb-1">
                  What Should I Do: Actionable Recommendation
                </span>
                <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 leading-relaxed">
                  {selectedFinding.recommendation}
                </div>
              </div>

              {/* Proposed Code Patch (Phase 7 Steps 14 & 15) */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                    Proposed Code Patch (V2 Preview)
                  </span>
                  {!showPatch ? (
                    <button
                      onClick={() => fetchPatch(selectedFinding.id)}
                      disabled={patchLoading}
                      className="px-2.5 py-1 rounded bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-800 text-indigo-300 font-mono text-[11px] flex items-center gap-1.5 transition-colors"
                    >
                      <Wrench className={`w-3 h-3 ${patchLoading ? 'animate-spin' : ''}`} />
                      {patchLoading ? 'Generating Patch...' : 'Preview Proposed Patch'}
                    </button>
                  ) : (
                    <button
                      onClick={() => setShowPatch(false)}
                      className="text-[10px] text-slate-400 hover:text-white"
                    >
                      Hide Patch
                    </button>
                  )}
                </div>

                {showPatch && patchData && (
                  <div className="rounded-lg bg-slate-950 border border-indigo-900/60 overflow-hidden space-y-2 p-3 font-mono">
                    <div className="p-2 rounded bg-amber-950/40 border border-amber-800/60 text-amber-300 text-[10px] flex items-center gap-2">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                      <span>{patchData.disclaimer}</span>
                    </div>

                    <pre className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                      {patchData.proposed_patch.split('\n').map((line, idx) => (
                        <div
                          key={idx}
                          className={
                            line.startsWith('+')
                              ? 'text-emerald-400 bg-emerald-950/30'
                              : line.startsWith('-')
                              ? 'text-rose-400 bg-rose-950/30'
                              : line.startsWith('@')
                              ? 'text-indigo-400 bg-indigo-950/30'
                              : 'text-slate-400'
                          }
                        >
                          {line}
                        </div>
                      ))}
                    </pre>
                  </div>
                )}
              </div>

              {/* Attribution Footer */}
              <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] text-slate-500">
                <div>
                  <span className="block text-slate-400">DETECTED BY:</span>
                  <span className="text-slate-300 capitalize">{selectedFinding.agent}</span>
                </div>
                <div>
                  <span className="block text-slate-400">TOOL:</span>
                  <span className="text-slate-300">{selectedFinding.tool_name || 'Static Analysis'}</span>
                </div>
                <div>
                  <span className="block text-slate-400">CRITIC AUDIT:</span>
                  <span className="text-emerald-400">{selectedFinding.critic_notes ? 'Verified' : 'Grounding Audit'}</span>
                </div>
                <div>
                  <span className="block text-slate-400">MERGED AGENTS:</span>
                  <span className="text-slate-300">
                    {selectedFinding.merged_agents && selectedFinding.merged_agents.length > 0
                      ? selectedFinding.merged_agents.join(', ')
                      : 'None'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
