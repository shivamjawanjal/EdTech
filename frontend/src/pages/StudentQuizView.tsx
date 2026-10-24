import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Clock,
  CheckCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Send,
  Award,
  HelpCircle,
  AlertCircle,
  RotateCcw,
} from 'lucide-react';
import { assessmentService } from '../api/assessmentService';
import type { TestDetail, AttemptResult } from '../types/assessment';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { FullPageLoader } from '../components/common/LoadingSpinner';

export const StudentQuizView: React.FC = () => {
  const { testId } = useParams<{ testId: string }>();
  const navigate = useNavigate();

  // Test state
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [test, setTest] = useState<TestDetail | null>(null);

  // Attempt state
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [attemptNumber, setAttemptNumber] = useState<number>(1);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);
  const [savedAnswers, setSavedAnswers] = useState<Record<string, string>>({});
  const [currentQIndex, setCurrentQIndex] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [showConfirmSubmit, setShowConfirmSubmit] = useState<boolean>(false);

  // Result state
  const [result, setResult] = useState<AttemptResult | null>(null);

  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!testId) return;
    loadTest();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [testId]);

  const loadTest = async () => {
    if (!testId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await assessmentService.getTest(testId);
      setTest(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load assessment');
    } finally {
      setLoading(false);
    }
  };

  // Start or resume attempt
  const handleStartAttempt = async () => {
    if (!testId) return;
    setLoading(true);
    setError(null);
    try {
      const startRes = await assessmentService.startTestAttempt(testId);
      setAttemptId(startRes.attempt_id);
      setAttemptNumber(startRes.attempt_number);
      setRemainingSeconds(startRes.remaining_seconds);
      setSavedAnswers(startRes.saved_answers || {});

      // Start authoritative countdown timer
      startTimer(startRes.remaining_seconds);
    } catch (err: any) {
      setError(err.message || 'Failed to start assessment attempt');
    } finally {
      setLoading(false);
    }
  };

  const startTimer = (seconds: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    let s = seconds;
    timerRef.current = window.setInterval(() => {
      s -= 1;
      setRemainingSeconds(s);
      if (s <= 0) {
        if (timerRef.current) clearInterval(timerRef.current);
        handleAutoSubmit();
      }
    }, 1000);
  };

  // Select and save option
  const handleSelectOption = async (questionId: string, optionKey: string) => {
    if (!attemptId) return;
    const previous = savedAnswers[questionId];
    const newSelection = previous === optionKey ? null : optionKey;

    // Optimistically update
    setSavedAnswers((prev) => {
      const updated = { ...prev };
      if (newSelection) {
        updated[questionId] = newSelection;
      } else {
        delete updated[questionId];
      }
      return updated;
    });

    try {
      await assessmentService.saveAnswer(attemptId, questionId, newSelection);
    } catch (err: any) {
      console.error('Failed to save answer:', err);
    }
  };

  // Submit attempt
  const handleSubmitAttempt = async () => {
    if (!attemptId) return;
    if (timerRef.current) clearInterval(timerRef.current);
    setIsSubmitting(true);
    setError(null);
    setShowConfirmSubmit(false);
    try {
      const res = await assessmentService.submitTestAttempt(attemptId);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to submit assessment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAutoSubmit = async () => {
    if (!attemptId) return;
    setIsSubmitting(true);
    try {
      const res = await assessmentService.submitTestAttempt(attemptId);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Assessment timed out');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(Math.max(0, secs) / 60);
    const s = Math.max(0, secs) % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <FullPageLoader message="Loading assessment environment..." />;
  }

  if (error && !test) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 rounded-2xl bg-white border border-rose-200 text-center space-y-4 shadow-sm">
        <AlertCircle className="h-10 w-10 text-rose-600 mx-auto" />
        <h2 className="text-base font-bold text-slate-900">Assessment Error</h2>
        <p className="text-xs text-slate-600">{error}</p>
        <Button size="sm" variant="outline" onClick={() => navigate('/student/home')}>
          Return to Dashboard
        </Button>
      </div>
    );
  }

  if (!test) return null;

  // 1. RESULT SCREEN
  if (result) {
    return (
      <div className="max-w-3xl mx-auto my-6 space-y-6">
        <div className="p-6 sm:p-8 rounded-3xl bg-white border border-slate-200 shadow-md text-center space-y-4">
          <div
            className={`flex h-16 w-16 items-center justify-center rounded-2xl mx-auto ${
              result.passed ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
            }`}
          >
            <Award className="h-9 w-9" />
          </div>

          <div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                result.passed
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-rose-100 text-rose-800'
              }`}
            >
              {result.passed ? 'Passed Successfully' : 'Needs Improvement'}
            </span>
            <h1 className="text-2xl font-black text-slate-900 sm:text-3xl mt-2">
              {result.score} / {result.total_marks} Marks
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Score: {result.percentage}% • Pass Requirement: {test.pass_percentage}%
            </p>
          </div>

          {/* Breakdown Pills */}
          <div className="grid grid-cols-3 gap-3 max-w-md mx-auto pt-2">
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100 text-center">
              <span className="text-xl font-bold text-emerald-800 block">{result.correct_count}</span>
              <span className="text-[11px] font-semibold text-emerald-600">Correct</span>
            </div>
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-center">
              <span className="text-xl font-bold text-rose-800 block">{result.incorrect_count}</span>
              <span className="text-[11px] font-semibold text-rose-600">Incorrect</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
              <span className="text-xl font-bold text-slate-700 block">{result.unattempted_count}</span>
              <span className="text-[11px] font-semibold text-slate-500">Unattempted</span>
            </div>
          </div>

          {/* Solutions status */}
          {!result.solutions_released ? (
            <div className="p-3 rounded-xl bg-slate-100 text-center text-xs text-slate-600 max-w-md mx-auto">
              Step-by-step solutions and explanations will be unlocked by the teacher once the deadline passes.
            </div>
          ) : result.answers && (
            <div className="text-left space-y-4 pt-4 border-t border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">Step-by-Step Question Solutions</h3>
              {result.answers.map((ans, idx) => (
                <div
                  key={ans.question_id}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between font-bold text-slate-800">
                    <span>Question {idx + 1}</span>
                    <span
                      className={
                        ans.is_correct
                          ? 'text-emerald-700'
                          : ans.selected_option
                          ? 'text-rose-700'
                          : 'text-slate-500'
                      }
                    >
                      {ans.is_correct
                        ? `+${ans.marks_awarded} marks`
                        : ans.selected_option
                        ? `${ans.marks_awarded} marks`
                        : 'Unattempted (0 marks)'}
                    </span>
                  </div>

                  <div className="flex gap-4 text-xs">
                    <span>Your Answer: <strong className="text-slate-900">{ans.selected_option || 'None'}</strong></span>
                    <span>Correct Key: <strong className="text-emerald-700">{ans.correct_option}</strong></span>
                  </div>

                  {ans.solution_explanation && (
                    <p className="text-[11px] text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200">
                      <strong>Solution Explanation:</strong> {ans.solution_explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="pt-4">
            <Button
              size="md"
              variant="primary"
              onClick={() => navigate('/student/home')}
              className="touch-target"
            >
              Back to Learning Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 2. PRE-ASSESSMENT SCREEN
  if (!attemptId) {
    return (
      <div className="max-w-xl mx-auto my-8 space-y-6">
        <Card className="border-indigo-100 shadow-md">
          <CardHeader className="text-center pb-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-white mx-auto mb-2">
              <Clock className="h-6 w-6" />
            </div>
            <CardTitle className="text-xl sm:text-2xl">{test.title}</CardTitle>
            <p className="text-xs text-slate-500 mt-1">
              Chapter Milestone Assessment • Server Authoritative Timing
            </p>
          </CardHeader>

          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[11px]">Duration</span>
                <span className="text-sm font-bold text-slate-900">{test.duration_minutes} Minutes</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[11px]">Total Marks</span>
                <span className="text-sm font-bold text-slate-900">{test.total_marks} Marks</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[11px]">Pass Requirement</span>
                <span className="text-sm font-bold text-slate-900">{test.pass_percentage}% Marks</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[11px]">Attempt Limit</span>
                <span className="text-sm font-bold text-slate-900">{test.max_attempts} Attempt(s)</span>
              </div>
            </div>

            <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3.5 space-y-1.5 text-xs text-amber-900">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                Assessment Integrity Rules
              </div>
              <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-800">
                <li>Server clock authoritatively computes elapsed time.</li>
                <li>Incorrect answers incur negative marking where configured.</li>
                <li>Refreshing or losing connection will safely resume your timer.</li>
                <li>Test will automatically submit when the timer expires.</li>
              </ul>
            </div>

            <div className="pt-2 flex items-center gap-3">
              <Button
                size="md"
                variant="outline"
                onClick={() => navigate('/student/home')}
                className="w-1/3"
              >
                Cancel
              </Button>
              <Button
                size="md"
                variant="primary"
                onClick={handleStartAttempt}
                className="flex-1 touch-target cursor-pointer font-bold"
                icon={<Clock className="h-4 w-4" />}
              >
                Start Timed Assessment
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 3. ACTIVE QUIZ INTERFACE
  const currentQuestion = test.questions[currentQIndex];
  const isLastQuestion = currentQIndex === test.questions.length - 1;
  const answeredCount = Object.keys(savedAnswers).length;
  const isUrgent = remainingSeconds < 120; // less than 2 minutes

  return (
    <div className="max-w-3xl mx-auto my-4 space-y-4">
      {/* Top Authoritative Bar */}
      <div className="sticky top-2 z-30 flex items-center justify-between p-3.5 sm:p-4 rounded-2xl bg-white border border-slate-200 shadow-md">
        <div>
          <h2 className="text-xs font-bold text-slate-900 truncate max-w-[200px] sm:max-w-md">
            {test.title}
          </h2>
          <span className="text-[11px] text-slate-400">
            Question {currentQIndex + 1} of {test.questions.length} • Attempt #{attemptNumber} • {answeredCount} answered
          </span>
        </div>

        {/* Autoritative Timer Pill */}
        <div
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-mono text-sm font-bold shadow-2xs ${
            isUrgent
              ? 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse'
              : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
          }`}
        >
          <Clock className="h-4 w-4" />
          <span>{formatTime(remainingSeconds)}</span>
        </div>
      </div>

      {/* Question Number Ribbon */}
      <div className="flex items-center gap-2 overflow-x-auto p-2 bg-slate-100 rounded-xl">
        {test.questions.map((q, idx) => {
          const isAnswered = !!savedAnswers[q.id];
          const isCurrent = idx === currentQIndex;
          return (
            <button
              key={q.id}
              onClick={() => setCurrentQIndex(idx)}
              className={`h-8 w-8 rounded-lg text-xs font-bold shrink-0 transition-all ${
                isCurrent
                  ? 'bg-indigo-600 text-white shadow-2xs'
                  : isAnswered
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-200'
              }`}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>

      {/* Active Question Card */}
      {currentQuestion && (
        <Card className="border-slate-200">
          <CardHeader className="border-b border-slate-100 pb-3">
            <div className="flex items-start justify-between gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                Question {currentQIndex + 1}
              </span>
              <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-md">
                +{currentQuestion.marks} / -{currentQuestion.negative_marks} marks
              </span>
            </div>
            <CardTitle className="text-base sm:text-lg pt-2 leading-relaxed text-slate-900">
              {currentQuestion.question_text}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3 pt-4">
            {/* Options List */}
            <div className="space-y-2.5">
              {Array.isArray(currentQuestion.options) &&
                currentQuestion.options.map((opt: any) => {
                  const isSelected = savedAnswers[currentQuestion.id] === opt.key;
                  return (
                    <button
                      key={opt.key}
                      onClick={() => handleSelectOption(currentQuestion.id, opt.key)}
                      className={`w-full flex items-center justify-between p-4 rounded-xl border text-left transition-all cursor-pointer ${
                        isSelected
                          ? 'border-indigo-600 bg-indigo-50/70 text-indigo-950 font-bold shadow-2xs'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50 text-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${
                            isSelected
                              ? 'bg-indigo-600 text-white'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {opt.key}
                        </span>
                        <span className="text-xs sm:text-sm">{opt.text}</span>
                      </div>
                      {isSelected && <CheckCircle className="h-5 w-5 text-indigo-600 shrink-0" />}
                    </button>
                  );
                })}
            </div>

            {/* Clear selection option */}
            {savedAnswers[currentQuestion.id] && (
              <div className="text-right pt-1">
                <button
                  onClick={() => handleSelectOption(currentQuestion.id, savedAnswers[currentQuestion.id])}
                  className="text-[11px] text-slate-400 hover:text-rose-600 inline-flex items-center gap-1 cursor-pointer"
                >
                  <RotateCcw className="h-3 w-3" /> Clear Selection
                </button>
              </div>
            )}

            {/* Navigation buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <Button
                size="sm"
                variant="outline"
                disabled={currentQIndex === 0}
                onClick={() => setCurrentQIndex((prev) => prev - 1)}
                icon={<ChevronLeft className="h-4 w-4" />}
              >
                Previous
              </Button>

              {isLastQuestion ? (
                <Button
                  size="md"
                  variant="primary"
                  onClick={() => setShowConfirmSubmit(true)}
                  className="touch-target cursor-pointer font-bold bg-emerald-600 hover:bg-emerald-700"
                  icon={<Send className="h-4 w-4" />}
                >
                  Submit Assessment
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => setCurrentQIndex((prev) => prev + 1)}
                  className="touch-target"
                >
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Confirmation Modal before Submit */}
      {showConfirmSubmit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 text-center space-y-4">
            <HelpCircle className="h-10 w-10 text-indigo-600 mx-auto" />
            <div>
              <h3 className="text-base font-bold text-slate-900">Submit Assessment?</h3>
              <p className="text-xs text-slate-500 mt-1">
                You have answered <strong>{answeredCount}</strong> of{' '}
                <strong>{test.questions.length}</strong> questions.
                {answeredCount < test.questions.length && (
                  <span className="block text-amber-700 font-semibold mt-1">
                    Warning: {test.questions.length - answeredCount} question(s) will be marked unattempted.
                  </span>
                )}
              </p>
            </div>

            <div className="flex items-center justify-center gap-3 pt-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowConfirmSubmit(false)}
                className="w-1/2"
              >
                Review Answers
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={handleSubmitAttempt}
                disabled={isSubmitting}
                className="w-1/2 font-bold"
              >
                {isSubmitting ? 'Scoring...' : 'Yes, Submit'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
