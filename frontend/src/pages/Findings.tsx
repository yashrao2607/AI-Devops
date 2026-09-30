import React from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';

export const Findings: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-amber-400" />
          Findings Directory
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Catalog of categorized issues, security risks, configuration drifts, and suggested remediations.
        </p>
      </div>

      <Card className="border-dashed border-slate-800/90 py-12 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
          <CheckCircle2 className="w-6 h-6 text-emerald-500" />
        </div>
        <h3 className="text-sm font-semibold text-white">No Active Repository Findings</h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
          Execute a readiness check from the Overview dashboard to populate findings.
        </p>
      </Card>
    </div>
  );
};
