# План интеграции модулей TeamMind (ТЗ §6.8)
**Ветка источника алгоритмов:** `HanyraH`  
**Дата актуализации:** 28 октября 2026 г.

Документ содержит пошаговый технический план для разработчиков команды (**Koroliov862**, **1-Soul-1**, **Dikiyarbuzz**) по подключению математического ядра, системы оценки рисков, симулятора Монте-Карло и пресетов к общему приложению.

---

## 0. Что уже реализовано в ветке `HanyraH` (Готово к интеграции)

В ветке `HanyraH` полностью реализовано и протестировано алгоритмическое ядро:
- **Формула ТЗ §6.8:** Интегральный расчет скора $S = 0.35K + 0.25A + 0.20L + 0.10T + 0.10C$.
- **Проверка 6 жестких ограничений (Hard Constraints):** увольнение, больничные, нулевая доступность, нежелательные проекты, дефицит ключевых навыков, конфликт критических проектов.
- **Генетический алгоритм:** с бесконфликтным оператором **Order Crossover (OX)** и адаптивным отжигом мутаций (**Simulated Annealing**).
- **Анализ устойчивости (Resilience) и Bus Factor:** выявление уязвимостей Single Point of Failure (SPOF) и риска выгорания (Burnout).
- **Монте-Карло симуляция:** вероятностная оценка успешной сдачи проекта в срок (Success Probability, 500 итераций).
- **Роли по Белбину (Belbin Team Roles):** учет ролевого баланса (Действие, Люди, Мышление) и предотвращение конфликтов лидерства.
- **Динамические пресеты весов:** `BALANCED`, `CRUNCH`, `MENTORSHIP`, `FAST_PACE`, `DISTRIBUTED_SYNC`.

### Доступные эндпоинты алгоритма:
- `POST /api/v1/algorithm/match/` — генерация от 3 до 5 вариантов команд (с поддержкой параметра `preset`).
- `POST /api/v1/algorithm/what-if/` — интерактивный перерасчет при замене участника + Монте-Карло стресс-тест.
- `POST /api/v1/algorithm/risks/` — аудит состава команды на Bus Factor, устойчивость и баланс по Белбину.
- `GET /api/v1/algorithm/presets/` — получение списка всех готовых пресетов с описаниями.

---

## 1. Задачи для `Koroliov862` (Backend Lead / Core & База данных)

### Задача 1.1: Регистрация приложений в настройках Django
**Файл:** `backend/teammind/settings.py`  
Добавить приложения алгоритмов и аналитики в `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... существующие приложения ...
    'apps.authentication',
    'apps.organization',
    'apps.absences',
    'apps.projects',
    # ДОБАВИТЬ:
    'apps.algorithm',
    'apps.analytics',
]
```

### Задача 1.2: Подключение URL-маршрутов
**Файл:** `backend/teammind/urls.py`  
Зарегистрировать пути в главном роутере проекта:
```python
urlpatterns = [
    # ... существующие пути ...
    path('api/v1/org/', include('apps.organization.urls')),
    path('api/v1/absences/', include('apps.absences.urls')),
    path('api/v1/projects/', include('apps.projects.urls')),
    # ДОБАВИТЬ:
    path('api/v1/algorithm/', include('apps.algorithm.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
]
```

### Задача 1.3: Добавление роли по Белбину в модель сотрудника
**Файл:** `backend/apps/organization/models.py`  
В класс `Employee` добавить поле:
```python
class Employee(BaseModel):
    # ... существующие поля ...
    belbin_role = models.CharField(
        max_length=30,
        default='SPECIALIST',
        choices=[
            ('COORDINATOR', 'Координатор'),
            ('SHAPER', 'Мотиватор (Shaper)'),
            ('PLANT', 'Генератор идей (Plant)'),
            ('MONITOR_EVALUATOR', 'Аналитик (Monitor Evaluator)'),
            ('IMPLEMENTER', 'Реализатор (Implementer)'),
            ('COMPLETER_FINISHER', 'Педант (Completer Finisher)'),
            ('TEAMWORKER', 'Душа команды (Teamworker)'),
            ('RESOURCE_INVESTIGATOR', 'Исследователь ресурсов'),
            ('SPECIALIST', 'Специалист'),
        ],
        verbose_name="Роль по Белбину"
    )
```

### Задача 1.4: Выполнение миграций и наполнение тестовой БД
Выполнить команды:
```bash
python backend/manage.py makemigrations organization algorithm analytics
python backend/manage.py migrate
```
**Критически важно:** заполнить базу через сидер или фикстуры:
- Минимум 1 активный проект с ролевыми требованиями (`ProjectRoleRequirement`) и обязательными навыками (`RequiredSkill`).
- Минимум 15-20 активных сотрудников со сформированными навыками (`EmployeeSkill` со шкалой от 1 до 5), хронотипами и ролями.

---

## 2. Задачи для `1-Soul-1` (Frontend Lead / UI Конструктора и Аналитика)

### Задача 2.1: Пресеты подбора в Конструкторе команд
**Файл:** `frontend/src/pages/TeamConstructor.tsx`  
1. Добавить селектор выбора режима стратегии перед кнопкой «Сформировать команду»:
   - `Сбалансированный (ТЗ §6.8)` (ключ: `BALANCED`)
   - `Аврал / Горящий релиз` (ключ: `CRUNCH`)
   - `Обучение и менторство` (ключ: `MENTORSHIP`)
   - `Быстрый старт (Мин. загрузка)` (ключ: `FAST_PACE`)
   - `Синхронность расписаний` (ключ: `DISTRIBUTED_SYNC`)
