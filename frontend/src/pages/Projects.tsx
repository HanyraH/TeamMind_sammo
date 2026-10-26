import React, { useState, useEffect } from 'react';
import { 
  FolderKanban, Plus, Calendar, Users, CheckCircle2, 
  ArrowRight, X, Briefcase, Clock, Sparkles
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getProjects, createProject, ProjectItem } from '../api/client';

export const Projects: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [pageError, setPageError] = useState('');
  const [createError, setCreateError] = useState('');
  const [saving, setSaving] = useState(false);

  // New Project Form state
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [budgetHours, setBudgetHours] = useState('480');
  const [plannedStart, setPlannedStart] = useState('2026-11-01');
  const [plannedEnd, setPlannedEnd] = useState('2027-02-28');
  const [roleTitle, setRoleTitle] = useState('Lead Fullstack Developer');

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await getProjects();
      setProjects(Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : []));
      setPageError('');
    } catch (err: any) {
      console.error('Failed to load projects:', err);
      setPageError(err?.response?.data?.error || err?.response?.data?.detail || 'Не удалось загрузить проекты. Проверьте соединение с backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setCreateError('Введите название проекта.'); return; }
    if (plannedEnd && plannedStart && plannedEnd < plannedStart) { setCreateError('Дата окончания не может быть раньше даты начала.'); return; }
    if (!Number.isFinite(Number(budgetHours)) || Number(budgetHours) < 0) { setCreateError('Бюджет должен быть неотрицательным числом.'); return; }
    setCreateError('');
    setSaving(true);

    try {
      await createProject({
        name,
        code: code || undefined,
        description,
        priority,
        budget_hours: Number(budgetHours),
        planned_start: plannedStart,
        planned_end: plannedEnd,
        roles: [
          { slot: 'DEVELOPER', title: roleTitle, headcount: 2 },
          { slot: 'QA', title: 'QA Engineer', headcount: 1 }
        ]
      });

      setIsCreateOpen(false);
      setName('');
      setCode('');
      setDescription('');
      await fetchProjects();
    } catch (err: any) {
      console.error('Failed to create project:', err);
      setCreateError(err?.response?.data?.error || err?.response?.data?.detail || (typeof err?.response?.data === 'string' ? err.response.data : '') || 'Не удалось создать проект. Проверьте backend и данные формы.');
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-6">
      {pageError && <div role="alert" className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">{pageError}</div>}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 glass-card p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-brand-sky" />
            Реестр проектов компании (ТЗ §6.6)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Управление жизненным циклом, бюджетом часов и требованиями к проектным командам
          </p>
        </div>
        <button 
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Создать проект</span>
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-slate-400">Загрузка проектов...</div>
      ) : projects.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-400">Проекты не найдены</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div 
              key={proj.id} 
              className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30">
                    {proj.status}
                  </span>
                  <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                    <Users className="w-3.5 h-3.5 text-brand-sky" /> {proj.teamSize} участника
                  </span>
                </div>

                <div>
                  <div className="text-[10px] text-slate-500 font-mono">{proj.code}</div>
                  <h3 className="text-base font-bold text-white tracking-tight mt-0.5">{proj.name}</h3>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {proj.description || 'Проект в стадии активного формирования и распределения ресурсов.'}
                </p>

                <div className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  <span>{proj.period}</span>
                </div>

                <div className="space-y-1.5 pt-2">
                  <div className="text-[11px] font-semibold text-slate-300">Требуемые роли и стек:</div>
                  <div className="flex flex-wrap gap-1">
                    {proj.roles && proj.roles.length > 0 ? (
                      proj.roles.map((r, rIdx) => (
                        <span key={rIdx} className="text-[10px] bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800">
                          {r}
                        </span>
                      ))
                    ) : (
                      <span className="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded">
                        Роли формируются
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800/80 space-y-3">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Бюджет: {proj.budget_hours || 400} ч</span>
                  <span className="text-white font-semibold font-mono">{proj.progress || 30}% выполнено</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${proj.progress || 30}%` }}></div>
                </div>

                <button
                  onClick={() => navigate('/constructor')}
                  className="w-full mt-2 flex items-center justify-center gap-2 py-2 bg-slate-800 hover:bg-blue-600/30 text-white rounded-xl text-xs font-semibold border border-slate-700 hover:border-blue-500/50 transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5 text-brand-sky" />
                  <span>Подобрать команду в конструкторе</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Create Project Modal ── */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            {createError && <div role="alert" className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-200">{createError}</div>}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="w-5 h-5 text-brand-sky" />
                Создание нового проекта (ТЗ §6.6)
              </h3>
              <button 
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Название проекта *</label>
              <input
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                placeholder="Система аналитики TeamMind 2.0"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Код проекта</label>
                <input
                  type="text"
                  value={code}
                  onChange={e => setCode(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                  placeholder="PRJ-004"
                />
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Приоритет</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="CRITICAL">Критический</option>
                  <option value="HIGH">Высокий</option>
                  <option value="MEDIUM">Средний</option>
                  <option value="LOW">Низкий</option>
                </select>
              </div>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Описание проекта</label>
              <textarea
                rows={2}
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                placeholder="Краткое описание целей и задач проекта..."
              />
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Дата начала</label>
                <input
                  type="date"
                  value={plannedStart}
                  onChange={e => setPlannedStart(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Дата окончания</label>
                <input
                  type="date"
                  value={plannedEnd}
                  onChange={e => setPlannedEnd(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Бюджет часов</label>
                <input
                  type="number"
                  value={budgetHours}
                  onChange={e => setBudgetHours(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Ключевая требуемая роль</label>
              <input
                type="text"
                value={roleTitle}
                onChange={e => setRoleTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                placeholder="Lead Backend Developer"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-md"
              >
                {saving ? 'Сохранение…' : 'Сохранить проект'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
