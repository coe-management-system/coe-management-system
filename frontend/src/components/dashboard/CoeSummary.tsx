import React from 'react';
import { CoeSummaryData } from '@/types/dashboard';
import { ShieldCheck, Award, Users, Cpu, ArrowUpRight } from 'lucide-react';

interface CoeSummaryProps {
  coeSummaries: CoeSummaryData[];
}

export const CoeSummary: React.FC<CoeSummaryProps> = ({ coeSummaries }) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Centers of Excellence Overview</h3>
            <p className="text-xs text-slate-500">Active industry partner hubs, student throughput & lab performance</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {coeSummaries.map((coe) => (
          <div
            key={coe.id}
            className="border border-slate-200 rounded-xl p-5 hover:border-indigo-300 transition-all bg-gradient-to-br from-white to-slate-50/50 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                    {coe.vendor}
                  </span>
                  <h4 className="text-lg font-bold text-slate-900 mt-1">{coe.name}</h4>
                  <p className="text-xs text-slate-500">{coe.partnerLevel}</p>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200 uppercase">
                  {coe.status}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
                <div className="p-3 bg-white rounded-lg border border-slate-100">
                  <div className="flex items-center text-slate-400 mb-1">
                    <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                    <span className="text-[10px]">Tracks</span>
                  </div>
                  <div className="text-base font-bold text-slate-900">{coe.activeTracks}</div>
                </div>

                <div className="p-3 bg-white rounded-lg border border-slate-100">
                  <div className="flex items-center text-slate-400 mb-1">
                    <Users className="w-3.5 h-3.5 mr-1" />
                    <span className="text-[10px]">Students</span>
                  </div>
                  <div className="text-base font-bold text-slate-900">{coe.enrolledStudents}</div>
                </div>

                <div className="p-3 bg-white rounded-lg border border-slate-100">
                  <div className="flex items-center text-slate-400 mb-1">
                    <Award className="w-3.5 h-3.5 mr-1" />
                    <span className="text-[10px]">Certs</span>
                  </div>
                  <div className="text-base font-bold text-slate-900">{coe.certificationsCompleted}</div>
                </div>

                <div className="p-3 bg-white rounded-lg border border-slate-100">
                  <div className="flex items-center text-slate-400 mb-1">
                    <Cpu className="w-3.5 h-3.5 mr-1" />
                    <span className="text-[10px]">Lab Usage</span>
                  </div>
                  <div className="text-base font-bold text-slate-900">{coe.labUtilizationRate}%</div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-600">
              <span>
                Lead Faculty: <strong className="text-slate-800 font-semibold">{coe.leadFaculty}</strong>
              </span>
              <button className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800">
                <span>Center of Excellence Dashboard</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
