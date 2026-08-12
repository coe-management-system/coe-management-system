import React from 'react';
import { DepartmentType, BatchType, GroupType } from '@/types/student';
import { Search, Filter, RotateCcw } from 'lucide-react';

interface StudentFiltersProps {
  searchQuery: string;
  department: string;
  batch: string;
  group: string;
  onSearchChange: (value: string) => void;
  onDepartmentChange: (value: string) => void;
  onBatchChange: (value: string) => void;
  onGroupChange: (value: string) => void;
  onResetFilters: () => void;
}

const DEPARTMENTS: (DepartmentType | 'All')[] = [
  'All',
  'Computer Science',
  'Electronics',
  'Information Tech',
  'Mechanical',
  'Civil',
];

const BATCHES: (BatchType | 'All')[] = ['All', '2023-2027', '2024-2028', '2022-2026'];
const GROUPS: (GroupType | 'All')[] = ['All', 'A1', 'A2', 'B1', 'B2'];

export const StudentFilters: React.FC<StudentFiltersProps> = ({
  searchQuery,
  department,
  batch,
  group,
  onSearchChange,
  onDepartmentChange,
  onBatchChange,
  onGroupChange,
  onResetFilters,
}) => {
  const isFilterActive = searchQuery !== '' || department !== 'All' || batch !== 'All' || group !== 'All';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-4 mb-6 shadow-xs space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
          <Filter className="w-4 h-4 text-indigo-600" />
          <span>Student Directory Filters</span>
        </div>
        {isFilterActive && (
          <button
            onClick={onResetFilters}
            className="inline-flex items-center space-x-1 text-xs font-semibold text-rose-600 hover:text-rose-800 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Filters</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by name, roll #, email..."
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          />
        </div>

        {/* Department Filter */}
        <div>
          <select
            value={department}
            onChange={(e) => onDepartmentChange(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          >
            <option value="All">All Departments</option>
            {DEPARTMENTS.filter((d) => d !== 'All').map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>

        {/* Batch Filter */}
        <div>
          <select
            value={batch}
            onChange={(e) => onBatchChange(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          >
            <option value="All">All Academic Batches</option>
            {BATCHES.filter((b) => b !== 'All').map((b) => (
              <option key={b} value={b}>
                Batch {b}
              </option>
            ))}
          </select>
        </div>

        {/* Group Filter */}
        <div>
          <select
            value={group}
            onChange={(e) => onGroupChange(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          >
            <option value="All">All Lab Groups</option>
            {GROUPS.filter((g) => g !== 'All').map((g) => (
              <option key={g} value={g}>
                Group {g}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};
