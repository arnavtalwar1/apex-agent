export type TaskStatus =
  | "pending"
  | "awaiting_approval"
  | "planning"
  | "researching"
  | "executing"
  | "reflecting"
  | "completed"
  | "failed"
  | "rejected";

export interface Task {
  id: number;
  user_id?: number;
  title: string | null;
  goal: string;
  status: TaskStatus | string;
  plan: string | null;
  current_node: string | null;
  reflection_count: number;
  final_output: string | null;
  requires_approval?: boolean;
  approval_status?: string;
  token_cost?: number;
  trace_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

export interface AgentLogEntry {
  timestamp: string;
  agent: "supervisor" | "planner" | "researcher" | "executor" | "reflector" | "system" | string;
  message: string;
  details?: string;
}
