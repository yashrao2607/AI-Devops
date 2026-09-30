import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  headerClassName?: string;
  bodyClassName?: string;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  hoverEffect = false,
}) => {
  return (
    <div
      className={`glass-panel rounded-lg border border-slate-800/80 bg-dark-900/90 shadow-sm ${
        hoverEffect ? 'glass-panel-hover' : ''
      } ${className}`}
    >
      {(title || action) && (
        <div className={`px-5 py-3.5 border-b border-slate-800/80 flex items-center justify-between ${headerClassName}`}>
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-200 tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-5 ${bodyClassName}`}>{children}</div>
    </div>
  );
};
