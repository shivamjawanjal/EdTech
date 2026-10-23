import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { AuthContext } from '../context/authContextDef';
import type { AuthContextType } from '../context/authContextDef';
import type { LoginCredentials, User } from '../types/auth';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage Component', () => {
  let mockLogin: ReturnType<typeof vi.fn<(credentials: LoginCredentials) => Promise<User>>>;
  let mockAuthContextValue: AuthContextType;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin = vi.fn<(credentials: LoginCredentials) => Promise<User>>();
    mockAuthContextValue = {
      user: null,
      role: null,
      isAuthenticated: false,
      isLoading: false,
      login: mockLogin,
      logout: vi.fn(),
      checkAuth: vi.fn(),
    };
  });

  const renderComponent = () => {
    return render(
      <AuthContext.Provider value={mockAuthContextValue}>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </AuthContext.Provider>
    );
  };

  it('renders login form elements with accessible labels and touch targets', () => {
    renderComponent();
    expect(screen.getByRole('heading', { name: /teacher learning platform/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/phone number or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in to classroom/i })).toBeInTheDocument();
  });

  it('populates demo credentials when clicking quick-fill buttons', () => {
    renderComponent();
    const teacherDemoBtn = screen.getByRole('button', { name: /teacher demo/i });
    fireEvent.click(teacherDemoBtn);

    const usernameInput = screen.getByLabelText(/phone number or email/i) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;

    expect(usernameInput.value).toBe('teacher@edtechweb.local');
    expect(passwordInput.value).toBe('TeacherPassword123!');
  });

  it('calls login handler with entered credentials upon submission', async () => {
    const fakeUser: User = {
      id: 'teacher-uuid',
      phone: '+919999900000',
      email: 'teacher@edtechweb.local',
      full_name: 'Prof. Rajesh Sharma',
      role: 'teacher',
      is_active: true,
      must_change_password: false,
    };
    mockLogin.mockResolvedValue(fakeUser);

    renderComponent();
    fireEvent.change(screen.getByLabelText(/phone number or email/i), {
      target: { value: 'teacher@edtechweb.local' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'TeacherPassword123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in to classroom/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'teacher@edtechweb.local',
        password: 'TeacherPassword123!',
      });
      expect(mockNavigate).toHaveBeenCalledWith('/teacher/dashboard', { replace: true });
    });
  });
});
