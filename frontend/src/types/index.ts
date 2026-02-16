export interface AnalysisResult {
  success: boolean;
  message: string;
  repo_url: string;
  analysis_id?: string;
  model_used?: string;
  technical_summary: string;
  executive_summary: string;
  timeline?: {
    total_duration_seconds: number;
    phases: Record<string, {
      status: string;
      duration_seconds: number;
      error?: string;
    }>;
  };
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
  user_id?: string;
  timeline?: Record<string, unknown>;
  trend_data?: Record<string, unknown>;
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
