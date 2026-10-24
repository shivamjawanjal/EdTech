import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/useAuth';
import { LoginPage } from './pages/LoginPage';
import { TeacherDashboard } from './pages/TeacherDashboard';
import { StudentHome } from './pages/StudentHome';
import { StudentLectureView } from './pages/StudentLectureView';
import { StudentQuizView } from './pages/StudentQuizView';
import { UnauthorizedPage } from './pages/UnauthorizedPage';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { FullPageLoader } from './components/common/LoadingSpinner';

const RootRedirect: React.FC = () => {
  const { isAuthenticated, isLoading, role } = useAuth();

  if (isLoading) {
    return <FullPageLoader message="Opening learning platform..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (role === 'teacher') {
    return <Navigate to="/teacher/dashboard" replace />;
  }

  return <Navigate to="/student/home" replace />;
};

const PublicLoginRoute: React.FC = () => {
  const { isAuthenticated, isLoading, role } = useAuth();

  if (isLoading) {
    return <FullPageLoader message="Checking authentication state..." />;
  }

  if (isAuthenticated) {
    return role === 'teacher' ? (
      <Navigate to="/teacher/dashboard" replace />
    ) : (
      <Navigate to="/student/home" replace />
    );
  }

  return <LoginPage />;
};

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<PublicLoginRoute />} />
      <Route
        path="/teacher/dashboard"
        element={
          <ProtectedRoute requiredRole="teacher">
            <TeacherDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/home"
        element={
          <ProtectedRoute requiredRole="student">
            <StudentHome />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/lectures/:lectureId"
        element={
          <ProtectedRoute requiredRole="student" useShell={false}>
            <StudentLectureView />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/tests/:testId"
        element={
          <ProtectedRoute requiredRole="student" useShell={false}>
            <StudentQuizView />
          </ProtectedRoute>
        }
      />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
