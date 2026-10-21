import React from 'react';
import { Search, Bell, Plus, Moon, Sparkles, Globe } from 'lucide-react';

interface NavbarProps {
  title?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title = 'Панель управления' }) => {
  return (
    <header className="h-16 bg-[#0B1120]/80 backdrop-blur-md border-b border-slate-800/80 px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Page Title & Breadcrumbs */}
      <div>
        <h1 className="text-lg font-semibold text-white tracking-tight">{title}</h1>
      </div>

      {/* Center Search Bar */}
      <div className="relative w-96 hidden md:block">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Поиск сотрудников, проектов, навыков... (Ctrl+F)"
          className="w-full bg-slate-900/90 border border-slate-700/70 rounded-lg pl-10 pr-12 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-brand-sky focus:ring-1 focus:ring-brand-sky transition-all"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
          ⌘K
        </kbd>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        <button className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium shadow-sm transition-colors">
          <Plus className="w-3.5 h-3.5" />
          <span>Новый проект</span>
        </button>

        <div className="h-5 w-px bg-slate-800 mx-1"></div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-500 ring-2 ring-[#0B1120]"></span>
        </button>

        {/* Language selector */}
        <button className="flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-white px-2 py-1.5 rounded-lg hover:bg-slate-800/60 transition-colors">
          <Globe className="w-3.5 h-3.5" />
          <span>RU</span>
        </button>
      </div>
    </header>
  );
};
