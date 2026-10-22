// VibeBreaker API Client
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// --- Types ---

export interface CreateSessionRequest {
  code: string;
  title?: string;
}

export interface CreateSessionResponse {
  session_id: string;
  title?: string;
  total_steps: number;
  first_objective: string;
  first_algorithm?: string;
  first_starter_hint?: string;
  step_index: number;
}

export interface SessionStep {
  id: string;
  step_index: number;
  objective: string;
  learning_concept: string | null;
  algorithm?: string;
  starter_hint?: string;
  reference_code?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  hint_level_used: string;
  created_at: string;
  completed_at: string | null;
}

export interface CurrentObjectiveInfo {
  objective: string;
  learning_concept?: string;
  algorithm?: string;
  starter_hint?: string;
}

export interface SessionState {
  session_id: string;
  title: string | null;
  original_code: string;
  language: string;
  created_at: string;
  current_step_index: number;
  status: string;
  steps: SessionStep[];
  total_steps: number;
  current_objective?: CurrentObjectiveInfo;
  progress?: string;
  completed_steps?: number;
  hint_usage?: number;
}

export interface AttemptResponse {
  evaluation_status: 'pass' | 'partial' | 'fail';
  feedback: string;
  next_objective: string | null;
  next_step_index: number | null;
  next_algorithm?: string;
  next_starter_hint?: string;
  is_complete: boolean;
}

export interface HintResponse {
  hint: string;
  level: string;
  step_index: number;
  escalation_ok?: boolean;
}

export interface ReflectionResponse {
  session_id: string;
  patterns_practiced: string[];
  hint_usage: Record<string, number>;
  weak_areas: string[];
  viva_questions: string[];
  completed_steps: number;
  total_steps: number;
}

export interface RevealCodeResponse {
  session_id: string;
  step_index: number;
  reference_code: string;
  full_code: string;
}

// --- API Functions ---

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  // Support both direct base URL and local rewrite proxy
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${res.status}`);
  }

  return res.json();
}

export async function createSession(code: string, title?: string): Promise<CreateSessionResponse> {
  return apiFetch<CreateSessionResponse>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ code, title }),
  });
}

export async function generateSessionFromPrompt(prompt: string, title?: string): Promise<CreateSessionResponse> {
  return apiFetch<CreateSessionResponse>('/api/sessions/generate', {
    method: 'POST',
    body: JSON.stringify({ prompt, title }),
  });
}

export async function getSession(sessionId: string): Promise<SessionState> {
  return apiFetch<SessionState>(`/api/sessions/${sessionId}`);
}

export async function submitAttempt(sessionId: string, studentCode: string): Promise<AttemptResponse> {
  return apiFetch<AttemptResponse>(`/api/sessions/${sessionId}/attempt`, {
    method: 'POST',
    body: JSON.stringify({ student_code: studentCode, code: studentCode }),
  });
}

export async function requestHint(sessionId: string, level: 'conceptual' | 'narrower' | 'code'): Promise<HintResponse> {
  return apiFetch<HintResponse>(`/api/sessions/${sessionId}/hint`, {
    method: 'POST',
    body: JSON.stringify({ level, hint_level: level }),
  });
}

export async function revealReferenceCode(sessionId: string, stepIndex?: number): Promise<RevealCodeResponse> {
  return apiFetch<RevealCodeResponse>(`/api/sessions/${sessionId}/reveal-code`, {
    method: 'POST',
    body: JSON.stringify({ step_index: stepIndex }),
  });
}

export async function finishSession(sessionId: string): Promise<ReflectionResponse> {
  return apiFetch<ReflectionResponse>(`/api/sessions/${sessionId}/finish`, {
    method: 'POST',
  });
}
