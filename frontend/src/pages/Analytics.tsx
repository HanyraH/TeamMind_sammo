import React, { useState, useEffect } from 'react';
import {
  BarChart3, Download, TrendingUp, AlertTriangle,
  CheckCircle2, PieChart, Users, Clock, ShieldCheck
} from 'lucide-react';
import { getDashboardKpi, downloadAnalyticsReport, DashboardKpiData } from '../api/client';

export const Analytics: React.FC = () => {
  const [data, setData] = useState<DashboardKpiData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const resp = await getDashboardKpi();
      setData(resp);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const months = ['Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт'];
  const monthlyHistory = [
    { month: 'Май', dev: 70, qa: 55, algo: 65 },
    { month: 'Июн', dev: 78, qa: 60, algo: 70 },
    { month: 'Июл', dev: 85, qa: 68, algo: 75 },
    { month: 'Авг', dev: 80, qa: 62, algo: 72 },
    { month: 'Сен', dev: 88, qa: 75, algo: 82 },
    { month: 'Окт', dev: 85, qa: 70, algo: 80 },
  ];

  const dist = data?.workload_distribution || { underloaded: 6, optimal: 32, overloaded: 7, total: 45 };
  const chronos = data?.chronotypes || { lark: 12, owl: 14, intermediate: 15, pigeon: 4 };

  const totalEmps = dist.total || 45;
  const optimalPercent = Math.round((dist.optimal / Math.max(1, totalEmps)) * 100);
  const overloadedPercent = Math.round((dist.overloaded / Math.max(1, totalEmps)) * 100);
  const underloadedPercent = Math.round((dist.underloaded / Math.max(1, totalEmps)) * 100);

  const handleExport = () => {
    const snapshot: DashboardKpiData = {
      kpis: data?.kpis || [],
      department_loads: data?.department_loads || [],
      workload_distribution: dist,
      chronotypes: chronos,
    };
    downloadAnalyticsReport(snapshot).catch((err) =>
      console.error('Analytics export failed:', err)
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-card p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-sky" />
            Аналитика ресурсов и баланс нагрузки (ТЗ §6.7, §7.9)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Утилизация сотрудников, распределение хронотипов и выявление рисков перегрузок
          </p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all shrink-0"
        >
          <Download className="w-4 h-4" />
          <span>Скачать сводный отчёт</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Bar Chart */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Динамика утилизации команд по месяцам (%)</h3>
              <p className="text-xs text-slate-400">Целевой оптимум по ТЗ §6.8: 80%</p>
            </div>
            <div className="hidden sm:flex items-center gap-4 text-[11px]">
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded bg-blue-500"></span> Backend Core
              </span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded bg-sky-400"></span> Frontend Core
              </span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded bg-indigo-500"></span> Algo / Data
              </span>
            </div>
          </div>

          <div className="h-64 flex items-end justify-between gap-4 pt-10 px-4 border-b border-slate-800 relative">
            {/* Target 80% dashed line */}
            <div className="absolute top-[20%] left-0 right-0 border-b border-dashed border-emerald-500/50 flex justify-end pr-2">
              <span className="text-[10px] text-emerald-400 font-mono font-bold bg-slate-900/90 px-1.5 py-0.5 rounded border border-emerald-500/30">
                Цель: 80%
              </span>
            </div>

            {monthlyHistory.map((item) => (
              <div key={item.month} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full flex items-end justify-center gap-1.5 h-48">
                  <div className="w-3.5 bg-blue-500 rounded-t transition-all hover:brightness-110" style={{ height: `${item.dev}%` }}></div>
                  <div className="w-3.5 bg-sky-400 rounded-t transition-all hover:brightness-110" style={{ height: `${item.qa}%` }}></div>
                  <div className="w-3.5 bg-indigo-500 rounded-t transition-all hover:brightness-110" style={{ height: `${item.algo}%` }}></div>
                </div>
                <span className="text-xs text-slate-400 font-medium">{item.month}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Breakdown Card: Workload & Chronotypes */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <PieChart className="w-4 h-4 text-brand-sky" />
            Баланс нагрузки команды
          </h3>

          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-1">
            <div className="text-xs font-bold text-emerald-400 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4" />
                Оптимальный диапазон (50–85%)
              </span>
              <span className="font-mono text-sm">{dist.optimal} чел. ({optimalPercent}%)</span>
            </div>
            <p className="text-[11px] text-slate-300">
              Сотрудники в зоне максимальной эффективности без риска выгорания.
            </p>
          </div>

          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl space-y-1">
            <div className="text-xs font-bold text-rose-400 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                Риск перегрузки (&gt;85%)
              </span>
              <span className="font-mono text-sm">{dist.overloaded} чел. ({overloadedPercent}%)</span>
            </div>
            <p className="text-[11px] text-slate-300">
              Сотрудники требуют разгрузки или подключения дублёров.
            </p>
          </div>

          <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl space-y-1">
            <div className="text-xs font-bold text-blue-400 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Users className="w-4 h-4" />
                Доступный резерв (&lt;50%)
              </span>
              <span className="font-mono text-sm">{dist.underloaded} чел. ({underloadedPercent}%)</span>
            </div>
            <p className="text-[11px] text-slate-300">
              Свободные мощности для подключения к новым спринтам.
            </p>
          </div>

          {/* Chronotype Distribution per TZ §6.4 */}
          <div className="pt-3 border-t border-slate-800 space-y-2">
            <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-brand-sky" />
              Распределение 4 хронотипов (ТЗ §6.4):
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-slate-400">Жаворонки: </span>
                <strong className="text-white font-mono">{chronos.lark}</strong>
              </div>
              <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-slate-400">Совы: </span>
                <strong className="text-white font-mono">{chronos.owl}</strong>
              </div>
              <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-slate-400">Дневные: </span>
                <strong className="text-white font-mono">{chronos.intermediate}</strong>
              </div>
              <div className="p-2 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-slate-400">Голуби: </span>
                <strong className="text-white font-mono">{chronos.pigeon}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};