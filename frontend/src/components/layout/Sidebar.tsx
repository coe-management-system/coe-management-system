'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Building2,
  Layers,
  FolderTree,
  CalendarCheck,
  GraduationCap,
  Award,
  CalendarDays,
  Briefcase,
  SlidersHorizontal,
  Bot,
  ShieldCheck,
  FileBarChart,
  FileSpreadsheet,
  HelpCircle,
  Settings,
  X,
} from 'lucide-react';

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Students', href: '/students', icon: Users },
  { label: 'Departments', href: '/departments', icon: Building2 },
  { label: 'Batches', href: '/batches', icon: Layers },
  { label: 'Groups', href: '/groups', icon: FolderTree },
  { label: 'Attendance', href: '/attendance', icon: CalendarCheck },
  { label: 'Training', href: '/training', icon: GraduationCap },
  { label: 'Certification', href: '/certification', icon: Award },
  { label: 'Timetable', href: '/timetable', icon: CalendarDays },
  { label: 'Workload', href: '/workload', icon: Briefcase },
  { label: 'Scheduling', href: '/scheduling', icon: SlidersHorizontal },
  { label: 'AI Assistant', href: '/ai-assistant', icon: Bot },
  { label: 'Center of Excellence', href: '/coe', icon: ShieldCheck },
  { label: 'Imports', href: '/imports', icon: FileSpreadsheet },
  { label: 'What-If Analysis', href: '/what-if', icon: HelpCircle },
  { label: 'Reports', href: '/reports', icon: FileBarChart },
  { label: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onCloseMobile }) => {
  const pathname = usePathname();

  const isNavActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard';
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-slate-300 flex flex-col transition-transform duration-300 ease-in-out border-r border-slate-800 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Sidebar Header / Branding */}
        <div className="h-16 px-5 flex items-center justify-between border-b border-slate-800 shrink-0">
          <Link href="/dashboard" className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-indigo-900/30 group-hover:scale-105 transition-transform shrink-0">
              CoE
            </div>
            <div className="min-w-0">
              <h1 className="text-xs font-bold text-white tracking-tight group-hover:text-indigo-300 transition-colors truncate">
                Center of Excellence Ops
              </h1>
              <p className="text-[9px] text-slate-400 font-medium truncate">Academic Management System</p>
            </div>
          </Link>

          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            aria-label="Close Sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Section */}
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1 custom-scrollbar">
          <div className="px-3 py-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Main Navigation
          </div>

          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isNavActive(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onCloseMobile}
                className={`flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 group ${
                  active
                    ? 'bg-indigo-600 text-white font-semibold shadow-sm shadow-indigo-900/40'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    active ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                <span>{item.label}</span>
                {item.href === '/dashboard' && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400" />
                )}
                {item.href === '/students' && (
                  <span className="ml-auto px-1.5 py-0.5 text-[10px] bg-slate-800 text-indigo-300 rounded font-semibold">
                    1.2k
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 shrink-0">
          <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-800 flex items-center space-x-3">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <div className="text-[11px]">
              <div className="font-semibold text-slate-200">System Online</div>
              <div className="text-slate-400 text-[10px]">Member 4 Frontend Active</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
