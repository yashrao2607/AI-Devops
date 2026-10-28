import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, LayoutDashboard, Terminal, FolderGit2, 
  History, AlertTriangle, Bot, FileText, Settings, 
  Server, GitBranch, RefreshCw, Cpu, Activity, Award
} from 'lucide-react';
import { StatusIndicator } from '../common/StatusIndicator.tsx';

export type NavItem = 
  | 'overview' 
  | 'analyze' 
  | 'repositories' 
  | 'runs' 
  | 'findings' 
  | 'agents' 
  | 'observability'
  | 'evaluation'
  | 'reports' 
  | 'settings';

interface ShellProps {
  currentTab: NavItem;
  onSelectTab: (tab: NavItem) => void;
  children: React.ReactNode;
}

interface BackendHealth {
  status: string;
  version: string;
  active_llm_provider: string;
  database_status: string;
  gemini_configured: boolean;
  groq_configured: boolean;
}

export const Shell: React.FC<ShellProps> = ({ currentTab, onSelectTab, children }) => {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  const fetchHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await fetch('/api/v1/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      } else {
        setHealth(null);
      }
    } catch {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'overview' as NavItem, label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'analyze' as NavItem, label: 'Analyze', icon: <Terminal className="w-4 h-4" /> },
    { id: 'repositories' as NavItem, label: 'Repositories', icon: <FolderGit2 className="w-4 h-4" /> },
    { id: 'runs' as NavItem, label: 'Runs', icon: <History className="w-4 h-4" /> },
    { id: 'findings' as NavItem, label: 'Findings', icon: <AlertTriangle className="w-4 h-4" /> },
    { id: 'agents' as NavItem, label: 'Agents', icon: <Bot className="w-4 h-4" /> },
    { id: 'observability' as NavItem, label: 'Observability', icon: <Activity className="w-4 h-4" /> },
    { id: 'evaluation' as NavItem, label: 'Evaluation', icon: <Award className="w-4 h-4" /> },
    { id: 'reports' as NavItem, label: 'Reports', icon: <FileText className="w-4 h-4" /> },
    { id: 'settings' as NavItem, label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <div className="flex h-screen bg-[#070b13] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800/80 bg-[#0a0f1d] flex flex-col shrink-0 select-none">
        {/* Brand header */}
        <div className="h-16 px-5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-sm shadow-emerald-950">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white">DeploySafe</span>
              <span className="block text-[10px] font-mono text-emerald-400 font-medium">PHASE 1 FOUNDATION</span>
            </div>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-wider">
            Platform Navigation
          </div>
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-slate-800/90 text-emerald-400 border border-slate-700/60 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <span className={isActive ? 'text-emerald-400' : 'text-slate-500'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* System telemetry footer */}
        <div className="p-4 border-t border-slate-800/80 bg-[#080d19] text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-slate-500" /> AI Provider
            </span>
            <span className="text-[11px] font-mono text-slate-200 font-medium">
              {health?.active_llm_provider || 'diagnostic_mock'}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>FastAPI: v{health?.version || '0.1.0'}</span>
            <span className={health?.database_status === 'connected' ? 'text-emerald-400' : 'text-amber-400'}>
              SQLite: {health?.database_status || 'connecting...'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="h-16 border-b border-slate-800/80 bg-[#0a0f1d]/80 backdrop-blur px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
              <Server className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-slate-400">Target Repo:</span>
              <span className="font-semibold text-white">DeploySafe (Local)</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
              <GitBranch className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-slate-400">Branch:</span>
              <span className="font-semibold text-emerald-400">main</span>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-950/60 text-blue-400 border border-blue-800/50">
              DEV MODE
            </span>
          </div>

          {/* Right Status Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={fetchHealth}
              disabled={healthLoading}
              title="Refresh backend status"
              className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? 'animate-spin' : ''}`} />
            </button>
            <StatusIndicator
              status={health ? (health.status === 'healthy' ? 'online' : 'degraded') : 'offline'}
              label={health ? `API ${health.status}` : 'API Disconnected'}
            />
          </div>
        </header>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
