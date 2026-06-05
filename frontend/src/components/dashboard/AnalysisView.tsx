import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { AnalysisResult } from "../../types";
import { GlassCard } from "../ui/GlassCard";
import { Button } from "../ui/Button";
import { FileText, Briefcase, TrendingUp, Download, Clock, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ReportService } from "../../services/api";
import { downloadBlob } from "../../lib/reportDownload";
import { ExecutiveView } from "./ExecutiveView";
import { ArchitectureDiagram } from "./ArchitectureDiagram";

function timestampForFilename(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

interface AnalysisViewProps {
  result: AnalysisResult;
}

const reportProseClass = "report-prose max-w-none";

function ReportMarkdown({ children }: { children: string }) {
  return (
    <div className={reportProseClass}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}

export function AnalysisView({ result }: AnalysisViewProps) {
  const [activeTab, setActiveTab] = useState<"technical" | "executive" | "timeline" | "trends">("technical");
  const [downloading, setDownloading] = useState<"technical" | "executive" | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPdf = async (reportType: "technical" | "executive") => {
    setDownloadError(null);
    setDownloading(reportType);
    try {
      const content =
        reportType === "technical"
          ? result.technical_summary || ""
          : result.executive_summary || "";
      const blob = await ReportService.fetchReportPdf(
        reportType,
        result.repo_url,
        content,
        result.model_used
      );
      const filename = `${reportType}_report_${timestampForFilename()}.pdf`;
      downloadBlob(blob, filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Download failed";
      setDownloadError(message);
    } finally {
      setDownloading(null);
    }
  };

  const tabs = [
    { id: "technical", label: "Technical View", icon: FileText },
    { id: "executive", label: "Executive View", icon: Briefcase },
    { id: "timeline", label: "Timeline", icon: Clock },
    { id: "trends", label: "Trends", icon: TrendingUp },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full space-y-6"
    >
      {/* Header Stats */}
      <GlassCard className="flex flex-wrap items-center justify-between gap-4 p-4">
        <div className="flex items-center gap-4">
          <div className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-mono uppercase">
            Analysis Complete
          </div>
          <span className="text-zinc-400 text-sm">{result.repo_url}</span>
        </div>
        <div className="flex items-center gap-2 text-zinc-500 text-sm">
          <span>Model: {result.model_used || "Unknown"}</span>
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Tabs */}
        <div className="lg:col-span-1 space-y-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === tab.id
                ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20"
                : "text-zinc-400 hover:bg-white/5 hover:text-white border border-transparent"
                }`}
            >
              <tab.icon className="w-5 h-5" />
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}

          <div className="pt-4 mt-4 border-t border-white/5 space-y-2">
            {downloadError && (
              <p className="text-sm text-red-400 px-1">{downloadError}</p>
            )}
            <Button
              variant="outline"
              className="w-full justify-start text-zinc-400"
              onClick={() => handleDownloadPdf("technical")}
              disabled={downloading !== null}
            >
              {downloading === "technical" ? (
                <Loader2 className="w-4 h-4 mr-2 shrink-0 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2 shrink-0" />
              )}
              Technical Report (PDF)
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start text-zinc-400"
              onClick={() => handleDownloadPdf("executive")}
              disabled={downloading !== null}
            >
              {downloading === "executive" ? (
                <Loader2 className="w-4 h-4 mr-2 shrink-0 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2 shrink-0" />
              )}
              Executive Report (PDF)
            </Button>
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3">
          <GlassCard className="min-h-[500px] p-8 md:p-10">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="min-w-0"
              >
                {activeTab === "technical" && (
                  <div>
                    <h2 className="text-2xl font-clash font-bold mb-8 text-white">
                      Technical Architecture
                    </h2>

                    {result.executive_stats?.architecture_diagram && (
                      <div className="mb-10">
                        <ArchitectureDiagram
                          chart={result.executive_stats.architecture_diagram}
                        />
                      </div>
                    )}

                    <ReportMarkdown>
                      {result.technical_summary ||
                        "*No technical summary available.*"}
                    </ReportMarkdown>
                  </div>
                )}
                {activeTab === "executive" && (
                  <div>
                    <h2 className="text-2xl font-clash font-bold mb-8 text-white">
                      Executive Summary
                    </h2>
                    <ExecutiveView
                      summary={result.executive_summary || "*No executive summary available.*"}
                      stats={result.executive_stats}
                    />
                  </div>
                )}
                {activeTab === "timeline" && (
                  <div className="space-y-4">
                    <h2 className="text-2xl font-clash font-bold mb-8 text-white">
                      Analysis Timeline
                    </h2>
                    {result.timeline?.phases ? (
                      <div className="space-y-3">
                        {Object.entries(result.timeline.phases).map(
                          ([name, phase]) => (
                            <div
                              key={name}
                              className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5"
                            >
                              <div className="flex items-center gap-3">
                                <div
                                  className={`w-2.5 h-2.5 rounded-full ${phase.status === "completed"
                                    ? "bg-green-500"
                                    : "bg-red-500"
                                    }`}
                                />
                                <span className="capitalize font-medium text-white">
                                  {name.replace(/_/g, " ")}
                                </span>
                              </div>
                              <span className="font-mono text-sm text-zinc-500">
                                {phase.duration_seconds?.toFixed(2)}s
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      <p className="text-zinc-500">No timeline data available.</p>
                    )}
                  </div>
                )}
                {activeTab === "trends" && (
                  <div>
                    <h2 className="text-2xl font-clash font-bold mb-8 text-white">
                      Trend Intelligence
                    </h2>
                    {result.trend_data ? (
                      <div className="space-y-6">
                        <div className="flex flex-wrap gap-2">
                          {result.trend_data.tags_searched?.map((tag) => (
                            <span
                              key={tag}
                              className="px-3 py-1.5 bg-indigo-500/10 text-indigo-300 rounded-lg text-xs font-medium border border-indigo-500/20"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                        <ReportMarkdown>
                          {result.trend_data.context ||
                            "No trend context available."}
                        </ReportMarkdown>
                      </div>
                    ) : (
                      <p className="text-zinc-500">
                        No specific trend data returned for this repository.
                      </p>
                    )}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </GlassCard>
        </div>
      </div>
    </motion.div>
  );
}
