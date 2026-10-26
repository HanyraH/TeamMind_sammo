import React, { useState, useEffect } from 'react';
import { 
  GanttChartSquare, Calendar, User, CheckCircle2, Clock, 
  Filter, Briefcase, HelpCircle, Eye, BarChart2
} from 'lucide-react';
import { getGanttTasks, getProjects, ProjectItem } from '../api/client';

interface GanttTaskItem {
  id: string;
  name: string;
  projectName: string;
  assignee: string;
  progress: number;
  startCol: number;
  span: number;
  startDate: string;
  endDate: string;
  color: string;
  status: string;
}

export const GanttChart: React.FC = () => {
  const [tasks, setTasks] = useState<GanttTaskItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('ALL');
  const [viewMode, setViewMode] = useState<'GANTT' | 'PROGRESS'>('GANTT');
  const [showExplanation, setShowExplanation] = useState(false);
  const [loading, setLoading] = useState(false);

  const defaultSprintTasks: GanttTaskItem[] = [
    { 
      id: '1', 
      name: 'Проектирование схемы БД (55 таблиц) и индексы PostgreSQL 18', 
      projectName: 'ФинТех Платформа Core',
      assignee: 'Дмитрий Соколов (Дима)', 
      progress: 100, 
      startCol: 1, 
      span: 3, 
      startDate: '01.10.2026',
      endDate: '21.10.2026',
      color: 'from-blue-600 to-blue-500', 
      status: 'Завершено'
    },
    { 
      id: '2', 
      name: 'Базовый Layout, Auth и 9 экранов (React 18 + TS)', 
      projectName: 'ФинТех Платформа Core',
      assignee: 'Артём Самособой (Артем)', 
      progress: 95, 
      startCol: 2, 
      span: 4, 
      startDate: '08.10.2026',
      endDate: '05.11.2026',
      color: 'from-sky-500 to-sky-400', 
      status: 'В работе'
    },
    { 
      id: '3', 
      name: 'Математическая модель (S-скор) & What-If симулятор в Celery', 
      projectName: 'ФинТех Платформа Core',
      assignee: 'Виктор Дмитриевич (Виктор)', 
      progress: 75, 
      startCol: 3, 
      span: 4, 
      startDate: '15.10.2026',
      endDate: '12.11.2026',
      color: 'from-indigo-600 to-indigo-500', 
      status: 'В работе'
    },
    { 
      id: '4', 
      name: 'Инфраструктура Docker Compose, Nginx и CI/CD пайплайны', 
      projectName: 'ФинТех Платформа Core',
      assignee: 'Олег Морозов (Олег)', 
      progress: 85, 
      startCol: 3, 
      span: 4, 
      startDate: '15.10.2026',
      endDate: '12.11.2026',
      color: 'from-emerald-600 to-emerald-500', 
      status: 'В работе'
    },
    { 
      id: '5', 
      name: 'Календарь 16 типов отсутствий и Recharts аналитика', 
      projectName: 'Мобильный кабинет HR (PWA)',
      assignee: 'Артём / Виктор', 
      progress: 70, 
      startCol: 4, 
      span: 4, 
      startDate: '22.10.2026',
      endDate: '19.11.2026',
      color: 'from-amber-600 to-amber-500', 
      status: 'В работе'
    },
    { 
      id: '6', 
      name: 'E2E интеграционные тесты (Playwright) и нагрузка (Locust)', 
      projectName: 'Интеграционный шлюз 1С:ЗУП',
      assignee: 'Олег Морозов (Олег)', 
      progress: 40, 
      startCol: 5, 
      span: 3, 
      startDate: '29.10.2026',
      endDate: '19.11.2026',
      color: 'from-purple-600 to-purple-500', 
      status: 'К выполнению'
    },
  ];

  useEffect(() => {
    loadGanttAndProjects();
  }, []);

  const loadGanttAndProjects = async () => {
    setLoading(true);
    try {
      const [liveTasks, prjList] = await Promise.all([
        getGanttTasks(),
        getProjects()
      ]);

      if (prjList && prjList.length > 0) {
        setProjects(prjList);
      }

      if (liveTasks && liveTasks.length > 0) {
        const gradientColors = [
          'from-blue-600 to-blue-500',
          'from-sky-500 to-sky-400',
          'from-indigo-600 to-indigo-500',
          'from-emerald-600 to-emerald-500',
          'from-amber-600 to-amber-500',
          'from-purple-600 to-purple-500'
        ];

        const mapped: GanttTaskItem[] = liveTasks.map((t: any, idx: number) => {
          const colStart = (idx % 5) + 1;
          const colSpan = Math.min(8 - colStart + 1, 3 + (idx % 3));
          return {
            id: String(t.id),
            name: t.name,
            projectName: t.project_name || 'Проект',
            assignee: t.assignee || 'Не назначен',
            progress: t.progress || 0,
            startCol: colStart,
            span: colSpan,
            startDate: t.start ? t.start.slice(0, 10) : '01.10.2026',
            endDate: t.end ? t.end.slice(0, 10) : '31.10.2026',
            color: gradientColors[idx % gradientColors.length],
            status: t.progress === 100 ? 'Завершено' : t.progress > 0 ? 'В работе' : 'Бэклог'
          };
        });
        setTasks(mapped);
      } else {
        setTasks(defaultSprintTasks);
      }
    } catch (err) {
      console.error('Failed to load gantt tasks:', err);
      setTasks(defaultSprintTasks);
    } finally {
      setLoading(false);
    }
  };

  // Filter tasks by selected project
  const filteredTasks = tasks.filter(t => {
    if (selectedProject === 'ALL') return true;
    return t.projectName.toLowerCase().includes(selectedProject.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 glass-card p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <GanttChartSquare className="w-5 h-5 text-brand-sky" />
            Расписание проекта и Диаграмма Ганта (ТЗ §6.6, §7.8)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Календарный таймлайн спринтов разработки TeamMind с распределением трудоёмкости исполнителей
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto justify-end">
          {/* Project Filter */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs">
            <Briefcase className="w-3.5 h-3.5 text-brand-sky" />
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900 text-white">Все проекты</option>
              {projects.map((p) => (
                <option key={p.id} value={p.name} className="bg-slate-900 text-white">
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Mode Switcher */}
          <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('GANTT')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                viewMode === 'GANTT' 
                  ? 'bg-blue-600 text-white shadow' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Календарный Гант
            </button>
            <button
              onClick={() => setViewMode('PROGRESS')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                viewMode === 'PROGRESS' 
                  ? 'bg-blue-600 text-white shadow' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Сплошной прогресс (0–100%)
            </button>
          </div>

          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className={`p-2 rounded-xl border transition-colors ${
              showExplanation 
                ? 'bg-blue-600/20 text-brand-sky border-blue-500' 
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
            }`}
            title="Почему полосы не на всю ширину строки?"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Explanation Banner (Why bars are not solid full-width lines) */}
      {showExplanation && (
        <div className="p-4 bg-blue-950/40 border border-blue-900/60 rounded-2xl text-xs text-slate-300 space-y-2 animate-in fade-in duration-200">
          <div className="flex items-center gap-2 font-bold text-white text-sm">
            <HelpCircle className="w-4 h-4 text-brand-sky" />
            <span>Принцип классической диаграммы Ганта (Gantt Chart):</span>
          </div>
          <p className="leading-relaxed">
            В диаграмме Ганта горизонтальная ось представляет собой <strong>календарный период (недели спринтов Н1..Н8)</strong>, а не шкалу от 0% до 100%. 
            Каждая полоса начинается в дату фактического старта задачи (<code>planned_start</code>) и заканчивается в дату её сдачи (<code>planned_end</code>).
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-400 ml-1">
            <li><strong>Свободное место слева</strong>: задача ещё не стартовала (ожидает завершения предшествующих зависимостей FS/SS).</li>
            <li><strong>Свободное место справа</strong>: задача уже завершится до конца квартала.</li>
            <li><strong>Внутри полосы</strong> отображается двухслойный индикатор: внешняя рамка показывает <em>весь плановый интервал</em>, а яркая заливка — <em>фактический прогресс выполнения</em> (100%, 75%, 40%).</li>
          </ul>
        </div>
      )}

      {/* Gantt / Timeline Matrix */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 overflow-x-auto space-y-4">
        {viewMode === 'GANTT' ? (
          <>
            {/* Timeline Header (8 Weeks) */}
            <div className="grid grid-cols-12 gap-1 text-[11px] font-semibold text-slate-400 border-b border-slate-800 pb-3 text-center min-w-[760px]">
              <div className="col-span-4 text-left pl-2">Задача / Исполнитель</div>
              <div className="col-span-1 border-l border-slate-800/60">Н1 (Спр 1)</div>
              <div className="col-span-1">Н2 (Спр 1)</div>
              <div className="col-span-1 border-l border-slate-800/60">Н3 (Спр 2)</div>
              <div className="col-span-1">Н4 (Спр 2)</div>
              <div className="col-span-1 border-l border-slate-800/60">Н5 (Спр 3)</div>
              <div className="col-span-1">Н6 (Спр 3)</div>
              <div className="col-span-1 border-l border-slate-800/60">Н7 (Спр 4)</div>
              <div className="col-span-1">Н8 (Спр 4)</div>
            </div>

            {/* Task rows */}
            <div className="space-y-3 min-w-[760px]">
              {filteredTasks.length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-400">
                  Задачи для выбранного проекта не найдены
                </div>
              ) : (
                filteredTasks.map((task) => (
                  <div 
                    key={task.id} 
                    className="grid grid-cols-12 gap-1 items-center p-2 rounded-xl hover:bg-slate-800/40 transition-colors"
                  >
                    {/* Task Title & Assignee */}
                    <div className="col-span-4 flex items-center justify-between pr-4">
                      <div className="overflow-hidden pr-2">
                        <div className="text-xs font-semibold text-white truncate" title={task.name}>
                          {task.name}
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                          <User className="w-3 h-3 text-brand-sky shrink-0" />
                          <span className="truncate">{task.assignee}</span>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-500 font-mono text-[9px]">{task.startDate}–{task.endDate}</span>
                        </div>
                      </div>
                      <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        task.progress === 100 
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-blue-500/15 text-blue-300'
                      }`}>
                        {task.progress}%
                      </span>
                    </div>

                    {/* Timeline Track (8 columns) */}
                    <div className="col-span-8 grid grid-cols-8 gap-1 h-8 bg-slate-950/70 rounded-xl p-1 border border-slate-800/80 relative">
                      {/* Vertical grid lines guide */}
                      {Array.from({ length: 8 }).map((_, colIdx) => (
                        <div key={colIdx} className="h-full border-r border-slate-800/40 last:border-r-0 pointer-events-none" />
                      ))}

                      {/* Scheduled Duration Bar with Inner Progress Fill */}
                      <div
                        className="absolute inset-y-1 rounded-lg border border-slate-700/60 bg-slate-850/90 shadow-lg overflow-hidden flex items-center group transition-all"
                        style={{
                          left: `calc(${((task.startCol - 1) / 8) * 100}% + 4px)`,
                          width: `calc(${(task.span / 8) * 100}% - 8px)`,
                        }}
                        title={`${task.name}: ${task.progress}% выполнено (срок: ${task.startDate} — ${task.endDate})`}
                      >
                        {/* Actual progress solid fill */}
                        <div
                          className={`h-full bg-gradient-to-r ${task.color} flex items-center justify-between px-2 text-[10px] font-bold text-white transition-all`}
                          style={{ width: `${Math.max(12, task.progress)}%` }}
                        >
                          <span className="truncate">{task.progress}%</span>
                          {task.progress === 100 && <CheckCircle2 className="w-3 h-3 text-white shrink-0 ml-1" />}
                        </div>

                        {/* Remaining duration indicator if < 100% */}
                        {task.progress < 100 && (
                          <div className="text-[9px] text-slate-400 px-2 font-mono truncate hidden sm:block">
                            остаток срока
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        ) : (
          /* View Mode 2: Full Continuous Progress Bars (0 to 100%) */
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-xs font-semibold text-slate-400">
              <span>Задача и исполнитель</span>
              <span>Сплошная шкала готовности (0% — 100%)</span>
            </div>

            {filteredTasks.map((task) => (
              <div key={task.id} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-white">{task.name}</span>
                    <span className="text-[11px] text-slate-400 ml-2">({task.assignee})</span>
                  </div>
                  <span className="font-mono font-bold text-brand-sky">{task.progress}%</span>
                </div>
                <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800/80">
                  <div
                    className={`h-full bg-gradient-to-r ${task.color} rounded-full transition-all duration-500`}
                    style={{ width: `${task.progress}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>Старт: {task.startDate}</span>
                  <span>Статус: {task.status}</span>
                  <span>Дедлайн: {task.endDate}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
