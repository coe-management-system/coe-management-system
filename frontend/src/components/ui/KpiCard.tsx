import React from 'react';
import { KpiMetric } from '@/types/dashboard';
import {
  Users,
  BookOpen,
  Award,
  CalendarCheck,
  Briefcase,
  FileText,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';

interface KpiCardProps {
  metric: KpiMetric;
}

const ICON_MAP: Record<string, React.ElementType> = {
  Users,
  BookOpen,
  Award,
  CalendarCheck,
  Briefcase,
  FileText,
  AlertTriangle,
};

export const KpiCard: React.FC<KpiCardProps> = ({ metric }) => {
  const IconComponent = ICON_MAP[metric.iconName] || Users;

  const renderTrendIcon = () => {
    if (!metric.changeType) return null;
    if (metric.changeType === 'positive') return <TrendingUp className="w-3.5 h-3.5 text-emerald-600 mr-1" />;
    if (metric.changeType === 'negative') return <TrendingDown className="w-3.5 h-3.5 text-rose-600 mr-1" />;
    return <Minus className="w-3.5 h-3.5 text-slate-500 mr-1" />;
  };

  const getTrendColor = () => {
    if (metric.changeType === 'positive') return 'text-emerald-700 bg-emerald-50 border-emerald-100';
    if (metric.changeType === 'negative') return 'text-rose-700 bg-rose-50 border-rose-100';
    return 'text-slate-700 bg-slate-50 border-slate-100';
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {metric.title}
          </span>
          <div className="p-2.5 rounded-lg bg-indigo-50/70 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-200">
            <IconComponent className="w-5 h-5" />
          </div>
        </div>

        <div className="flex items-baseline space-x-2">
          <h3 className="text-2xl font-bold text-slate-900 tracking-tight">{metric.value}</h3>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        {metric.change && (
          <span
            className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-md border ${getTrendColor()}`}
          >
            {renderTrendIcon()}
            {metric.change}
          </span>
        )}
        {metric.subtitle && (
          <span className="text-xs text-slate-500 font-normal truncate max-w-[150px]" title={metric.subtitle}>
            {metric.subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
