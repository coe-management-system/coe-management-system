import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'severity' | 'department' | 'generic' | 'readiness';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'generic', className = '' }) => {
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  if (type === 'severity') {
    switch (status.toUpperCase()) {
      case 'HIGH':
        colorClasses = 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800';
        break;
      case 'MEDIUM':
        colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
        break;
      case 'LOW':
        colorClasses = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800';
        break;
    }
  } else if (type === 'readiness') {
    switch (status) {
      case 'A+':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300';
        break;
      case 'A':
        colorClasses = 'bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300';
        break;
      case 'B+':
      case 'B':
        colorClasses = 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300';
        break;
      case 'C':
        colorClasses = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300';
        break;
    }
  } else {
    switch (status.toLowerCase()) {
      case 'active':
      case 'completed':
      case 'verified':
        colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
        break;
      case 'in progress':
      case 'expanding':
      case 'pending audit':
        colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
        break;
      case 'requires review':
      case 'expired':
        colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
        break;
    }
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colorClasses} ${className}`}
    >
      {status}
    </span>
  );
};
