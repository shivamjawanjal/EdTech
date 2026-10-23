import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, LogOut } from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { Button } from '../components/common/Button';

export const UnauthorizedPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleReturnHome = () => {
    if (user?.role === 'teacher') {
      navigate('/teacher/dashboard', { replace: true });
    } else if (user?.role === 'student') {
      navigate('/student/home', { replace: true });
    } else {
      navigate('/login', { replace: true });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 text-center shadow-xs">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-600 mb-4">
          <ShieldAlert className="h-7 w-7" />
        </div>

        <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">
          Access Restricted
        </h1>
        <p className="mt-2 text-xs text-slate-600 leading-relaxed">
          Your account ({user?.full_name || 'Anonymous'}, Role: {user?.role || 'Guest'}) does not have permission to view this section of the educational platform.
        </p>

        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            variant="primary"
            onClick={handleReturnHome}
            icon={<ArrowLeft className="h-4 w-4" />}
            className="w-full sm:w-auto"
          >
            Return to My Portal
          </Button>
          <Button
            variant="outline"
            onClick={logout}
            icon={<LogOut className="h-4 w-4" />}
            className="w-full sm:w-auto"
          >
            Sign Out
          </Button>
        </div>
      </div>
    </div>
  );
};
