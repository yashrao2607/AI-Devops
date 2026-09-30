import React from 'react';
import { FolderGit2, GitBranch } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge } from '../components/common/Badge.tsx';

export const Repositories: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FolderGit2 className="w-6 h-6 text-emerald-400" />
            Connected Repositories
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Registered repositories available for deployment readiness analysis.
          </p>
        </div>
      </div>

      <Card title="Active Workspace Repository" subtitle="Current workspace mounted in DeploySafe runtime.">
        <div className="flex items-center justify-between p-4 rounded bg-slate-900/60 border border-slate-800 font-mono text-xs">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white text-sm">DeploySafe (Local)</span>
              <Badge variant="success">ACTIVE</Badge>
            </div>
            <div className="text-slate-400 flex items-center gap-2">
              <GitBranch className="w-3.5 h-3.5" /> main
              <span>•</span>
              <span>FastAPI Backend + React Shell + CrewAI Flow</span>
            </div>
          </div>
          <div className="text-right text-[11px] text-slate-500">
            Phase 1 Foundation
          </div>
        </div>
      </Card>

      <Card className="border-dashed border-slate-800/90 text-center py-8">
        <p className="text-xs text-slate-400 font-mono">
          Remote GitHub repository connection will be enabled in Phase 2 (Repository Loader & Ingestion).
        </p>
      </Card>
    </div>
  );
};
