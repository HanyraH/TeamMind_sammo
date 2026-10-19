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
    print("=" * 65)
    print("[SUCCESS] All Algorithm & Math modules (TZ 6.8) work correctly! OK\n")

if __name__ == "__main__":
    run_demo()
