import React from 'react';
import { OperationalAlert } from '@/types/dashboard';
import { AlertCard } from '@/components/ui/AlertCard';
import { ShieldAlert } from 'lucide-react';

interface AlertCenterProps {
  alerts: OperationalAlert[];
}

export const AlertCenter: React.FC<AlertCenterProps> = ({ alerts }) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Critical Operational Alerts</h3>
            <p className="text-xs text-slate-500">Live operational & academic risk indicators requiring attention</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold px-2.5 py-1 bg-red-100 text-red-800 rounded-full">
            {alerts.filter((a) => a.severity === 'HIGH').length} High Priority
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {alerts.slice(0, 6).map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
};
