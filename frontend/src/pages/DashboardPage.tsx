import { useState } from "react";
import { Navbar } from "../components/layout/Navbar";
import { Footer } from "../components/layout/Footer";
import { RepoSelector } from "../components/dashboard/RepoSelector";
import { AnalysisView } from "../components/dashboard/AnalysisView";
import { AnalysisService } from "../services/api";
import type { AnalysisResult } from "../types";
import { AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

export function DashboardPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (url: string, token?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      // Check health first (optional but good for UX)
      const isHealthy = await AnalysisService.checkHealth();
      if (!isHealthy) {
        throw new Error("Backend API is unreachable. Please ensure the server is running.");
      }

      const data = await AnalysisService.analyzeRepo({ repo_url: url, github_token: token });

      if (data.success) {
        setResult(data);
      } else {
        throw new Error(data.message || "Analysis failed unexpectedly.");
      }
    } catch (err: any) {
      console.error(err);
      const backendMessage = err.response?.data?.detail;
      setError(backendMessage || err.message || "An error occurred during analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-black min-h-screen text-white flex flex-col">
      <Navbar />

      <main className="flex-grow container mx-auto px-6 py-24 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <h1 className="text-4xl font-clash font-bold mb-4">Repository Intelligence</h1>
          <p className="text-zinc-400">Generate deep technical and executive insights in minutes.</p>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl mx-auto mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-200"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p>{error}</p>
          </motion.div>
        )}

        {!result ? (
          <div className="flex gap-8 justify-center">
            {/* Repo Selector */}
            <div className="flex-1 min-w-0 max-w-2xl mx-auto">
              <RepoSelector onAnalyze={handleAnalyze} isLoading={isLoading} />
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <button
              onClick={() => setResult(null)}
              className="text-sm text-zinc-500 hover:text-white transition-colors mb-4"
            >
              ← Analyze another repository
            </button>
            <AnalysisView result={result} />
          </div>
        )}
      </main>

      {/* Decorative Background */}
      <div className="fixed top-0 left-0 right-0 h-screen overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[100px]" />
      </div>

      <Footer />
    </div>
  );
}
