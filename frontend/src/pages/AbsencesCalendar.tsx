import React, { useState, useEffect } from 'react';
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, Plus, 
  AlertCircle, X, CheckCircle, Clock, Users, UserCheck, Info, Sparkles
} from 'lucide-react';
import { getAbsences, submitAbsence, getEmployees, AbsenceEvent, EmployeeItem } from '../api/client';

// 16 types of absence according to TZ §6.3 and color-coding TZ §7.7
const absenceTypes = [
  { id: 'ANNUAL', name: 'Основной оплачиваемый отпуск', color: '#3B82F6' },
  { id: 'UNPAID', name: 'Отпуск без сохранения з/п', color: '#64748B' },
  { id: 'SICK', name: 'Больничный лист', color: '#EF4444' },
  { id: 'SICK_CHILD', name: 'Больничный по уходу за ребёнком', color: '#DC2626' },
  { id: 'MATERNITY', name: 'Отпуск по беременности и родам', color: '#EC4899' },
  { id: 'PARENTAL', name: 'Отпуск по уходу за ребёнком до 3 лет', color: '#F472B6' },
  { id: 'STUDY', name: 'Учебный отпуск (сессия)', color: '#10B981' },
  { id: 'BUSINESS', name: 'Служебная командировка', color: '#8B5CF6' },
  { id: 'REMOTE_DAY', name: 'Работа из дома (удалённый день)', color: '#F59E0B' },
  { id: 'DAY_OFF', name: 'Отгул / донорский день', color: '#F97316' },
  { id: 'COMP_TIME', name: 'Отгул за переработку', color: '#FB923C' },
  { id: 'QUARANTINE', name: 'Карантин', color: '#D97706' },
  { id: 'TRAINING', name: 'Повышение квалификации', color: '#06B6D4' },
  { id: 'PERSONAL', name: 'Семейные обстоятельства', color: '#6366F1' },
  { id: 'SUSPENSION', name: 'Приостановление договора', color: '#475569' },
  { id: 'OTHER', name: 'Иное отсутствие', color: '#94A3B8' },
];

const toDateString = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
const parseLocalDate = (value: string) => { const [year, month, day] = value.slice(0, 10).split('-').map(Number); return new Date(year, month - 1, day); };

