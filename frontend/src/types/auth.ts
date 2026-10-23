export type UserRole = 'teacher' | 'student';

export interface StudentProfile {
  roll_number?: string | null;
  parent_name?: string | null;
  parent_phone?: string | null;
  school_name?: string | null;
  grade_level?: string | null;
  target_exam?: string | null;
  teacher_notes?: string | null;
}

export interface User {
  id: string;
  phone: string;
  email?: string | null;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  must_change_password: boolean;
  profile?: StudentProfile | null;
}

export interface LoginCredentials {
  username: string; // Email or phone number
  password: string;
}

export interface TokenResponse {
  message: string;
  token_type: string;
  user: User;
  access_token?: string;
}

export interface ApiErrorResponse {
  error: string;
  detail?: string;
  code?: string;
  request_id?: string;
}
