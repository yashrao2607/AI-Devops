import React, { useState } from 'react';
import { Terminal, Play } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Button } from '../components/common/Button.tsx';

export const Analyze: React.FC = () => {
  const [prompt, setPrompt] = useState('Analyze deployment safety for this release.');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const handleTestDiagnostic = async () => {
    setLoading(true);
    setResponse(null);
    try {
      const res = await fetch('/api/v1/diagnostic/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (err: any) {
      setResponse({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Terminal className="w-6 h-6 text-emerald-400" />
          AI Diagnostic & Analysis Console
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Direct testing console for the backend LLM provider abstraction and fallback system.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Diagnostic LLM Prompt" subtitle="Send an evaluation prompt to test the active provider.">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-mono text-slate-400 block mb-1.5">Prompt</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                className="w-full rounded-md bg-dark-950 border border-slate-800 p-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>
            <Button
              variant="primary"
              size="md"
              icon={<Play className="w-4 h-4 fill-current" />}
              isLoading={loading}
              onClick={handleTestDiagnostic}
            >
              Test LLM Provider
            </Button>
          </div>
        </Card>

        <Card title="Diagnostic Output" subtitle="Response payload and measured round-trip latency.">
          {response ? (
            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-400">Provider Used:</span>
                <span className="text-emerald-400 font-semibold">{response.provider_used}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-400">Latency:</span>
                <span className="text-cyan-400">{response.latency_ms} ms</span>
              </div>
              <div className="p-3 rounded bg-dark-950 border border-slate-800 text-slate-200 whitespace-pre-wrap">
                {response.success ? response.content : <span className="text-rose-400">{response.error}</span>}
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-xs font-mono text-slate-500">
              Run a test prompt to observe provider latency and output.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
