export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  email: string;
  role: string;
}

export interface DashboardSummary {
  total_conversations: number;
  nps_score: number | null;
  frt_avg_minutes: number | null;
  art_avg_minutes: number | null;
  rating_avg: number | null;
  sla_compliance_pct: number | null;
  total_messages: number;
  unique_contacts: number;
  returning_contacts: number;
}

export interface BSCData {
  header: string[];
  data_t1: (string | number | null)[][];
  data_t2: (string | number | null)[][];
  kpi_config: Record<string, unknown> | null;
}

export interface KPIItem {
  name: string;
  value: number | null;
  meta: string | number | null;
  peso: number;
  score: number | null;
  tipo: string;
}

export interface KPIResponse {
  department: string;
  kpis: KPIItem[];
}

export interface EvolutionMonth {
  year: number;
  month: number;
  label: string;
  total_conversations: number;
  nps_score: number | null;
  art_avg_minutes: number | null;
  frt_avg_minutes: number | null;
  sla_compliance_pct: number | null;
  rating_avg: number | null;
}

export interface EvolutionResponse {
  evolution: EvolutionMonth[];
}

export interface AgentRankingItem {
  rank: number;
  agent_name: string;
  department: string;
  group: string;
  total_chats: number;
  nps_score: number | null;
  rating_avg: number | null;
  art_avg_minutes: number | null;
  frt_avg_minutes: number | null;
  sla_compliance_pct: number | null;
  total_messages: number;
}

export interface AgentRankingResponse {
  agents: AgentRankingItem[];
}

export interface ChannelItem {
  channel_id: string;
  channel_name: string;
  total_conversations: number;
  total_messages: number;
  nps_score: number | null;
  rating_avg: number | null;
}

export interface ChannelResponse {
  channels: ChannelItem[];
}

export interface Message {
  message_id: string;
  direction: string;
  content: string;
  created_at: string;
  agent_id: string | null;
  agent_name: string | null;
}

export interface ConversationItem {
  id: string;
  contact: string;
  phone: string;
  contact_id: number;
  agent: string;
  department: string;
  channel: string;
  status: string;
  start_time: string;
  end_time: string;
  duration_minutes: number | null;
  frt_minutes: number | null;
  art_minutes: number | null;
  rating: number | null;
  nps: number | null;
  msg_count: number;
  reopened_count: number;
}

export interface ConversationListResponse {
  conversations: ConversationItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface ConversationDetail extends ConversationItem {
  messages: Message[];
}

export interface ConversationMessagesResponse {
  conversation_id: string;
  messages: Message[];
  total: number;
}

export interface ReportRequest {
  type: "monthly" | "annual";
  year: number;
  month?: number;
  group?: string;
}

export interface GenerateReportResponse {
  status: string;
  report_id: string;
}

export interface DownloadReportResponse {
  download_url: string;
}

export interface AvailableReportItem {
  report_id: string;
  type: string;
  year: number;
  month?: number;
  group?: string;
  filename: string;
  created_at: string;
}

export interface AvailableReportsResponse {
  reports: AvailableReportItem[];
}

export interface SyncStatus {
  last_sync: string | null;
  status: string;
  records_synced: number;
  duration_seconds: number | null;
  error: string | null;
}

export interface SyncTriggerRequest {
  full_sync?: boolean;
  sync_messages?: boolean;
  messages_days?: number;
  year?: number;
  month?: number;
  backfill_surveys?: boolean;
}

export interface AgentItem {
  bird_id: string;
  name: string;
  group: string;
}

export interface AgentListResponse {
  agents: AgentItem[];
}

export interface DepartmentItem {
  dept_id: number;
  label: string;
}

export interface DepartmentListResponse {
  departments: DepartmentItem[];
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
}
