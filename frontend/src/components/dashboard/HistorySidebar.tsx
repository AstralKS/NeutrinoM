import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    History,
    Calendar,
    GitBranch,
    ChevronRight,
    Loader2,
    FolderOpen,
} from "lucide-react";
import { UserService } from "../../services/api";
import { useAuth } from "../../contexts/AuthProvider";
import type { HistoryItem, AnalysisResult } from "../../types";

interface HistorySidebarProps {
    /** Called when the user clicks a history item */
    onSelectAnalysis: (result: AnalysisResult) => void;
    /** Optional trigger to force refresh history list */
    refreshTrigger?: number;
}

export function HistorySidebar({ onSelectAnalysis, refreshTrigger = 0 }: HistorySidebarProps) {
    const { user } = useAuth();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    useEffect(() => {
        if (user) {
            fetchHistory();
        } else {
            setHistory([]);
            setLoading(false);
        }
    }, [user, refreshTrigger]);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const data = await UserService.getHistory();
            setHistory(data.analyses);
        } catch (err: any) {
            // Silently handle auth errors — user session may not be fully set up
            if (err?.response?.status !== 401 && err?.response?.status !== 403) {
                console.error("Failed to fetch history:", err);
            }
            setHistory([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (item: HistoryItem) => {
        setSelectedId(item.id);
        // Convert HistoryItem to AnalysisResult shape
        onSelectAnalysis({
            success: true,
            message: "Loaded from history",
            repo_url: item.repo_url,
            analysis_id: item.id,
            model_used: item.model_used,
            technical_summary: item.technical_summary,
            executive_summary: item.executive_summary,
            timeline: item.timeline as AnalysisResult["timeline"],
            trend_data: item.trend_data as AnalysisResult["trend_data"],
        });
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return "Today";
        if (diffDays === 1) return "Yesterday";
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    };

    const extractRepoName = (url: string) => {
        try {
            const parts = url.replace(/\.git$/, "").split("/");
            return parts.slice(-2).join("/");
        } catch {
            return url;
        }
    };

    if (!user) return null;

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-full"
        >
            {/* Header */}
            <div className="flex items-center gap-2 mb-4 px-1">
                <History className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">Analysis History</h3>
                <span className="text-xs text-zinc-500 ml-auto">
                    {history.length} {history.length === 1 ? "report" : "reports"}
                </span>
            </div>

            {/* Content */}
            <div className="space-y-1.5 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
                {loading ? (
                    <div className="flex items-center justify-center py-8 text-zinc-500">
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        <span className="text-sm">Loading...</span>
                    </div>
                ) : history.length === 0 ? (
                    <div className="text-center py-8">
                        <FolderOpen className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
                        <p className="text-sm text-zinc-500">No analyses yet</p>
                        <p className="text-xs text-zinc-600 mt-1">
                            Your reports will appear here
                        </p>
                    </div>
                ) : (
                    <AnimatePresence>
                        {history.map((item, index) => (
                            <motion.button
                                key={item.id}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.03 }}
                                onClick={() => handleSelect(item)}
                                className={`w-full text-left p-3 rounded-xl transition-all group ${selectedId === item.id
                                    ? "bg-indigo-500/15 border border-indigo-500/30"
                                    : "bg-white/[0.02] border border-transparent hover:bg-white/[0.05] hover:border-white/5"
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <div className="min-w-0 flex-1">
                                        <div className="flex items-center gap-1.5 mb-1">
                                            <GitBranch className="w-3 h-3 text-zinc-500 flex-shrink-0" />
                                            <span className="text-sm font-medium text-white truncate">
                                                {extractRepoName(item.repo_url)}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-zinc-500">
                                            <Calendar className="w-3 h-3" />
                                            {formatDate(item.created_at)}
                                            <span className="text-zinc-700">•</span>
                                            <span className="truncate">{item.model_used}</span>
                                        </div>
                                    </div>
                                    <ChevronRight
                                        className={`w-4 h-4 flex-shrink-0 transition-all mt-0.5 ${selectedId === item.id
                                            ? "text-indigo-400"
                                            : "text-zinc-700 group-hover:text-zinc-400"
                                            }`}
                                    />
                                </div>
                            </motion.button>
                        ))}
                    </AnimatePresence>
                )}
            </div>
        </motion.div>
    );
}
