"""
Автономный тест математической модели TeamMind (ТЗ §6.8).
Запускается напрямую без Django сервера и базы данных!
Формула: S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "apps" / "algorithm"))
from engine import TeamMatchingEngine, DEFAULT_WEIGHTS

def run_demo():
    print("=" * 65)
    print("[Algo & Analytics] TeamMind AI Math Algorithm Engine (TZ 6.8)")
    print("=" * 65)
    engine = TeamMatchingEngine()
    print("1. Default weights (TZ 6.8):")
    for k, v in engine.weights.items():
        print(f"   [{k}] = {v:.2f}")

    # Check 6 Hard Constraints
    print("2. Check 6 Hard Constraints:")
    cand_fired = {"id": 1, "name": "Fired Person", "is_active": False, "status": "FIRED"}
    passed, reason = engine.filter_hard_constraints(cand_fired, {"id": "P1"})
    print(f"   - Fired employee: passed={passed} ({reason})")
    assert not passed, "Fired candidate must be blocked!"

    cand_active = {
        "id": 2, "name": "Ivan Lead", "is_active": True, "status": "ACTIVE",
        "availability_percent": 100.0, "current_load_percent": 60.0,
        "chronotype": "LARK", "skills_dict": {"Python": 5, "Django": 4}
    }
    passed, reason = engine.filter_hard_constraints(cand_active, {"id": "P1"})
    print(f"   - Active candidate: passed={passed} ({reason})")
    assert passed, "Active candidate must pass hard constraints!"

    # Score calculation
    print("3. Score calculation S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C:")
    req = {"id": "P1", "required_skills": {"Python": 4, "Django": 4}, "estimated_load_percent": 25.0, "target_chronotype": "LARK"}
    score_data = engine.calculate_score(cand_active, req)
    print(f"   -> Total score S = {score_data['total_score']:.1f} / 100")
    print(f"      K (skills)       = {score_data['k_score']:.1f}%")
    print(f"      A (availability) = {score_data['a_score']:.1f}%")
    print(f"      L (load)         = {score_data['l_score']:.1f}%")
    print(f"      T (chronotype)   = {score_data['t_score']:.1f}%")
    assert score_data['total_score'] > 80, "High candidate score expected!"

    # What-If replacement
    print("4. Interactive What-If Member Swap Analysis:")
    team = [{"id": 10, "name": "Old Member", "final_score": 75.0, "role_assigned": "Backend"}]
    new_cand = {"id": 20, "name": "New Lead", "current_load_percent": 50.0, "skills_dict": {"Python": 5}}
    what_if = engine.what_if_swap(team, old_member_id=10, new_candidate=new_cand)
    print(f"   -> Score delta: {what_if['delta']:+.1f}% | Risk: {what_if['risk_assessment']}")
    print(f"   -> Resilience Score: {what_if['resilience_score']}% | Bus-Factor: {what_if['bus_factor']}")

    # 5. Team Resilience & Bus-Factor Risk Analysis
    print("5. Team Resilience & Bus-Factor Risk Analysis (TZ §6.8):")
    sample_team = [
        {"id": 101, "name": "Senior Python Lead", "current_load_percent": 92.0, "skills_dict": {"Python": 5, "Architecture": 5}},
        {"id": 102, "name": "Junior Frontend", "current_load_percent": 40.0, "skills_dict": {"React": 3, "CSS": 4}},
        {"id": 103, "name": "DevOps Engineer", "current_load_percent": 82.0, "skills_dict": {"Docker": 4, "Kubernetes": 4}}
    ]
    project_roles = [
        {"role_title": "Backend Lead", "required_skills": {"Python": 4, "Architecture": 4}},
        {"role_title": "Frontend", "required_skills": {"React": 3}},
        {"role_title": "DevOps", "required_skills": {"Kubernetes": 4, "Security": 3}}
    ]
    risks = engine.analyze_team_risks(sample_team, project_roles)
    print(f"   -> Team Resilience Score: {risks['resilience_score']}% (Risk Level: {risks['overall_risk_level']})")
    print(f"   -> Team Bus Factor: {risks['bus_factor']}")
    print(f"   -> Burnout Risk Level: {risks['burnout_risk']['risk_level']} (High-load members: {len(risks['burnout_risk']['high_load_members'])})")
    print("   -> Critical Skills & Single Points of Failure (SPOF):")
    for item in risks['critical_skills_at_risk']:
        print(f"      * [{item['status']}] {item['description']}")
    print("   -> Mitigation Recommendations:")
    for rec in risks['recommendations']:
        print(f"      * {rec}")

    assert risks['resilience_score'] > 0, "Resilience score should be calculated"
    assert len(risks['critical_skills_at_risk']) >= 2, "Should identify uncovered Security and SPOF for Architecture/Kubernetes"

    # 6. Advanced Genetic Algorithm with Order Crossover (OX) & Simulated Annealing
    print("6. Genetic Solver (Order Crossover & Annealing Convergence):")
    candidates_pool = [
        {"id": i, "name": f"Candidate {i}", "is_active": True, "status": "ACTIVE",
         "availability_percent": 100.0, "current_load_percent": 50.0 + (i % 20),
         "chronotype": "DAY", "skills_dict": {"Python": (i % 5) + 1, "Django": ((i + 2) % 5) + 1}}
        for i in range(1, 25)
    ]
    roles_req = [
        {"role_title": "Lead", "required_skills": {"Python": 5}, "headcount": 1},
        {"role_title": "Senior Dev", "required_skills": {"Python": 4, "Django": 4}, "headcount": 2},
        {"role_title": "Junior Dev", "required_skills": {"Python": 2}, "headcount": 1}
    ]
    gen_team, history = engine.run_genetic(candidates_pool, roles_req, generations=20, return_convergence=True)
    team_ids = [m["id"] for m in gen_team]
    print(f"   -> Team assembled: {len(gen_team)} members (Unique IDs: {len(set(team_ids))} of {len(team_ids)})")
    assert len(team_ids) == len(set(team_ids)), "OX Crossover must guarantee duplicate-free assignments!"
    print(f"   -> Convergence recorded: {len(history)} generations (Gen 1 best: {history[0]['best_fitness']} -> Gen {len(history)} best: {history[-1]['best_fitness']})")
    assert history[-1]['best_fitness'] >= history[0]['best_fitness'], "Genetic solver must converge or maintain fitness!"

    # 7. Monte Carlo Operational Risk & Stress-Testing Simulator
    print("7. Monte Carlo Operational Risk & Stress-Testing Simulator (TZ §6.8):")
    mc_res = engine.simulate_monte_carlo_risks(sample_team, project_roles, iterations=300)
    print(f"   -> Success Probability: {mc_res['success_probability']}% (Risk Profile: {mc_res['risk_profile']})")
    print(f"   -> Failure Causes: {mc_res['failure_breakdown_percent']}")
    print(f"   -> Summary: {mc_res['summary']}")
    assert mc_res['iterations_run'] == 300, "Should execute 300 Monte Carlo iterations"

    # 8. Belbin Team Roles & Cognitive Diversity Balance
    print("8. Belbin Team Roles & Cognitive Diversity Balance (TZ §6.8):")
    belbin_team = [
        {"id": 1, "name": "Alice Leader", "belbin_role": "COORDINATOR"},
        {"id": 2, "name": "Bob Builder", "belbin_role": "IMPLEMENTER"},
        {"id": 3, "name": "Charlie Thinker", "belbin_role": "PLANT"}
    ]
    b_res = engine.analyze_belbin_balance(belbin_team)
    print(f"   -> Belbin Balance Score: {b_res['balance_score']}% (Clusters: {b_res['clusters']})")
    print(f"   -> Advice: {b_res['advice']}")
    assert b_res['balance_score'] >= 90.0, "Balanced team covering 3 clusters should have high score"

    print("=" * 65)
    print("[SUCCESS] All Algorithm, Genetic, Belbin, Monte-Carlo & Risk modules (TZ 6.8) OK!\n")

if __name__ == "__main__":
    run_demo()




