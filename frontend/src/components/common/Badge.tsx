import React from 'react';

export type BadgeVariant = 'critical' | 'high' | 'moderate' | 'low' | 'info' | 'success' | 'warning' | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = ''
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    critical: 'bg-red-950/70 text-red-400 border-red-800/60',
    high: 'bg-orange-950/70 text-orange-400 border-orange-800/60',
    moderate: 'bg-yellow-950/70 text-yellow-400 border-yellow-800/60',
    warning: 'bg-amber-950/70 text-amber-400 border-amber-800/60',
    low: 'bg-blue-950/70 text-blue-400 border-blue-800/60',
    info: 'bg-cyan-950/70 text-cyan-400 border-cyan-800/60',
    success: 'bg-emerald-950/70 text-emerald-400 border-emerald-800/60',
    neutral: 'bg-slate-800/70 text-slate-300 border-slate-700/60',
  };

  const sizeStyles: Record<'sm' | 'md' | 'lg', string> = {
    sm: 'px-1.5 py-0.2 text-[10px]',
    md: 'px-2 py-0.5 text-xs',
    lg: 'px-2.5 py-1 text-sm'
  };

  return (
    <span
      className={`inline-flex items-center rounded font-medium font-mono border tracking-wide ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
