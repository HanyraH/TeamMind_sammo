import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  FolderKanban, 
  Sparkles, 
  CalendarDays, 
  BarChart3, 
  Sliders, 
  GanttChartSquare,
  ShieldCheck,
  Brain
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Дашборд', icon: LayoutDashboard },
  { path: '/employees', label: 'Сотрудники', icon: Users },
  { path: '/projects', label: 'Проекты', icon: FolderKanban },
  { path: '/constructor', label: 'Конструктор команд', icon: Sparkles, badge: 'AI' },
  { path: '/calendar', label: 'Календарь отсутствий', icon: CalendarDays },
  { path: '/analytics', label: 'Аналитика и загрузка', icon: BarChart3 },
  { path: '/gantt', label: 'Расписание проектов', icon: GanttChartSquare },
  { path: '/settings', label: 'Справочники и настройки', icon: Sliders },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#0B1120] border-r border-slate-800/80 flex flex-col h-screen sticky top-0 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800/60">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-blue to-brand-sky flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-lg tracking-wide text-white">Team<span className="text-brand-sky">Mind</span></span>
          <div className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Resource AI Core</div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Основное меню
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-blue-600/15 text-brand-sky border border-blue-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-sm">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* User Status Bar */}
      <div className="p-4 border-t border-slate-800/60 bg-[#070C18]/60">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-slate-700 flex items-center justify-center font-semibold text-white text-sm border border-slate-600">
              ИП
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-[#070C18]"></span>
          </div>
          <div className="overflow-hidden">
            <div className="text-sm font-semibold text-slate-200 truncate">Иван Петров</div>
            <div className="text-xs text-slate-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-brand-sky" />
              <span>Resource Manager</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
