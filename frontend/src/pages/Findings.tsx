import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle2, FileCode, Filter, RefreshCw } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';
import { Button } from '../components/common/Button.tsx';

interface Finding {
  id: string;
  category: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
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
  critic_notes?: string | null;
}

export const Findings: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/analysis/latest/report');
      if (res.ok) {
        const data = await res.json();
        if (data && data.findings) {
          setFindings(data.findings);
        }
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

  const filtered = findings.filter((f) => {
    if (severityFilter === 'ALL') return true;
    return f.severity === severityFilter;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-amber-400" />
            Findings Directory
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Audited repository issues, deployment hazards, configuration drifts, and Critic validation status.
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

      {findings.length === 0 ? (
        <Card className="border-dashed border-slate-800/90 py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
          </div>
          <h3 className="text-sm font-semibold text-white">No Active Repository Findings</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            Execute a deployment analysis from the Analyze tab to evaluate the demo repository.
          </p>
        </Card>
      ) : (
        <Card title={`Discovered Findings (${findings.length} Total)`} subtitle="Real verified issues detected by Phase 3 specialized agents.">
          <div className="flex items-center gap-2 pb-4 mb-4 border-b border-slate-800">
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

          <div className="space-y-3">
            {filtered.map((f) => (
              <div
                key={f.id}
                className="p-4 rounded-lg bg-dark-950 border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={getSeverityBadgeVariant(f.severity)}>{f.severity}</Badge>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                      {f.category}
                    </span>
                    <span className="text-xs font-mono text-slate-400">ID: {f.id}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className="text-slate-400">By: <span className="text-cyan-400">{f.agent}</span></span>
                    <span className="text-emerald-400 border border-emerald-800/60 bg-emerald-950/80 px-2 py-0.5 rounded">
                      {f.status}
                    </span>
                  </div>
                </div>

                <div className="text-sm font-semibold text-slate-200">{f.title}</div>
                <div className="text-xs text-slate-400 leading-relaxed">{f.summary}</div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs font-mono text-slate-400">
                  <div className="flex items-center gap-1.5 text-cyan-300">
                    <FileCode className="w-3.5 h-3.5" />
                    <span>{f.file_path}</span>
                    {f.line_start !== null && <span>:L{f.line_start}</span>}
                  </div>
                  {f.critic_notes && (
                    <div className="text-slate-400 text-[11px] truncate max-w-md">
                      Critic: {f.critic_notes}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
