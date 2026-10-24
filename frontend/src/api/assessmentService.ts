import { apiClient } from './client';
import type {
  Assignment,
  AssignmentSubmissionQueue,
  Submission,
  Test,
  TestDetail,
  Question,
  AttemptStartResponse,
  AttemptResult,
} from '../types/assessment';

export const assessmentService = {
  // Assignments
  async getAssignments(params?: { lecture_id?: string; course_id?: string }): Promise<Assignment[]> {
    const query = new URLSearchParams();
    if (params?.lecture_id) query.append('lecture_id', params.lecture_id);
    if (params?.course_id) query.append('course_id', params.course_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<Assignment[]>(`/api/v1/assessment/assignments${qs}`);
  },

  async getAssignment(assignmentId: string): Promise<Assignment> {
    return apiClient<Assignment>(`/api/v1/assessment/assignments/${assignmentId}`);
  },

  async createAssignment(payload: {
    lecture_id: string;
    title: string;
    instructions: string;
    max_marks: number;
    deadline: string;
    allow_late_submission?: boolean;
    late_deadline?: string | null;
    is_published?: boolean;
  }): Promise<Assignment> {
    return apiClient<Assignment>('/api/v1/assessment/assignments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async submitAssignment(assignmentId: string, studentContent?: string): Promise<Submission> {
    return apiClient<Submission>(`/api/v1/assessment/assignments/${assignmentId}/submissions`, {
      method: 'POST',
      body: JSON.stringify({ student_content: studentContent }),
    });
  },

  async getAssignmentSubmissions(
    assignmentId: string,
    statusFilter?: string
  ): Promise<AssignmentSubmissionQueue> {
    const qs = statusFilter ? `?status=${statusFilter}` : '';
    return apiClient<AssignmentSubmissionQueue>(
      `/api/v1/assessment/assignments/${assignmentId}/submissions${qs}`
    );
  },

  async getMySubmissions(assignmentId: string): Promise<Submission[]> {
    return apiClient<Submission[]>(`/api/v1/assessment/assignments/${assignmentId}/submissions/my`);
  },

  async gradeSubmission(
    submissionId: string,
    payload: {
      obtained_marks: number | string;
      teacher_feedback?: string;
      is_released?: boolean;
    }
  ): Promise<Submission> {
    return apiClient<Submission>(`/api/v1/assessment/submissions/${submissionId}/grade`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async releaseAssignmentGrades(assignmentId: string): Promise<{ message: string; detail?: string }> {
    return apiClient<{ message: string; detail?: string }>(
      `/api/v1/assessment/assignments/${assignmentId}/release-grades`,
      { method: 'POST' }
    );
  },

  // Timed MCQ Tests
  async getTests(params?: { chapter_id?: string; course_id?: string }): Promise<Test[]> {
    const query = new URLSearchParams();
    if (params?.chapter_id) query.append('chapter_id', params.chapter_id);
    if (params?.course_id) query.append('course_id', params.course_id);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return apiClient<Test[]>(`/api/v1/assessment/tests${qs}`);
  },

  async getTest(testId: string): Promise<TestDetail> {
    return apiClient<TestDetail>(`/api/v1/assessment/tests/${testId}`);
  },

  async createTest(payload: {
    chapter_id: string;
    title: string;
    description?: string;
    duration_minutes: number;
    pass_percentage?: number;
    deadline: string;
    max_attempts?: number;
    is_published?: boolean;
    solutions_released_at?: string | null;
    results_released_at?: string | null;
  }): Promise<Test> {
    return apiClient<Test>('/api/v1/assessment/tests', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async addQuestion(
    testId: string,
    payload: {
      question_text: string;
      options: Array<{ key: string; text: string }>;
      correct_option: string;
      marks?: number;
      negative_marks?: number | string;
      solution_explanation?: string;
      order_index?: number;
    }
  ): Promise<Question> {
    return apiClient<Question>(`/api/v1/assessment/tests/${testId}/questions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async startTestAttempt(testId: string): Promise<AttemptStartResponse> {
    return apiClient<AttemptStartResponse>(`/api/v1/assessment/tests/${testId}/attempts/start`, {
      method: 'POST',
    });
  },

  async saveAnswer(
    attemptId: string,
    questionId: string,
    selectedOption: string | null
  ): Promise<{ message: string }> {
    return apiClient<{ message: string }>(
      `/api/v1/assessment/tests/attempts/${attemptId}/save-answer`,
      {
        method: 'POST',
        body: JSON.stringify({ question_id: questionId, selected_option: selectedOption }),
      }
    );
  },

  async submitTestAttempt(attemptId: string): Promise<AttemptResult> {
    return apiClient<AttemptResult>(`/api/v1/assessment/tests/attempts/${attemptId}/submit`, {
      method: 'POST',
    });
  },

  async getTestAttempts(testId: string): Promise<AttemptResult[]> {
    return apiClient<AttemptResult[]>(`/api/v1/assessment/tests/${testId}/attempts`);
  },

  async getMyTestAttempts(testId: string): Promise<AttemptResult[]> {
    return apiClient<AttemptResult[]>(`/api/v1/assessment/tests/${testId}/attempts/my`);
  },
};
