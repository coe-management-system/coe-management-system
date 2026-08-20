'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Clock, MapPin, Filter } from 'lucide-react';
import { showcaseApi, type ShowcaseTimetableEvent } from '@/lib/api/showcase';

interface TimeSlot {
  time: string;
  monday?: { subject: string; code: string; room: string; faculty: string };
  tuesday?: { subject: string; code: string; room: string; faculty: string };
  wednesday?: { subject: string; code: string; room: string; faculty: string };
  thursday?: { subject: string; code: string; room: string; faculty: string };
  friday?: { subject: string; code: string; room: string; faculty: string };
}

const WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] as const;

function formatTimeRange(startTime: string): string {
  const [hour, minute] = startTime.split(':').map(Number);
  const endMinutes = hour * 60 + minute + 60;
  const endHour = Math.floor(endMinutes / 60) % 24;
  const endMinute = endMinutes % 60;
  const to12Hour = (h: number, m: number): string => {
    const period = h >= 12 ? 'PM' : 'AM';
    const hour12 = h % 12 === 0 ? 12 : h % 12;
    return `${String(hour12).padStart(2, '0')}:${String(m).padStart(2, '0')} ${period}`;
  };
  return `${to12Hour(hour, minute)} - ${to12Hour(endHour, endMinute)}`;
}

export default function TimetablePage() {
  const [department, setDepartment] = useState('Computer Science');
  const [batch, setBatch] = useState('Batch 2022-2026');
  const [events, setEvents] = useState<ShowcaseTimetableEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [liveData, setLiveData] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const fetched = await showcaseApi.getTimetable();
        setEvents(fetched);
        setLiveData(true);
      } catch {
        // Backend error; keep mock/empty state.
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const grid = useMemo<TimeSlot[]>(() => {
    const uniqueStarts = Array.from(new Set(events.map((e) => e.startTime)))
      .filter((start) => {
        const hour = parseInt(start.slice(0, 2), 10);
        return hour >= 8 && hour < 18;
      })
      .sort((a, b) => a.localeCompare(b));

    return uniqueStarts.map((start) => {
      const row: TimeSlot = { time: formatTimeRange(start) };
      WEEKDAYS.forEach((day, index) => {
        const event = events.find((e) => e.startTime === start && e.dayIndex === index + 1);
        if (event) {
          row[day] = { subject: event.subject, code: event.code, room: event.room, faculty: event.faculty };
        }
      });
      return row;
    });
  }, [events]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Academic & CoE Master Timetable"
        subtitle="Institutional Weekly Class Schedule, Room Allocations & Laboratory Assignments"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Timetable' }]}
      />

      {/* Live API Status Banner */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-start space-x-3 text-xs text-emerald-800">
        <div>
          {loading ? (
            'Loading live timetable from backend...'
          ) : liveData ? (
            <>
              <span className="font-bold">Live API Data: </span>
              GET /api/v1/timetable connected. Showing {events.length} scheduled sessions.
            </>
          ) : (
            <>
              <span className="font-bold">Offline Preview Mode: </span>
              Backend unreachable; showing local preview data.
            </>
          )}
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-semibold">
            <Filter className="w-3.5 h-3.5" />
            <span>Select Cohort:</span>
          </div>

          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            <option value="Computer Science">Computer Science & Eng.</option>
            <option value="Electronics & Comm.">Electronics & Comm. Eng.</option>
            <option value="Mechanical Eng.">Mechanical Eng.</option>
          </select>

          <select
            value={batch}
            onChange={(e) => setBatch(e.target.value)}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            <option value="Batch 2022-2026">Batch 2022-2026 (Semester 6)</option>
            <option value="Batch 2023-2027">Batch 2023-2027 (Semester 4)</option>
          </select>
        </div>

        <div className="text-xs text-slate-500 font-medium">
          Showing schedule for <span className="font-bold text-slate-900">{department} ({batch})</span>
        </div>
      </div>

      {/* Weekly Grid */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-900 text-white font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4 border-r border-slate-800 w-44">Time Slot</th>
                <th className="py-3.5 px-4 border-r border-slate-800">Monday</th>
                <th className="py-3.5 px-4 border-r border-slate-800">Tuesday</th>
                <th className="py-3.5 px-4 border-r border-slate-800">Wednesday</th>
                <th className="py-3.5 px-4 border-r border-slate-800">Thursday</th>
                <th className="py-3.5 px-4">Friday</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {grid.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-10 px-4 text-center text-slate-400 italic">
                    No sessions scheduled.
                  </td>
                </tr>
              )}
              {grid.map((slot) => (
                <tr key={slot.time} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-4 px-4 font-bold text-slate-700 bg-slate-50/80 border-r border-slate-200">
                    <div className="flex items-center space-x-1.5 text-indigo-600 mb-0.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span className="text-[11px] font-mono">{slot.time}</span>
                    </div>
                  </td>

                  {['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].map((day) => {
                    const session = slot[day as keyof TimeSlot] as {
                      subject: string;
                      code: string;
                      room: string;
                      faculty: string;
                    };

                    if (!session) {
                      return <td key={day} className="py-4 px-4 border-r border-slate-200 text-slate-300 italic">Recess / Break</td>;
                    }

                    return (
                      <td key={day} className="py-3.5 px-4 border-r border-slate-200 align-top">
                        <div className="p-2.5 bg-indigo-50/50 border border-indigo-100 rounded-xl space-y-1">
                          <div className="font-bold text-slate-900 leading-snug">{session.subject}</div>
                          <div className="flex items-center justify-between text-[10px] text-slate-500">
                            <span className="font-mono text-indigo-700 font-semibold">{session.code}</span>
                            <span className="flex items-center space-x-0.5 font-medium text-slate-600">
                              <MapPin className="w-3 h-3 text-slate-400" />
                              <span>{session.room}</span>
                            </span>
                          </div>
                          <div className="text-[10px] text-slate-600 font-medium pt-0.5 border-t border-indigo-100/60">
                            {session.faculty}
                          </div>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
