import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading data...',
  className = '',
}) => {
  return (
    <div className={`p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-2xs ${className}`}>
      <Loader2 className="w-7 h-7 text-indigo-600 animate-spin mx-auto mb-3" />
      <p className="text-sm font-semibold text-slate-700">{message}</p>
    </div>
  );
};
