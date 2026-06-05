export interface ProStat {
  id: string; // e.g., "health", "roi", "risk"
  label: string;
  value: string | number;
  trend: string; // e.g., "+12%", "Critical"
  trend_direction: 'up' | 'down' | 'neutral';
}

export interface DeepSection {
  title: string;
  detailed_markdown: string;
  associated_stat?: ProStat | null;
}

export interface ExecutiveStats {
  overall_health_score: number;
  radar_metrics: {
    Security: number;
    Scalability: number;
    Maintainability: number;
    Performance: number;
    Modernity: number;
  };
  tech_debt_estimate_days: number;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  architecture_diagram?: string;
  tldr_strip?: Record<string, string>;
  sections?: DeepSection[];
}

export interface AnalysisResult {
  success: boolean;
  message: string;
  repo_url: string;
  analysis_id?: string;
  model_used?: string;
  technical_summary: string;
  executive_summary: string;
  executive_stats?: ExecutiveStats;
  timeline?: {
    total_duration_seconds: number;
    phases: Record<string, {
      status: string;
      duration_seconds: number;
      error?: string;
    }>;
  };
  api_call_timings?: number[];
  trend_data?: {
    tags_searched: string[];
    context: string;
  };
}

export interface AnalyzeRequest {
  repo_url: string;
  github_token?: string;
}

export interface HistoryItem {
  id: string;
  repo_url: string;
  repo_name: string;
  analyzed_at: string;
  model_used: string;
  technical_summary: string;
  executive_summary: string;
  created_at: string;
  executive_stats?: ExecutiveStats;
  user_id?: string;
  timeline?: AnalysisResult['timeline'];
  trend_data?: AnalysisResult['trend_data'];
  api_call_timings?: number[];
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  html_url: string;
  description: string | null;
  language: string | null;
  stargazers_count: number;
  updated_at: string | null;
  private: boolean;
}
