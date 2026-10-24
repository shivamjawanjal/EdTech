import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { StudentQuizView } from '../pages/StudentQuizView';
import { TeacherAssessmentConsole } from '../components/assessment/TeacherAssessmentConsole';
import { assessmentService } from '../api/assessmentService';

vi.mock('../api/assessmentService', () => ({
  assessmentService: {
    getTest: vi.fn(),
    startTestAttempt: vi.fn(),
    saveAnswer: vi.fn(),
    submitTestAttempt: vi.fn(),
    getAssignments: vi.fn(),
    getAssignmentSubmissions: vi.fn(),
    gradeSubmission: vi.fn(),
    releaseAssignmentGrades: vi.fn(),
    getTests: vi.fn(),
    getTestAttempts: vi.fn(),
  },
}));

describe('StudentQuizView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockTestDetail = {
    id: 'test-123',
    chapter_id: 'chap-1',
    title: 'Kinematics Weekly Assessment',
    description: 'Test covering 1D motion',
    duration_minutes: 15,
    total_marks: 6,
    pass_percentage: 50,
    deadline: new Date(Date.now() + 86400000).toISOString(),
    max_attempts: 2,
    is_published: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    question_count: 2,
    my_attempts_count: 0,
    questions: [
      {
        id: 'q-1',
        test_id: 'test-123',
        question_text: 'Which graph is linear for uniform acceleration?',
        options: [
          { key: 'A', text: 'Velocity-Time' },
          { key: 'B', text: 'Displacement-Time' },
        ],
        marks: 4,
        negative_marks: '1.00',
        order_index: 1,
      },
      {
        id: 'q-2',
        test_id: 'test-123',
        question_text: 'What is the SI unit of acceleration?',
        options: [
          { key: 'A', text: 'm/s' },
          { key: 'B', text: 'm/s^2' },
        ],
        marks: 2,
        negative_marks: '0.50',
        order_index: 2,
      },
    ],
  };

  it('renders pre-assessment overview card with rules and duration', async () => {
    vi.mocked(assessmentService.getTest).mockResolvedValue(mockTestDetail as any);

    render(
      <MemoryRouter initialEntries={['/student/tests/test-123']}>
        <Routes>
          <Route path="/student/tests/:testId" element={<StudentQuizView />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Kinematics Weekly Assessment')).toBeInTheDocument();
    expect(screen.getByText('15 Minutes')).toBeInTheDocument();
    expect(screen.getByText('6 Marks')).toBeInTheDocument();
    expect(screen.getByText('Start Timed Assessment')).toBeInTheDocument();
  });

  it('starts timed attempt and displays question with options and authoritative timer', async () => {
    vi.mocked(assessmentService.getTest).mockResolvedValue(mockTestDetail as any);
    vi.mocked(assessmentService.startTestAttempt).mockResolvedValue({
      attempt_id: 'att-999',
      test_id: 'test-123',
      attempt_number: 1,
      started_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 900000).toISOString(),
      remaining_seconds: 900,
      is_resumed: false,
      saved_answers: {},
    });

    render(
      <MemoryRouter initialEntries={['/student/tests/test-123']}>
        <Routes>
          <Route path="/student/tests/:testId" element={<StudentQuizView />} />
        </Routes>
      </MemoryRouter>
    );

    const startBtn = await screen.findByText('Start Timed Assessment');
    fireEvent.click(startBtn);

    expect(
      await screen.findByText('Which graph is linear for uniform acceleration?')
    ).toBeInTheDocument();
    expect(screen.getByText('Velocity-Time')).toBeInTheDocument();
    expect(screen.getByText('Displacement-Time')).toBeInTheDocument();
    expect(screen.getByText('15:00')).toBeInTheDocument();
  });
});

describe('TeacherAssessmentConsole Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders assignment queue metrics and submission list', async () => {
    const mockAssignments = [
      {
        id: 'asn-1',
        lecture_id: 'lec-1',
        title: 'Daily Homework 1: Quadratic Equations',
        instructions: 'Solve problems 1-5',
        max_marks: 10,
        deadline: new Date().toISOString(),
        allow_late_submission: true,
        is_published: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        submission_count: 5,
        evaluated_count: 2,
        pending_count: 3,
        missing_count: 10,
      },
    ];

    const mockQueue = {
      assignment: mockAssignments[0],
      total_enrolled: 15,
      submitted_count: 5,
      evaluated_count: 2,
      pending_count: 3,
      late_count: 1,
      missing_count: 10,
      submissions: [
        {
          id: 'sub-1',
          assignment_id: 'asn-1',
          student_id: 'st-1',
          attempt_number: 1,
          is_latest: true,
          status: 'submitted',
          student_content: 'Step 1: ax^2 + bx + c = 0',
          submitted_at: new Date().toISOString(),
          is_evaluated: false,
          is_released: false,
          attachments: [],
          student_name: 'Aarav Patel',
          student_email: 'aarav@edtech.local',
        },
      ],
    };

    vi.mocked(assessmentService.getAssignments).mockResolvedValue(mockAssignments as any);
    vi.mocked(assessmentService.getAssignmentSubmissions).mockResolvedValue(mockQueue as any);

    render(<TeacherAssessmentConsole onClose={() => {}} />);

    expect(await screen.findByText('Assessment & Evaluation Engine')).toBeInTheDocument();
    expect(screen.getByText('Total Enrolled')).toBeInTheDocument();
    expect(screen.getByText('Pending Grading')).toBeInTheDocument();
    expect(screen.getByText('Missing Work')).toBeInTheDocument();
    expect(screen.getByText('Aarav Patel')).toBeInTheDocument();
    expect(screen.getByText('Grade Submission')).toBeInTheDocument();
  });
});
