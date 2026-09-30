import React, { useState } from 'react';
import { 
  Play, Shield, Activity, Layers, CheckCircle2, 
  AlertCircle, FileCode, Zap
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Button } from '../components/common/Button.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';

interface Finding {
  id: string;
  category: string;
  severity: string;
  confidence: number;
  title: string;
  summary: string;
  file_path: string;
  evidence: string;
  recommendation: string;
  agent: string;
}

interface FlowResult {
  repository_name: string;
  target_branch: string;
  analyzed_at: string;
  overall_risk_level: string;
  risk_score: number;
  findings: Finding[];
  agent_trace: Array<{ step: string; status: string; [key: string]: any }>;
  summary: string;
}

export const Dashboard: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<FlowResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunInitialFlow = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/flow/run-initial', {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }
      const data: FlowResult = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to trigger Phase-1 flow. Is the FastAPI backend running on port 8000?');
    } finally {
      setIsRunning(false);
    }
  };

  const getSeverityBadge = (sev: string): BadgeVariant => {
    const s = sev.toUpperCase();
    if (s === 'CRITICAL') return 'critical';
    if (s === 'HIGH') return 'high';
    if (s === 'MEDIUM' || s === 'MODERATE') return 'moderate';
    if (s === 'LOW') return 'low';
    return 'neutral';
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Deployment Readiness Dashboard
            <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
              Phase 1 Active
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic repository evaluation, structured CrewAI flow orchestration, and explainable risk synthesis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="md"
            icon={<Play className="w-4 h-4 fill-current" />}
            isLoading={isRunning}
            onClick={handleRunInitialFlow}
          >
            {isRunning ? 'Analyzing Repository...' : 'Run Phase-1 Readiness Check'}
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div>
            <span className="font-semibold block mb-0.5">Execution Failed</span>
            {error}
          </div>
        </div>
      )}

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>RISK SCORE</span>
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-white">
              {result ? result.risk_score : '--'}
            </span>
            <span className="text-xs text-slate-500 font-mono">/ 100</span>
          </div>
          <div className="mt-2 text-[11px] font-mono">
            {result ? (
              <Badge variant={getSeverityBadge(result.overall_risk_level)}>
                {result.overall_risk_level} RISK
              </Badge>
            ) : (
              <span className="text-slate-500">No active analysis</span>
            )}
          </div>
        </Card>

        <Card className="border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>FINDINGS DETECTED</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold font-mono text-white">
            {result ? result.findings.length : '--'}
          </div>
          <p className="mt-2 text-[11px] text-slate-500 font-mono">
            {result ? 'Structured Pydantic findings' : 'Awaiting flow execution'}
          </p>
        </Card>

        <Card className="border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>ACTIVE CREW FLOW</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-sm font-semibold text-slate-200 mt-1">
            RepositoryReadinessFlow
          </div>
          <p className="mt-3 text-[11px] text-slate-500 font-mono">
            Status: {result ? 'Execution Succeeded' : 'Idle'}
          </p>
        </Card>

        <Card className="border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
            <span>DATA SOURCE</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-sm font-semibold text-slate-200 mt-1">
            Local Workspace
          </div>
          <p className="mt-3 text-[11px] text-slate-500 font-mono">
            Deterministic + LLM reasoning
          </p>
        </Card>
      </div>

      {/* Main Analysis Section */}
      {result ? (
        <div className="space-y-6">
          {/* Executive Summary Card */}
          <Card 
            title="Executive Readiness Summary"
            subtitle={`Analyzed at ${new Date(result.analyzed_at).toLocaleTimeString()} UTC`}
            className="border-emerald-950/60 bg-emerald-950/10"
          >
            <p className="text-sm text-slate-300 leading-relaxed font-sans">
              {result.summary}
            </p>
          </Card>

          {/* Findings Table */}
          <Card 
            title={`Discovered Findings (${result.findings.length})`}
            subtitle="Verified issues with concrete repository evidence and recommended remediations."
          >
            {result.findings.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs font-mono">
                No deployment risks detected. Baseline checks pass cleanly.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {result.findings.map((f) => (
                  <div key={f.id} className="py-4 space-y-2 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={getSeverityBadge(f.severity)}>{f.severity}</Badge>
                        <span className="text-xs font-mono text-slate-400 font-semibold">{f.id}</span>
                        <span className="text-sm font-semibold text-white">{f.title}</span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-500">Agent: {f.agent}</span>
                    </div>

                    <p className="text-xs text-slate-300">{f.summary}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-dark-950/60 p-3 rounded border border-slate-800/70 font-mono">
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase">Evidence File</span>
                        <span className="text-emerald-400 flex items-center gap-1 mt-0.5">
                          <FileCode className="w-3.5 h-3.5" /> {f.file_path}
                        </span>
                        <p className="text-[11px] text-slate-400 mt-1">{f.evidence}</p>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase">Remediation Fix</span>
                        <span className="text-cyan-400 mt-0.5 block">{f.recommendation}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Execution Trace */}
          <Card 
            title="Agent Execution Trace"
            subtitle="Observable pipeline steps captured during flow execution."
          >
            <div className="space-y-2 font-mono text-xs">
              {result.agent_trace.map((step, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 rounded bg-slate-900/60 border border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-slate-200 font-medium">{step.step}</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">
                    Status: <span className="text-slate-300">{step.status}</span>
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      ) : (
        /* Empty State */
        <Card className="border-dashed border-slate-800/90 py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-4">
            <Activity className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No Analysis Run Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1.5 mb-6">
            Phase 1 provides the live evaluation flow foundation. Click below to execute the real initial readiness flow against this repository.
          </p>
          <Button
            variant="primary"
            size="md"
            icon={<Play className="w-4 h-4 fill-current" />}
            isLoading={isRunning}
            onClick={handleRunInitialFlow}
          >
            Run Initial Readiness Check
          </Button>
        </Card>
      )}
    </div>
  );
};
