import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to load data',
  message = 'An error occurred while connecting to the institutional database. Please try again.',
  onRetry,
  className = '',
}) => {
  return (
    <div className={`p-8 text-center bg-rose-50/50 rounded-2xl border border-rose-200 shadow-2xs ${className}`}>
      <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
      <h3 className="text-sm font-bold text-rose-900">{title}</h3>
      {message && <p className="text-xs text-rose-600 mt-1 max-w-md mx-auto">{message}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center space-x-2 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-semibold hover:bg-rose-700 transition-colors shadow-2xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try again</span>
        </button>
      )}
    </div>
  );
};
