import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, Download, UserPlus, Clock, Award, X, 
  Briefcase, Calendar, Shield, FileText, Laptop, Users, History, CheckCircle, AlertTriangle
} from 'lucide-react';
import { 
  getEmployees, getEmployeeDetail, createEmployee, 
  EmployeeItem, EmployeeDetailProfile 
} from '../api/client';

export const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [search, setSearch] = useState('');
  const [filterDept, setFilterDept] = useState('ALL');
  const [loading, setLoading] = useState(false);

  // 9-tab Profile Modal state (TZ §7.6)
  const [selectedEmpId, setSelectedEmpId] = useState<string | null>(null);
  const [empProfile, setEmpProfile] = useState<EmployeeDetailProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<number>(1);

  // New Employee Modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newFirstName, setNewFirstName] = useState('');
  const [newLastName, setNewLastName] = useState('');
  const [newTabNumber, setNewTabNumber] = useState('');
  const [newDept, setNewDept] = useState('Backend Core');
  const [newPosition, setNewPosition] = useState('Senior Backend Developer');
  const [newSkills, setNewSkills] = useState('Django, PostgreSQL, DRF');
  const [newChronotype, setNewChronotype] = useState('INTERMEDIATE');
  const [newWorkFormat, setNewWorkFormat] = useState('OFFICE');
  const [newLoad, setNewLoad] = useState('65');

  useEffect(() => {
    fetchEmployeeList();
  }, [filterDept]);

  const fetchEmployeeList = async () => {
    setLoading(true);
    try {
      const resp = await getEmployees({ 
        search, 
        department: filterDept !== 'ALL' ? filterDept : undefined 
      });
      if (resp.results) {
        setEmployees(resp.results);
      }
    } catch (err) {
      console.error('Failed to load employees:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEmployeeList();
  };

  const handleOpenProfile = async (id: string) => {
    setSelectedEmpId(id);
    setProfileLoading(true);
    setActiveTab(1);
    try {
      const profile = await getEmployeeDetail(id);
      setEmpProfile(profile);
    } catch (err) {
      console.error('Failed to load employee profile:', err);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFirstName || !newLastName) return;

    try {
      await createEmployee({
        first_name: newFirstName,
        last_name: newLastName,
        tab_number: newTabNumber || undefined,
        department: newDept,
        position: newPosition,
        skills: newSkills.split(',').map(s => s.trim()).filter(Boolean),
        chronotype: newChronotype,
        work_format: newWorkFormat,
        load: Number(newLoad),
      });

      setIsCreateOpen(false);
      setNewFirstName('');
      setNewLastName('');
      setNewTabNumber('');
      fetchEmployeeList();
    } catch (err) {
      console.error('Failed to create employee:', err);
    }
  };

  const handleExport = () => {
    window.open('/api/v1/org/employees/import-export/', '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 glass-card p-4 rounded-xl border border-slate-800">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по ФИО, должности или навыкам..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-brand-sky"
            />
          </div>

          <select
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-brand-sky"
          >
            <option value="ALL">Все отделы</option>
            <option value="Backend Core">Backend Core</option>
            <option value="Frontend Core">Frontend Core</option>
            <option value="AI & Math Lab">AI & Math Lab</option>
            <option value="DevOps & QA">DevOps & QA</option>
            <option value="Product & Design">Product & Design</option>
            <option value="Mobile Development">Mobile Development</option>
          </select>

          <button
            type="submit"
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-xs text-white rounded-lg border border-slate-700"
          >
            Найти
          </button>
        </form>

        <div className="flex items-center gap-2.5 w-full md:w-auto justify-end">
          <button 
            onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Экспорт списка</span>
          </button>
          <button 
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Добавить сотрудника</span>
          </button>
        </div>
      </div>

      {/* Employees Table */}
      <div className="glass-card rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-900/90 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                <th className="py-3.5 px-5">Сотрудник</th>
                <th className="py-3.5 px-4">Отдел / Должность</th>
                <th className="py-3.5 px-4">Загрузка</th>
                <th className="py-3.5 px-4">Ключевые навыки</th>
                <th className="py-3.5 px-4">Хронотип</th>
                <th className="py-3.5 px-4">Статус</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Загрузка списка сотрудников...
                  </td>
                </tr>
              ) : employees.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Сотрудники не найдены
                  </td>
                </tr>
              ) : (
                employees.map((emp) => (
                  <tr 
                    key={emp.id} 
                    onClick={() => handleOpenProfile(emp.id)}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                  >
                    <td className="py-3.5 px-5">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white text-xs shadow shrink-0">
                          {emp.name ? emp.name[0] : 'E'}
                        </div>
                        <div>
                          <div className="font-semibold text-white text-sm hover:text-brand-sky transition-colors">
                            {emp.name}
                          </div>
                          <div className="text-[11px] text-slate-400">{emp.tab_number} • {emp.position}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      <div>{emp.department}</div>
                      <div className="text-[11px] text-slate-500">{emp.grade}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${emp.load > 80 ? 'bg-rose-500' : 'bg-brand-sky'}`} 
                            style={{ width: `${Math.min(100, emp.load)}%` }}
                          ></div>
                        </div>
                        <span className="font-bold text-white text-xs font-mono">{emp.load}%</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {emp.skills.slice(0, 3).map((skill, sIdx) => (
                          <span key={sIdx} className="text-[10px] bg-slate-800/90 text-slate-300 px-2 py-0.5 rounded border border-slate-700/60 font-medium">
                            {skill}
                          </span>
                        ))}
                        {emp.skills.length > 3 && (
                          <span className="text-[10px] bg-blue-900/40 text-blue-300 px-1.5 py-0.5 rounded">
                            +{emp.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{emp.chronotype ? emp.chronotype.split(' ')[0] : 'Дневной'}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        emp.status_code === 'ACTIVE' || emp.status === 'Активен' || emp.status === 'В офисе'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' 
                          : emp.status_code === 'REMOTE' || emp.status === 'Удалённо'
                          ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30' 
                          : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                      }`}>
                        {emp.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── 9-Tab Employee Detail Profile Modal (TZ §7.6) ── */}
      {selectedEmpId && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] shadow-2xl flex flex-col overflow-hidden animate-in fade-in duration-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white text-lg shadow-lg">
                  {empProfile?.basic_info?.full_name ? empProfile.basic_info.full_name[0] : 'E'}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {empProfile?.basic_info?.full_name || 'Карточка сотрудника'}
                  </h3>
                  <div className="text-xs text-slate-400">
                    {empProfile?.basic_info?.position} • {empProfile?.basic_info?.department} • {empProfile?.basic_info?.tab_number}
                  </div>
                </div>
              </div>
              <button 
                onClick={() => { setSelectedEmpId(null); setEmpProfile(null); }}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* 9 Tabs Bar per TZ §7.6 */}
            <div className="flex border-b border-slate-800 overflow-x-auto bg-slate-950/40 text-xs font-medium text-slate-400 px-4">
              {[
                { id: 1, label: '1. Основная инфо', icon: Users },
                { id: 2, label: '2. Навыки (1–5)', icon: Award },
                { id: 3, label: '3. Занятость & Проекты', icon: Briefcase },
                { id: 4, label: '4. Отсутствия (16)', icon: Calendar },
                { id: 5, label: '5. График & Хронотип', icon: Clock },
                { id: 6, label: '6. Совместимость', icon: Users },
                { id: 7, label: '7. Оборудование', icon: Laptop },
                { id: 8, label: '8. Документы HR', icon: FileText },
                { id: 9, label: '9. Аудит лог', icon: History },
              ].map(tab => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-1.5 py-3 px-3 border-b-2 whitespace-nowrap transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-white font-bold bg-blue-500/10'
                        : 'border-transparent hover:text-slate-200'
                    }`}
                  >
                    <IconComponent className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Modal Body with 9 Tabs Content */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1 text-xs">
              {profileLoading ? (
                <div className="py-12 text-center text-slate-400">Загрузка данных профиля...</div>
              ) : !empProfile ? (
                <div className="py-12 text-center text-slate-400">Данные профиля недоступны</div>
              ) : (
                <>
                  {/* Tab 1: Основная информация */}
                  {activeTab === 1 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                        <h4 className="font-bold text-white text-sm mb-2 border-b border-slate-800 pb-1">Кадровые данные</h4>
                        <div><span className="text-slate-400">ФИО:</span> <strong className="text-white">{empProfile.basic_info.full_name}</strong></div>
                        <div><span className="text-slate-400">Табельный номер:</span> <span className="font-mono text-sky-400">{empProfile.basic_info.tab_number}</span></div>
                        <div><span className="text-slate-400">Подразделение:</span> {empProfile.basic_info.department}</div>
                        <div><span className="text-slate-400">Должность:</span> {empProfile.basic_info.position}</div>
                        <div><span className="text-slate-400">Грейд:</span> <span className="px-2 py-0.5 bg-blue-600/20 text-blue-300 rounded font-bold">{empProfile.basic_info.grade}</span></div>
                        <div><span className="text-slate-400">Статус:</span> {empProfile.basic_info.status}</div>
                      </div>

                      <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                        <h4 className="font-bold text-white text-sm mb-2 border-b border-slate-800 pb-1">Контакты и локация</h4>
                        <div><span className="text-slate-400">Email:</span> <span className="text-white">{empProfile.basic_info.email}</span></div>
                        <div><span className="text-slate-400">Телефон:</span> {empProfile.basic_info.phone}</div>
                        <div><span className="text-slate-400">Город / Страна:</span> {empProfile.basic_info.location_city}, {empProfile.basic_info.location_country}</div>
                        <div><span className="text-slate-400">Часовой пояс:</span> {empProfile.basic_info.timezone}</div>
                        <div><span className="text-slate-400">Дата приёма:</span> {empProfile.basic_info.hire_date}</div>
                        <div><span className="text-slate-400">Опыт работы:</span> {empProfile.basic_info.years_experience} года</div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Матрица навыков (1–5) */}
                  {activeTab === 2 && (
                    <div className="space-y-3">
                      <div className="text-slate-400 text-xs">
                        Оценка компетенций по 5-балльной шкале ТЗ §6.5 (1=новичок, 5=эксперт):
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {empProfile.skills_matrix.map((sk, idx) => (
                          <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                            <div>
                              <div className="font-semibold text-white">{sk.skill_name}</div>
                              <div className="text-[10px] text-slate-400">
                                {sk.skill_type} • {sk.verification_source}
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5">
                              {[1, 2, 3, 4, 5].map(lvl => (
                                <div 
                                  key={lvl} 
                                  className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
                                    lvl <= sk.level 
                                      ? 'bg-blue-600 text-white' 
                                      : 'bg-slate-800 text-slate-500'
                                  }`}
                                >
                                  {lvl}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Занятость & Проекты */}
                  {activeTab === 3 && (
                    <div className="space-y-4">
                      <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                        <div>
                          <div className="text-xs text-slate-400">Текущий уровень загрузки</div>
                          <div className="text-2xl font-extrabold text-white font-mono mt-1">
                            {empProfile.workload_info.current_load_percent}%
                          </div>
                        </div>
                        <div className="text-right text-slate-400">
                          <div>Норма: {empProfile.workload_info.weekly_hours_norm} ч/неделю</div>
                          <div>Доступно в день: {empProfile.workload_info.daily_hours_available} ч</div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <h4 className="font-bold text-white">Активные назначения и задачи:</h4>
                        {empProfile.workload_info.active_projects.length === 0 ? (
                          <div className="p-4 text-center text-slate-400 bg-slate-950/40 rounded-xl">
                            Нет активных блокирующих задач в спринте. Сотрудник доступен для новых проектов.
                          </div>
                        ) : (
                          empProfile.workload_info.active_projects.map((proj, pIdx) => (
                            <div key={pIdx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                              <div>
                                <div className="font-semibold text-white">[{proj.project_code}] {proj.task_title}</div>
                                <div className="text-[11px] text-slate-400">{proj.project_name}</div>
                              </div>
                              <span className="px-2 py-0.5 bg-blue-600/20 text-blue-300 rounded font-medium text-[10px]">
                                {proj.status} ({proj.progress}%)
                              </span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* Tab 4: Отсутствия (16 типов по ТЗ §6.3) */}
                  {activeTab === 4 && (
                    <div className="space-y-3">
                      <div className="text-slate-400">История отсутствий сотрудника (16 категорий ТЗ §6.3):</div>
                      {empProfile.absences.length === 0 ? (
                        <div className="p-4 text-center text-slate-400 bg-slate-950/40 rounded-xl">
                          Нет зарегистрированных отсутствий на текущий период.
                        </div>
                      ) : (
                        empProfile.absences.map((ab, idx) => (
                          <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                            <div>
                              <div className="font-semibold text-white">{ab.type}</div>
                              <div className="text-[11px] text-slate-400">{ab.start_date} — {ab.end_date} ({ab.working_days} раб. дн.)</div>
                              {ab.reason && <div className="text-[10px] text-slate-500 mt-0.5">{ab.reason}</div>}
                            </div>
                            <span className="px-2.5 py-1 bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded font-semibold text-[10px]">
                              {ab.status}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* Tab 5: График & Хронотип */}
                  {activeTab === 5 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                        <h4 className="font-bold text-white text-sm mb-2 border-b border-slate-800 pb-1">Хронотип и биоритмы</h4>
                        <div><span className="text-slate-400">Хронотип:</span> <strong className="text-white">{empProfile.schedule.chronotype}</strong></div>
                        <div><span className="text-slate-400">Формат работы:</span> {empProfile.schedule.work_format}</div>
                        <div><span className="text-slate-400">Рабочий интервал:</span> {empProfile.schedule.work_day_start} — {empProfile.schedule.work_day_end}</div>
                        <div><span className="text-slate-400">Стиль общения:</span> {empProfile.schedule.communication_style}</div>
                      </div>

                      <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                        <h4 className="font-bold text-white text-sm mb-2 border-b border-slate-800 pb-1">Предпочтения по митингам</h4>
                        <div>
                          <span className="text-slate-400">Встречи до полудня:</span>{' '}
                          <span className={empProfile.schedule.meetings_before_noon ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                            {empProfile.schedule.meetings_before_noon ? 'Комфортно' : 'Нежелательно'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400">Встречи после 18:00:</span>{' '}
                          <span className={empProfile.schedule.meetings_after_18 ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                            {empProfile.schedule.meetings_after_18 ? 'Допустимо' : 'Исключено'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 6: Совместимость с коллегами */}
                  {activeTab === 6 && (
                    <div className="space-y-3">
                      <div className="text-slate-400">Оценка психологической совместимости и предпочтения работы в парах:</div>
                      {empProfile.colleague_compatibility.length === 0 ? (
                        <div className="p-4 text-center text-slate-400 bg-slate-950/40 rounded-xl">
                          Предпочтения по коллегам не заданы. Совместимость рассчитывается как нейтральная.
                        </div>
                      ) : (
                        empProfile.colleague_compatibility.map((cp, idx) => (
                          <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                            <div>
                              <div className="font-semibold text-white">{cp.colleague_name}</div>
                              <div className="text-[11px] text-slate-400">{cp.colleague_position}</div>
                              {cp.reason && <div className="text-[10px] text-slate-500">{cp.reason}</div>}
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              cp.pref_type === 'Желаемый' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                            }`}>
                              {cp.pref_type}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* Tab 7: Оборудование */}
                  {activeTab === 7 && (
                    <div className="space-y-2">
                      <div className="text-slate-400">Учёт выданного рабочего оборудования и доступов:</div>
                      {empProfile.equipment.map((eq, idx) => (
                        <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-white">{eq.item}</div>
                            <div className="text-[11px] font-mono text-slate-400">{eq.serial}</div>
                          </div>
                          <span className="px-2 py-0.5 bg-emerald-500/15 text-emerald-400 rounded text-[10px] font-semibold">
                            {eq.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 8: Документы HR */}
                  {activeTab === 8 && (
                    <div className="space-y-2">
                      <div className="text-slate-400">Кадровые соглашения и внутренние регламенты:</div>
                      {empProfile.documents.map((doc, idx) => (
                        <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-white">{doc.title}</div>
                            <div className="text-[11px] text-slate-400">№ {doc.doc_number} от {doc.date}</div>
                          </div>
                          <span className="px-2 py-0.5 bg-blue-500/15 text-blue-400 rounded text-[10px] font-semibold">
                            {doc.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 9: Аудит лог */}
                  {activeTab === 9 && (
                    <div className="space-y-2">
                      <div className="text-slate-400">Журнал аудита действий и изменений профиля (ТЗ §8.1):</div>
                      {empProfile.audit_history.map((hist, idx) => (
                        <div key={idx} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-white">{hist.action}</div>
                            <div className="text-[11px] text-slate-400">Инициатор: {hist.actor}</div>
                          </div>
                          <div className="text-[11px] font-mono text-slate-500">{hist.date}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Create Employee Modal ── */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-brand-sky" />
                Добавление нового сотрудника (ТЗ §6.2)
              </h3>
              <button 
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Имя *</label>
                <input
                  type="text"
                  required
                  value={newFirstName}
                  onChange={e => setNewFirstName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  placeholder="Иван"
                />
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Фамилия *</label>
                <input
                  type="text"
                  required
                  value={newLastName}
                  onChange={e => setNewLastName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  placeholder="Петров"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Табельный номер</label>
                <input
                  type="text"
                  value={newTabNumber}
                  onChange={e => setNewTabNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white font-mono"
                  placeholder="Автогенерируется"
                />
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Отдел</label>
                <select
                  value={newDept}
                  onChange={e => setNewDept(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="Backend Core">Backend Core</option>
                  <option value="Frontend Core">Frontend Core</option>
                  <option value="AI & Math Lab">AI & Math Lab</option>
                  <option value="DevOps & QA">DevOps & QA</option>
                  <option value="Product & Design">Product & Design</option>
                </select>
              </div>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Должность</label>
              <input
                type="text"
                value={newPosition}
                onChange={e => setNewPosition(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                placeholder="Senior Fullstack Developer"
              />
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Навыки (через запятую)</label>
              <input
                type="text"
                value={newSkills}
                onChange={e => setNewSkills(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                placeholder="Python, React, TypeScript, Docker"
              />
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Хронотип</label>
                <select
                  value={newChronotype}
                  onChange={e => setNewChronotype(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="LARK">Жаворонок</option>
                  <option value="INTERMEDIATE">Дневной</option>
                  <option value="OWL">Сова</option>
                  <option value="PIGEON">Голубь</option>
                </select>
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Формат</label>
                <select
                  value={newWorkFormat}
                  onChange={e => setNewWorkFormat(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="OFFICE">Офис</option>
                  <option value="REMOTE">Удаленно</option>
                  <option value="HYBRID">Гибрид</option>
                </select>
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Загрузка %</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={newLoad}
                  onChange={e => setNewLoad(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
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
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md"
              >
                Создать сотрудника
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
