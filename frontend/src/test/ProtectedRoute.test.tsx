import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '../components/layout/ProtectedRoute';
import { AuthContext } from '../context/authContextDef';
import type { AuthContextType } from '../context/authContextDef';
import type { User } from '../types/auth';

describe('ProtectedRoute Guard Component', () => {
  const createMockAuth = (overrides: Partial<AuthContextType> = {}): AuthContextType => ({
    user: null,
    role: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
    ...overrides,
  });

  const studentUser: User = {
    id: 'student-1',
    phone: '+919800000001',
    full_name: 'Student 001',
    role: 'student',
    is_active: true,
    must_change_password: false,
  };

  const teacherUser: User = {
    id: 'teacher-1',
    phone: '+919999900000',
    full_name: 'Prof. Sharma',
    role: 'teacher',
    is_active: true,
    must_change_password: false,
  };

  it('renders loading indicator when auth state is loading', () => {
    const authVal = createMockAuth({ isLoading: true });
    render(
      <AuthContext.Provider value={authVal}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <ProtectedRoute>
            <div>Dashboard Content</div>
          </ProtectedRoute>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText(/restoring session/i)).toBeInTheDocument();
  });

  it('redirects unauthenticated users to /login', () => {
    const authVal = createMockAuth({ isAuthenticated: false, isLoading: false });
    render(
      <AuthContext.Provider value={authVal}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <div>Secret Dashboard</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>Login Page Screen</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Login Page Screen')).toBeInTheDocument();
    expect(screen.queryByText('Secret Dashboard')).not.toBeInTheDocument();
  });

  it('redirects student attempting to access teacher route to /unauthorized', () => {
    const authVal = createMockAuth({
      user: studentUser,
      role: 'student',
      isAuthenticated: true,
      isLoading: false,
    });

    render(
      <AuthContext.Provider value={authVal}>
        <MemoryRouter initialEntries={['/teacher/dashboard']}>
          <Routes>
            <Route
              path="/teacher/dashboard"
              element={
                <ProtectedRoute requiredRole="teacher">
                  <div>Teacher Secret Console</div>
                </ProtectedRoute>
              }
            />
            <Route path="/unauthorized" element={<div>Access Denied Screen</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Access Denied Screen')).toBeInTheDocument();
    expect(screen.queryByText('Teacher Secret Console')).not.toBeInTheDocument();
  });

  it('renders children when user role matches requirement', () => {
    const authVal = createMockAuth({
      user: teacherUser,
      role: 'teacher',
      isAuthenticated: true,
      isLoading: false,
    });

    render(
      <AuthContext.Provider value={authVal}>
        <MemoryRouter initialEntries={['/teacher/dashboard']}>
          <Routes>
            <Route
              path="/teacher/dashboard"
              element={
                <ProtectedRoute requiredRole="teacher" useShell={false}>
                  <div>Authorized Teacher Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    expect(screen.getByText('Authorized Teacher Content')).toBeInTheDocument();
  });
});
