import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Info } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge } from '../components/common/Badge.tsx';

interface HealthData {
  status: string;
  version: string;
  environment: string;
  active_llm_provider: string;
  gemini_configured: boolean;
  groq_configured: boolean;
  database_status: string;
}

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);

  useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then((data) => setHealth(data))
      .catch(() => setHealth(null));
  }, []);

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-emerald-400" />
          Platform Settings & Environment
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Inspect backend configuration, provider status, and security disclosures.
        </p>
      </div>

      {/* Academic / Security Disclosure */}
      <div className="p-4 rounded-lg bg-indigo-950/40 border border-indigo-800/60 text-xs text-indigo-200 flex items-start gap-3 font-sans">
        <Info className="w-4 h-4 shrink-0 text-indigo-400 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold block text-indigo-300">Data Disclosure Notice</span>
          <p className="text-[11px] text-indigo-300/90 leading-relaxed">
            Repository code snippets and metadata may be transmitted to your configured LLM provider (Google Gemini or Groq Cloud) for reasoning and risk evaluation. Sensitive tokens and secrets are redacted prior to transmission.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Provider Configuration Status" subtitle="Loaded securely from server-side .env file.">
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Google Gemini API:</span>
              <Badge variant={health?.gemini_configured ? 'success' : 'neutral'}>
                {health?.gemini_configured ? 'KEY DETECTED' : 'NOT CONFIGURED'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Groq Cloud API:</span>
              <Badge variant={health?.groq_configured ? 'success' : 'neutral'}>
                {health?.groq_configured ? 'KEY DETECTED' : 'NOT CONFIGURED'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Active Provider:</span>
              <span className="text-emerald-400 font-semibold">{health?.active_llm_provider || 'diagnostic_mock'}</span>
            </div>
          </div>
        </Card>

        <Card title="Database & Runtime" subtitle="Persistent storage and server runtime parameters.">
          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Database Engine:</span>
              <span className="text-slate-200">SQLite (deploysafe.db)</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Connection State:</span>
              <span className={health?.database_status === 'connected' ? 'text-emerald-400' : 'text-amber-400'}>
                {health?.database_status || 'checking...'}
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Environment:</span>
              <span className="text-slate-200 uppercase">{health?.environment || 'DEVELOPMENT'}</span>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Need Help Adding API Keys?" subtitle="Follow the step-by-step setup guide.">
        <p className="text-xs text-slate-300 font-sans leading-relaxed">
          Open the <code className="text-emerald-400 font-mono bg-dark-950 px-1.5 py-0.5 rounded border border-slate-800">ENV_SETUP.md</code> file in your workspace for easy instructions on generating free API keys for Google Gemini and Groq Cloud.
        </p>
      </Card>
    </div>
  );
};
