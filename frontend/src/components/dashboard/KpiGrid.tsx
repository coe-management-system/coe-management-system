import React from 'react';
import { KpiMetric } from '@/types/dashboard';
import { KpiCard } from '@/components/ui/KpiCard';

interface KpiGridProps {
  metrics: KpiMetric[];
}

export const KpiGrid: React.FC<KpiGridProps> = ({ metrics }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {metrics.map((metric) => (
        <KpiCard key={metric.id} metric={metric} />
      ))}
    </div>
  );
};
