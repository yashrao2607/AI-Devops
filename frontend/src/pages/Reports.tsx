import React from 'react';
import { FileText } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';

export const Reports: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <FileText className="w-6 h-6 text-emerald-400" />
          Deployment Reports
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Exportable risk assessments in Markdown, JSON, and HTML formats.
        </p>
      </div>

      <Card className="border-dashed border-slate-800/90 py-12 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500 mb-3">
          <FileText className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-white">No Stored Final Reports</h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
          Complete exportable deployment reports are scheduled for release in Phase 4 & Phase 6.
        </p>
      </Card>
    </div>
  );
};
