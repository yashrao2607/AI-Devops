import React from 'react';

export type BadgeVariant = 'critical' | 'high' | 'moderate' | 'low' | 'info' | 'success' | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', className = '' }) => {
  const variantStyles: Record<BadgeVariant, string> = {
    critical: 'bg-red-950/70 text-red-400 border-red-800/60',
    high: 'bg-orange-950/70 text-orange-400 border-orange-800/60',
    moderate: 'bg-yellow-950/70 text-yellow-400 border-yellow-800/60',
    low: 'bg-blue-950/70 text-blue-400 border-blue-800/60',
    info: 'bg-cyan-950/70 text-cyan-400 border-cyan-800/60',
    success: 'bg-emerald-950/70 text-emerald-400 border-emerald-800/60',
    neutral: 'bg-slate-800/70 text-slate-300 border-slate-700/60',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono border tracking-wide ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
