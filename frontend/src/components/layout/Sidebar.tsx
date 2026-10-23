import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  CheckSquare,
  Users,
  BookOpen,
  HelpCircle,
  LogOut,
  GraduationCap,
} from 'lucide-react';
import { useAuth } from '../../context/useAuth';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const isTeacher = user?.role === 'teacher';

  const teacherLinks = [
    { to: '/teacher/dashboard', label: 'Overview', icon: LayoutDashboard },
    { to: '#schedule', label: 'Teaching Schedule', icon: Calendar, badge: 'Live' },
    { to: '#grading', label: 'Pending Grading', icon: CheckSquare, badge: '14' },
    { to: '#students', label: 'Students Triage', icon: Users },
    { to: '#curriculum', label: 'Course Curriculum', icon: BookOpen },
    { to: '#doubts', label: 'Student Doubts', icon: HelpCircle, badge: '3' },
  ];

  const studentLinks = [
    { to: '/student/home', label: 'Daily Mission', icon: LayoutDashboard },
    { to: '#curriculum', label: 'My Subjects', icon: BookOpen },
    { to: '#assignments', label: 'Homework & Tests', icon: CheckSquare, badge: '1 Due' },
    { to: '#schedule', label: 'Live Classes', icon: Calendar },
    { to: '#doubts', label: 'Ask Doubts', icon: HelpCircle },
  ];

  const links = isTeacher ? teacherLinks : studentLinks;

  return (
    <aside className="hidden md:flex fixed inset-y-0 left-0 z-40 w-64 flex-col justify-between border-r border-slate-200 bg-white">
      <div>
        {/* Brand Logo Header */}
        <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-900 leading-none">
              Shiksha
            </h1>
            <span className="text-[11px] font-medium text-slate-500">
              {isTeacher ? 'Teacher Console' : 'Student Workspace'}
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1 px-3 py-4">
          <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Platform Navigation
          </p>
          {links.map((link) => {
            const Icon = link.icon;
            const isHash = link.to.startsWith('#');

            return isHash ? (
              <a
                key={link.label}
                href={link.to}
                className="flex items-center justify-between rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4 text-slate-400" />
                  <span>{link.label}</span>
                </div>
                {link.badge && (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600">
                    {link.badge}
                  </span>
                )}
              </a>
            ) : (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center justify-between rounded-xl px-3.5 py-2.5 text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 shadow-2xs font-bold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4" />
                  <span>{link.label}</span>
                </div>
                {link.badge && (
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                    {link.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer User Info */}
      <div className="border-t border-slate-100 p-4">
        <div className="rounded-xl bg-slate-50 p-3 mb-2 flex items-center justify-between">
          <div className="truncate pr-2">
            <p className="text-xs font-semibold text-slate-900 truncate">{user?.full_name}</p>
            <p className="text-[10px] text-slate-500 truncate">{user?.phone || user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="text-slate-400 hover:text-rose-600 p-1 rounded-lg transition-colors"
            title="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
