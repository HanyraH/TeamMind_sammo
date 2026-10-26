import React, { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar.tsx';
import { Navbar } from './Navbar.tsx';

const pageTitles: Record<string, string> = {
  '/': 'Сводный дашборд ресурсов',
  '/employees': 'Управление сотрудниками и профили',
  '/projects': 'Реестр проектов и потребностей',
  '/constructor': 'Интеллектуальный конструктор команд (AI Matching)',
  '/calendar': 'Календарь отсутствий и отпусков (16 типов)',
  '/analytics': 'Аналитика утилизации и баланса нагрузки',
  '/gantt': 'Диаграмма Ганта и расписание задач',
  '/settings': 'Справочники навыков, ролей и системные настройки',
};

export const Layout: React.FC = () => {
  const location = useLocation();
  const [language, setLanguage] = useState<'ru'|'en'>(() => (localStorage.getItem('teammind-language') as 'ru'|'en') || 'ru');
  useEffect(() => { const update = (e: Event) => setLanguage((e as CustomEvent<'ru'|'en'>).detail); window.addEventListener('teammind-language-change', update); return () => window.removeEventListener('teammind-language-change', update); }, []);
  const englishTitles: Record<string,string> = {'/':'Resource dashboard','/employees':'Employee management','/projects':'Project registry','/constructor':'AI team builder','/calendar':'Absence calendar','/analytics':'Workload analytics','/gantt':'Project schedule','/settings':'Reference data & settings'};
  const currentTitle = language === 'en' ? (englishTitles[location.pathname] || 'TeamMind') : (pageTitles[location.pathname] || 'TeamMind');

  return (
    <div className="flex min-h-screen bg-[#070C18]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar title={currentTitle} />
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
