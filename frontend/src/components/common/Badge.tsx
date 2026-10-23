import React from 'react';

export type HealthStatus = 'ON_TRACK' | 'NEEDS_ATTENTION' | 'AT_RISK';

interface HealthBadgeProps {
  status: HealthStatus | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({
  status,
  size = 'md',
  className = '',
}) => {
  const normalized = status.toUpperCase();

  const configs = {
    ON_TRACK: {
      label: 'On Track',
      dotColor: 'bg-emerald-500',
      classes: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    NEEDS_ATTENTION: {
      label: 'Needs Attention',
      dotColor: 'bg-amber-500',
      classes: 'bg-amber-50 text-amber-700 border-amber-200',
    },
    AT_RISK: {
      label: 'At Risk',
      dotColor: 'bg-rose-500',
      classes: 'bg-rose-50 text-rose-700 border-rose-200',
    },
  };

  const config =
    configs[normalized as HealthStatus] || {
      label: status,
      dotColor: 'bg-slate-400',
      classes: 'bg-slate-100 text-slate-700 border-slate-200',
    };

  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${sizeClasses} ${config.classes} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotColor}`} />
      {config.label}
    </span>
  );
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'brand' | 'neutral' | 'success' | 'warning' | 'danger';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
}) => {
  const variantStyles = {
    brand: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    danger: 'bg-rose-50 text-rose-700 border-rose-200',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
