import React from 'react';
import { Sliders, Plus, CheckCircle, Database, Shield, Cpu } from 'lucide-react';

export const Settings: React.FC = () => {
  const skillCategories = [
    { name: 'Hard Skills (Языки и фреймворки)', count: 28, skills: ['Python', 'Django', 'React', 'TypeScript', 'PostgreSQL', 'Redis', 'Docker'] },
    { name: 'Soft Skills (Коммуникация и лидерство)', count: 12, skills: ['Agile / Scrum', 'Mentoring', 'Conflict Resolution', 'Presentation'] },
    { name: 'Tools (Инструменты разработки)', count: 18, skills: ['Git', 'GitLab CI', 'Playwright', 'Locust', 'Grafana', 'Prometheus'] },
    { name: 'Language (Иностранные языки)', count: 4, skills: ['Русский (Native)', 'English (B2/C1)', 'Deutsch (A2)'] },
    { name: 'Domain (Предметные области)', count: 6, skills: ['FinTech', 'HRTech', 'E-Commerce', 'Data Science & AI'] }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between glass-card p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white">Справочники системы и дерево навыков</h2>
          <p className="text-xs text-slate-400">Управление 5 категориями навыков (Hard/Soft/Tool/Language/Domain) и ролевой матрицей</p>
        </div>
        <button className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-sm">
          <Plus className="w-3.5 h-3.5" />
          <span>Добавить навык</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {skillCategories.map((cat, idx) => (
          <div key={idx} className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">{cat.name}</h3>
              <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                {cat.count} элементов
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {cat.skills.map((s, sIdx) => (
                <span key={sIdx} className="text-xs bg-slate-900 border border-slate-700/80 text-slate-200 px-2.5 py-1 rounded-lg">
                  {s}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
