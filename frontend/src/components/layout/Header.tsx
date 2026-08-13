'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { MOCK_USER } from '@/lib/mock-data/auth';
import {
  Menu,
  Search,
  Bell,
  LogOut,
  ChevronDown,
  User as UserIcon,
  ShieldAlert,
  Building,
} from 'lucide-react';

interface HeaderProps {
  onOpenMobileSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileSidebar }) => {
  const router = useRouter();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const handleLogout = () => {
    setDropdownOpen(false);
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      {/* Left Area: Mobile Menu & Search */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Open Sidebar Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Institutional Search */}
        <div className="relative hidden md:block w-64 lg:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search students, roll numbers, Center of Excellence tracks..."
            className="w-full pl-9 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Right Area: System Status, Notifications & User Pill */}
      <div className="flex items-center space-x-3">
        {/* Institutional Academic Badge */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
          <Building className="w-3.5 h-3.5 text-indigo-600" />
          <span className="font-semibold text-slate-800">Academic Ops</span>
          <span className="text-slate-300">|</span>
          <span className="text-slate-500 font-medium">AY 2026-27</span>
        </div>

        {/* Notifications Dropdown Toggle */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white" />
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl border border-slate-200 shadow-lg p-3 z-50 animate-in fade-in-50 duration-100">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-900">Notifications & Alerts</span>
                <span className="text-[10px] font-semibold bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded">
                  3 High Priority
                </span>
              </div>
              <div className="py-2 space-y-2 max-h-60 overflow-y-auto">
                <div className="p-2 hover:bg-slate-50 rounded-lg text-xs cursor-pointer border border-transparent hover:border-slate-100">
                  <div className="flex items-center space-x-1.5 text-red-600 font-semibold text-[11px] mb-0.5">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Low Attendance Alert</span>
                  </div>
                  <p className="text-slate-600 text-[11px] line-clamp-2">
                    Mechanical Batch 2024 (Group B1) attendance dropped to 74.2%.
                  </p>
                </div>
                <div className="p-2 hover:bg-slate-50 rounded-lg text-xs cursor-pointer border border-transparent hover:border-slate-100">
                  <div className="flex items-center space-x-1.5 text-amber-600 font-semibold text-[11px] mb-0.5">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Exam Registration Capacity</span>
                  </div>
                  <p className="text-slate-600 text-[11px] line-clamp-2">
                    Palo Alto PCCET exam seats 98% booked.
                  </p>
                </div>
              </div>
              <div className="pt-2 border-t border-slate-100 text-center">
                <Link
                  href="/dashboard"
                  onClick={() => setNotificationsOpen(false)}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                >
                  View All Alerts on Dashboard
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill & Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center space-x-2.5 p-1.5 pl-2.5 rounded-xl hover:bg-slate-100 transition-colors border border-transparent hover:border-slate-200"
          >
            <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white font-bold flex items-center justify-center text-xs">
              SJ
            </div>
            <div className="hidden sm:block text-left">
              <div className="text-xs font-bold text-slate-800 leading-tight">{MOCK_USER.name}</div>
              <div className="text-[10px] text-slate-500 font-medium">Center of Excellence Administrator</div>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl border border-slate-200 shadow-xl py-1 z-50">
              <div className="px-4 py-2.5 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-900">{MOCK_USER.name}</p>
                <p className="text-[11px] text-slate-500 truncate">{MOCK_USER.email}</p>
              </div>
              <Link
                href="/settings"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center space-x-2 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50"
              >
                <UserIcon className="w-4 h-4 text-slate-400" />
                <span>Account Profile</span>
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center space-x-2 px-4 py-2 text-xs text-rose-600 hover:bg-rose-50 border-t border-slate-100 text-left font-medium"
              >
                <LogOut className="w-4 h-4" />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
