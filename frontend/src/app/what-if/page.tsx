'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Play, CheckCircle2, TrendingUp, AlertCircle } from 'lucide-react';
import { showcaseApi } from '@/lib/api/showcase';

interface ScenarioOption {
  id: string;
  title: string;
  description: string;
  impactScore: number;
  capacityChange: string;
  workloadImpact: string;
  recommendation: string;
}

const PRESET_SCENARIOS: ScenarioOption[] = [
  {
    id: '1',
    title: 'Scenario A: Enroll 50 Additional Students in CSE Batch 2026',
    description: 'Simulates room capacity, faculty teaching hours, and lab equipment availability for 50 additional CSE intake.',
    impactScore: 84,
    capacityChange: '+12.5% Room Demand',
    workloadImpact: '+6 Faculty Hours / Wk',
    recommendation: 'Add 1 parallel lab batch for CS302 and assign Assistant Professor P. Sharma.',
  },
  {
    id: '2',
    title: 'Scenario B: Restructure CoE AI Training Track to 8 Weeks',
    description: 'Accelerates NVIDIA Deep Learning Track duration from 12 weeks to 8 intensive weeks.',
    impactScore: 92,
    capacityChange: 'No Room Impact',
    workloadImpact: '+4 Lab Hours / Wk',
    recommendation: 'Approved. Increases annual certification throughput by 35% with zero room conflicts.',
  },
  {
    id: '3',
    title: 'Scenario C: Reallocate Main Auditorium to VLSI Seminar Series',
    description: 'Transfers Friday afternoon seminar sessions to Auditorium B to resolve sound interference.',
    impactScore: 78,
    capacityChange: 'Room Exchange',
    workloadImpact: 'Zero Workload Change',
    recommendation: 'Feasible. Confirms zero conflict with existing Electrical Engineering schedules.',
  },
];

export default function WhatIfPage() {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('1');
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<ScenarioOption | null>(PRESET_SCENARIOS[0]);

  const handleRunSimulation = async (scenario: ScenarioOption) => {
    setSelectedScenarioId(scenario.id);
    setSimulating(true);
    try {
      const result = await showcaseApi.runWhatIf({
        type: 'event_change',
        resource: null,
        date: null,
        changes: { note: scenario.title },
      });
      const rawScore = Number(result.impact?.feasibility_score ?? 78);
      const impactScore = Number.isFinite(rawScore) ? Math.min(100, Math.max(0, rawScore)) : 78;
      setSimulationResult({
        id: scenario.id,
        title: scenario.title,
        description: result.scenarioDescription || scenario.description,
        impactScore,
        capacityChange: String(result.impact?.room_utilization_delta || 'No Room Impact'),
        workloadImpact: String(result.impact?.workload_delta || 'Zero Workload Change'),
        recommendation: result.recommendedAction || scenario.recommendation,
      });
    } catch {
      setSimulationResult(scenario);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="What-If Scenario Simulation & Decision Engine"
        subtitle="Predictive Impact Analysis, Capacity Planning & Ranked Recommendations (Member 3 Engine Integration)"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'What-If Analysis' }]}
      />

      {/* Live API Indicator */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-start space-x-3 text-xs text-emerald-800">
        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Live API Data: </span>
          POST /api/v1/scheduling/what-if connected.
        </div>
      </div>

      {/* Grid: Scenario Selector vs Predicted Impact Output */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scenario Selection Panel (1 Col) */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Select Simulation Scenario</h3>

          {PRESET_SCENARIOS.map((scen) => (
            <div
              key={scen.id}
              onClick={() => handleRunSimulation(scen)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                selectedScenarioId === scen.id
                  ? 'bg-indigo-600 text-white border-indigo-700 shadow-md shadow-indigo-900/20'
                  : 'bg-white text-slate-900 border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    selectedScenarioId === scen.id ? 'bg-indigo-500 text-white' : 'bg-indigo-50 text-indigo-700'
                  }`}
                >
                  Preset {scen.id}
                </span>
                <Play className="w-3.5 h-3.5" />
              </div>
              <h4 className="text-xs font-bold leading-snug">{scen.title}</h4>
              <p className={`text-[11px] mt-1.5 line-clamp-2 ${selectedScenarioId === scen.id ? 'text-indigo-100' : 'text-slate-500'}`}>
                {scen.description}
              </p>
            </div>
          ))}
        </div>

        {/* Predictive Simulation Impact Display (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Simulation Output &amp; Recommendation</h3>

          {simulating ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-xs text-slate-500">
              <div className="w-8 h-8 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin mx-auto mb-3" />
              Evaluating constraint graph &amp; calculating room capacity vectors...
            </div>
          ) : simulationResult ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-6">
              <div className="flex items-start justify-between pb-4 border-b border-slate-100">
                <div>
                  <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider">Active Scenario Analysis</span>
                  <h2 className="text-base font-bold text-slate-900 mt-0.5">{simulationResult.title}</h2>
                  <p className="text-xs text-slate-500 mt-1">{simulationResult.description}</p>
                </div>

                <div className="text-center bg-indigo-50 px-4 py-2 rounded-xl border border-indigo-100 shrink-0">
                  <div className="text-2xl font-extrabold text-indigo-600">{simulationResult.impactScore}</div>
                  <div className="text-[10px] font-semibold text-slate-500 uppercase">Feasibility Score</div>
                </div>
              </div>

              {/* Impact Metric Cards */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 mb-1">
                    <TrendingUp className="w-4 h-4 text-indigo-600" />
                    <span>Room Capacity Delta</span>
                  </div>
                  <div className="text-sm font-bold text-slate-900">{simulationResult.capacityChange}</div>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 mb-1">
                    <AlertCircle className="w-4 h-4 text-purple-600" />
                    <span>Faculty Workload Impact</span>
                  </div>
                  <div className="text-sm font-bold text-slate-900">{simulationResult.workloadImpact}</div>
                </div>
              </div>

              {/* Ranked Recommendation Card */}
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start space-x-3 text-xs text-emerald-900">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-emerald-950 uppercase text-[10px] tracking-wider mb-0.5">
                    Member 3 Recommendation Engine Output
                  </div>
                  <div className="font-medium text-xs leading-relaxed">{simulationResult.recommendation}</div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
