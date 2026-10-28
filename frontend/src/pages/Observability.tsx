import React, { useState, useEffect } from 'react';
import { 
  Activity, Clock, Cpu, RefreshCw, Wrench
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge } from '../components/common/Badge.tsx';

interface TimelineEvent {
  timestamp: string;
  event_type: string;
  component: string;
  message: string;
  status: 'SUCCESS' | 'WARNING' | 'ERROR' | 'INFO';
  metadata?: Record<string, any>;
}

interface AgentTraceRecord {
  agent_name: string;
  role: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  start_time: string;
  end_time?: string;
  duration_ms: number;
  tool_calls_count: number;
  findings_count: number;
  error?: string;
}

interface ToolTraceRecord {
  tool_name: string;
  agent_name: string;
  status: 'SUCCESS' | 'FAILED';
  duration_ms: number;
  input_summary: string;
  output_summary: string;
  error?: string;
}

interface RunTrace {
  run_id: string;
  repository_name: string;
  commit_sha?: string;
  pr_number?: number;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_seconds: number;
  risk_score: number;
  risk_level: string;
  provider: string;
  model: string;
  rag_chunks_retrieved: number;
  agent_traces: AgentTraceRecord[];
  tool_traces: ToolTraceRecord[];
  events: TimelineEvent[];
}

