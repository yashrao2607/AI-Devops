import React from 'react';

interface StatusIndicatorProps {
  status: 'online' | 'degraded' | 'offline' | 'loading';
  label?: string;
  showPulse?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  showPulse = true,
}) => {
  const dotColor = {
    online: 'bg-emerald-400',
    degraded: 'bg-amber-400',
    offline: 'bg-rose-400',
    loading: 'bg-blue-400 animate-pulse',
  };

  return (
    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-mono bg-slate-900/90 border border-slate-800">
      <span className="relative flex h-2 w-2">
        {showPulse && status === 'online' && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColor[status]}`}></span>
      </span>
      {label && <span className="text-slate-300 capitalize">{label}</span>}
    </div>
  );
};
