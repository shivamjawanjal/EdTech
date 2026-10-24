import React, { useState, useEffect } from 'react';
import {
  FileText,
  Clock,
  CheckCircle,
  Plus,
  Send,
  Award,
  Filter,
  RefreshCw,
  X,
  FileCheck,
} from 'lucide-react';
import { assessmentService } from '../../api/assessmentService';
import type {
  Assignment,
  AssignmentSubmissionQueue,
  Submission,
  Test,
  TestDetail,
  AttemptResult,
} from '../../types/assessment';
import { Button } from '../common/Button';

interface TeacherAssessmentConsoleProps {
  onClose: () => void;
}

export const TeacherAssessmentConsole: React.FC<TeacherAssessmentConsoleProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<'assignments' | 'tests'>('assignments');
  const [loading, setLoading] = useState<boolean>(true);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [tests, setTests] = useState<Test[]>([]);

  // Selected assignment & queue
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [queue, setQueue] = useState<AssignmentSubmissionQueue | null>(null);
  const [queueLoading, setQueueLoading] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Selected submission for grading
  const [gradingSubmission, setGradingSubmission] = useState<Submission | null>(null);
  const [gradeMarks, setGradeMarks] = useState<string>('');
  const [gradeFeedback, setGradeFeedback] = useState<string>('');
  const [gradeRelease, setGradeRelease] = useState<boolean>(false);
  const [gradeSubmitting, setGradeSubmitting] = useState<boolean>(false);
  const [gradeError, setGradeError] = useState<string | null>(null);

  // Selected test & attempts
  const [selectedTest, setSelectedTest] = useState<TestDetail | null>(null);
  const [testAttempts, setTestAttempts] = useState<AttemptResult[]>([]);
  const [testLoading, setTestLoading] = useState<boolean>(false);

  // New question form
  const [showAddQuestion, setShowAddQuestion] = useState<boolean>(false);
  const [qText, setQText] = useState<string>('');
  const [optA, setOptA] = useState<string>('');
  const [optB, setOptB] = useState<string>('');
  const [optC, setOptC] = useState<string>('');
  const [optD, setOptD] = useState<string>('');
  const [correctOpt, setCorrectOpt] = useState<string>('A');
  const [qMarks, setQMarks] = useState<number>(4);
  const [qNegMarks, setQNegMarks] = useState<string>('1.00');
  const [qExplanation, setQExplanation] = useState<string>('');

  // Load initial lists
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'assignments') {
        const list = await assessmentService.getAssignments();
        setAssignments(list);
        if (list.length > 0 && !selectedAssignment) {
          loadAssignmentQueue(list[0].id);
        }
      } else {
        const testList = await assessmentService.getTests();
        setTests(testList);
        if (testList.length > 0 && !selectedTest) {
          loadTestDetail(testList[0].id);
        }
      }
    } catch (err: any) {
      console.error('Failed to load assessment data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadAssignmentQueue = async (assignmentId: string, filter?: string) => {
    setQueueLoading(true);
    try {
      const q = await assessmentService.getAssignmentSubmissions(assignmentId, filter);
      setQueue(q);
      setSelectedAssignment(q.assignment);
    } catch (err: any) {
      console.error('Failed to load queue:', err);
    } finally {
      setQueueLoading(false);
    }
  };

  const loadTestDetail = async (testId: string) => {
    setTestLoading(true);
    try {
      const [tDetail, attempts] = await Promise.all([
        assessmentService.getTest(testId),
        assessmentService.getTestAttempts(testId),
      ]);
      setSelectedTest(tDetail);
      setTestAttempts(attempts);
    } catch (err: any) {
      console.error('Failed to load test details:', err);
    } finally {
      setTestLoading(false);
    }
  };

  const handleOpenGrading = (sub: Submission) => {
    setGradingSubmission(sub);
    setGradeMarks(sub.obtained_marks ? String(sub.obtained_marks) : '');
    setGradeFeedback(sub.teacher_feedback || '');
    setGradeRelease(sub.is_released);
    setGradeError(null);
  };

  const handleSaveGrade = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gradingSubmission || !selectedAssignment) return;

    const numMarks = parseFloat(gradeMarks);
    if (isNaN(numMarks) || numMarks < 0) {
      setGradeError('Please enter a valid non-negative marks score');
      return;
    }
    if (numMarks > selectedAssignment.max_marks) {
      setGradeError(`Marks cannot exceed maximum marks of ${selectedAssignment.max_marks}`);
      return;
    }

    setGradeSubmitting(true);
    setGradeError(null);
    try {
      await assessmentService.gradeSubmission(gradingSubmission.id, {
        obtained_marks: numMarks,
        teacher_feedback: gradeFeedback.trim() || undefined,
        is_released: gradeRelease,
      });
      // Refresh queue
      await loadAssignmentQueue(selectedAssignment.id, statusFilter);
      setGradingSubmission(null);
    } catch (err: any) {
      setGradeError(err.message || 'Failed to save grade');
    } finally {
      setGradeSubmitting(false);
    }
  };

  const handleBatchRelease = async () => {
    if (!selectedAssignment) return;
    if (
      !window.confirm(
        'Release marks and written feedback to all evaluated students for this assignment?'
      )
    ) {
      return;
    }
    try {
      const res = await assessmentService.releaseAssignmentGrades(selectedAssignment.id);
      alert(res.message);
      await loadAssignmentQueue(selectedAssignment.id, statusFilter);
    } catch (err: any) {
      alert(err.message || 'Failed to release grades');
    }
  };

  const handleAddQuestionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTest) return;
    try {
      await assessmentService.addQuestion(selectedTest.id, {
        question_text: qText.trim(),
        options: [
          { key: 'A', text: optA.trim() },
          { key: 'B', text: optB.trim() },
          { key: 'C', text: optC.trim() },
          { key: 'D', text: optD.trim() },
        ],
        correct_option: correctOpt,
        marks: qMarks,
        negative_marks: qNegMarks,
        solution_explanation: qExplanation.trim() || undefined,
      });
      setShowAddQuestion(false);
      // Reset form
      setQText('');
      setOptA('');
      setOptB('');
      setOptC('');
      setOptD('');
      setQExplanation('');
      await loadTestDetail(selectedTest.id);
    } catch (err: any) {
      alert(err.message || 'Failed to add question');
    }
  };

  return (
    <div className="relative w-full max-w-5xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50/80 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">Assessment & Evaluation Engine</h2>
            <p className="text-xs text-slate-500">
              Manage daily assignments, submission review queue, and timed MCQ quizzes.
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
          title="Close Console"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-6">
        <button
          onClick={() => {
            setActiveTab('assignments');
            setSelectedAssignment(null);
          }}
          className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition-all ${
            activeTab === 'assignments'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileText className="h-4 w-4" />
          Daily Assignments & Grading
        </button>
        <button
          onClick={() => {
            setActiveTab('tests');
            setSelectedTest(null);
          }}
          className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition-all ${
            activeTab === 'tests'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Clock className="h-4 w-4" />
          Timed MCQ Assessments
        </button>
      </div>

      {/* Main Content Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading ? (
          <div className="py-16 text-center text-xs text-slate-500">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-indigo-600 mb-2" />
            Loading assessments...
          </div>
        ) : activeTab === 'assignments' ? (
          /* ASSIGNMENTS VIEW */
          <div className="space-y-6">
            {/* Assignment Selector Chips */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {assignments.map((a) => (
                <button
                  key={a.id}
                  onClick={() => loadAssignmentQueue(a.id)}
                  className={`shrink-0 rounded-xl px-4 py-2 text-left border transition-all ${
                    selectedAssignment?.id === a.id
                      ? 'border-indigo-600 bg-indigo-50/50 shadow-2xs'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <p className="text-xs font-bold text-slate-900 truncate max-w-[200px]">{a.title}</p>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-1">
                    <span>Max {a.max_marks}m</span>
                    <span>•</span>
                    <span className="text-amber-600 font-semibold">{a.pending_count} pending</span>
                  </div>
                </button>
              ))}
            </div>

            {queueLoading ? (
              <div className="py-12 text-center text-xs text-slate-500">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto text-indigo-600 mb-2" />
                Loading submission queue...
              </div>
            ) : queue ? (
              <div className="space-y-4">
                {/* Queue Summary Metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                    <span className="text-[11px] text-slate-500 block">Total Enrolled</span>
                    <span className="text-xl font-bold text-slate-900">{queue.total_enrolled}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-emerald-100 bg-emerald-50/40">
                    <span className="text-[11px] text-emerald-700 block">Submitted</span>
                    <span className="text-xl font-bold text-emerald-800">{queue.submitted_count}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-indigo-100 bg-indigo-50/40">
                    <span className="text-[11px] text-indigo-700 block">Evaluated</span>
                    <span className="text-xl font-bold text-indigo-800">{queue.evaluated_count}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-amber-100 bg-amber-50/40">
                    <span className="text-[11px] text-amber-700 block">Pending Grading</span>
                    <span className="text-xl font-bold text-amber-800">{queue.pending_count}</span>
                  </div>
                  <div className="p-3 rounded-xl border border-rose-100 bg-rose-50/40">
                    <span className="text-[11px] text-rose-700 block">Missing Work</span>
                    <span className="text-xl font-bold text-rose-800">{queue.missing_count}</span>
                  </div>
                </div>

                {/* Submissions Action Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="flex items-center gap-1.5">
                    <Filter className="h-4 w-4 text-slate-400" />
                    {['', 'pending', 'evaluated', 'late'].map((st) => (
                      <button
                        key={st}
                        onClick={() => {
                          setStatusFilter(st);
                          if (selectedAssignment) loadAssignmentQueue(selectedAssignment.id, st);
                        }}
                        className={`rounded-lg px-2.5 py-1 text-xs font-semibold capitalize transition-all ${
                          statusFilter === st
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {st || 'All'}
                      </button>
                    ))}
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleBatchRelease}
                    icon={<Send className="h-3.5 w-3.5 text-indigo-600" />}
                  >
                    Batch Release Evaluated Grades
                  </Button>
                </div>

                {/* Submissions Table / Cards */}
                {queue.submissions.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                    No submissions found for the selected filter.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {queue.submissions.map((sub) => (
                      <div
                        key={sub.id}
                        className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-200 transition-all gap-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-slate-900">
                              {sub.student_name || 'Student'}
                            </span>
                            <span className="text-xs text-slate-400">{sub.student_email}</span>
                            <span
                              className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase ${
                                sub.status === 'late'
                                  ? 'bg-amber-100 text-amber-800'
                                  : sub.is_evaluated
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : 'bg-slate-100 text-slate-700'
                              }`}
                            >
                              {sub.is_evaluated ? 'Evaluated' : sub.status}
                            </span>
                            {sub.is_released && (
                              <span className="rounded-md bg-indigo-100 text-indigo-800 px-2 py-0.5 text-[10px] font-bold">
                                Released
                              </span>
                            )}
                          </div>

                          {sub.student_content && (
                            <p className="text-xs text-slate-600 italic line-clamp-1">
                              "{sub.student_content}"
                            </p>
                          )}

                          <div className="flex items-center gap-3 text-[11px] text-slate-400 pt-0.5">
                            <span>Attempt {sub.attempt_number}</span>
                            <span>•</span>
                            <span>{sub.attachments.length} attachment(s)</span>
                            {sub.obtained_marks !== null && (
                              <>
                                <span>•</span>
                                <span className="font-bold text-slate-800">
                                  Score: {sub.obtained_marks} / {selectedAssignment?.max_marks}
                                </span>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-end sm:self-center">
                          <Button
                            size="sm"
                            variant={sub.is_evaluated ? 'outline' : 'primary'}
                            onClick={() => handleOpenGrading(sub)}
                            icon={<Award className="h-3.5 w-3.5" />}
                          >
                            {sub.is_evaluated ? 'Edit Grade' : 'Grade Submission'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        ) : (
          /* MCQ TESTS VIEW */
          <div className="space-y-6">
            {/* Test Selector Chips */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {tests.map((t) => (
                <button
                  key={t.id}
                  onClick={() => loadTestDetail(t.id)}
                  className={`shrink-0 rounded-xl px-4 py-2 text-left border transition-all ${
                    selectedTest?.id === t.id
                      ? 'border-indigo-600 bg-indigo-50/50 shadow-2xs'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <p className="text-xs font-bold text-slate-900 truncate max-w-[200px]">{t.title}</p>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-1">
                    <span>{t.duration_minutes}m</span>
                    <span>•</span>
                    <span>{t.total_marks} Marks</span>
                    <span>•</span>
                    <span className="text-indigo-600 font-semibold">{t.question_count} Qs</span>
                  </div>
                </button>
              ))}
            </div>

            {testLoading ? (
              <div className="py-12 text-center text-xs text-slate-500">
                <RefreshCw className="h-5 w-5 animate-spin mx-auto text-indigo-600 mb-2" />
                Loading test assessment details...
              </div>
            ) : selectedTest ? (
              <div className="space-y-6">
                {/* Test Meta Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-slate-50">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-900">{selectedTest.title}</h3>
                    <p className="text-xs text-slate-500">
                      Duration: {selectedTest.duration_minutes} mins • Pass: {selectedTest.pass_percentage}% • Max Attempts: {selectedTest.max_attempts}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => setShowAddQuestion(true)}
                    icon={<Plus className="h-4 w-4" />}
                  >
                    Add Question
                  </Button>
                </div>

                {/* Question List */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Questions ({selectedTest.questions.length})
                  </h4>
                  {selectedTest.questions.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                      No questions configured for this test yet. Click "Add Question" above.
                    </div>
                  ) : (
                    selectedTest.questions.map((q, idx) => (
                      <div
                        key={q.id}
                        className="p-4 rounded-xl border border-slate-200 bg-white space-y-2"
                      >
                        <div className="flex items-start justify-between">
                          <span className="text-xs font-bold text-slate-900">
                            Q{idx + 1}. {q.question_text}
                          </span>
                          <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md">
                            +{q.marks} / -{q.negative_marks} marks
                          </span>
                        </div>

                        {/* Options preview */}
                        <div className="grid grid-cols-2 gap-2 pt-1">
                          {Array.isArray(q.options) &&
                            q.options.map((opt: any) => (
                              <div
                                key={opt.key}
                                className={`text-xs p-2 rounded-lg border flex items-center justify-between ${
                                  opt.key === q.correct_option
                                    ? 'border-emerald-500 bg-emerald-50 text-emerald-900 font-bold'
                                    : 'border-slate-100 bg-slate-50 text-slate-600'
                                }`}
                              >
                                <span>
                                  {opt.key}. {opt.text}
                                </span>
                                {opt.key === q.correct_option && (
                                  <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
                                )}
                              </div>
                            ))}
                        </div>

                        {q.solution_explanation && (
                          <p className="text-[11px] text-slate-500 bg-slate-50 p-2 rounded-lg">
                            <span className="font-semibold text-slate-700">Explanation:</span>{' '}
                            {q.solution_explanation}
                          </p>
                        )}
                      </div>
                    ))
                  )}
                </div>

                {/* Student Attempts & Automated Scores */}
                <div className="space-y-3 pt-4 border-t border-slate-200">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Student Completed Attempts ({testAttempts.length})
                  </h4>
                  {testAttempts.length === 0 ? (
                    <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                      No student attempts recorded yet.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {testAttempts.map((att) => (
                        <div
                          key={att.attempt_id}
                          className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-white"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-900">
                                Attempt #{att.attempt_number}
                              </span>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                                  att.passed
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-rose-100 text-rose-800'
                                }`}
                              >
                                {att.passed ? 'PASSED' : 'NEEDS IMPROVEMENT'}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500">
                              {att.correct_count} correct • {att.incorrect_count} incorrect •{' '}
                              {att.unattempted_count} unattempted
                            </p>
                          </div>

                          <div className="text-right">
                            <span className="text-base font-bold text-slate-900 block">
                              {att.score} / {att.total_marks}
                            </span>
                            <span className="text-[10px] text-slate-400">{att.percentage}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* MODAL: Grading Submission */}
      {gradingSubmission && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Grade Submission — {gradingSubmission.student_name}
                </h3>
                <p className="text-xs text-slate-500">
                  Assignment: {selectedAssignment?.title} (Max Marks: {selectedAssignment?.max_marks})
                </p>
              </div>
              <button
                onClick={() => setGradingSubmission(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Student Content Preview */}
            {gradingSubmission.student_content && (
              <div className="rounded-xl bg-slate-50 p-3 space-y-1">
                <span className="text-[10px] font-bold uppercase text-slate-400">Student Answer</span>
                <p className="text-xs text-slate-700 whitespace-pre-wrap">
                  {gradingSubmission.student_content}
                </p>
              </div>
            )}

            {/* Attachments */}
            {gradingSubmission.attachments.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold uppercase text-slate-400">
                  Attached Homework Photos ({gradingSubmission.attachments.length})
                </span>
                <div className="flex flex-wrap gap-2">
                  {gradingSubmission.attachments.map((att) => (
                    <div
                      key={att.id}
                      className="flex items-center gap-2 p-2 rounded-lg border border-slate-200 text-xs text-slate-700 bg-white"
                    >
                      <FileCheck className="h-4 w-4 text-emerald-600" />
                      <span className="truncate max-w-[150px]">{att.file_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <form onSubmit={handleSaveGrade} className="space-y-4 pt-2">
              {gradeError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
                  {gradeError}
                </div>
              )}

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Marks Awarded (Max: {selectedAssignment?.max_marks})
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max={selectedAssignment?.max_marks}
                  required
                  value={gradeMarks}
                  onChange={(e) => setGradeMarks(e.target.value)}
                  placeholder="e.g. 18.5"
                  className="w-full rounded-xl border border-slate-300 p-2.5 text-sm focus:border-indigo-600 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Pedagogical Feedback & Guidance
                </label>
                <textarea
                  rows={3}
                  value={gradeFeedback}
                  onChange={(e) => setGradeFeedback(e.target.value)}
                  placeholder="e.g. Excellent work on step 3. Review sign convention in Q2."
                  className="w-full rounded-xl border border-slate-300 p-2.5 text-xs focus:border-indigo-600 focus:outline-hidden"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="release_toggle"
                  checked={gradeRelease}
                  onChange={(e) => setGradeRelease(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="release_toggle" className="text-xs font-medium text-slate-700 cursor-pointer">
                  Release mark & feedback immediately to student
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  size="sm"
                  variant="outline"
                  type="button"
                  onClick={() => setGradingSubmission(null)}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  type="submit"
                  disabled={gradeSubmitting}
                  icon={<CheckCircle className="h-4 w-4" />}
                >
                  {gradeSubmitting ? 'Saving...' : 'Save Evaluation'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Add MCQ Question */}
      {showAddQuestion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-sm font-bold text-slate-900">Add MCQ Assessment Question</h3>
              <button
                onClick={() => setShowAddQuestion(false)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddQuestionSubmit} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Question Text</label>
                <textarea
                  required
                  rows={2}
                  value={qText}
                  onChange={(e) => setQText(e.target.value)}
                  placeholder="e.g. Which of the following is Newton's Second Law?"
                  className="w-full rounded-xl border border-slate-300 p-2 text-xs focus:border-indigo-600 focus:outline-hidden"
                />
              </div>

              <div className="space-y-2">
                <label className="font-bold text-slate-700 block">Answer Options (A-D)</label>
                <div className="flex items-center gap-2">
                  <span className="font-bold w-4">A:</span>
                  <input
                    required
                    type="text"
                    value={optA}
                    onChange={(e) => setOptA(e.target.value)}
                    placeholder="Option A"
                    className="flex-1 rounded-lg border border-slate-300 p-1.5"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold w-4">B:</span>
                  <input
                    required
                    type="text"
                    value={optB}
                    onChange={(e) => setOptB(e.target.value)}
                    placeholder="Option B"
                    className="flex-1 rounded-lg border border-slate-300 p-1.5"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold w-4">C:</span>
                  <input
                    required
                    type="text"
                    value={optC}
                    onChange={(e) => setOptC(e.target.value)}
                    placeholder="Option C"
                    className="flex-1 rounded-lg border border-slate-300 p-1.5"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold w-4">D:</span>
                  <input
                    required
                    type="text"
                    value={optD}
                    onChange={(e) => setOptD(e.target.value)}
                    placeholder="Option D"
                    className="flex-1 rounded-lg border border-slate-300 p-1.5"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Correct Key</label>
                  <select
                    value={correctOpt}
                    onChange={(e) => setCorrectOpt(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-1.5 font-bold"
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Marks (+)</label>
                  <input
                    type="number"
                    min="1"
                    value={qMarks}
                    onChange={(e) => setQMarks(parseInt(e.target.value) || 1)}
                    className="w-full rounded-lg border border-slate-300 p-1.5"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Negative (-)</label>
                  <input
                    type="text"
                    value={qNegMarks}
                    onChange={(e) => setQNegMarks(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-1.5"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Solution Explanation</label>
                <textarea
                  rows={2}
                  value={qExplanation}
                  onChange={(e) => setQExplanation(e.target.value)}
                  placeholder="Revealed to students after solutions release date"
                  className="w-full rounded-xl border border-slate-300 p-2 text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  size="sm"
                  variant="outline"
                  type="button"
                  onClick={() => setShowAddQuestion(false)}
                >
                  Cancel
                </Button>
                <Button size="sm" variant="primary" type="submit">
                  Save Question
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
