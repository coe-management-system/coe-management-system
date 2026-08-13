import React from 'react';
import { Student } from '@/types/student';
import { StatusBadge } from '@/components/ui/StatusBadge';
import {
  Mail,
  Phone,
  Building2,
  Calendar,
  Award,
  BookOpen,
  Zap,
} from 'lucide-react';

interface StudentProfileViewProps {
  student: Student;
}

export const StudentProfileView: React.FC<StudentProfileViewProps> = ({ student }) => {
  const readiness = student.readiness || {
    overallScore: 85,
    grade: 'A',
    technicalRating: 88,
    aptitudeRating: 85,
    softSkillsRating: 82,
    recommendation: 'Recommended for Core Industry Placement',
  };

  const roll = student.roll_no || student.rollNumber || '';
  const subjectAttendance = student.subjectAttendance || [];
  const trainingTracks = student.trainingTracks || [];
  const certifications = student.certifications || [];
  const skills = student.skills || [];

  return (
    <div className="space-y-6">
      {/* Student Header 360 Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-full blur-3xl -z-0 opacity-70" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-800 text-white font-bold text-2xl flex items-center justify-center shadow-md shadow-indigo-900/20 shrink-0">
              {student.name ? student.name.split(' ').map((n) => n[0]).join('') : 'ST'}
            </div>

            <div>
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold text-slate-900">{student.name}</h2>
                <StatusBadge status={student.status || 'Active'} />
                <StatusBadge status={readiness.grade} type="readiness" />
              </div>
              <p className="text-xs text-slate-500 font-mono mt-0.5">Roll No: {roll} | ID: {student.id}</p>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3 text-xs text-slate-600">
                <span className="flex items-center space-x-1">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  <span>{student.email}</span>
                </span>
                {student.phone && (
                  <span className="flex items-center space-x-1">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{student.phone}</span>
                  </span>
                )}
                <span className="flex items-center space-x-1">
                  <Building2 className="w-3.5 h-3.5 text-indigo-500" />
                  <span className="font-semibold text-slate-800">{student.department}</span>
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 shrink-0">
            <div className="text-center px-3 border-r border-slate-200">
              <div className="text-[10px] uppercase font-bold text-slate-400">Batch</div>
              <div className="text-xs font-bold text-slate-800">{student.batch}</div>
            </div>
            <div className="text-center px-3 border-r border-slate-200">
              <div className="text-[10px] uppercase font-bold text-slate-400">Group</div>
              <div className="text-xs font-bold text-indigo-600">{student.group}</div>
            </div>
            <div className="text-center px-3">
              <div className="text-[10px] uppercase font-bold text-slate-400">Audit Status</div>
              <StatusBadge status={student.reportAuditStatus || 'Verified'} />
            </div>
          </div>
        </div>
      </div>

      {/* Grid Section: Readiness Index & Attendance Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Industry Readiness Index (1 Col) */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-amber-500" />
                <h3 className="text-sm font-bold text-slate-900">Industry Readiness 360</h3>
              </div>
              <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                Grade {readiness.grade}
              </span>
            </div>

            <div className="my-4 text-center p-4 bg-gradient-to-b from-indigo-50/50 to-white rounded-xl border border-indigo-100">
              <div className="text-3xl font-extrabold text-slate-900 tracking-tight">
                {readiness.overallScore} <span className="text-base font-normal text-slate-400">/ 100</span>
              </div>
              <p className="text-xs text-slate-500 mt-1 font-medium">Overall Employability & Skill Index</p>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Technical Proficiency</span>
                  <span>{readiness.technicalRating}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-indigo-600 h-full rounded-full" style={{ width: `${readiness.technicalRating}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Aptitude & Problem Solving</span>
                  <span>{readiness.aptitudeRating}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${readiness.aptitudeRating}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Soft Skills & Communication</span>
                  <span>{readiness.softSkillsRating}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-purple-500 h-full rounded-full" style={{ width: `${readiness.softSkillsRating}%` }} />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-slate-100 bg-slate-50 p-3 rounded-lg text-xs text-slate-600">
            <span className="font-semibold text-slate-800">Recommendation: </span>
            {readiness.recommendation}
          </div>
        </div>

        {/* Academic Attendance Profile (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Academic Attendance Profile</h3>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500">Overall:</span>
              <span className="text-sm font-extrabold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-100">
                {student.attendancePercentage ?? 88}%
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {subjectAttendance.map((subj) => (
              <div key={subj.subjectCode} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 mb-1.5">
                  <span>
                    {subj.subjectName} <span className="text-slate-400 font-mono">({subj.subjectCode})</span>
                  </span>
                  <span>
                    {subj.attended} / {subj.total} Classes ({subj.percentage}%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      subj.percentage >= 90
                        ? 'bg-emerald-500'
                        : subj.percentage >= 80
                        ? 'bg-amber-500'
                        : 'bg-rose-500'
                    }`}
                    style={{ width: `${subj.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Grid Section: Training Tracks & Certifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CoE Training Tracks */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Enrolled Center of Excellence Training Tracks</h3>
            </div>
          </div>

          {trainingTracks.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4 text-center">No active training tracks enrolled.</p>
          ) : (
            <div className="space-y-3">
              {trainingTracks.map((track) => (
                <div key={track.id} className="p-3.5 border border-slate-200 rounded-xl bg-slate-50/50">
                  <div className="flex items-start justify-between mb-1.5">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{track.name}</h4>
                      <p className="text-[11px] text-slate-500">{track.provider}</p>
                    </div>
                    <StatusBadge status={track.status} />
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                    <span>Progress: {track.progress}%</span>
                    <span>Enrolled: {track.enrolledDate}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Verified Certifications */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Award className="w-5 h-5 text-purple-600" />
              <h3 className="text-sm font-bold text-slate-900">Verified Center of Excellence Industry Credentials</h3>
            </div>
          </div>

          {certifications.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4 text-center">No verified certifications earned yet.</p>
          ) : (
            <div className="space-y-3">
              {certifications.map((cert) => (
                <div key={cert.id} className="p-3.5 border border-purple-100 rounded-xl bg-purple-50/30">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{cert.name}</h4>
                      <p className="text-[11px] text-slate-600">{cert.issuingBody}</p>
                      <p className="text-[10px] text-slate-400 font-mono mt-1">Cred ID: {cert.credentialId}</p>
                    </div>
                    <StatusBadge status={cert.status} />
                  </div>
                  <div className="mt-2 text-[10px] text-slate-500">Issued Date: {cert.issueDate}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Skills Matrix */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-3">Verified Skills Matrix</h3>
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <span
              key={skill}
              className="px-3 py-1 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition-colors"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
