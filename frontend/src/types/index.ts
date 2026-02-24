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
  trend_data?: {
    tags_searched: string[];
    context: string;
  };
}

export interface AnalyzeRequest {
  repo_url: string;
  access_token?: string;
}
