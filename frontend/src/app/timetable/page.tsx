'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Clock, MapPin, Info, Filter } from 'lucide-react';

interface TimeSlot {
  time: string;
  monday?: { subject: string; code: string; room: string; faculty: string };
  tuesday?: { subject: string; code: string; room: string; faculty: string };
  wednesday?: { subject: string; code: string; room: string; faculty: string };
  thursday?: { subject: string; code: string; room: string; faculty: string };
  friday?: { subject: string; code: string; room: string; faculty: string };
}

const TIMETABLE_SLOTS: TimeSlot[] = [
  {
    time: '09:00 AM - 10:00 AM',
    monday: { subject: 'Data Structures & Algorithms', code: 'CS301', room: 'Hall 101', faculty: 'Dr. S. Ramanujan' },
    tuesday: { subject: 'Database Management Systems', code: 'CS302', room: 'Lab 2', faculty: 'Prof. A. Kulkarni' },
    wednesday: { subject: 'Operating Systems Architecture', code: 'CS303', room: 'Hall 102', faculty: 'Dr. M. Roy' },
    thursday: { subject: 'Computer Networks & Protocols', code: 'CS304', room: 'Lab 4', faculty: 'Dr. P. Sharma' },
    friday: { subject: 'Machine Learning Fundamentals', code: 'CS305', room: 'CoE AI Lab', faculty: 'Dr. V. Gupta' },
  },
  {
    time: '10:15 AM - 11:15 AM',
    monday: { subject: 'Computer Networks & Protocols', code: 'CS304', room: 'Lab 4', faculty: 'Dr. P. Sharma' },
    tuesday: { subject: 'Data Structures & Algorithms', code: 'CS301', room: 'Hall 101', faculty: 'Dr. S. Ramanujan' },
    wednesday: { subject: 'Machine Learning Fundamentals', code: 'CS305', room: 'CoE AI Lab', faculty: 'Dr. V. Gupta' },
    thursday: { subject: 'Operating Systems Architecture', code: 'CS303', room: 'Hall 102', faculty: 'Dr. M. Roy' },
    friday: { subject: 'Database Management Systems', code: 'CS302', room: 'Lab 2', faculty: 'Prof. A. Kulkarni' },
  },
  {
    time: '11:30 AM - 12:30 PM',
    monday: { subject: 'Machine Learning Fundamentals', code: 'CS305', room: 'CoE AI Lab', faculty: 'Dr. V. Gupta' },
    tuesday: { subject: 'Operating Systems Architecture', code: 'CS303', room: 'Hall 102', faculty: 'Dr. M. Roy' },
    wednesday: { subject: 'Database Management Systems', code: 'CS302', room: 'Lab 2', faculty: 'Prof. A. Kulkarni' },
    thursday: { subject: 'Data Structures & Algorithms', code: 'CS301', room: 'Hall 101', faculty: 'Dr. S. Ramanujan' },
    friday: { subject: 'CoE Hands-on Project Lab', code: 'CS306', room: 'CoE Main Hub', faculty: 'Team Instructors' },
  },
  {
    time: '01:30 PM - 03:30 PM',
    monday: { subject: 'CoE AI & Robotics Lab', code: 'LAB301', room: 'CoE Robotics Lab', faculty: 'Dr. V. Gupta' },
    tuesday: { subject: 'Cloud Infrastructure Practical', code: 'LAB302', room: 'AWS Cloud Lab', faculty: 'Prof. A. Kulkarni' },
    wednesday: { subject: 'Cybersecurity SOC Practicum', code: 'LAB303', room: 'Cyber SOC Center', faculty: 'Dr. P. Sharma' },
    thursday: { subject: 'VLSI Chip Design Simulation', code: 'LAB304', room: 'VLSI CAD Suite', faculty: 'Dr. M. Roy' },
    friday: { subject: 'Weekly Capstone Seminar', code: 'SEM301', room: 'Auditorium A', faculty: 'Department Chair' },
  },
];

export default function TimetablePage() {
  const [department, setDepartment] = useState('Computer Science');
  const [batch, setBatch] = useState('Batch 2022-2026');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Academic & CoE Master Timetable"
        subtitle="Institutional Weekly Class Schedule, Room Allocations & Laboratory Assignments"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Timetable' }]}
      />

      {/* Backend Dependency Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-800">
        <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Backend Dependency Notice: </span>
          The live Timetable API (<code className="bg-amber-100 px-1 py-0.5 rounded text-[11px]">GET /api/v1/timetable</code>) is pending implementation by Member 3. Operating in client-side preview mode.
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
              {TIMETABLE_SLOTS.map((slot) => (
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
