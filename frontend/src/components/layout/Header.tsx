import React from 'react';
import { LogOut, User as UserIcon, BookOpen, Shield } from 'lucide-react';
import { useAuth } from '../../context/useAuth';
import { Button } from '../common/Button';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur-md sm:px-6 md:pl-68">
      {/* Platform Branding on Mobile / Small screens */}
      <div className="flex items-center gap-2.5 md:hidden">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs">
          <BookOpen className="h-5 w-5" />
        </div>
        <div>
          <span className="text-sm font-bold tracking-tight text-slate-900 block leading-none">
            Shiksha
          </span>
          <span className="text-[10px] text-slate-500 font-medium leading-none">
            Learning Platform
          </span>
        </div>
      </div>

      <div className="hidden md:block">
        <h2 className="text-base font-semibold text-slate-800">
          {user?.role === 'teacher' ? 'Teacher Command Console' : 'Student Study Center'}
        </h2>
      </div>

      {/* User Status & Profile Actions */}
      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-2.5">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-slate-900 leading-tight">
                {user.full_name}
              </span>
              <span className="text-[11px] text-slate-500 font-medium capitalize">
                {user.role} {user.profile?.grade_level ? `• ${user.profile.grade_level}` : ''}
              </span>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 font-bold text-xs">
              {user.role === 'teacher' ? (
                <Shield className="h-4 w-4 text-indigo-600" />
              ) : (
                <UserIcon className="h-4 w-4 text-indigo-600" />
              )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              title="Sign Out"
              aria-label="Sign Out"
              className="text-slate-500 hover:text-rose-600 hover:bg-rose-50"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        )}
      </div>
    </header>
  );
};
