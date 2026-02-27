import axios from "axios";
import type { AnalysisResult, AnalyzeRequest, HistoryItem, GitHubRepo } from "../types";
import { supabase } from "./supabase";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 1200000, // 20 minutes (same as Streamlit app)
});

// Interceptor: attach Supabase JWT to all outgoing requests
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export const AnalysisService = {
  checkHealth: async (): Promise<boolean> => {
    try {
      const response = await api.get("/health");
      return response.status === 200;
    } catch (error) {
      console.error("API Health Check Failed:", error);
      return false;
    }
  },

  analyzeRepo: async (data: AnalyzeRequest): Promise<AnalysisResult> => {
    const response = await api.post("/analyze", data);
    return response.data;
  },
};

export const UserService = {
  /** Fetch the authenticated user's analysis history */
  getHistory: async (): Promise<{ analyses: HistoryItem[]; count: number }> => {
    const response = await api.get("/user/history");
    return response.data;
  },

  /** Fetch the user's GitHub repos (requires GitHub OAuth) */
  getGithubRepos: async (page = 1, perPage = 30, githubToken?: string): Promise<{ repos: GitHubRepo[]; count: number }> => {
    const headers: Record<string, string> = {};
    if (githubToken) {
      headers["X-GitHub-Token"] = githubToken;
    }
    const response = await api.get("/user/github/repos", {
      params: { page, per_page: perPage },
      headers,
    });
    return response.data;
  },
};

export type ReportType = "technical" | "executive";

export const ReportService = {
  /**
   * Request a PDF report from the backend. Returns the PDF as a Blob.
   */
  fetchReportPdf: async (
    reportType: ReportType,
    repoUrl: string,
    content: string,
    modelUsed?: string
  ): Promise<Blob> => {
    const response = await api.post(
      "/report/pdf",
      {
        report_type: reportType,
        repo_url: repoUrl,
        content,
        model_used: modelUsed ?? null,
      },
      { responseType: "blob" }
    );
    return response.data as Blob;
  },
};
