import React, { useState } from 'react';
import { Sliders, Plus, X, CheckCircle } from 'lucide-react';

interface SkillCategory {
  name: string;
  count: number;
  skills: string[];
}

const initialCategories: SkillCategory[] = [
  { name: 'Hard Skills (Языки и фреймворки)', count: 28, skills: ['Python', 'Django', 'React', 'TypeScript', 'PostgreSQL', 'Redis', 'Docker'] },
  { name: 'Soft Skills (Коммуникация и лидерство)', count: 12, skills: ['Agile / Scrum', 'Mentoring', 'Conflict Resolution', 'Presentation'] },
  { name: 'Tools (Инструменты разработки)', count: 18, skills: ['Git', 'GitLab CI', 'Playwright', 'Locust', 'Grafana', 'Prometheus'] },
  { name: 'Language (Иностранные языки)', count: 4, skills: ['Русский (Native)', 'English (B2/C1)', 'Deutsch (A2)'] },
  { name: 'Domain (Предметные области)', count: 6, skills: ['FinTech', 'HRTech', 'E-Commerce', 'Data Science & AI'] },
];

export const Settings: React.FC = () => {
  const [categories, setCategories] = useState<SkillCategory[]>(initialCategories);

  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newSkill, setNewSkill] = useState('');
  const [targetCategory, setTargetCategory] = useState(0);
  const [addedSuccess, setAddedSuccess] = useState(false);

  const handleAddSkill = (e: React.FormEvent) => {
    e.preventDefault();
    const value = newSkill.trim();
    if (!value) return;

    // Защита от дублей в выбранной категории
    const alreadyExists = categories[targetCategory].skills.some(
      (s) => s.toLowerCase() === value.toLowerCase()
    );
    if (alreadyExists) return;

    setCategories((prev) =>
      prev.map((cat, idx) =>
        idx === targetCategory
          ? { ...cat, skills: [...cat.skills, value], count: cat.count + 1 }
          : cat
      )
    );

    setNewSkill('');
    setAddedSuccess(true);
    setTimeout(() => {
      setAddedSuccess(false);
      setIsAddOpen(false);
    }, 900);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between glass-card p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white">Справочники системы и дерево навыков</h2>
          <p className="text-xs text-slate-400">
            Управление 5 категориями навыков (Hard/Soft/Tool/Language/Domain) и ролевой матрицей
          </p>
        </div>
        <button
          onClick={() => setIsAddOpen(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Добавить навык</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {categories.map((cat, idx) => (
          <div key={idx} className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">{cat.name}</h3>
              <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                {cat.count} элементов
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {cat.skills.map((s, sIdx) => (
                <span
                  key={sIdx}
                  className="text-xs bg-slate-900 border border-slate-700/80 text-slate-200 px-2.5 py-1 rounded-lg"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* ── Модалка «Добавить навык» ── */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleAddSkill}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-brand-sky" />
                Добавление навыка в справочник
              </h3>
              <button
                type="button"
                onClick={() => setIsAddOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {addedSuccess && (
              <div className="p-3 bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>Навык успешно добавлен в справочник</span>
              </div>
            )}

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Категория *</label>
              <select
                value={targetCategory}
                onChange={(e) => setTargetCategory(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white"
              >
                {categories.map((c, i) => (
                  <option key={i} value={i}>{c.name}</option>
                ))}
              </select>
            </div>

            <div className="text-xs">
              <label className="text-slate-300 font-medium block mb-1">Название навыка *</label>
              <input
                type="text"
                required
                autoFocus
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Например: Kubernetes, Rust, Figma..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setIsAddOpen(false)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              >
                Отмена
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md"
              >
                Добавить навык
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};