2. Передавать выбранный `preset` в теле запроса `POST /api/v1/algorithm/match/`:
   ```ts
   const payload = {
     project_id: selectedProjectId,
     preset: selectedPreset,
     count: 3
   };
   ```

### Задача 2.2: Карточки вариантов — вывод Resilience & Bus Factor
**Файл:** `frontend/src/pages/TeamConstructor.tsx`  
В карточке каждого сгенерированного варианта отображать:
- **Resilience Score** (`variant.resilience_score`): индикатор устойчивости команды (в %).
  - $>80\%$ — зелёный (Высокая стабильность);
  - $60-80\%$ — жёлтый (Умеренный риск);
  - $<60\%$ — красный (Критический риск).
- **Bus Factor** (`variant.bus_factor`):
  - Если `= 1` — выводить предупреждающий бейдж `SPOF риск`.
  - Список критических компетенций из `variant.risk_details.critical_skills_at_risk` с подсказкой, кто является единственным носителем.
- **График сходимости (Convergence history):**
  - Для варианта №1 отображать sparkline/линейный график обучения по массиву `variant.convergence_history` (`generation` против `best_fitness`).

### Задача 2.3: Монте-Карло симулятор в окне What-If
**Файл:** `frontend/src/pages/TeamConstructor.tsx`  
При интерактивной замене сотрудника в блоке результатов отображать блок Монте-Карло:
- **Вероятность сдачи проекта в срок:** `data.monte_carlo_stress_test.success_probability` (например: `84.2%`).
- **Стресс-профиль надежности:** бейдж `data.monte_carlo_stress_test.risk_profile` (`STABLE`, `MODERATE_RISK`, `HIGH_RISK`).

### Задача 2.4: Виджет ролевого баланса по Белбину
**Файл:** `frontend/src/pages/Analytics.tsx`  
Добавить блок «Психологический баланс команды»:
- Круговая диаграмма распределения участников по 3 кластерам: Действие (`ACTION`), Люди (`PEOPLE`), Мышление (`THOUGHT`).
- Блок предупреждений о конфликтах: вывод списка `variant.risk_details.belbin_balance.conflicts`.

---

## 3. Задачи для `Dikiyarbuzz` (Frontend / Сотрудники, Календарь, API-клиент)

### Задача 3.1: Расширение API-клиента и TypeScript интерфейсов
**Файл:** `frontend/src/api/client.ts`  
Добавить типизацию новых ответов алгоритма:
```typescript
export interface BelbinClusterData {
  ACTION: number;
  PEOPLE: number;
  THOUGHT: number;
}

export interface RiskDetails {
  resilience_score: number;
  overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  bus_factor: number;
  critical_skills_at_risk: Array<{
    skill: string;
    bus_factor: number;
    status: string;
    sole_carrier?: string;
    description: string;
  }>;
  belbin_balance?: {
    balance_score: number;
    clusters: BelbinClusterData;
    conflicts: string[];
    advice: string[];
  };
  recommendations: string[];
}

// Расширение интерфейса варианта команды
export interface AlgoVariant {
  variant_id: number;
  strategy_name: string;
  strategy_key: string;
  overall_score: number;
  skills_coverage: number;
  avg_availability: number;
  avg_load: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  resilience_score: number;
  bus_factor: number;
  risk_details: RiskDetails;
  convergence_history?: Array<{ generation: number; best_fitness: number; avg_fitness: number }>;
  members: AlgoMember[];
  explanation?: string;
}

// Новые API-методы
export const getAlgorithmPresets = async () => {
  const { data } = await api.get('/algorithm/presets/');
  return data.presets;
};

export const getTeamRisks = async (payload: { team: any[]; project_id?: string }) => {
  const { data } = await api.post('/algorithm/risks/', payload);
  return data;
};
```

### Задача 3.2: Выбор роли по Белбину в карточке сотрудника
**Файл:** `frontend/src/pages/Employees.tsx`  
В модальное окно создания и редактирования сотрудника:
- Добавить селектор `Роль по Белбину`: Координатор, Реализатор, Мотиватор (Shaper), Генератор идей (Plant), Аналитик, Педант, Душа команды, Исследователь ресурсов, Специалист.
- Убедиться, что навыки сотрудника сохраняются со шкалой уровня от 1 до 5 (целые числа).

### Задача 3.3: Синхронизация отсутствий с фильтрами доступности
**Файл:** `frontend/src/pages/AbsencesCalendar.tsx`  
- Алгоритм Hard Constraints автоматически проверяет `availability_percent` и `has_critical_absence`.
- Убедиться, что утвержденные больничные и отпуска (`status === 'APPROVED'`) корректно уменьшают рабочие часы и доступность сотрудника на период проекта.

---

## 4. Порядок выкатки и интеграционного тестирования

1. Влить ветку `HanyraH` в `main`.
2. **Koroliov862** выполняет задачи 1.1–1.4 (регистрация приложений, миграции, сидер).
3. **Dikiyarbuzz** выполняет задачи 3.1–3.3 (обновление `client.ts` и формы сотрудников).
4. **1-Soul-1** выполняет задачи 2.1–2.4 (селектор пресетов, визуализация рисков, Монте-Карло, Белбин).
5. Сквозная проверка: запуск генерации команды на реальных данных из базы через кнопку «Сформировать команду».
