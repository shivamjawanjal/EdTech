import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlayCircle,
  FileText,
  Clock,
  Calendar,
  AlertCircle,
  ChevronRight,
  Camera,
} from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import { HealthBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { StudentAttachmentUploader } from '../components/media/StudentAttachmentUploader';

export const StudentHome: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeSubject, setActiveSubject] = useState<'MATH' | 'SCI' | 'REAS'>('MATH');
  const [showUploader, setShowUploader] = useState<boolean>(false);

  return (
    <div className="space-y-5 max-w-4xl mx-auto">
      {/* Student Greeting & Weekly Summary Card */}
      <div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-indigo-800 p-5 sm:p-6 text-white shadow-md shadow-indigo-100">
        <div className="flex items-start justify-between">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-2.5 py-0.5 text-[11px] font-semibold text-white backdrop-blur-xs mb-2">
              Roll No: {user?.profile?.roll_number || '2026-001'} • {user?.profile?.grade_level || 'Class 10'}
            </span>
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
              Hello, {user?.full_name?.split(' ')[0]}!
            </h1>
            <p className="text-xs text-indigo-100 mt-0.5">
              Target: {user?.profile?.target_exam || 'Board Exam + Olympiad'}
            </p>
          </div>

          <div className="text-right">
            <span className="text-[11px] text-indigo-200 block">Health Status</span>
            <HealthBadge status="ON_TRACK" size="sm" className="mt-1 bg-white text-emerald-800" />
          </div>
        </div>

        {/* Weekly Progress Bar */}
        <div className="mt-5 pt-4 border-t border-indigo-500/50">
          <div className="flex items-center justify-between text-xs font-medium mb-1.5 text-indigo-100">
            <span>Weekly Target Completion</span>
            <span className="font-bold text-white">4 / 5 Lessons (80%)</span>
          </div>
          <div className="h-2 w-full rounded-full bg-indigo-950/30 overflow-hidden">
            <div className="h-full rounded-full bg-emerald-400 w-4/5 transition-all duration-500" />
          </div>
        </div>
      </div>

      {/* Subject Selector Tabs (Mobile thumb friendly) */}
      <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-200/80 max-w-md mx-auto sm:mx-0">
        <button
          onClick={() => setActiveSubject('MATH')}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all min-h-[40px] ${
            activeSubject === 'MATH'
              ? 'bg-white text-indigo-700 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Mathematics
        </button>
        <button
          onClick={() => setActiveSubject('SCI')}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all min-h-[40px] ${
            activeSubject === 'SCI'
              ? 'bg-white text-indigo-700 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Science
        </button>
        <button
          onClick={() => setActiveSubject('REAS')}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all min-h-[40px] ${
            activeSubject === 'REAS'
              ? 'bg-white text-indigo-700 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Reasoning
        </button>
      </div>

      {/* TODAY'S MISSION: Primary Learning CTA */}
      <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/40 to-white overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-indigo-700">
              <PlayCircle className="h-4 w-4" />
              <span>Next Video Lesson</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 sm:text-lg">
              Lecture 03: Quadratic Equations & Discriminant Method
            </h3>
            <p className="text-xs text-slate-600 max-w-lg">
              Learn how to calculate roots and discriminant for board examination problem sheets.
            </p>
            <div className="flex items-center gap-3 text-xs text-slate-500 pt-1">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-slate-400" /> 24 mins
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-indigo-600 font-medium">
                <FileText className="h-3.5 w-3.5" /> PDF Notes Attached
              </span>
            </div>
          </div>

          <Button
            size="lg"
            variant="primary"
            onClick={() => navigate('/student/lectures/lecture-seed-demo')}
            className="w-full sm:w-auto shrink-0 touch-target cursor-pointer"
            icon={<PlayCircle className="h-5 w-5" />}
          >
            Watch Lesson Now
          </Button>
        </div>
      </Card>

      {/* Two Column Grid: Today's Homework & Upcoming Assessments */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Homework Submission Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md">
                <AlertCircle className="h-3.5 w-3.5 text-amber-600" /> Due Today, 8:00 PM
              </span>
              <span className="text-xs text-slate-400">10 Marks</span>
            </div>
            <CardTitle className="pt-1.5">HW 03: Quadratic Problem Set</CardTitle>
            <CardDescription>Questions 1 through 8 from textbook page 48.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-xl bg-slate-50 p-3 space-y-1.5 text-xs text-slate-600">
              <div className="flex items-center justify-between">
                <span>Status:</span>
                <span className="font-semibold text-amber-600">PENDING SUBMISSION</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Max File Size: 15MB</span>
                <span>Camera photos / PDF</span>
              </div>
            </div>

            <Button
              size="md"
              variant="outline"
              onClick={() => setShowUploader(true)}
              className="w-full mt-3 touch-target cursor-pointer"
              icon={<Camera className="h-4 w-4 text-indigo-600" />}
            >
              Submit Homework Photos
            </Button>
          </CardContent>
        </Card>

        {/* Milestone Test Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md">
                <Clock className="h-3.5 w-3.5 text-indigo-600" /> Timed Quiz
              </span>
              <span className="text-xs text-slate-400">5 Questions • 20m</span>
            </div>
            <CardTitle className="pt-1.5">Chapter 2 Milestone Test</CardTitle>
            <CardDescription>Objective MCQ test with instant automated scoring.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-xl bg-slate-50 p-3 space-y-1.5 text-xs text-slate-600">
              <div className="flex items-center justify-between">
                <span>Pass Requirement:</span>
                <span className="font-semibold text-slate-900">40% (2/5 Marks)</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Single Attempt</span>
                <span>Deadline: Tomorrow</span>
              </div>
            </div>

            <Button
              size="md"
              variant="secondary"
              className="w-full mt-3 touch-target"
              icon={<ChevronRight className="h-4 w-4" />}
            >
              Start Timed Test
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Live Class Notice Banner */}
      <div className="flex items-center justify-between p-4 rounded-2xl border border-indigo-200 bg-indigo-50/70">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shrink-0">
            <Calendar className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900">
              Today's Live Class at 05:00 PM
            </h4>
            <p className="text-xs text-indigo-700 mt-0.5">
              Doubt Solving & Board Exam Questions on Quadratic Equations
            </p>
          </div>
        </div>
        <Button size="sm" variant="primary" className="hidden sm:inline-flex">
          Join Google Meet
        </Button>
      </div>

      <div className="p-3 rounded-xl bg-slate-100 text-center text-[11px] text-slate-500 font-medium">
        [Development Mock Preview] Curriculum progression, video player, and camera upload modals will connect in subsequent tasks.
      </div>

      {showUploader && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <StudentAttachmentUploader
            submissionId="sub-001-demo"
            pageOrder={1}
            onCancel={() => setShowUploader(false)}
            onSuccess={() => {
              alert('Homework attachment uploaded and verified!');
              setShowUploader(false);
            }}
          />
        </div>
      )}
    </div>
  );
};
