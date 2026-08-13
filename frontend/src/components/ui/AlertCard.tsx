import React from 'react';
import { OperationalAlert } from '@/types/dashboard';
import { StatusBadge } from './StatusBadge';
import { AlertCircle, Clock, ArrowRight } from 'lucide-react';

interface AlertCardProps {
  alert: OperationalAlert;
  onDismiss?: (id: string) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center space-x-2">
            <AlertCircle
              className={`w-4 h-4 shrink-0 ${
                alert.severity === 'HIGH'
                  ? 'text-red-600'
                  : alert.severity === 'MEDIUM'
                  ? 'text-amber-600'
                  : 'text-blue-600'
              }`}
            />
            <h4 className="text-sm font-semibold text-slate-900 leading-snug">{alert.title}</h4>
          </div>
          <StatusBadge status={alert.severity} type="severity" />
        </div>

        <p className="text-xs text-slate-600 mb-3 pl-6 leading-relaxed">{alert.description}</p>
      </div>

      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 pl-6">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{alert.timestamp}</span>
          </span>
          {alert.affectedEntity && (
            <span className="hidden sm:inline-block px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[11px]">
              {alert.affectedEntity}
            </span>
          )}
        </div>

        {alert.actionRequired && (
          <button className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors">
            <span>Resolve</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