export const AbsencesCalendar: React.FC = () => {
  const [events, setEvents] = useState<AbsenceEvent[]>([]);
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [loading, setLoading] = useState(false);
  // Календарь всегда открывается на текущем месяце и текущей дате.
  const today = new Date();
  const [visibleMonth, setVisibleMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDateStr, setSelectedDateStr] = useState(() => toDateString(new Date()));
  const selectedDate = parseLocalDate(selectedDateStr);
  const selectedDay = selectedDate.getDate();
  const currentMonth = visibleMonth.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });
  const daysInMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 0).getDate();
  const firstWeekdayOffset = (new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1).getDay() + 6) % 7;
  const isSameMonth = selectedDate.getFullYear() === visibleMonth.getFullYear() && selectedDate.getMonth() === visibleMonth.getMonth();

  // Submit Modal state
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [selectedEmpId, setSelectedEmpId] = useState('');
  const [absenceType, setAbsenceType] = useState('ANNUAL');
  const [startDate, setStartDate] = useState(() => toDateString(new Date()));
  const [endDate, setEndDate] = useState(() => { const date = new Date(); date.setDate(date.getDate() + 7); return toDateString(date); });
  const [reason, setReason] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    loadCalendarData();
  }, []);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      const [absData, empData] = await Promise.all([
        getAbsences(),
        getEmployees()
      ]);
      setEvents(absData);
      if (empData.results) {
        setEmployees(empData.results);
        if (empData.results.length > 0) {
          setSelectedEmpId(empData.results[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load absences:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmpId || !startDate || !endDate || endDate < startDate) return;

    try {
      await submitAbsence({
        employee_id: selectedEmpId,
        absence_type: absenceType,
        start_date: startDate,
        end_date: endDate,
        reason: reason || 'Плановое отсутствие'
      });

      setSubmitSuccess(true);
      setTimeout(() => {
        setSubmitSuccess(false);
        setIsSubmitOpen(false);
      }, 1200);

      loadCalendarData();
    } catch (err) {
      console.error('Failed to submit absence:', err);
    }
  };

  // Утверждённые отсутствия считаются фактическими; ожидающие согласования
  // остаются видимыми в календаре как заявки и не уменьшают доступность.
  const eventsOnSelectedDay = events.filter(e => {
    const s = e.start.slice(0, 10);
    const end = e.end.slice(0, 10);
    return selectedDateStr >= s && selectedDateStr <= end;
  });
  const absentOnSelectedDay = eventsOnSelectedDay.filter(
    e => String(e.status || '').toUpperCase() === 'APPROVED'
  );

  const formatDateDisplay = (isoStr: string) => {
    if (!isoStr) return '';
    const parts = isoStr.slice(0, 10).split('-');
    if (parts.length === 3) {
      return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
    return isoStr;
  };

  const calculateDaysRemaining = (endIso: string) => {
    try {
      const target = new Date(endIso.slice(0, 10));
      const current = new Date(selectedDateStr);
      const diffTime = target.getTime() - current.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      return Math.max(1, diffDays);
    } catch {
      return 1;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 glass-card p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/10 rounded-xl text-brand-sky">
            <CalendarIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span>{currentMonth}</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/15 text-blue-400">
                16 типов отсутствий
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Нажмите на любую дату в сетке, чтобы просмотреть подробный список отсутствующих сотрудников и даты их возвращения
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          <button 
            onClick={() => setVisibleMonth(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1))}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button 
            onClick={() => { const now = new Date(); setVisibleMonth(new Date(now.getFullYear(), now.getMonth(), 1)); setSelectedDateStr(toDateString(now)); }}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-semibold text-white transition-colors"
          >
            Сегодня
          </button>
          <button 
            onClick={() => setVisibleMonth(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1))}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <div className="h-4 w-px bg-slate-700 mx-2"></div>
          <button 
            onClick={() => {
              setStartDate(selectedDateStr);
              setIsSubmitOpen(true);
            }}
            className="flex items-center gap-1.5 px-3 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Заявка на отсутствие</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols): Clean Interactive Calendar Grid */}
        <div className="lg:col-span-7 glass-card p-6 rounded-2xl border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
              <span className="text-xs font-semibold text-slate-300">Сетка дней месяца</span>
              <span className="text-[11px] text-slate-400">Кликните по дню для детального просмотра сбоку</span>
            </div>

            <div className="grid grid-cols-7 gap-2 text-center text-xs font-semibold text-slate-400 pb-1">
              <div>ПН</div><div>ВТ</div><div>СР</div><div>ЧТ</div><div>ПТ</div><div className="text-rose-400">СБ</div><div className="text-rose-400">ВС</div>
            </div>

            <div className="grid grid-cols-7 gap-2">
              {Array.from({ length: firstWeekdayOffset + daysInMonth }).map((_, i) => {
                if (i < firstWeekdayOffset) return <div key={`empty-${i}`} aria-hidden="true" />;
                const day = i - firstWeekdayOffset + 1;
                const dateStr = toDateString(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), day));
                
                // Absences on this date
                const dayEvents = events.filter(e => {
                  const s = e.start.slice(0, 10);
                  const end = e.end.slice(0, 10);
                  return dateStr >= s && dateStr <= end &&
                    String(e.status || '').toUpperCase() === 'APPROVED';
                });

                const isSelected = selectedDateStr === dateStr;
                const now = new Date();
                const isToday = now.getFullYear() === visibleMonth.getFullYear() && now.getMonth() === visibleMonth.getMonth() && day === now.getDate();

                return (
                  <button
                    key={day}
                    onClick={() => setSelectedDateStr(dateStr)}
                    className={`h-20 p-2 rounded-xl border flex flex-col justify-between text-left transition-all relative ${
                      isSelected
                        ? 'bg-blue-600/20 border-blue-500 shadow-lg ring-2 ring-blue-500/50 scale-[1.02] z-10'
                        : isToday
                        ? 'bg-slate-900 border-blue-500/50 hover:border-slate-600'
                        : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-850'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className={`text-xs font-bold ${
                        isSelected 
                          ? 'text-white' 
                          : isToday 
                          ? 'text-brand-sky' 
                          : 'text-slate-300'
                      }`}>
                        {day}
                      </span>
                      {isToday && (
                        <span className="text-[8px] bg-blue-500 text-white px-1 py-0.2 rounded font-semibold">
                          Сегодня
                        </span>
                      )}
                    </div>

                    {/* Indicator of absences */}
                    <div className="w-full space-y-1">
                      {dayEvents.length > 0 && (
                        <div className="flex items-center gap-1 flex-wrap">
                          {dayEvents.slice(0, 3).map((evt, eIdx) => (
                            <span 
                              key={eIdx}
                              className="w-2 h-2 rounded-full shrink-0 shadow-sm"
                              style={{ backgroundColor: evt.color || '#3B82F6' }}
                              title={`${evt.employee_name}: ${evt.type_display}`}
                            />
                          ))}
                          {dayEvents.length > 3 && (
                            <span className="text-[9px] font-bold text-slate-400">
                              +{dayEvents.length - 3}
                            </span>
                          )}
                        </div>
                      )}

                      {dayEvents.length > 0 ? (
                        <span className={`text-[10px] font-semibold block truncate ${
                          isSelected ? 'text-blue-300' : 'text-slate-400'
                        }`}>
                          {dayEvents.length} {dayEvents.length === 1 ? 'отпуск' : 'чел.'}
                        </span>
                      ) : (
                        <span className="text-[9px] text-slate-600 block">
                          В строю
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Mini helper banner */}
          <div className="p-3 bg-slate-900/90 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-slate-300">
              <Sparkles className="w-3.5 h-3.5 text-brand-sky" />
              Выбран день: <strong className="text-white">{selectedDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}</strong>
            </span>
            <span className="font-mono text-brand-sky">
              {absentOnSelectedDay.length > 0 ? `${absentOnSelectedDay.length} отсутствующих` : 'Нет утверждённых отсутствий'}
            </span>
          </div>
        </div>

        {/* Right Column (5 cols): Selected Date Detailed Absences Panel */}
        <div className="lg:col-span-5 glass-card p-6 rounded-2xl border border-slate-800 space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Panel Header */}
            <div className="border-b border-slate-800 pb-3 flex items-start justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  Отпуска на дату:
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5 flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4 text-brand-sky" />
                  <span>{selectedDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                </h3>
              </div>
              <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                absentOnSelectedDay.length > 0 
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30' 
                  : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              }`}>
                {absentOnSelectedDay.length > 0 ? `${absentOnSelectedDay.length} отсутствуют` : 'Нет утверждённых отсутствий'}
              </span>
            </div>

            {/* List of absent employees on the selected date */}
            <div className="space-y-3 overflow-y-auto max-h-[440px] pr-1">
              {eventsOnSelectedDay.length === 0 ? (
                <div className="p-6 bg-slate-900/50 rounded-2xl border border-slate-800 text-center space-y-3 my-4">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                    <UserCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">Все сотрудники на рабочем месте</div>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      На {selectedDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })} нет оформленных отпусков, больничных или командировок. Доступность ресурсов составляет 100%.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setStartDate(selectedDateStr);
                      setIsSubmitOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold border border-slate-700 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5 text-brand-sky" />
                    <span>Подать заявку на этот день</span>
                  </button>
                </div>
              ) : (
                eventsOnSelectedDay.map((evt, idx) => {
                  const daysLeft = calculateDaysRemaining(evt.end);
                  return (
                    <div 
                      key={idx}
                      className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors space-y-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-xs shadow-md shrink-0"
                            style={{ 
                              background: `linear-gradient(135deg, ${evt.color || '#3B82F6'}, #1E293B)` 
                            }}
                          >
                            {evt.employee_name ? evt.employee_name[0] : 'U'}
                          </div>
                          <div>
                            <div className="text-sm font-bold text-white leading-tight">
                              {evt.employee_name}
                            </div>
                            <div className="text-[11px] text-slate-400">
                              {evt.position || 'Сотрудник'} {evt.department ? `• ${evt.department}` : ''}
                            </div>
                          </div>
                        </div>

                        <span className={`text-[10px] font-bold px-2 py-1 rounded-full shrink-0 ${
                          String(evt.status || '').toUpperCase() === 'APPROVED'
                            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        }`}>
                          {evt.status_display || (String(evt.status || '').toUpperCase() === 'APPROVED' ? 'Утверждено' : 'На согласовании')}
                        </span>
                        <span 
                          className="text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0"
                          style={{
                            backgroundColor: `${evt.color || '#3B82F6'}25`,
                            color: evt.color || '#3B82F6',
                            border: `1px solid ${evt.color || '#3B82F6'}50`
                          }}
                        >
                          {evt.type_display || evt.type}
                        </span>
                      </div>

                      {/* Explicit "До какого числа" block requested by user */}
                      <div className="p-2.5 bg-slate-950/70 rounded-lg border border-slate-800/80 text-xs flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-slate-300">
                          <Clock className="w-3.5 h-3.5 text-brand-sky" />
                          <span>Период: <strong>{formatDateDisplay(evt.start)}</strong> — <strong>{formatDateDisplay(evt.end)}</strong></span>
                        </div>
                        <span className="font-mono font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded text-[11px] border border-amber-500/20">
                          До {formatDateDisplay(evt.end)} (ещё {daysLeft} дн.)
                        </span>
                      </div>

                      {evt.reason && (
                        <div className="text-[11px] text-slate-400 flex items-start gap-1.5 italic">
                          <Info className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                          <span>Основание: «{evt.reason}»</span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Compact 16 Types Legend */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Цветовая кодировка (ТЗ §7.7)
            </div>
            <div className="grid grid-cols-2 gap-1.5 text-[10px] text-slate-300">
              <div className="flex items-center gap-1.5 truncate">
                <span className="w-2 h-2 rounded-full shrink-0 bg-blue-500"></span>
                <span className="truncate">Отпуск (оплачиваемый)</span>
              </div>
              <div className="flex items-center gap-1.5 truncate">
                <span className="w-2 h-2 rounded-full shrink-0 bg-rose-500"></span>
                <span className="truncate">Больничный лист</span>
              </div>
              <div className="flex items-center gap-1.5 truncate">
                <span className="w-2 h-2 rounded-full shrink-0 bg-purple-500"></span>
                <span className="truncate">Командировка</span>
              </div>
              <div className="flex items-center gap-1.5 truncate">
                <span className="w-2 h-2 rounded-full shrink-0 bg-amber-500"></span>
                <span className="truncate">Удалённый день</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Submit Absence Request Modal ── */}
      {isSubmitOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CalendarIcon className="w-5 h-5 text-brand-sky" />
                Подача заявления на отсутствие (ТЗ §6.3, UC-02)
              </h3>
              <button 
                type="button"
                onClick={() => setIsSubmitOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {submitSuccess && (
              <div className="p-3 bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>Заявка успешно отправлена на согласование руководителю!</span>
              </div>
            )}

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Сотрудник *</label>
              <select
                value={selectedEmpId}
                onChange={e => setSelectedEmpId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white"
              >
                {employees.map(emp => (
                  <option key={emp.id} value={emp.id}>
                    {emp.name} ({emp.position}) — {emp.tab_number}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Тип отсутствия (16 категорий) *</label>
              <select
                value={absenceType}
                onChange={e => setAbsenceType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white"
              >
                {absenceTypes.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Дата начала *</label>
                <input
                  type="date"
                  required
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white"
                />
              </div>
              <div>
                <label className="text-slate-300 font-medium block mb-1">Дата окончания *</label>
                <input
                  type="date"
                  required
                  min={startDate}
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white"
                />
              </div>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Основание / Причина</label>
              <textarea
                rows={2}
                value={reason}
                onChange={e => setReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                placeholder="Причина отсутствия или основание..."
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setIsSubmitOpen(false)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              >
                Отмена
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md"
              >
                Отправить заявку
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};