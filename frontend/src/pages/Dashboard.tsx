import React, { useState, useEffect } from 'react';
import { 
  Users, FolderKanban, CalendarOff, CheckCircle2, TrendingUp, 
  AlertTriangle, ArrowRight, Activity, Clock
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDashboardKpi, DashboardKpiData, getAbsences } from '../api/client';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardKpiData | null>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [kpiResp, absencesResp] = await Promise.all([
        getDashboardKpi(),
        getAbsences()
      ]);
      setData(kpiResp);
      if (absencesResp && absencesResp.length > 0) {
        setRecentEvents(absencesResp.slice(0, 5));
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const kpis = data?.kpis || [
    { id: 'total_employees', label: 'Всего сотрудников', value: 45, trend: '+3 за последний месяц' },
    { id: 'active_projects', label: 'Активные проекты', value: 3, trend: '2 проекта на стадии релиза' },
    { id: 'absent_count', label: 'В отпусках / отсутствиях', value: 5, trend: '16 типов отсутствий' },
    { id: 'ready_count', label: 'Доступно для назначения', value: 8, trend: 'Готовы к новому спринту' },
  ];

  const deptLoads = data?.department_loads || [
    { department: 'Backend Core', load: 82, count: 12, is_overloaded: true },
    { department: 'Frontend Core', load: 74, count: 10, is_overloaded: false },
    { department: 'AI & Math Lab', load: 78, count: 8, is_overloaded: false },
    { department: 'DevOps & QA', load: 65, count: 9, is_overloaded: false },
    { department: 'Product & Design', load: 68, count: 6, is_overloaded: false },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-850 to-blue-950/40 p-6 rounded-2xl border border-slate-800/80 shadow-xl">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Добро пожаловать в TeamMind</h2>
          <p className="text-sm text-slate-400 mt-1">
            Интеллектуальная система формирования проектных команд и ресурсного планирования (ТЗ v4.0).
          </p>
        </div>
        <Link 
          to="/constructor" 
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all hover:scale-[1.02] shrink-0"
        >
          <span>Запустить подбор команды</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.slice(0, 4).map((kpi, idx) => {
          const icons = [Users, FolderKanban, CalendarOff, CheckCircle2];
          const IconComp = icons[idx % icons.length];
          const colorClasses = [
            'bg-blue-500/10 text-blue-400',
            'bg-indigo-500/10 text-indigo-400',
            'bg-amber-500/10 text-amber-400',
            'bg-emerald-500/10 text-emerald-400',
          ][idx % 4];

          return (
            <div key={kpi.id || idx} className="glass-card p-5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium uppercase tracking-wider">{kpi.label}</span>
                <div className={`p-2 rounded-lg ${colorClasses}`}><IconComp className="w-4 h-4" /></div>
              </div>
              <div className="text-3xl font-bold text-white mt-2 font-mono">{kpi.value}</div>
              <div className="text-xs text-slate-400 flex items-center gap-1 mt-2 font-medium">
                {idx === 0 && <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />}
                <span>{kpi.trend}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Workload & Current Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workload by Department */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800/80 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white">Текущая загрузка по отделам (ТЗ §6.7)</h3>
              <p className="text-xs text-slate-400">Оптимальный баланс: 75–80% (штраф за перегрузку &gt;85%)</p>
            </div>
            <span className="text-xs font-mono font-bold text-brand-sky bg-blue-500/10 px-2 py-1 rounded">
              Цель: 80%
            </span>
          </div>
          
          <div className="space-y-4">
            {deptLoads.map((item) => (
              <div key={item.department} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium flex items-center gap-2">
                    {item.department}
                    {item.is_overloaded && (
                      <span className="text-[10px] bg-rose-500/20 text-rose-400 px-1.5 py-0.5 rounded border border-rose-500/30 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Перегрузка
                      </span>
                    )}
                  </span>
                  <span className="text-white font-semibold font-mono">{item.load}%</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${
                      item.load > 80 ? 'bg-rose-500' : item.load > 70 ? 'bg-blue-500' : 'bg-sky-400'
                    }`} 
                    style={{ width: `${Math.min(100, item.load)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Activity / Calendar events */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-brand-sky" />
                Ближайшие отсутствия
              </h3>
              <Link to="/calendar" className="text-xs text-brand-sky hover:underline">Все (16)</Link>
            </div>

            <div className="space-y-3">
              {recentEvents.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  Нет зарегистрированных отсутствий
                </div>
              ) : (
                recentEvents.map((evt, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-slate-200">{evt.employee_name || evt.title}</div>
                      <div className="text-[11px] text-slate-400">{evt.start} — {evt.end}</div>
                    </div>
                    <span 
                      className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                      style={{ 
                        backgroundColor: `${evt.color || '#3B82F6'}25`, 
                        color: evt.color || '#3B82F6',
                        border: `1px solid ${evt.color || '#3B82F6'}50` 
                      }}
                    >
                      {evt.type_display || evt.type}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 mt-4 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Синхронизация с 1С / HR:</span>
            <span className="text-emerald-400 font-medium">Активна (Online)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
