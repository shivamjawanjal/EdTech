import React, { useState } from 'react';
import {
  Upload,
  X,
  Award,
  Send,
} from 'lucide-react';
import { assessmentService } from '../../api/assessmentService';
import type { Assignment, Submission } from '../../types/assessment';
import { Button } from '../common/Button';
import { StudentAttachmentUploader } from '../media/StudentAttachmentUploader';

interface StudentAssignmentSubmitModalProps {
  assignment: Assignment;
  onClose: () => void;
  onSubmitted: () => void;
}

export const StudentAssignmentSubmitModal: React.FC<StudentAssignmentSubmitModalProps> = ({
  assignment,
  onClose,
  onSubmitted,
}) => {
  const [content, setContent] = useState<string>(
    assignment.my_submission?.student_content || ''
  );
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSubmission, setActiveSubmission] = useState<Submission | null>(
    assignment.my_submission || null
  );
  const [showAttachmentUploader, setShowAttachmentUploader] = useState<boolean>(false);

  const isEvaluated = activeSubmission?.is_evaluated || false;
  const isReleased = activeSubmission?.is_released || false;
  const isLocked = isEvaluated && activeSubmission?.status !== 'resubmission_requested';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const sub = await assessmentService.submitAssignment(assignment.id, content.trim() || undefined);
      setActiveSubmission(sub);
      onSubmitted();
    } catch (err: any) {
      setError(err.message || 'Failed to submit assignment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden space-y-4 p-6 max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between border-b pb-3">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md">
              Daily Assignment
            </span>
            <h2 className="text-base font-bold text-slate-900 mt-1">{assignment.title}</h2>
            <p className="text-xs text-slate-500">
              Max Marks: {assignment.max_marks} • Deadline:{' '}
              {new Date(assignment.deadline).toLocaleDateString()}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 rounded-lg p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Instructions */}
        <div className="rounded-xl bg-slate-50 p-3.5 space-y-1 text-xs">
          <span className="font-bold text-slate-700 block">Instructions:</span>
          <p className="text-slate-600 whitespace-pre-wrap">{assignment.instructions}</p>
        </div>

        {/* Evaluation Feedback Banner (if evaluated and released) */}
        {isEvaluated && isReleased && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
                <Award className="h-4 w-4 text-emerald-600" /> Evaluation Result Released
              </span>
              <span className="text-sm font-black text-emerald-900">
                {activeSubmission?.obtained_marks} / {assignment.max_marks} Marks
              </span>
            </div>
            {activeSubmission?.teacher_feedback && (
              <p className="text-xs text-emerald-800 bg-white/70 p-2.5 rounded-lg border border-emerald-100">
                <strong>Teacher's Feedback:</strong> {activeSubmission.teacher_feedback}
              </p>
            )}
          </div>
        )}

        {/* Resubmission requested banner */}
        {activeSubmission?.status === 'resubmission_requested' && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            <strong>Resubmission Requested:</strong> The teacher has requested revisions for your submission. Please update your response or attachments below and click &quot;Submit Revision&quot;.
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">
              Your Written Response / Solution Notes
            </label>
            <textarea
              rows={4}
              value={content}
              disabled={isLocked}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Type your answer, formulas, or explanation here..."
              className="w-full rounded-xl border border-slate-300 p-2.5 text-xs focus:border-indigo-600 focus:outline-hidden disabled:bg-slate-100 disabled:text-slate-500"
            />
          </div>

          {/* Submission Status & Attachments */}
          {activeSubmission ? (
            <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Submission Status:</span>
                <span className="font-bold text-emerald-700 uppercase">
                  {activeSubmission.status} (Attempt #{activeSubmission.attempt_number})
                </span>
              </div>

              {activeSubmission.attachments.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] text-slate-500">Uploaded Attachments:</span>
                  <div className="flex flex-wrap gap-2">
                    {activeSubmission.attachments.map((att) => (
                      <span
                        key={att.id}
                        className="bg-white border px-2 py-1 rounded-md text-[11px] font-medium text-slate-700"
                      >
                        {att.file_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {!isLocked && (
                <Button
                  size="sm"
                  variant="outline"
                  type="button"
                  onClick={() => setShowAttachmentUploader(true)}
                  className="w-full mt-2"
                  icon={<Upload className="h-3.5 w-3.5 text-indigo-600" />}
                >
                  Upload Homework Photo / PDF File
                </Button>
              )}
            </div>
          ) : null}

          {showAttachmentUploader && activeSubmission && (
            <div className="pt-2">
              <StudentAttachmentUploader
                submissionId={activeSubmission.id}
                pageOrder={(activeSubmission.attachments.length || 0) + 1}
                onCancel={() => setShowAttachmentUploader(false)}
                onSuccess={() => {
                  setShowAttachmentUploader(false);
                  onSubmitted();
                }}
              />
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t">
            <Button size="sm" variant="outline" type="button" onClick={onClose}>
              Close
            </Button>
            {!isLocked && (
              <Button
                size="sm"
                variant="primary"
                type="submit"
                disabled={submitting}
                icon={<Send className="h-4 w-4" />}
              >
                {submitting
                  ? 'Submitting...'
                  : activeSubmission?.status === 'resubmission_requested'
                  ? 'Submit Revision'
                  : activeSubmission
                  ? 'Update Response'
                  : 'Submit Homework'}
              </Button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
