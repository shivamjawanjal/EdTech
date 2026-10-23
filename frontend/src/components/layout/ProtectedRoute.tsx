import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/useAuth';
import type { UserRole } from '../../types/auth';
import { FullPageLoader } from '../common/LoadingSpinner';
import { AppShell } from './AppShell';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  useShell?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  useShell = true,
}) => {
  const { isAuthenticated, isLoading, role } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullPageLoader message="Restoring session..." />;
  }

  if (!isAuthenticated) {
    // Preserve attempted destination for post-login redirection
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  return useShell ? <AppShell>{children}</AppShell> : <>{children}</>;
};
