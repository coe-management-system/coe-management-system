import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  icon?: React.ElementType;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  message = 'There are no items matching the specified criteria in the system.',
  icon: Icon = AlertTriangle,
  className = '',
}) => {
  return (
    <div className={`bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs ${className}`}>
      <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-3">
        <Icon className="w-6 h-6 text-slate-400" />
      </div>
      <h3 className="text-sm font-bold text-slate-800">{title}</h3>
      {message && <p className="text-xs text-slate-500 mt-1">{message}</p>}
    </div>
  );
};
