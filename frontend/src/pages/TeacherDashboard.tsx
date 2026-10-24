import React, { useState } from 'react';
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  Calendar,
  Video,
  FileText,
  ChevronRight,
  ExternalLink,
  Upload,
} from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import { HealthBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { TeacherMediaManager } from '../components/media/TeacherMediaManager';
import { TeacherAssessmentConsole } from '../components/assessment/TeacherAssessmentConsole';

export const TeacherDashboard: React.FC = () => {
  const { user } = useAuth();
  const [showMediaManager, setShowMediaManager] = useState<boolean>(false);
  const [showAssessmentConsole, setShowAssessmentConsole] = useState<boolean>(false);

  // Mock data clearly isolated for development preview
  const triageStudents = [
    {
      id: '1',
      name: 'Student 135 Patel',
      roll: 'ROLL-2026-135',
      batch: 'Class 9 Foundation Olympiad',
      status: 'AT_RISK',
      inactiveDays: 5,
      missingAssignments: 4,
      reason: 'No video progress in 5 days; 4 consecutive missing assignments',
    },
    {
      id: '2',
      name: 'Student 142 Kumar',
      roll: 'ROLL-2026-142',
      batch: 'Class 9 Foundation Olympiad',
      status: 'AT_RISK',
      inactiveDays: 6,
      missingAssignments: 3,
      reason: 'Milestone test score < 25%; absent from last 2 live classes',
    },
    {
      id: '3',
      name: 'Student 105 Kumar',
      roll: 'ROLL-2026-105',
      batch: 'Class 10 STEM Evening',
      status: 'NEEDS_ATTENTION',
      inactiveDays: 2,
      missingAssignments: 1,
      reason: 'Resubmission requested for Chapter 2 homework',
    },
    {
      id: '4',
      name: 'Student 112 Patel',
      roll: 'ROLL-2026-112',
      batch: 'Class 10 STEM Evening',
      status: 'NEEDS_ATTENTION',
      inactiveDays: 3,
      missingAssignments: 2,
      reason: 'Video completion rate dropped to 52%',
    },
  ];

  const pendingGrading = [
    {
      id: 'sub-1',
      student: 'Student 014 Sharma',
      roll: 'ROLL-2026-014',
      assignment: 'Math HW 03: Quadratic Equations',
      pages: 3,
      submittedAt: 'Today, 04:15 PM',
      attempt: 1,
    },
    {
      id: 'sub-2',
      student: 'Student 028 Patel',
      roll: 'ROLL-2026-028',
      assignment: 'Science HW 02: Chemical Reactions',
      pages: 2,
      submittedAt: 'Today, 03:50 PM',
      attempt: 1,
    },
    {
      id: 'sub-3',
      student: 'Student 105 Kumar',
      roll: 'ROLL-2026-105',
      assignment: 'Math HW 02: Polynomials (Resubmission)',
      pages: 4,
      submittedAt: 'Today, 02:10 PM',
      attempt: 2,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome & Top Actions Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">
            Welcome, {user?.full_name}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Tracking 150 students across Class 10 STEM & Class 9 Foundation batches.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowMediaManager(true)}
            icon={<Upload className="h-4 w-4" />}
          >
            Upload Media
          </Button>
          <Button size="sm" variant="outline" icon={<Calendar className="h-4 w-4" />}>
            Schedule Class
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowAssessmentConsole(true)}
            icon={<FileText className="h-4 w-4" />}
          >
            Assessments & Grading
          </Button>
        </div>
      </div>

      {/* Compliance Metric Counters */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Watched Today</span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <Video className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">88</span>
            <span className="text-xs text-slate-400">/ 150 students (58%)</span>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">HW Submitted</span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <CheckCircle className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">92</span>
            <span className="text-xs text-slate-400">/ 150 students (61%)</span>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Pending Grading</span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <Clock className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">14</span>
            <span className="text-xs text-slate-400">submissions</span>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">At Risk Flagged</span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
              <AlertTriangle className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-600">20</span>
            <span className="text-xs text-slate-400">need triage</span>
          </div>
        </Card>
      </div>

      {/* Main Grid: At Risk Triage & Today's Schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* At-Risk Students Triage (Takes 2 columns on desktop) */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Students Needing Immediate Attention</CardTitle>
                <CardDescription>
                  Automated pedagogical rule engine flagged 20 students based on 14-day telemetry.
                </CardDescription>
              </div>
              <span className="text-[11px] font-semibold text-indigo-600 hover:underline cursor-pointer">
                View All (20) →
              </span>
            </CardHeader>
            <CardContent className="space-y-3 pt-2">
              {triageStudents.map((st) => (
                <div
                  key={st.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl border border-slate-100 bg-slate-50/60 hover:bg-slate-50 transition-colors gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-900">{st.name}</span>
                      <span className="text-xs text-slate-400">• {st.roll}</span>
                      <HealthBadge status={st.status} size="sm" />
                    </div>
                    <p className="text-xs text-slate-600 leading-snug">{st.reason}</p>
                    <span className="text-[11px] text-slate-400 block">{st.batch}</span>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                    <Button size="sm" variant="outline">
                      Call Guardian
                    </Button>
                    <Button size="sm" variant="secondary">
                      Details
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Pending Grading Queue */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Pending Homework Grading Queue</CardTitle>
                <CardDescription>14 student submissions waiting for evaluation.</CardDescription>
              </div>
              <Button size="sm" variant="primary">
                Open Rapid Grading Console
              </Button>
            </CardHeader>
            <CardContent className="space-y-2.5 pt-2">
              {pendingGrading.map((sub) => (
                <div
                  key={sub.id}
                  className="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-900">{sub.student}</span>
                      <span className="text-[11px] text-slate-400">({sub.roll})</span>
                      {sub.attempt > 1 && (
                        <span className="text-[10px] bg-amber-50 text-amber-700 px-1.5 py-0.2 rounded-md font-medium">
                          Attempt {sub.attempt}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600">{sub.assignment}</p>
                    <p className="text-[10px] text-slate-400">
                      {sub.pages} photos attached • Submitted {sub.submittedAt}
                    </p>
                  </div>

                  <Button size="sm" variant="outline" onClick={() => setShowAssessmentConsole(true)}>
                    Grade <ChevronRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Today's Schedule & Quick Links */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Today's Live Class Schedule</CardTitle>
              <CardDescription>Google Meet live class integration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                    Live at 05:00 PM
                  </span>
                  <span className="text-[11px] text-slate-500">60 mins</span>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">
                    Quadratic Formula & Problem Solving
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Class 10 STEM Foundation (Morning & Evening)
                  </p>
                </div>
                <Button size="sm" variant="primary" className="w-full" icon={<ExternalLink className="h-3.5 w-3.5" />}>
                  Launch Google Meet Room
                </Button>
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-600">Tomorrow, 06:00 PM</span>
                  <span className="text-[11px] text-slate-400">45 mins</span>
                </div>
                <h5 className="text-xs font-semibold text-slate-800">
                  Chemical Reactions & Equations Live Doubt Clear
                </h5>
                <p className="text-[11px] text-slate-500">Science Batch 1</p>
              </div>
            </CardContent>
          </Card>

          {/* Quick Curriculum Status */}
          <Card>
            <CardHeader>
              <CardTitle>Curriculum Content Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600 font-medium">Mathematics (Class 10)</span>
                <span className="font-semibold text-slate-900">3 Chapters • 3 Lectures</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600 font-medium">Science (Class 10)</span>
                <span className="font-semibold text-slate-900">3 Chapters • 3 Lectures</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600 font-medium">Reasoning (Class 9)</span>
                <span className="font-semibold text-slate-900">3 Chapters • 3 Lectures</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="p-3 rounded-xl bg-slate-100 text-center text-[11px] text-slate-500 font-medium">
        [Development Mock Preview] Data presented above represents initial layout scaffolding; live curriculum and grading endpoints will connect in subsequent tasks.
      </div>

      {showMediaManager && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <TeacherMediaManager onClose={() => setShowMediaManager(false)} />
        </div>
      )}

      {showAssessmentConsole && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <TeacherAssessmentConsole onClose={() => setShowAssessmentConsole(false)} />
        </div>
      )}
    </div>
  );
};
