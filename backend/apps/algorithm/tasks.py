import time
from celery import shared_task
from .engine import TeamMatchingEngine

@shared_task(bind=True)
def async_calculate_team(self, project_id: int, candidate_ids: list, weights: dict = None):
    """
    Фоновый расчет подбора команды через Celery + Redis.
    Имитирует сложный расчет на 100+ сотрудников (до 30 сек).
    """
    total_steps = 10
    for step in range(total_steps):
        time.sleep(0.5)  # симуляция итераций генетического алгоритма
        self.update_state(
            state='PROGRESS',
            meta={'current': step + 1, 'total': total_steps, 'percent': int((step + 1) / total_steps * 100)}
        )
    
    engine = TeamMatchingEngine(weights=weights)
    return {
        "status": "SUCCESS",
        "project_id": project_id,
        "variants_count": 3,
        "best_score": 88.4
    }
