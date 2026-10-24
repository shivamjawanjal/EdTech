export interface SubmissionAttachment {
  id: string;
  s3_key: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  page_order: number;
  created_at: string;
}

export interface Submission {
  id: string;
  assignment_id: string;
  student_id: string;
  attempt_number: number;
  is_latest: boolean;
  status: string; // 'submitted' | 'late' | 'evaluated' | 'resubmission_requested'
  student_content?: string | null;
  submitted_at: string;
  is_evaluated: boolean;
  obtained_marks?: string | number | null;
  teacher_feedback?: string | null;
  evaluated_at?: string | null;
  is_released: boolean;
  released_at?: string | null;
  attachments: SubmissionAttachment[];
  student_name?: string | null;
  student_email?: string | null;
}

export interface Assignment {
  id: string;
  lecture_id: string;
  title: string;
  instructions: string;
  max_marks: number;
  deadline: string;
  allow_late_submission: boolean;
  late_deadline?: string | null;
  is_published: boolean;
  created_at: string;
  updated_at: string;
  course_id?: string | null;
  course_title?: string | null;
  lecture_title?: string | null;
  submission_count: number;
  evaluated_count: number;
  pending_count: number;
  missing_count: number;
  my_submission?: Submission | null;
}

export interface AssignmentSubmissionQueue {
  assignment: Assignment;
  total_enrolled: number;
  submitted_count: number;
  evaluated_count: number;
  pending_count: number;
  late_count: number;
  missing_count: number;
  submissions: Submission[];
}

export interface QuestionOption {
  key: string;
  text: string;
}

export interface Question {
  id: string;
  test_id: string;
  question_text: string;
  question_image_s3_key?: string | null;
  options: QuestionOption[] | Record<string, string>;
  correct_option?: string | null;
  marks: number;
  negative_marks: number | string;
  solution_explanation?: string | null;
  order_index: number;
}

export interface Test {
  id: string;
  chapter_id: string;
  title: string;
  description?: string | null;
  duration_minutes: number;
  total_marks: number;
  pass_percentage: number;
  deadline: string;
  max_attempts: number;
  is_published: boolean;
  solutions_released_at?: string | null;
  results_released_at?: string | null;
  created_at: string;
  updated_at: string;
  chapter_title?: string | null;
  course_id?: string | null;
  course_title?: string | null;
  question_count: number;
  my_attempts_count: number;
  my_best_score?: number | string | null;
  active_attempt_id?: string | null;
}

export interface TestDetail extends Test {
  questions: Question[];
}

export interface AttemptStartResponse {
  attempt_id: string;
  test_id: string;
  attempt_number: number;
  started_at: string;
  expires_at: string;
  remaining_seconds: number;
  is_resumed: boolean;
  saved_answers: Record<string, string>;
}

export interface AnswerDetailItem {
  question_id: string;
  selected_option?: string | null;
  correct_option?: string | null;
  is_correct?: boolean | null;
  marks_awarded?: number | string | null;
  solution_explanation?: string | null;
}

export interface AttemptResult {
  attempt_id: string;
  test_id: string;
  attempt_number: number;
  is_completed: boolean;
  score: string | number;
  total_marks: number;
  percentage: string | number;
  passed: boolean;
  total_questions: number;
  correct_count: number;
  incorrect_count: number;
  unattempted_count: number;
  started_at: string;
  submitted_at?: string | null;
  solutions_released: boolean;
  results_released?: boolean;
  results_released_at?: string | null;
  answers?: AnswerDetailItem[] | null;
}
