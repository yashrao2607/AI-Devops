import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  RefreshCw,
  Code,
  Globe,
  FileCode
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';
import { Button } from '../components/common/Button.tsx';

interface RunOption {
  run_id: string;
  repository_id: string;
  repository_name: string;
  risk_score: number;
  risk_level: string;
  analyzed_at: string;
}

export const Reports: React.FC = () => {
  const [runs, setRuns] = useState<RunOption[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'html' | 'markdown' | 'json'>('html');
  const [markdownContent, setMarkdownContent] = useState<string>('');
  const [jsonContent, setJsonContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Fetch runs
  useEffect(() => {
    const fetchRuns = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/v1/runs');
        if (res.ok) {
          const data = await res.json();
          setRuns(data);
          if (data.length > 0) {
            setSelectedRunId(data[0].run_id);
          }
        }
      } catch (e) {
        console.error('Failed to load runs:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, []);

  // Fetch report text when selected run or tab changes
  useEffect(() => {
    if (!selectedRunId) return;

    const fetchReport = async () => {
      setContentLoading(true);
      try {
        if (activeTab === 'markdown') {
          const res = await fetch(`/api/v1/runs/${selectedRunId}/report?format=markdown`);
          if (res.ok) {
            const text = await res.text();
            setMarkdownContent(text);
          }
        } else if (activeTab === 'json') {
          const res = await fetch(`/api/v1/runs/${selectedRunId}/report?format=json`);
          if (res.ok) {
            const data = await res.json();
            setJsonContent(JSON.stringify(data, null, 2));
          }
        }
      } catch (e) {
        console.error('Failed to load report:', e);
      } finally {
        setContentLoading(false);
      }
    };

    fetchReport();
  }, [selectedRunId, activeTab]);

  const selectedRun = runs.find((r) => r.run_id === selectedRunId);

  const getRiskLevelBadgeVariant = (lvl?: string): BadgeVariant => {
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

  const handleCopy = () => {
    const textToCopy = activeTab === 'markdown' ? markdownContent : jsonContent;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (format: 'html' | 'markdown' | 'json') => {
    if (!selectedRunId) return;
    const url = `/api/v1/runs/${selectedRunId}/report?format=${format}`;
    const filename = `deploysafe-report-${selectedRunId}.${format === 'markdown' ? 'md' : format}`;

    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-emerald-400" />
            Deployment Reports & Exports
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Exportable multi-format risk audits (styled standalone HTML, documentation Markdown, structured JSON).
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => handleDownload('html')}
            disabled={!selectedRunId}
          >
            Export HTML
          </Button>
          <Button
            variant="outline"
            size="sm"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => handleDownload('markdown')}
            disabled={!selectedRunId}
          >
            Export Markdown
          </Button>
          <Button
            variant="outline"
            size="sm"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={() => handleDownload('json')}
            disabled={!selectedRunId}
          >
            Export JSON
          </Button>
        </div>
      </div>

      {/* Run Selection & Tab Navigation */}
      {runs.length === 0 && !loading ? (
        <Card className="border-dashed border-slate-800/90 py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-white">No Stored Final Reports</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            Execute a repository analysis in the Analyze section to generate exportable reports.
          </p>
        </Card>
      ) : (
        <>
          <Card noPadding className="p-4 bg-slate-900/40 border-slate-800">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Select Target Run */}
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-400">Target Run:</span>
                <select
                  value={selectedRunId}
                  onChange={(e) => setSelectedRunId(e.target.value)}
                  className="bg-slate-950 text-white border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-emerald-500"
                >
                  {runs.map((r) => (
                    <option key={r.run_id} value={r.run_id}>
                      {r.run_id} ({r.repository_name || r.repository_id}) - {r.risk_score} {r.risk_level}
                    </option>
                  ))}
                </select>

                {selectedRun && (
                  <Badge variant={getRiskLevelBadgeVariant(selectedRun.risk_level)} size="sm">
                    {selectedRun.risk_level} ({selectedRun.risk_score}/100)
                  </Badge>
                )}
              </div>

              {/* Format Tabs */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 font-mono text-xs">
                <button
                  onClick={() => setActiveTab('html')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                    activeTab === 'html'
                      ? 'bg-slate-800 text-white font-semibold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Globe className="w-3.5 h-3.5 text-emerald-400" />
                  HTML Document
                </button>
                <button
                  onClick={() => setActiveTab('markdown')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                    activeTab === 'markdown'
                      ? 'bg-slate-800 text-white font-semibold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                  Markdown
                </button>
                <button
                  onClick={() => setActiveTab('json')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
                    activeTab === 'json'
                      ? 'bg-slate-800 text-white font-semibold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Code className="w-3.5 h-3.5 text-amber-400" />
                  JSON Contract
                </button>
              </div>
            </div>
          </Card>

          {/* Report Viewer Container */}
          <div className="rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl min-h-[600px] flex flex-col">
            {/* Viewer Header */}
            <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span>
                  Viewing {activeTab.toUpperCase()} format for run{' '}
                  <strong className="text-white">{selectedRunId}</strong>
                </span>
              </div>

              {activeTab !== 'html' && (
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-slate-400 hover:text-white px-2.5 py-1 rounded bg-slate-800 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy Content'}</span>
                </button>
              )}
            </div>

            {/* Viewer Body */}
            <div className="flex-1 relative flex flex-col">
              {contentLoading ? (
                <div className="py-24 text-center">
                  <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
                  <p className="text-xs text-slate-400 font-mono">Rendering report format...</p>
                </div>
              ) : activeTab === 'html' ? (
                <iframe
                  title="HTML Report"
                  src={`/api/v1/runs/${selectedRunId}/report?format=html`}
                  className="w-full flex-1 border-0 min-h-[700px] bg-slate-950"
                />
              ) : activeTab === 'markdown' ? (
                <pre className="p-6 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                  {markdownContent}
                </pre>
              ) : (
                <pre className="p-6 text-xs font-mono text-emerald-300/90 overflow-x-auto whitespace-pre leading-relaxed">
                  {jsonContent}
                </pre>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
