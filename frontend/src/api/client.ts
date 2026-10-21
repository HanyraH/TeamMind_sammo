/**
 * TeamMind API Client
 * Provides typed methods for REST endpoints across all 6 domain apps.
 */
import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// ── 1. Employees & Organization (TZ §6.2, §7.6) ──
export interface EmployeeItem {
  id: string;
  tab_number: string;
  name: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  department: string;
  department_code?: string;
  position: string;
  grade: string;
  load: number;
  skills: string[];
  chronotype: string;
  chronotype_code?: string;
  work_format: string;
  status: string;
  status_code?: string;
  email: string;
  phone: string;
  weekly_capacity: number;
  years_experience: number;
}

export interface EmployeeDetailProfile {
  basic_info: {
    id: string;
    tab_number: string;
    full_name: string;
    first_name: string;
    last_name: string;
    middle_name?: string;
    department: string;
    position: string;
    grade: string;
    status: string;
    birth_date: string;
    hire_date: string;
    location_city: string;
    location_country: string;
    timezone: string;
    email: string;
    phone: string;
    years_experience: number;
  };
  skills_matrix: Array<{
    skill_name: string;
    skill_type: string;
    level: number;
    is_verified: boolean;
    verification_source: string;
  }>;
  workload_info: {
    current_load_percent: number;
    weekly_hours_norm: number;
    daily_hours_available: number;
    active_tasks_count: number;
    active_projects: Array<{
      project_code: string;
      project_name: string;
      task_title: string;
      status: string;
      progress: number;
    }>;
  };
  absences: Array<{
    id: string;
    type: string;
    start_date: string;
    end_date: string;
    working_days: number;
    status: string;
    reason: string;
  }>;
  schedule: {
    chronotype: string;
    chronotype_code: string;
    work_format: string;
    work_day_start: string;
    work_day_end: string;
    meetings_before_noon: boolean;
    meetings_after_18: boolean;
    communication_style: string;
  };
  colleague_compatibility: Array<{
    colleague_name: string;
    colleague_position: string;
    pref_type: string;
    reason: string;
  }>;
  equipment: Array<{
    item: string;
    serial: string;
    status: string;
  }>;
  documents: Array<{
    title: string;
    doc_number: string;
    date: string;
    status: string;
  }>;
  audit_history: Array<{
    date: string;
    action: string;
    actor: string;
  }>;
}

export const getEmployees = async (params?: { search?: string; department?: string; status?: string }) => {
  const { data } = await api.get('/org/employees/', { params });
  return data;
};

export const getEmployeeDetail = async (id: string): Promise<EmployeeDetailProfile> => {
  const { data } = await api.get(`/org/employees/${id}/`);
  return data;
};

export const createEmployee = async (payload: any) => {
  const { data } = await api.post('/org/employees/', payload);
  return data;
};

// ── 2. Projects & Tasks (TZ §6.6, §7.8) ──
export interface ProjectItem {
  id: string;
  code: string;
  name: string;
  description: string;
  status: string;
  status_code: string;
  priority: string;
  priority_code: string;
  period: string;
  planned_start: string;
  planned_end: string;
  budget_hours: number;
  roles: string[];
  teamSize: number;
  progress: number;
}

export const getProjects = async (): Promise<ProjectItem[]> => {
  const { data } = await api.get('/projects/');
  return data;
};

export const createProject = async (payload: any) => {
  const { data } = await api.post('/projects/', payload);
  return data;
};

export const getGanttTasks = async () => {
  const { data } = await api.get('/projects/gantt/');
  return data;
};

// ── 3. Absences Calendar (TZ §6.3, §7.7 — 16 типов) ──
export interface AbsenceEvent {
  id: string;
  title: string;
  employee_name: string;
  department?: string;
  position?: string;
  start: string;
  end: string;
  type: string;
  type_display: string;
  color: string;
  status: string;
  status_display: string;
  reason?: string;
  working_days: number;
  availability_percent: number;
}


export const getAbsences = async (): Promise<AbsenceEvent[]> => {
  const { data } = await api.get('/absences/calendar/');
  return data;
};

export const submitAbsence = async (payload: any) => {
  const { data } = await api.post('/absences/submit/', payload);
  return data;
};

// ── 4. Algorithm & What-If Simulation (TZ §6.8) ──
export interface AlgoMember {
  id: string;
  name: string;
  position?: string;
  role_assigned?: string;
  role?: string;
  chronotype: string;
  chronotype_display?: string;
  final_score?: number;
  score?: number;
  current_load_percent?: number;
  score_breakdown?: {
    total_score: number;
    k_score: number;
    a_score: number;
    l_score: number;
    t_score: number;
    c_score: number;
    projected_load: number;
  };
}

export interface AlgoVariant {
  variant_id: number;
  strategy_name: string;
  strategy_key: string;
  overall_score: number;
  skills_coverage: number;
  avg_availability: number;
  avg_load: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  members: AlgoMember[];
  explanation?: string;
}

export const runTeamMatch = async (payload: {
  project_id?: string;
  weights?: { K: number; A: number; L: number; T: number; C: number };
  count?: number;
}) => {
  const { data } = await api.post('/algorithm/match/', payload);
  return data;
};

export const getWhatIfCandidates = async (excludeIds: string[] = []) => {
  const { data } = await api.get('/algorithm/what-if/', {
    params: { exclude_ids: excludeIds },
  });
  return data.candidates || [];
};

export const runWhatIfSwap = async (payload: {
  current_team: any[];
  old_id: string;
  candidate_id?: string;
  candidate?: any;
  weights?: any;
}) => {
  const { data } = await api.post('/algorithm/what-if/', payload);
  return data;
};

// ── 5. Analytics & KPI (TZ §6.7, §7.9) ──
export interface DashboardKpiData {
  kpis: Array<{
    id: string;
    label: string;
    value: string | number;
    trend: string;
    type: string;
  }>;
  department_loads: Array<{
    department: string;
    code?: string;
    count: number;
    load: number;
    is_overloaded: boolean;
  }>;
  workload_distribution: {
    underloaded: number;
    optimal: number;
    overloaded: number;
    total: number;
  };
  chronotypes: {
    lark: number;
    owl: number;
    intermediate: number;
    pigeon: number;
  };
}

export const getDashboardKpi = async (): Promise<DashboardKpiData> => {
  const { data } = await api.get('/analytics/kpi/');
  return data;
};

export const downloadAnalyticsReport = () => {
  window.open('/api/v1/analytics/export/', '_blank');
};
