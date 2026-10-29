import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Sliders, CheckCircle, RefreshCw, AlertCircle, 
  ArrowRightLeft, ShieldAlert, X, UserCheck, TrendingUp, TrendingDown,
  Briefcase, Clock, Zap, Shield, Activity, AlertTriangle
} from 'lucide-react';
import { 
  runTeamMatch, getWhatIfCandidates, runWhatIfSwap, getProjects, 
  ProjectItem, AlgoVariant, AlgoMember 
} from '../api/client';

export const TeamConstructor: React.FC = () => {
  // Weights according to TZ §6.8 formula: S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C
  const [weightK, setWeightK] = useState(35); // Skills
  const [weightA, setWeightA] = useState(25); // Availability
  const [weightL, setWeightL] = useState(20); // Workload balance
  const [weightT, setWeightT] = useState(10); // Timezone / Chronotype
  const [weightC, setWeightC] = useState(10); // Compatibility
  
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [variants, setVariants] = useState<AlgoVariant[]>([]);
  const [selectedVariantId, setSelectedVariantId] = useState<number>(1);
  const [isCalculating, setIsCalculating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  //////
  /////
  const [presets, setPresets] = useState<Array<{key: string; name: string; description: string}>>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('Balanced');
  ///
  ///

  // What-If interactive replacement state
  const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
  const [replacingMember, setReplacingMember] = useState<AlgoMember | null>(null);
  const [candidateList, setCandidateList] = useState<any[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>('');
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [whatIfResult, setWhatIfResult] = useState<any | null>(null);

  // Initial load
  useEffect(() => {
    loadProjectsAndMatch();
  }, []);

  const loadProjectsAndMatch = async () => {
    try {
      const list = await getAlgorithmPresets();
      if (Array.isArray(list) && list.length >=0) {
        setPresets(list);
        setSelectedPreset(list[0].key);
      }
    } catch (err: any) {
      console.warn('Failed  to load presets, fallback to BALANCED', err);
    }

    try {
      const prjList = await getProjects();
      setProjects(prjList);
      const initialPrjId = prjList.length > 0 ? prjList[0].id : '';
      setSelectedProjectId(initialPrjId);
      await executeMatch(initialPrjId, 'BALANCED');
    } catch(err: any) {
      console.error('Failed to initialize projects:', err);
      await executeMatch('', 'BALANCED');
    }
  };

  const executeMatch = async (prjId: string, preset: string) => {
    setIsCalculating(true);
    setErrorMsg(null);
    try {
      const payload: Record<string, unknown> = {
        project_id: prjId || undefined,
        preset,
        count: 3,
      };

      if (preset === 'CUSTOM ') {
        const totalW = (weightK + weightA + weightL + weightT + weightC) || 100;
        payload.weights = {
          K: weightK / totalW,
          A: weightA / totalW,
          L: weightL / totalW,
          T: weightT / totalW,
          C: weightC / totalW
        };
      }

      const resp = await runTeamMatch(payload as any);

      if (resp.variants && resp.variants.length > 0) {
        setVariants(resp.variants);
        setSelectedVariantId(resp.variants[0].variant_id);
      }
    } catch (err: any) {
      console.error('Error running team matching:', err);
      setErrorMsg('не удалось выполнить подбор через API. проверьте соединение с сервером.');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleRunMatch = () => {
    executeMatch(selectedProjectId, selectedPreset);
  };

  // Open What-If Modal for a member
  const handleOpenWhatIf = async (member: AlgoMember) => {
    setReplacingMember(member);
    setIsWhatIfOpen(true);
    setWhatIfResult(null);
    setSelectedCandidateId('');

    const activeTeam = variants.find(v => v.variant_id === selectedVariantId);
    const excludeIds = activeTeam ? activeTeam.members.map(m => String(m.id)) : [];

    try {
      const candidates = await getWhatIfCandidates(excludeIds);
      setCandidateList(candidates);
      if (candidates.length > 0) {
        setSelectedCandidateId(candidates[0].id);
      }
    } catch (err) {
      console.error('Failed to load what-if candidates:', err);
    }
  };

  // Run What-If calculation
  const handleCalculateSwap = async () => {
    if (!replacingMember || !selectedCandidateId) return;

    setWhatIfLoading(true);
    const activeTeam = variants.find(v => v.variant_id === selectedVariantId);
    try {
      const result = await runWhatIfSwap({
        current_team: activeTeam ? activeTeam.members : [],
        old_id: String(replacingMember.id),
        candidate_id: selectedCandidateId,
        weights: {
          K: weightK / 100,
          A: weightA / 100,
          L: weightL / 100,
          T: weightT / 100,
          C: weightC / 100,
        }
      });
      setWhatIfResult(result);
    } catch (err) {
      console.error('Error in what-if calculation:', err);
    } finally {
      setWhatIfLoading(false);
    }
  };

  // Apply What-If swap to active variant
  const handleApplySwap = () => {
    if (!whatIfResult || !replacingMember) return;

    setVariants(prev => prev.map(v => {
      if (v.variant_id !== selectedVariantId) return v;
      return {
        ...v,
        overall_score: whatIfResult.overall_match_score,
        skills_coverage: whatIfResult.skills_coverage,
        members: whatIfResult.updated_team,
        explanation: `Состав скорректирован в режиме What-If. ${whatIfResult.risk_assessment}.`
      };
    }));

    setIsWhatIfOpen(false);
    setReplacingMember(null);
    setWhatIfResult(null);
  };

  const activeVariant = variants.find(v => v.variant_id === selectedVariantId) || variants[0];
  const sumWeights = weightK + weightA + weightL + weightT + weightC;

  return (
    <div className="space-y-6">
      {/* Top Banner & Project Selector */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 glass-card p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-sky" />
            Интеллектуальный генератор и конструктор команд
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Математическая модель (ТЗ §6.8): 6 жестких ограничений, оптимизация навыков, расписаний и 16 типов отсутствий.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {projects.length > 0 && (
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs">
              <Briefcase className="w-4 h-4 text-brand-sky" />
              <select
                value={selectedProjectId}
                onChange={(e) => {
                  setSelectedProjectId(e.target.value);
                  executeMatch(e.target.value, selectedPreset);
                }}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id} className="bg-slate-900 text-white">
                    {p.name} ({p.code})
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={handleRunMatch}
            disabled={isCalculating}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50 shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isCalculating ? 'animate-spin' : ''}`} />
            <span>{isCalculating ? 'Расчет в Celery / Algo...' : 'Сгенерировать варианты'}</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Algorithm Parameters & Sliders */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-brand-sky" />
              Весовые коэффициенты формулы
            </h3>
            <span className={`text-[11px] font-mono font-bold ${sumWeights === 100 ? 'text-emerald-400' : 'text-amber-400'}`}>
              Σ = {sumWeights}%
            </span>
          </div>

          <div className="space-y-4 text-xs">
            {/* Skills */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-300 font-medium">K (Навыки и стек)</span>
                <span className="text-brand-sky font-bold font-mono">{weightK}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="60"
                value={weightK}
                onChange={(e) => setWeightK(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            {/* Availability */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-300 font-medium">A (Доступность без отпусков)</span>
                <span className="text-brand-sky font-bold font-mono">{weightA}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                value={weightA}
                onChange={(e) => setWeightA(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            {/* Workload */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-300 font-medium">L (Баланс нагрузки ~80%)</span>
                <span className="text-brand-sky font-bold font-mono">{weightL}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                value={weightL}
                onChange={(e) => setWeightL(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            {/* Chronotype */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-300 font-medium">T (Пересечение хронотипов)</span>
                <span className="text-brand-sky font-bold font-mono">{weightT}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={weightT}
                onChange={(e) => setWeightT(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            {/* Compatibility */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-300 font-medium">C (Совместимость в команде)</span>
                <span className="text-brand-sky font-bold font-mono">{weightC}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={weightC}
                onChange={(e) => setWeightC(Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>
          </div>

          <div className="p-3 bg-blue-950/30 border border-blue-900/50 rounded-xl text-[11px] text-blue-300 space-y-1">
            <strong>Модель оптимизации ТЗ §6.8:</strong>
            <code className="block bg-slate-900/80 p-1.5 rounded font-mono text-[10px] text-sky-300">
              S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C
            </code>
            <p className="text-[10px] text-slate-400">
              6 Hard Constraints отсекают неактивных, уволенных, критические отсутствия и нежелательные проекты.
            </p>
          </div>
        </div>

        {/* Center & Right Columns: Generated Variants & What-If Analyzer */}
        <div className="lg:col-span-2 space-y-5">
          {/* Variants Selector Tabs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {variants.map((v) => (
              <button
                key={v.variant_id}
                onClick={() => setSelectedVariantId(v.variant_id)}
                className={`p-4 rounded-xl text-left border transition-all ${
                  selectedVariantId === v.variant_id
                    ? 'bg-blue-600/15 border-blue-500 shadow-md ring-1 ring-blue-500/50'
                    : 'glass-card border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white line-clamp-1">{v.strategy_name}</span>
                  <span className="text-xs font-extrabold text-brand-sky bg-blue-500/10 px-2 py-0.5 rounded font-mono">
                    {v.overall_score}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-2 line-clamp-2">
                  Покрытие: {v.skills_coverage}%, Нагрузка: {v.avg_load || 75}%
                </div>
                <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/60 text-[10px]">
                  <span className="text-slate-400">Участников: {v.members.length}</span>
                  <span className={`font-semibold ${v.risk_level === 'LOW' ? 'text-emerald-400' : v.risk_level === 'MEDIUM' ? 'text-amber-400' : 'text-rose-400'}`}>
                    Риск: {v.risk_level}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Active Variant Members List with What-If Action */}
          {activeVariant && (
            <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                  <h4 className="text-base font-bold text-white">{activeVariant.strategy_name}</h4>
                  <div className="text-xs text-slate-400">
                    Интегральный скор: <span className="text-brand-sky font-bold font-mono">{activeVariant.overall_score}</span> / 100 • Покрытие навыков: {activeVariant.skills_coverage}%
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5" />
                    Квота закрыта ({activeVariant.members.length} чел.)
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                {activeVariant.members.map((member, idx) => {
                  const mScore = member.final_score || member.score || 85;
                  const mRole = member.role_assigned || member.role || member.position || 'Специалист';
                  return (
                    <div 
                      key={idx} 
                      className="p-3.5 bg-slate-900/70 border border-slate-800 rounded-xl flex items-center justify-between hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 border border-blue-500/40 flex items-center justify-center font-bold text-white text-xs shadow">
                          {member.name ? member.name[0] : 'U'}
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-white">{member.name}</div>
                          <div className="text-[11px] text-slate-400">{mRole}</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-xs">
                        <div className="hidden sm:flex items-center gap-1 text-slate-400 text-[11px]">
                          <Clock className="w-3 h-3 text-slate-500" />
                          <span>{member.chronotype_display || member.chronotype || 'Дневной'}</span>
                        </div>

                        <div className="text-right">
                          <div className="font-bold text-brand-sky font-mono">{mScore}%</div>
                          <div className="text-[10px] text-slate-500">соответствие</div>
                        </div>

                        <button 
                          onClick={() => handleOpenWhatIf(member)}
                          title="Интерактивная замена участника (What-If симулятор)"
                          className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-blue-600/30 text-slate-300 hover:text-white rounded-lg border border-slate-700 text-xs transition-colors"
                        >
                          <ArrowRightLeft className="w-3.5 h-3.5 text-brand-sky" />
                          <span className="hidden sm:inline">Заменить</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Explanation & What-If Box */}
              <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl flex items-start gap-3 mt-4">
                <ShieldAlert className="w-4 h-4 text-brand-sky shrink-0 mt-0.5" />
                <div className="text-xs text-slate-300">
                  <strong className="text-white">Интерпретация ИИ-решения (ТЗ §6.8):</strong>{' '}
                  {activeVariant.explanation || `Данный вариант сформирован по стратегии "${activeVariant.strategy_name}". Покрытие навыков составляет ${activeVariant.skills_coverage}%, уровень риска: ${activeVariant.risk_level}.`}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── What-If Interactive Replacement Modal (TZ §6.8) ── */}
      {isWhatIfOpen && replacingMember && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl p-6 space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-500/10 rounded-lg text-brand-sky">
                  <ArrowRightLeft className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Интерактивный What-If анализ замены</h3>
                  <p className="text-xs text-slate-400">Мгновенная оценка изменения скора команды и рисков</p>
                </div>
              </div>
              <button 
                onClick={() => setIsWhatIfOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Member to Replace */}
            <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Текущий участник:</span>
                <div className="text-sm font-bold text-white mt-0.5">{replacingMember.name}</div>
                <div className="text-xs text-slate-400">{replacingMember.role_assigned || replacingMember.role || 'Специалист'}</div>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono font-bold text-slate-300">{replacingMember.final_score || replacingMember.score || 85}%</span>
                <div className="text-[10px] text-slate-500">исходный скор</div>
              </div>
            </div>

            {/* Alternative Candidate Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">
                Выберите кандидата из резерва базы данных:
              </label>
              <select
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:border-brand-sky"
              >
                {candidateList.map(cand => (
                  <option key={cand.id} value={cand.id}>
                    {cand.name} — {cand.position} ({cand.department}) [Загрузка: {cand.load}%]
                  </option>
                ))}
              </select>
            </div>

            {/* Calculate Swap Action Button */}
            <div className="flex justify-end">
              <button
                onClick={handleCalculateSwap}
                disabled={whatIfLoading || !selectedCandidateId}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition-all disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5 text-amber-300" />
                <span>{whatIfLoading ? 'Расчет What-If...' : 'Рассчитать эффект замены'}</span>
              </button>
            </div>

            {/* What-If Results Card */}
            {whatIfResult && (
              <div className="p-4 bg-blue-950/30 border border-blue-900/60 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Новый интегральный скор команды:</span>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-extrabold text-brand-sky font-mono">
                      {whatIfResult.overall_match_score}%
                    </span>
                    <span className={`text-xs font-bold flex items-center gap-0.5 ${
                      whatIfResult.delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {whatIfResult.delta >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {whatIfResult.delta >= 0 ? `+${whatIfResult.delta}` : whatIfResult.delta}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span>Покрытие навыков команды:</span>
                  <span className="font-mono font-bold text-white">{whatIfResult.skills_coverage}%</span>
                </div>

                <div className="text-xs text-slate-300 pt-2 border-t border-blue-900/40">
                  <span className="font-semibold text-white">Оценка риска: </span>
                  {whatIfResult.risk_assessment}
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    onClick={() => setIsWhatIfOpen(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleApplySwap}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-md"
                  >
                    <UserCheck className="w-3.5 h-3.5" />
                    <span>Применить замену в вариант</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
