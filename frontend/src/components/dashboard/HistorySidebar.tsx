import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, ExternalLink, Loader2, GitBranch, ChevronLeft, ChevronRight } from "lucide-react";
import { UserService } from "../../services/api";
import type { AnalysisResult, HistoryItem } from "../../types";

interface HistorySidebarProps {
    onSelect: (analysis: AnalysisResult) => void;
    refreshTrigger: number;
    isOpen: boolean;
    onToggle: () => void;
}

export function HistorySidebar({ onSelect, refreshTrigger, isOpen, onToggle }: HistorySidebarProps) {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchHistory();
    }, [refreshTrigger]);

    const fetchHistory = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await UserService.getHistory();
            setHistory(data.analyses);
        } catch (err: any) {
            console.error("Failed to fetch history:", err);
            if (!err.response?.data?.detail?.includes("does not exist")) {
                setError("Failed to load history.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelect = (item: HistoryItem) => {
        const result: AnalysisResult = {
            success: true,
            message: "Loaded from history",
            repo_url: item.repo_url,
            analysis_id: item.id,
            technical_summary: item.technical_summary,
            executive_summary: item.executive_summary,
            executive_stats: item.executive_stats,
            model_used: item.model_used,
            timeline: item.timeline,
            api_call_timings: item.api_call_timings,
            trend_data: item.trend_data,
        };
        onSelect(result);
    };

    const sidebarWidth = isOpen ? 320 : 64; // w-80 (320px) vs collapsed base (64px)

    if (isLoading && history.length === 0) {
        return (
            <motion.div 
                initial={false}
                animate={{ width: sidebarWidth }}
                className="h-full flex flex-col border-r border-white/5 bg-black/20 flex-shrink-0 overflow-hidden"
            >
                <div className="p-3 border-b border-white/5 flex items-center justify-end">
                    <button onClick={onToggle} className="p-1.5 hover:bg-white/10 rounded-md transition-colors text-zinc-400">
                        {isOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>
                </div>
                <div className="flex-1 flex items-center justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
                </div>
            </motion.div>
        );
    }

    if (error && history.length === 0) {
        return (
            <motion.div 
                initial={false}
                animate={{ width: sidebarWidth }}
                className="h-full flex flex-col border-r border-white/5 bg-black/20 flex-shrink-0 overflow-hidden"
            >
                <div className="p-3 border-b border-white/5 flex items-center justify-end">
                    <button onClick={onToggle} className="p-1.5 hover:bg-white/10 rounded-md transition-colors text-zinc-400">
                        {isOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>
                </div>
                {isOpen ? (
                    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                        <p className="text-zinc-500 text-sm mb-4">{error}</p>
                        <button onClick={fetchHistory} className="text-indigo-400 hover:text-indigo-300 text-xs font-medium">Try Again</button>
                    </div>
                ) : (
                    <div className="flex-1 flex items-center justify-center">
                        <span className="text-red-500 font-bold">!</span>
                    </div>
                )}
            </motion.div>
        );
    }

    return (
        <motion.div 
            initial={false}
            animate={{ width: sidebarWidth }}
            className="h-full border-r border-white/5 bg-black/20 flex flex-col flex-shrink-0 overflow-hidden whitespace-nowrap"
        >
            <div className={`p-4 border-b border-white/5 flex items-center ${isOpen ? 'justify-between' : 'justify-center'}`}>
                {isOpen && (
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-zinc-400" />
                        <h3 className="font-medium text-zinc-200">Recent Analyses</h3>
                    </div>
                )}
                <button 
                    onClick={onToggle} 
                    className="p-1.5 hover:bg-white/10 rounded-md transition-colors text-zinc-400"
                    title={isOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                >
                    {isOpen ? <ChevronLeft className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                </button>
            </div>

            <div className={`flex-1 overflow-y-auto w-full scrollbar-thin ${isOpen ? 'p-3 space-y-2' : 'p-2 space-y-3'}`}>
                {history.length === 0 ? (
                    isOpen ? (
                        <div className="text-center py-8 px-4">
                            <p className="text-zinc-500 text-sm">No analysis history yet.</p>
                            <p className="text-zinc-600 text-xs mt-1">Your recent scans will appear here.</p>
                        </div>
                    ) : null
                ) : (
                    history.map((item, i) => (
                        <motion.button
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.05 }}
                            key={item.id}
                            onClick={() => handleSelect(item)}
                            className={`w-full text-left rounded-lg hover:bg-white/5 border border-transparent hover:border-white/10 transition-all group flex flex-col justify-center ${isOpen ? 'p-3 gap-2' : 'p-3 items-center aspect-square'}`}
                            title={!isOpen ? item.repo_name : undefined}
                        >
                            {isOpen ? (
                                <>
                                    <div className="flex items-center justify-between w-full">
                                        <div className="flex items-center gap-2 min-w-0 pr-2">
                                            <GitBranch className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                                            <span className="font-medium text-sm text-zinc-200 truncate group-hover:text-indigo-300 transition-colors">
                                                {item.repo_name}
                                            </span>
                                        </div>
                                        <a
                                            href={item.repo_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="text-zinc-500 hover:text-white flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                            title="View on GitHub"
                                        >
                                            <ExternalLink className="w-3.5 h-3.5" />
                                        </a>
                                    </div>
                                    <div className="flex items-center justify-between text-xs text-zinc-500 w-full mt-1">
                                        <span>{new Date(item.analyzed_at).toLocaleDateString()}</span>
                                        {item.model_used && (
                                            <span className="truncate max-w-[100px] opacity-70">
                                                {item.model_used.split("/").pop()}
                                            </span>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <GitBranch className="w-5 h-5 text-indigo-400 opacity-70 group-hover:opacity-100" />
                            )}
                        </motion.button>
                    ))
                )}
            </div>
        </motion.div>
    );
}
