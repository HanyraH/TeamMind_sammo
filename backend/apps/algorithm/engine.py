"""
TeamMind Team Selection Engine
TZ §6.8 — Алгоритм формирования команд (Математическая модель).
Жадный + Генетический алгоритмы + Интерактивный What-If анализ.
Формула: S = 0.35*K + 0.25*A + 0.20*L + 0.10*T + 0.10*C
"""
import random
from typing import List, Dict, Any, Optional

# Веса по умолчанию согласно ТЗ §6.8
DEFAULT_WEIGHTS = {
    'K': 0.35,  # Навыки (Skills Match)
    'A': 0.25,  # Доступность (Availability)
    'L': 0.20,  # Баланс нагрузки (Workload Balance, оптимум 80%)
    'T': 0.10,  # Совместимость расписаний и хронотипов (Schedule / Chronotype)
    'C': 0.10   # Совместимость с коллегами (Colleague Compatibility)
}

class TeamMatchingEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        # Нормализация весов если сумма != 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def filter_hard_constraints(
        self,
        candidate: Dict[str, Any],
        project_reqs: Dict[str, Any],
        force_override: bool = False
    ) -> tuple[bool, str]:
        """
        Проверка 6 жестких ограничений (Hard Constraints) по ТЗ §6.8:
        (1) Отпуск, больничный или декрет на весь период проекта
        (2) Статус «уволен» (FIRED) или неактивен
        (3) Проект помечен сотрудником как нежелательный (disliked_projects)
        (4) Отсутствие обязательного навыка на минимально требуемом уровне
        (5) Занятость на другом критическом проекте в тот же период
        (6) Командировка без доступа к рабочему времени (availability == 0)
        """
        # (2) Уволен или неактивен
        if not candidate.get('is_active', True) or candidate.get('status') == 'FIRED':
            return False, "Сотрудник неактивен или уволен"

        # (1) Критическое отсутствие на весь период
        if candidate.get('has_critical_absence', False):
            return False, "Длительное отсутствие на весь период проекта"

        # (6) Нулевая доступность
        if candidate.get('availability_percent', 100.0) <= 0:
            return False, "Нулевая доступность в расчётном периоде"

        # (3) Нежелательный проект
        project_id = str(project_reqs.get('id', ''))
        project_code = str(project_reqs.get('code', ''))
        disliked = candidate.get('disliked_projects', [])
        if not force_override and (project_id in disliked or project_code in disliked):
            return False, "Проект находится в списке нежелательных для сотрудника"

        # (5) Двойное бронирование на критическом проекте
        if candidate.get('has_critical_project_conflict', False):
            return False, "Занят на другом критическом проекте в тот же период"

        # (4) Минимальные обязательные навыки роли
        required_skills = project_reqs.get('required_skills', {})  # {skill_name: min_level}
        candidate_skills = candidate.get('skills_dict', {})        # {skill_name: level}
        for skill_name, min_lvl in required_skills.items():
            cand_lvl = candidate_skills.get(skill_name, 0)
            if cand_lvl < min_lvl:
                return False, f"Недостаточный уровень обязательного навыка '{skill_name}': {cand_lvl} < {min_lvl}"

        return True, "Ограничения соблюдены"

    def calculate_score(
        self,
        candidate: Dict[str, Any],
        project_reqs: Dict[str, Any],
        team_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Расчет интегрального скора по формуле ТЗ §6.8:
        S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C
        Возвращает итоговый балл S и детальную разбивку K, A, L, T, C.
        """
        # --- K: Skills Match [0..100] ---
        req_skills = project_reqs.get('required_skills', {})
        cand_skills = candidate.get('skills_dict', {})
        if req_skills:
            skill_ratios = []
            k_details = {}
            for s_name, req_lvl in req_skills.items():
                c_lvl = cand_skills.get(s_name, 0)
                # Превышение требуемого уровня нормируется как 100%
                ratio = min(1.0, c_lvl / max(1, req_lvl)) * 100.0
                skill_ratios.append(ratio)
                k_details[s_name] = {"candidate_level": c_lvl, "required_level": req_lvl, "ratio": round(ratio, 1)}
            k_score = sum(skill_ratios) / len(skill_ratios)
        else:
            k_score = float(candidate.get('skill_match_percent', 85.0))
            k_details = {}

        # --- A: Availability [0..100] ---
        # Отношение доступных часов к требуемым часам проекта (максимум 100%)
        absence_overlap = float(candidate.get('absence_days_overlap_percent', 0.0))
        base_availability = float(candidate.get('availability_percent', 100.0))
        a_score = max(0.0, min(100.0, base_availability - absence_overlap))

        # --- L: Workload Balance [0..100] ---
        # 100 - |(текущая загрузка + новая нагрузка) - 80%|, штраф 1.5 при превышении 80%
        curr_load = float(candidate.get('current_load_percent', 50.0))
        project_added_load = float(project_reqs.get('estimated_load_percent', 25.0))
        total_proj_load = curr_load + project_added_load
        
        diff = total_proj_load - 80.0
        if diff > 0:
            l_score = max(0.0, 100.0 - (diff * 1.5))
        else:
            l_score = max(0.0, 100.0 - abs(diff))

        # --- T: Schedule & Chronotype Compatibility [0..100] ---
        target_chrono = project_reqs.get('target_chronotype', 'DAY')
        cand_chrono = candidate.get('chronotype', 'DAY')
        # Пересечение хронотипов: жаворонок (LARK), дневной (DAY), сова (OWL)
        chrono_compat_matrix = {
            ('LARK', 'LARK'): 100.0, ('LARK', 'DAY'): 85.0, ('LARK', 'OWL'): 55.0,
            ('DAY', 'LARK'): 85.0,   ('DAY', 'DAY'): 100.0, ('DAY', 'OWL'): 80.0,
            ('OWL', 'LARK'): 55.0,   ('OWL', 'DAY'): 80.0,  ('OWL', 'OWL'): 100.0,
        }
        t_score = chrono_compat_matrix.get((cand_chrono, target_chrono), 80.0)

        # --- C: Colleague Compatibility [0..100] ---
        c_score = 80.0
        if team_context:
            pref_colleagues = set(candidate.get('preferred_colleagues', []))
            disliked_colleagues = set(candidate.get('disliked_colleagues', []))
            team_ids = {m.get('id') for m in team_context if m.get('id') != candidate.get('id')}
            
            bonus = len(pref_colleagues & team_ids) * 10.0
            penalty = len(disliked_colleagues & team_ids) * 25.0
            c_score = max(20.0, min(100.0, c_score + bonus - penalty))
        else:
            c_score = float(candidate.get('compatibility_rating', 80.0))

        # Итоговая формула ТЗ: S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C
        w = self.weights
        total_score = (
            w['K'] * k_score +
            w['A'] * a_score +
            w['L'] * l_score +
            w['T'] * t_score +
            w['C'] * c_score
        )
        total_score = round(max(0.0, min(100.0, total_score)), 2)

        return {
            "total_score": total_score,
            "k_score": round(k_score, 1),
            "a_score": round(a_score, 1),
            "l_score": round(l_score, 1),
            "t_score": round(t_score, 1),
            "c_score": round(c_score, 1),
            "k_details": k_details,
            "projected_load": round(total_proj_load, 1)
        }

    def run_greedy(
        self,
        candidates: List[Dict[str, Any]],
        role_requirements: List[Dict[str, Any]],
        weights_override: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Жадный алгоритм: последовательное назначение лучших кандидатов на каждую роль проекта.
        """
        engine = TeamMatchingEngine(weights_override or self.weights)
        selected_members = []
        used_ids = set()

        for role_req in role_requirements:
            role_title = role_req.get('role_title', 'Developer')
            role_skills = role_req.get('required_skills', {})
            headcount = role_req.get('headcount', 1)

            for _ in range(headcount):
                candidates_pool = []
                for cand in candidates:
                    if cand.get('id') in used_ids:
                        continue
                    
                    req_params = {
                        'required_skills': role_skills,
                        'target_chronotype': role_req.get('target_chronotype', 'DAY'),
                        'estimated_load_percent': role_req.get('estimated_load_percent', 25.0),
                    }
                    is_valid, _ = engine.filter_hard_constraints(cand, req_params)
                    if not is_valid:
                        continue

                    score_data = engine.calculate_score(cand, req_params, team_context=selected_members)
                    candidates_pool.append((score_data['total_score'], score_data, cand))

                if candidates_pool:
                    candidates_pool.sort(key=lambda x: x[0], reverse=True)
                    best_score, score_data, best_cand = candidates_pool[0]
                    used_ids.add(best_cand.get('id'))
                    selected_members.append({
                        **best_cand,
                        'role_assigned': role_title,
                        'final_score': best_score,
                        'score_breakdown': score_data
                    })

        return selected_members

    def run_genetic(
        self,
        candidates: List[Dict[str, Any]],
        role_requirements: List[Dict[str, Any]],
        generations: int = 40,
        population_size: int = 16
    ) -> List[Dict[str, Any]]:
        """
        Генетический алгоритм подбора оптимальной команды.
        Хромосома: вектор назначений кандидатов по ролевым слотам.
        Операторы: скрещивание (crossover), мутация (mutation), селекция (elitism).
        """
        # Сформируем список требуемых слотов
        slots = []
        for r_req in role_requirements:
            for _ in range(r_req.get('headcount', 1)):
                slots.append(r_req)

        if not slots or not candidates:
            return self.run_greedy(candidates, role_requirements)

        # Кандидаты, удовлетворяющие базовым фильтрам
        valid_candidates = [c for c in candidates if c.get('is_active', True) and c.get('status') != 'FIRED']
        if len(valid_candidates) < len(slots):
            valid_candidates = candidates

        def evaluate_team(team: List[Dict[str, Any]]) -> float:
            if not team:
                return 0.0
            total = 0.0
            seen_ids = set()
            dup_penalty = 0.0
            for i, member in enumerate(team):
                m_id = member.get('id')
                if m_id in seen_ids:
                    dup_penalty += 35.0
                seen_ids.add(m_id)
                r_req = slots[min(i, len(slots) - 1)]
                res = self.calculate_score(member, r_req, team_context=team)
                total += res['total_score']
            avg = total / len(team)
            return max(0.0, avg - dup_penalty)

        # Начальная популяция (жадное решение + случайные вариации)
        population = []
        greedy_seed = self.run_greedy(candidates, role_requirements)
        if len(greedy_seed) == len(slots):
            population.append(greedy_seed)

        while len(population) < population_size:
            rand_team = []
            chosen_cands = random.sample(valid_candidates, min(len(valid_candidates), len(slots)))
            for i, c in enumerate(chosen_cands):
                r_title = slots[i].get('role_title', 'Member')
                rand_team.append({**c, 'role_assigned': r_title})
            population.append(rand_team)

        # Эволюционный цикл
        for gen in range(generations):
            scored_pop = [(evaluate_team(t), t) for t in population]
            scored_pop.sort(key=lambda x: x[0], reverse=True)

            # Элитизм: берем топ-4
            new_pop = [t for _, t in scored_pop[:4]]

            while len(new_pop) < population_size:
                p1 = random.choice(scored_pop[:8])[1]
                p2 = random.choice(scored_pop[:8])[1]

                # Кроссовер (одноточечный обмен ролями)
                split = random.randint(1, max(1, len(slots) - 1))
                child = p1[:split] + p2[split:]

                # Мутация (15% шанс случайной замены кандидата)
                if random.random() < 0.25:
                    mutate_idx = random.randint(0, len(child) - 1)
                    new_cand = random.choice(valid_candidates)
                    r_title = slots[mutate_idx].get('role_title', 'Member')
                    child[mutate_idx] = {**new_cand, 'role_assigned': r_title}

                new_pop.append(child)

            population = new_pop

        # Финальный выбор лучшей команды
        final_scored = [(evaluate_team(t), t) for t in population]
        final_scored.sort(key=lambda x: x[0], reverse=True)
        best_team = final_scored[0][1]

        # Обогащаем результат скорами
        enriched_team = []
        for i, member in enumerate(best_team):
            r_req = slots[min(i, len(slots) - 1)]
            score_res = self.calculate_score(member, r_req, team_context=best_team)
            enriched_team.append({
                **member,
                'role_assigned': slots[min(i, len(slots) - 1)].get('role_title', 'Member'),
                'final_score': score_res['total_score'],
                'score_breakdown': score_res
            })

        return enriched_team

    def analyze_team_risks(
        self,
        team: List[Dict[str, Any]],
        role_requirements: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Комплексный анализ рисков команды (ТЗ §6.8):
        1. Анализ Bus Factor (уязвимость к потере ключевого носителя навыка / Single Point of Failure).
        2. Индекс выгорания (Burnout Risk) и дисбаланс нагрузки.
        3. Коэффициент устойчивости команды (Resilience Score, 0..100).
        4. Автоматические рекомендации по кросс-обучению и менторству.
        """
        if not team:
            return {
                "resilience_score": 0.0,
                "overall_risk_level": "HIGH",
                "bus_factor": 0,
                "critical_skills_at_risk": [],
                "burnout_risk": {"risk_level": "LOW", "high_load_members": []},
                "recommendations": ["Команда пуста. Требуется назначение участников."]
            }

        # 1. Bus Factor Analysis (Single Point of Failure)
        req_skills_map: Dict[str, int] = {}
        if role_requirements:
            for req in role_requirements:
                for skill_name, min_lvl in req.get('required_skills', {}).items():
                    req_skills_map[skill_name] = max(req_skills_map.get(skill_name, 0), int(min_lvl))

        # Карта навыков участников команды
        skill_coverage: Dict[str, List[Dict[str, Any]]] = {}
        for member in team:
            m_skills = member.get('skills_dict', {})
            for s_name, s_lvl in m_skills.items():
                if s_name not in skill_coverage:
                    skill_coverage[s_name] = []
                skill_coverage[s_name].append({
                    "id": member.get('id'),
                    "name": member.get('name', f"Employee #{member.get('id')}"),
                    "level": int(s_lvl)
                })

        critical_skills_at_risk = []
        min_bus_factor = 999
        skills_to_check = req_skills_map if req_skills_map else {s: 3 for s in skill_coverage.keys()}

        for s_name, min_lvl in skills_to_check.items():
            capable_members = [
                m for m in skill_coverage.get(s_name, [])
                if m["level"] >= min_lvl
            ]
            carriers_count = len(capable_members)
            min_bus_factor = min(min_bus_factor, carriers_count)

            if carriers_count == 0:
                critical_skills_at_risk.append({
                    "skill": s_name,
                    "bus_factor": 0,
                    "status": "UNCOVERED",
                    "description": f"Навык '{s_name}' (требуемый уровень {min_lvl}) не закрыт ни одним участником!"
                })
            elif carriers_count == 1:
                critical_skills_at_risk.append({
                    "skill": s_name,
                    "bus_factor": 1,
                    "status": "CRITICAL_SPOF",
                    "sole_carrier": capable_members[0]["name"],
                    "sole_carrier_level": capable_members[0]["level"],
                    "description": f"Уязвимость Bus Factor = 1: только {capable_members[0]['name']} владеет навыком '{s_name}' на уровне {capable_members[0]['level']}."
                })

        if min_bus_factor == 999:
            min_bus_factor = 1

        # 2. Burnout Risk & Load Imbalance
        high_load_members = []
        total_loads = []
        for member in team:
            b_down = member.get('score_breakdown', {})
            proj_load = b_down.get('projected_load', float(member.get('current_load_percent', 50.0)))
            total_loads.append(proj_load)
            m_name = member.get('name', f"Employee #{member.get('id')}")
            if proj_load >= 90.0:
                high_load_members.append({
                    "name": m_name,
                    "load_percent": proj_load,
                    "severity": "CRITICAL"
                })
            elif proj_load >= 80.0:
                high_load_members.append({
                    "name": m_name,
                    "load_percent": proj_load,
                    "severity": "ELEVATED"
                })

        avg_load = sum(total_loads) / len(total_loads) if total_loads else 0.0
        load_variance = sum((x - avg_load) ** 2 for x in total_loads) / len(total_loads) if total_loads else 0.0
        load_std_dev = load_variance ** 0.5

        # 3. Resilience Score (0..100)
        resilience = 100.0
        uncovered_cnt = sum(1 for s in critical_skills_at_risk if s.get('status') == 'UNCOVERED')
        spof_cnt = sum(1 for s in critical_skills_at_risk if s.get('status') == 'CRITICAL_SPOF')
        resilience -= uncovered_cnt * 30.0
        resilience -= spof_cnt * 12.0

        for h in high_load_members:
            if h["severity"] == "CRITICAL":
                resilience -= 15.0
            else:
                resilience -= 5.0

        if load_std_dev > 25.0:
            resilience -= 10.0

        resilience = round(max(0.0, min(100.0, resilience)), 1)

        if resilience >= 80.0:
            overall_risk = "LOW"
        elif resilience >= 60.0:
            overall_risk = "MEDIUM"
        elif resilience >= 40.0:
            overall_risk = "HIGH"
        else:
            overall_risk = "CRITICAL"

        # 4. Рекомендации по оптимизации
        recommendations = []
        if uncovered_cnt > 0:
            recommendations.append(f"Критично: добавьте в команду носителей {uncovered_cnt} недостающих навыков.")
        if spof_cnt > 0:
            recommendations.append(f"Риск потери кадров (Bus Factor=1) по {spof_cnt} компетенциям. Организуйте кросс-ревью и парное менторство.")
        if any(h["severity"] == "CRITICAL" for h in high_load_members):
            recommendations.append("Обнаружен риск выгорания: перераспределите задачи со сверхзагруженных сотрудников (>90%).")
        if not recommendations:
            recommendations.append("Команда сбалансирована, риски концентрации компетенций и перегрузок минимальны.")

        return {
            "resilience_score": resilience,
            "overall_risk_level": overall_risk,
            "bus_factor": min_bus_factor,
            "critical_skills_at_risk": critical_skills_at_risk,
            "burnout_risk": {
                "risk_level": "HIGH" if any(h["severity"] == "CRITICAL" for h in high_load_members) else ("MEDIUM" if high_load_members else "LOW"),
                "avg_load_percent": round(avg_load, 1),
                "load_std_dev": round(load_std_dev, 1),
                "high_load_members": high_load_members
            },
            "recommendations": recommendations
        }

    def generate_all_variants(
        self,
        candidates: List[Dict[str, Any]],
        role_requirements: List[Dict[str, Any]],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Формирование от 3 до 5 вариантов состава команды с различными стратегиями по ТЗ §6.8:
        1. Сбалансированная (Рекомендуемая) — баланс всех факторов
        2. Максимальный грейд и навыки — приоритет K (0.50K)
        3. Минимальная загрузка — приоритет L (0.45L)
        4. Синхронные расписания — приоритет T (0.35T)
        5. Высокая совместимость — приоритет C (0.35C)
        """
        strategies = [
            {
                "id": 1,
                "name": "Сбалансированная (Рекомендуемая)",
                "weights": DEFAULT_WEIGHTS,
                "strategy_key": "BALANCED",
                "risk_level": "LOW",
                "algo": "GENETIC"
            },
            {
                "id": 2,
                "name": "Максимальный грейд и навыки",
                "weights": {'K': 0.50, 'A': 0.20, 'L': 0.15, 'T': 0.08, 'C': 0.07},
                "strategy_key": "MAX_SKILLS",
                "risk_level": "MEDIUM",
                "algo": "GREEDY"
            },
            {
                "id": 3,
                "name": "Минимальная загрузка (быстрый старт)",
                "weights": {'K': 0.25, 'A': 0.20, 'L': 0.45, 'T': 0.05, 'C': 0.05},
                "strategy_key": "MIN_LOAD",
                "risk_level": "LOW",
                "algo": "GREEDY"
            },
            {
                "id": 4,
                "name": "Максимальная синхронность расписаний",
                "weights": {'K': 0.30, 'A': 0.20, 'L': 0.15, 'T': 0.25, 'C': 0.10},
                "strategy_key": "MAX_SYNC",
                "risk_level": "LOW",
                "algo": "GREEDY"
            },
            {
                "id": 5,
                "name": "Психологическая совместимость",
                "weights": {'K': 0.25, 'A': 0.20, 'L': 0.15, 'T': 0.15, 'C': 0.25},
                "strategy_key": "HIGH_COMPAT",
                "risk_level": "LOW",
                "algo": "GREEDY"
            }
        ]

        variants = []
        for st in strategies[:max(3, min(5, count))]:
            if st["algo"] == "GENETIC":
                members = self.run_genetic(candidates, role_requirements)
            else:
                members = self.run_greedy(candidates, role_requirements, weights_override=st["weights"])

            if not members:
                continue

            avg_score = round(sum(m.get('final_score', 80.0) for m in members) / len(members), 1)
            avg_skills = round(sum(m.get('score_breakdown', {}).get('k_score', 85.0) for m in members) / len(members), 1)
            avg_avail = round(sum(m.get('score_breakdown', {}).get('a_score', 90.0) for m in members) / len(members), 1)
            avg_load = round(sum(m.get('score_breakdown', {}).get('projected_load', 75.0) for m in members) / len(members), 1)

            # Комплексный анализ рисков и устойчивости команды (Bus Factor & Burnout)
            risk_analysis = self.analyze_team_risks(members, role_requirements)

            variants.append({
                "variant_id": st["id"],
                "strategy_name": st["name"],
                "strategy_key": st["strategy_key"],
                "overall_score": avg_score,
                "skills_coverage": avg_skills,
                "avg_availability": avg_avail,
                "avg_load": avg_load,
                "risk_level": risk_analysis["overall_risk_level"],
                "resilience_score": risk_analysis["resilience_score"],
                "bus_factor": risk_analysis["bus_factor"],
                "risk_details": risk_analysis,
                "members": members,
                "explanation": f"Вариант сформирован по стратегии '{st['name']}'. Покрытие навыков: {avg_skills}%, средняя планируемая загрузка: {avg_load}%. Устойчивость команды: {risk_analysis['resilience_score']}% (Bus Factor = {risk_analysis['bus_factor']})."
            })

        return variants

    def what_if_swap(
        self,
        current_team: List[Dict[str, Any]],
        old_member_id: Any,
        new_candidate: Dict[str, Any],
        project_reqs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Интерактивный What-If анализ: мгновенный перерасчёт метрик
        при замене одного участника команды на другого в конструкторе.
        """
        project_reqs = project_reqs or {'target_chronotype': 'DAY', 'estimated_load_percent': 25.0}
        
        # Удаляем старого участника
        old_member = next((m for m in current_team if str(m.get('id')) == str(old_member_id)), None)
        role_assigned = old_member.get('role_assigned', 'Developer') if old_member else 'Developer'
        
        filtered_team = [m for m in current_team if str(m.get('id')) != str(old_member_id)]
        
        # Рассчитываем нового кандидата
        new_score_data = self.calculate_score(new_candidate, project_reqs, team_context=filtered_team)
        
        updated_member = {
            **new_candidate,
            'role_assigned': role_assigned,
            'final_score': new_score_data['total_score'],
            'score_breakdown': new_score_data
        }
        filtered_team.append(updated_member)

        # Новые средние метрики
        new_avg = round(sum(m.get('final_score', 80.0) for m in filtered_team) / max(1, len(filtered_team)), 1)
        old_avg = round(sum(m.get('final_score', 80.0) for m in current_team) / max(1, len(current_team)), 1) if current_team else 80.0
        delta = round(new_avg - old_avg, 1)

        # Покрытие навыков
        new_k_avg = round(sum(m.get('score_breakdown', {}).get('k_score', 85.0) for m in filtered_team) / max(1, len(filtered_team)), 1)
        
        # Комплексный анализ рисков и Bus Factor для обновленного состава
        risk_data = self.analyze_team_risks(filtered_team)
        risk = f"Устойчивость: {risk_data['resilience_score']}%, Bus-Factor: {risk_data['bus_factor']} ({risk_data['overall_risk_level']})"
        if risk_data['critical_skills_at_risk']:
            risk += f" | {risk_data['critical_skills_at_risk'][0]['description']}"
        elif delta < -5.0:
            risk += " | Умеренный риск: интегральный скор снизился"
        elif new_k_avg >= 85.0 and delta >= 0:
            risk += " | Отличная замена: компетенции команды сбалансированы"

        return {
            "updated_team": filtered_team,
            "overall_match_score": new_avg,
            "skills_coverage": new_k_avg,
            "delta": delta,
            "risk_assessment": risk,
            "resilience_score": risk_data["resilience_score"],
            "bus_factor": risk_data["bus_factor"],
            "risk_details": risk_data,
            "replaced_member": old_member,
            "new_member": updated_member
        }
