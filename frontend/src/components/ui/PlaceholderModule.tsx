import React from 'react';
import Link from 'next/link';
import { PageHeader } from './PageHeader';
import { Layers, ArrowLeft, Clock } from 'lucide-react';

interface PlaceholderModuleProps {
  moduleName: string;
  description?: string;
}

export const PlaceholderModule: React.FC<PlaceholderModuleProps> = ({
  moduleName,
  description = 'Institutional Management Module.',
}) => {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title={moduleName}
        subtitle="Institutional Center of Excellence Operations Module"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: moduleName },
        ]}
      />

      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs my-8 max-w-2xl mx-auto">
        <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Layers className="w-8 h-8" />
        </div>

        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 mb-4">
          <Clock className="w-3.5 h-3.5" />
          <span>Planned for Future Phase</span>
        </span>

        <h2 className="text-xl font-bold text-slate-900 mb-2">{moduleName} Module</h2>
        <p className="text-sm text-slate-600 mb-6 max-w-md mx-auto leading-relaxed">
          {description} This module is structured in the system shell architecture and will be connected to backend engines in upcoming development sprints.
        </p>

        <div className="pt-6 border-t border-slate-100 flex justify-center">
          <Link
            href="/dashboard"
            className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
