import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, BookOpen, CheckSquare, User } from 'lucide-react';
import { useAuth } from '../../context/useAuth';

export const MobileNav: React.FC = () => {
  const { user } = useAuth();
  const isTeacher = user?.role === 'teacher';

  const homePath = isTeacher ? '/teacher/dashboard' : '/student/home';

  const navItems = [
    { to: homePath, label: isTeacher ? 'Console' : 'Daily', icon: Home },
    { to: '#curriculum', label: 'Subjects', icon: BookOpen },
    { to: '#assignments', label: isTeacher ? 'Grading' : 'Homework', icon: CheckSquare },
    { to: '#profile', label: 'Profile', icon: User },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white/95 border-t border-slate-200 backdrop-blur-md pb-safe">
      <div className="grid grid-cols-4 h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isHash = item.to.startsWith('#');

          return isHash ? (
            <a
              key={item.label}
              href={item.to}
              className="touch-target flex flex-col items-center justify-center text-slate-500 hover:text-indigo-600 transition-colors select-none"
            >
              <Icon className="h-5 w-5 mb-0.5" />
              <span className="text-[10px] font-medium leading-none">{item.label}</span>
            </a>
          ) : (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) =>
                `touch-target flex flex-col items-center justify-center transition-colors select-none ${
                  isActive ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-900'
                }`
              }
            >
              <Icon className="h-5 w-5 mb-0.5" />
              <span className="text-[10px] font-medium leading-none">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};
