import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Search, Bell, Plus, Globe, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getEmployees, getProjects, EmployeeItem, ProjectItem } from '../api/client';

interface NavbarProps {
  title?: string;
}

interface NotificationItem {
  id: string;
  title: string;
  description: string;
  time: string;
  type: 'warning' | 'success' | 'info';
  unread: boolean;
}

const initialNotifications: NotificationItem[] = [
  {
    id: 'n1',
    title: 'Перегрузка отдела Backend Core',
    description: 'Средняя загрузка 82% — превышает порог 80%. Требуется разгрузка.',
    time: '5 мин назад',
    type: 'warning',
    unread: true,
  },
  {
    id: 'n2',
    title: 'Заявка на отпуск',
    description: 'Дмитрий Соколов: 19.10.2026 — 27.10.2026 (Основной отпуск).',
    time: '42 мин назад',
    type: 'info',
    unread: true,
  },
  {
    id: 'n3',
    title: 'Спринт завершён успешно',
    description: 'Команда «ФинТех Платформа Core» закрыла 11 из 12 задач.',
    time: '2 ч назад',
    type: 'success',
    unread: false,
  },
];

export const Navbar: React.FC<NavbarProps> = ({ title = 'Панель управления' }) => {
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<NotificationItem[]>(initialNotifications);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<NotificationItem | null>(null);
  const [language, setLanguage] = useState<'ru' | 'en'>(() => (localStorage.getItem('teammind-language') as 'ru' | 'en') || 'ru');
  const [globalSearch, setGlobalSearch] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{label:string; detail:string; path:string}>>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => n.unread).length;

  // Клик вне панели — закрыть
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setIsNotifOpen(false);
      }
    };
    if (isNotifOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isNotifOpen]);

  useEffect(() => {
    const query = globalSearch.trim();
    if (!query) { setSearchResults([]); setSearchOpen(false); return; }
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const [employeesResp, projectsResp] = await Promise.all([getEmployees({search: query}), getProjects()]);
        if (cancelled) return;
        const employeeRows: EmployeeItem[] = employeesResp.results || [];
        const projectRows: ProjectItem[] = Array.isArray(projectsResp) ? projectsResp : [];
        setSearchResults([
          ...employeeRows.slice(0,5).map(e => ({label:e.name, detail:`${e.position} · ${e.department}`, path:'/employees'})),
          ...projectRows.filter(p => `${p.name} ${p.code} ${p.description || ''}`.toLowerCase().includes(query.toLowerCase())).slice(0,5).map(p => ({label:p.name, detail:p.code, path:'/projects'}))
        ]); setSearchOpen(true);
      } catch (err) { console.error('Global search failed', err); setSearchResults([]); setSearchOpen(true); }
    }, 250);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [globalSearch]);

  const toggleLanguage = () => { const next = language === 'ru' ? 'en' : 'ru'; setLanguage(next); localStorage.setItem('teammind-language', next); window.dispatchEvent(new CustomEvent('teammind-language-change', {detail: next})); };

  const handleNewProject = () => {
    navigate('/projects');
  };

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
  };

  const iconByType = (type: NotificationItem['type']) => {
    if (type === 'warning') return <AlertTriangle className="w-4 h-4 text-amber-400" />;
    if (type === 'success') return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    return <Clock className="w-4 h-4 text-brand-sky" />;
  };

  return (
    <header className="h-16 bg-[#0B1120]/80 backdrop-blur-md border-b border-slate-800/80 px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h1 className="text-lg font-semibold text-white tracking-tight">{title}</h1>
      </div>

      <div className="relative w-96 hidden md:block">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input type="text" value={globalSearch} onChange={(e) => setGlobalSearch(e.target.value)} onFocus={() => globalSearch.trim() && setSearchOpen(true)}
          placeholder={language === 'ru' ? 'Поиск сотрудников и проектов...' : 'Search employees and projects...'}
          className="w-full bg-slate-900/90 border border-slate-700/70 rounded-lg pl-10 pr-12 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-brand-sky focus:ring-1 focus:ring-brand-sky transition-all" />
        {searchOpen && <div className="absolute top-10 left-0 right-0 z-50 rounded-xl border border-slate-700 bg-slate-900 shadow-xl overflow-hidden">
          {searchResults.length ? searchResults.map((r, i) => <button key={`${r.path}-${r.label}-${i}`} onClick={() => { navigate(r.path); setGlobalSearch(''); setSearchOpen(false); }} className="block w-full text-left px-4 py-3 hover:bg-slate-800 border-b border-slate-800 last:border-0"><div className="text-xs text-white font-semibold">{r.label}</div><div className="text-[11px] text-slate-400">{r.detail}</div></button>) : <div className="px-4 py-3 text-xs text-slate-400">{language === 'ru' ? 'Ничего не найдено' : 'No results found'}</div>}
        </div>}
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
          ⌘K
        </kbd>
      </div>

      <div className="flex items-center gap-3">
        {/* Новый проект */}
        <button
          onClick={handleNewProject}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium shadow-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{language === 'ru' ? 'Новый проект' : 'New project'}</span>
        </button>

        <div className="h-5 w-px bg-slate-800 mx-1"></div>

        {/* Уведомления */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setIsNotifOpen((v) => !v)}
            className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            aria-label="Уведомления"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-blue-500 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-[#0B1120]">
                {unreadCount}
              </span>
            )}
          </button>

          {isNotifOpen && (
            <div className="absolute right-0 top-16 w-96 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50">
              <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-sm font-bold text-white">{language === 'ru' ? 'Уведомления' : 'Notifications'}</div>
                  <div className="text-[11px] text-slate-400">
                    {unreadCount > 0 ? (language === 'ru' ? `Непрочитанных: ${unreadCount}` : `Unread: ${unreadCount}`) : (language === 'ru' ? 'Все прочитаны' : 'All read')}
                  </div>
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[11px] text-brand-sky hover:underline font-medium"
                  >
                    {language === 'ru' ? 'Прочитать все' : 'Mark all read'}
                  </button>
                )}
              </div>

              <div className="max-h-96 overflow-y-auto divide-y divide-slate-800/70">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400">
                    Уведомлений нет
                  </div>
                ) : (
                  notifications.map((n) => (
                    <button
                      type="button" key={n.id} onClick={() => { setSelectedNotification(n); setNotifications(prev => prev.map(x => x.id === n.id ? {...x, unread:false} : x)); }}
                      className={`w-full text-left p-3 flex items-start gap-3 hover:bg-slate-800/40 transition-colors ${
                        n.unread ? 'bg-blue-500/5' : ''
                      }`}
                    >
                      <div className="p-1.5 rounded-lg bg-slate-800/80 shrink-0 mt-0.5">
                        {iconByType(n.type)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <div className="text-xs font-semibold text-white leading-tight">
                            {n.title}
                          </div>
                          {n.unread && (
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0 mt-1" />
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-1 leading-snug">
                          {n.description}
                        </div>
                        <div className="text-[10px] text-slate-500 mt-1">{n.time}</div>
                      </div>
                    </button>
                  ))
                )}
              </div>

              <div className="p-2 border-t border-slate-800 bg-slate-950/40 text-center">
                <button
                  onClick={() => setIsNotifOpen(false)}
                  className="text-[11px] text-slate-400 hover:text-white font-medium py-1 px-3 rounded-lg hover:bg-slate-800/60 transition-colors"
                >
                  Закрыть
                </button>
              </div>
            </div>
          )}
        </div>

        <button onClick={toggleLanguage} title={language === 'ru' ? 'Switch to English' : 'Переключить на русский'} className="flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-white px-2 py-1.5 rounded-lg hover:bg-slate-800/60 transition-colors"><Globe className="w-3.5 h-3.5" /><span>{language.toUpperCase()}</span></button>
      </div>

      {/* Модальное окно уведомления вынесено в Portal, чтобы избежать конфликта с backdrop-blur у header */}
      {selectedNotification && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4" onClick={() => setSelectedNotification(null)}>
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-lg font-bold text-white">{selectedNotification.title}</h2>
              <button onClick={() => setSelectedNotification(null)} className="text-slate-400 hover:text-white text-xl leading-none" aria-label="Close">×</button>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">{selectedNotification.description}</p>
            <div className="mt-4 text-xs text-slate-500">{selectedNotification.time}</div>
            <div className="mt-6 flex justify-end">
              <button onClick={() => setSelectedNotification(null)} className="rounded-lg bg-blue-600 hover:bg-blue-500 px-4 py-2 text-sm text-white font-medium transition-colors">
                {language === 'ru' ? 'Закрыть' : 'Close'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </header>
  );
};