export const Observability: React.FC = () => {
  const [traces, setTraces] = useState<RunTrace[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [currentTrace, setCurrentTrace] = useState<RunTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'timeline' | 'agents' | 'tools' | 'telemetry'>('timeline');
  const [telemetryEvents, setTelemetryEvents] = useState<any[]>([]);

  const fetchTraces = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/observability/traces');
      if (res.ok) {
        const data: RunTrace[] = await res.json();
        setTraces(data);
        if (data.length > 0 && !selectedRunId) {
          setSelectedRunId(data[data.length - 1].run_id);
        }
      }
      
      const telRes = await fetch('/api/v1/observability/telemetry');
      if (telRes.ok) {
        const telData = await telRes.json();
        setTelemetryEvents(telData.telemetry_events || []);
      }
    } catch (err) {
      console.error('Error fetching observability traces:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTraces();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      fetch(`/api/v1/runs/${selectedRunId}/trace`)
        .then(r => r.ok ? r.json() : null)
        .then(data => setCurrentTrace(data))
        .catch(() => setCurrentTrace(null));
    }
  }, [selectedRunId]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Observability & Run Tracing</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            End-to-end execution audit: GitHub PRs &rarr; Agent Telemetry &rarr; Tool Invocations &rarr; RAG Retrievals &rarr; LLM Provider Events
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select 
            value={selectedRunId} 
            onChange={(e) => setSelectedRunId(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500 font-mono"
          >
            {traces.length === 0 ? (
              <option value="">No traces recorded yet</option>
            ) : (
              traces.map(t => (
                <option key={t.run_id} value={t.run_id}>
                  {t.run_id} — {t.repository_name} ({t.risk_score.toFixed(1)} pts)
                </option>
              ))
            )}
          </select>
          <button
            onClick={fetchTraces}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {loading && !currentTrace ? (
        <Card className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
          Loading execution traces...
        </Card>
      ) : !currentTrace ? (
        <Card className="p-8 text-center text-slate-400">
          <Activity className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm">No trace selected. Run an analysis from the CLI or Analyze page to record telemetry.</p>
        </Card>
      ) : (
        <>
          {/* Run Header Overview */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Target Repository</span>
              <div className="text-sm font-semibold text-white mt-1 truncate">
                {currentTrace.repository_name}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
                Commit: {currentTrace.commit_sha ? currentTrace.commit_sha.slice(0, 8) : 'HEAD'}
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Risk Evaluation</span>
              <div className="text-sm font-semibold text-white mt-1">
                {currentTrace.risk_score.toFixed(1)} / 100
              </div>
              <div className="mt-1">
                <Badge variant={currentTrace.risk_score >= 75 ? 'critical' : currentTrace.risk_score >= 50 ? 'high' : currentTrace.risk_score >= 25 ? 'moderate' : 'low'} size="sm">
                  {currentTrace.risk_level}
                </Badge>
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Total Latency</span>
              <div className="text-sm font-semibold text-white mt-1">
                {currentTrace.duration_seconds}s
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Status: {currentTrace.status}
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">Active LLM Provider</span>
              <div className="text-sm font-semibold text-white mt-1 uppercase font-mono">
                {currentTrace.provider}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
                {currentTrace.model}
              </div>
            </Card>

            <Card className="p-3.5">
              <span className="text-[11px] font-mono text-slate-400 uppercase">RAG Retrievals</span>
              <div className="text-sm font-semibold text-white mt-1">
                {currentTrace.rag_chunks_retrieved} chunks
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Vector store: Chroma
              </div>
            </Card>
          </div>

          {/* Navigation Sub-Tabs */}
          <div className="flex border-b border-slate-800 gap-6 text-xs font-medium">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                activeTab === 'timeline' 
                  ? 'border-indigo-500 text-indigo-400 font-semibold' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              Event Timeline ({currentTrace.events.length})
            </button>
            <button
              onClick={() => setActiveTab('agents')}
              className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                activeTab === 'agents' 
                  ? 'border-indigo-500 text-indigo-400 font-semibold' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              Agent Telemetry ({currentTrace.agent_traces.length})
            </button>
            <button
              onClick={() => setActiveTab('tools')}
              className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                activeTab === 'tools' 
                  ? 'border-indigo-500 text-indigo-400 font-semibold' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Wrench className="w-3.5 h-3.5" />
              Tool Executions ({currentTrace.tool_traces.length})
            </button>
            <button
              onClick={() => setActiveTab('telemetry')}
              className={`pb-2.5 flex items-center gap-1.5 border-b-2 transition ${
                activeTab === 'telemetry' 
                  ? 'border-indigo-500 text-indigo-400 font-semibold' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Provider Fallbacks ({telemetryEvents.length})
            </button>
          </div>

          {/* TAB 1: Event Timeline */}
          {activeTab === 'timeline' && (
            <Card className="p-4 space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Milestone Chronology</h3>
              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {currentTrace.events.map((ev, idx) => (
                  <div key={idx} className="relative flex items-start gap-3 text-xs">
                    <div className={`absolute -left-6 top-1 w-2.5 h-2.5 rounded-full ring-4 ring-slate-950 ${
                      ev.status === 'SUCCESS' ? 'bg-emerald-500' :
                      ev.status === 'ERROR' ? 'bg-red-500' :
                      ev.status === 'WARNING' ? 'bg-amber-500' : 'bg-indigo-500'
                    }`} />
                    <div className="flex-1 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between text-[11px] mb-1 font-mono">
                        <span className="font-semibold text-indigo-300">{ev.event_type}</span>
                        <span className="text-slate-500">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-slate-300 text-xs">{ev.message}</p>
                      <div className="text-[10px] text-slate-500 mt-1 font-mono">Component: {ev.component}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* TAB 2: Agent Telemetry */}
          {activeTab === 'agents' && (
            <Card className="overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800 text-xs font-semibold text-slate-300 uppercase">
                Specialized Agent Execution Breakdown
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900/80 text-slate-400 font-mono text-[11px]">
                    <tr>
                      <th className="px-4 py-2.5">Agent</th>
                      <th className="px-4 py-2.5">Role</th>
                      <th className="px-4 py-2.5">Status</th>
                      <th className="px-4 py-2.5">Duration</th>
                      <th className="px-4 py-2.5">Tools Called</th>
                      <th className="px-4 py-2.5">Findings</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {currentTrace.agent_traces.map((agent, i) => (
                      <tr key={i} className="hover:bg-slate-900/40">
                        <td className="px-4 py-2.5 font-semibold text-white font-mono">{agent.agent_name}</td>
                        <td className="px-4 py-2.5 text-slate-400 font-mono text-[11px]">{agent.role}</td>
                        <td className="px-4 py-2.5">
                          <Badge variant={agent.status === 'COMPLETED' ? 'success' : agent.status === 'FAILED' ? 'critical' : 'warning'} size="sm">
                            {agent.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-2.5 font-mono text-slate-300">{agent.duration_ms.toFixed(1)} ms</td>
                        <td className="px-4 py-2.5 font-mono text-slate-300">{agent.tool_calls_count}</td>
                        <td className="px-4 py-2.5 font-mono text-indigo-400 font-semibold">{agent.findings_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* TAB 3: Tool Executions */}
          {activeTab === 'tools' && (
            <Card className="overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800 text-xs font-semibold text-slate-300 uppercase">
                Sanitized Tool Invocations
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900/80 text-slate-400 font-mono text-[11px]">
                    <tr>
                      <th className="px-4 py-2.5">Tool Name</th>
                      <th className="px-4 py-2.5">Invoked By</th>
                      <th className="px-4 py-2.5">Status</th>
                      <th className="px-4 py-2.5">Duration</th>
                      <th className="px-4 py-2.5">Summary</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono">
                    {currentTrace.tool_traces.map((tool, i) => (
                      <tr key={i} className="hover:bg-slate-900/40">
                        <td className="px-4 py-2.5 text-indigo-300 font-semibold">{tool.tool_name}</td>
                        <td className="px-4 py-2.5 text-slate-400">{tool.agent_name}</td>
                        <td className="px-4 py-2.5">
                          <Badge variant={tool.status === 'SUCCESS' ? 'success' : 'critical'} size="sm">
                            {tool.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-2.5 text-slate-300">{tool.duration_ms.toFixed(1)} ms</td>
                        <td className="px-4 py-2.5 text-slate-400 text-[11px] truncate max-w-xs">{tool.output_summary}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* TAB 4: Provider Telemetry */}
          {activeTab === 'telemetry' && (
            <Card className="p-4 space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">LLM Provider Call Latency & Failover Audit</h3>
              <div className="divide-y divide-slate-800">
                {telemetryEvents.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4 text-center">No provider calls recorded yet.</p>
                ) : (
                  telemetryEvents.map((evt, idx) => (
                    <div key={idx} className="py-2.5 flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <Badge variant={evt.success ? 'success' : 'critical'} size="sm">
                          {evt.provider}
                        </Badge>
                        <span className="text-slate-300">{evt.model}</span>
                        {evt.fallback_used && (
                          <Badge variant="warning" size="sm">FALLBACK TRIGGERED</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-slate-400">
                        <span>{evt.latency_ms} ms</span>
                        <span className="text-slate-500 text-[10px]">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
};
