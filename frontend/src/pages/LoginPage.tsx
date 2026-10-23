import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { GraduationCap, Lock, Phone, AlertCircle, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { ApiError } from '../api/client';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username.trim()) {
      setError('Please enter your registered phone number or email.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await login({ username: username.trim(), password });
      
      // Determine redirection target based on role or original destination
      if (from && from !== '/login' && from !== '/unauthorized') {
        navigate(from, { replace: true });
      } else if (user.role === 'teacher') {
        navigate('/teacher/dashboard', { replace: true });
      } else {
        navigate('/student/home', { replace: true });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data.error || 'Authentication failed. Please verify credentials.');
      } else {
        setError('Unable to reach server. Please check your connection.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoCredentials = (role: 'teacher' | 'student') => {
    if (role === 'teacher') {
      setUsername('teacher@edtechweb.local');
      setPassword('TeacherPassword123!');
    } else {
      setUsername('student001@edtechweb.local');
      setPassword('StudentPassword123!');
    }
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="w-full max-w-md text-center mb-6">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-200 mb-3">
          <GraduationCap className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Teacher Learning Platform
        </h1>
        <p className="mt-1.5 text-xs text-slate-500 max-w-xs mx-auto">
          Private academic ecosystem for Mathematics, Science & Reasoning
        </p>
      </div>

      {/* Main Login Card */}
      <div className="w-full max-w-md rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-500 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <Input
            label="Phone Number or Email"
            type="text"
            placeholder="+919800000001 or student@..."
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            prefixIcon={<Phone className="h-4 w-4" />}
            autoComplete="username"
            required
          />

          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            prefixIcon={<Lock className="h-4 w-4" />}
            suffixIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-slate-400 hover:text-slate-600 focus:outline-none"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
            autoComplete="current-password"
            required
          />

          <Button
            type="submit"
            size="lg"
            className="w-full mt-2 font-semibold"
            isLoading={isSubmitting}
          >
            Sign In to Classroom
          </Button>
        </form>

        {/* Development Quick Fill Helpers */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 text-center mb-2.5">
            Development Quick-Fill Credentials
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillDemoCredentials('teacher')}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-indigo-100 bg-indigo-50/60 py-2 px-3 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Teacher Demo
            </button>
            <button
              type="button"
              onClick={() => fillDemoCredentials('student')}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 py-2 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <GraduationCap className="h-3.5 w-3.5" />
              Student Demo
            </button>
          </div>
        </div>
      </div>

      {/* Security Notice */}
      <p className="mt-6 text-center text-[11px] text-slate-400 max-w-sm">
        Protected by session token rotation and HttpOnly cookies. Private institutional access only.
      </p>
    </div>
  );
};
