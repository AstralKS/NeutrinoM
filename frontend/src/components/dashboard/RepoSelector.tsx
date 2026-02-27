import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../ui/Button";
import { GlassCard } from "../ui/GlassCard";
import {
    Github,
    Link,
    Lock,
    Search,
    Star,
    GitBranch,
    Loader2,
    AlertCircle,
} from "lucide-react";
import { UserService } from "../../services/api";
import { useAuth } from "../../contexts/AuthProvider";
import type { GitHubRepo } from "../../types";

interface RepoSelectorProps {
    onAnalyze: (url: string, token?: string) => void;
    isLoading: boolean;
}

type Tab = "url" | "import";

export function RepoSelector({ onAnalyze, isLoading }: RepoSelectorProps) {
    const [activeTab, setActiveTab] = useState<Tab>("url");
    const [url, setUrl] = useState("");
    const [token, setToken] = useState("");
    const [showToken, setShowToken] = useState(false);

    // GitHub import state
    const { user, session } = useAuth();
    const [repos, setRepos] = useState<GitHubRepo[]>([]);
    const [reposLoading, setReposLoading] = useState(false);
    const [reposError, setReposError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

    // Fetch GitHub repos when import tab is selected
    useEffect(() => {
        if (activeTab === "import" && user && repos.length === 0 && !reposLoading) {
            fetchRepos();
        }
    }, [activeTab, user]);

    const fetchRepos = async () => {
        setReposLoading(true);
        setReposError(null);
        try {
            // Pass the provider token from the session (if available)
            // This is critical because backend can't always retrieve it from identity
            const githubToken = session?.provider_token;
            const data = await UserService.getGithubRepos(1, 100, githubToken ?? undefined);
            setRepos(data.repos);
        } catch (err: any) {
            console.error("Failed to fetch repos:", err);
            setReposError(
                err?.response?.data?.detail ||
                "Failed to load repositories. Ensure GitHub is your login provider."
            );
        } finally {
            setReposLoading(false);
        }
    };

    const filteredRepos = useMemo(() => {
        if (!searchQuery) return repos;
        const q = searchQuery.toLowerCase();
        return repos.filter(
            (r) =>
                r.name.toLowerCase().includes(q) ||
                r.full_name.toLowerCase().includes(q) ||
                r.description?.toLowerCase().includes(q) ||
                r.language?.toLowerCase().includes(q)
        );
    }, [repos, searchQuery]);

    const handleUrlSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (url) onAnalyze(url, token || undefined);
    };

    const handleRepoSelect = (repo: GitHubRepo) => {
        // Pass the provider token if available (needed for private repos)
        const token = session?.provider_token;
        if (repo.private && !token) {
            // Optional: warn user if trying to analyze private repo without token
            console.warn("Analyzing private repo but no provider token found");
        }
        onAnalyze(repo.html_url, token ?? undefined);
    };

    const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
        { key: "url", label: "Paste URL", icon: <Link className="w-4 h-4" /> },
        { key: "import", label: "Import", icon: <Github className="w-4 h-4" /> },
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl mx-auto"
        >
            <GlassCard className="p-8">
                {/* Header */}
                <div className="flex flex-col items-center text-center mb-6">
                    <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center mb-4">
                        <Github className="w-6 h-6 text-indigo-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Analyze a Repository</h2>
                    <p className="text-zinc-400 text-sm">
                        Paste a URL or import directly from your GitHub account.
                    </p>
                </div>

                {/* Tab Bar */}
                <div className="flex bg-black/40 rounded-xl p-1 mb-6 border border-white/5">
                    {tabs.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${activeTab === tab.key
                                ? "bg-indigo-600/80 text-white shadow-lg shadow-indigo-500/20"
                                : "text-zinc-400 hover:text-white"
                                }`}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <AnimatePresence mode="wait">
                    {activeTab === "url" ? (
                        <motion.form
                            key="url-tab"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 10 }}
                            transition={{ duration: 0.2 }}
                            onSubmit={handleUrlSubmit}
                            className="space-y-4"
                        >
                            <div className="relative">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                                <input
                                    type="url"
                                    placeholder="https://github.com/owner/repository"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                                    required
                                />
                            </div>

                            <div>
                                <button
                                    type="button"
                                    onClick={() => setShowToken(!showToken)}
                                    className="text-sm text-zinc-500 hover:text-indigo-400 flex items-center gap-2 mb-2 transition-colors"
                                >
                                    <Lock className="w-3 h-3" />
                                    {showToken ? "Hide Access Token" : "Add Private Repo Token"}
                                </button>

                                {showToken && (
                                    <motion.input
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        type="password"
                                        placeholder="ghp_xxxxxxxxxxxx"
                                        value={token}
                                        onChange={(e) => setToken(e.target.value)}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-sm"
                                    />
                                )}
                            </div>

                            <Button
                                type="submit"
                                variant="primary"
                                size="lg"
                                className="w-full mt-4"
                                isLoading={isLoading}
                                disabled={!url || isLoading}
                            >
                                {isLoading ? "Analyzing..." : "Start Analysis"}
                            </Button>
                        </motion.form>
                    ) : (
                        <motion.div
                            key="import-tab"
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            transition={{ duration: 0.2 }}
                            className="space-y-4"
                        >
                            {!user ? (
                                <div className="text-center py-8 text-zinc-400">
                                    <Github className="w-10 h-10 mx-auto mb-3 text-zinc-600" />
                                    <p className="mb-2">Sign in with GitHub to import repos</p>
                                    <p className="text-xs text-zinc-600">
                                        Go to the login page to connect your GitHub account.
                                    </p>
                                </div>
                            ) : (
                                <>
                                    {/* Search */}
                                    <div className="relative">
                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                                        <input
                                            type="text"
                                            placeholder="Search your repositories..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="w-full bg-black/40 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-sm"
                                        />
                                    </div>

                                    {/* Repos List */}
                                    <div className="max-h-[340px] overflow-y-auto space-y-2 pr-1 scrollbar-thin">
                                        {reposLoading ? (
                                            <div className="flex items-center justify-center py-12 text-zinc-400">
                                                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                                                Loading repositories...
                                            </div>
                                        ) : reposError ? (
                                            <div className="flex items-center gap-3 py-6 px-4 text-red-300 bg-red-500/10 rounded-xl border border-red-500/20">
                                                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                                <p className="text-sm">{reposError}</p>
                                            </div>
                                        ) : filteredRepos.length === 0 ? (
                                            <div className="text-center py-8 text-zinc-500 text-sm">
                                                {searchQuery
                                                    ? "No repositories match your search."
                                                    : "No repositories found."}
                                            </div>
                                        ) : (
                                            filteredRepos.map((repo) => (
                                                <button
                                                    key={repo.id}
                                                    onClick={() => handleRepoSelect(repo)}
                                                    disabled={isLoading}
                                                    className="w-full text-left p-4 rounded-xl bg-black/30 border border-white/5 hover:border-indigo-500/40 hover:bg-indigo-500/5 transition-all group disabled:opacity-50 disabled:pointer-events-none"
                                                >
                                                    <div className="flex items-start justify-between gap-3">
                                                        <div className="min-w-0 flex-1">
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <GitBranch className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
                                                                <span className="font-medium text-white text-sm truncate group-hover:text-indigo-300 transition-colors">
                                                                    {repo.full_name}
                                                                </span>
                                                                {repo.private && (
                                                                    <Lock className="w-3 h-3 text-amber-500 flex-shrink-0" />
                                                                )}
                                                            </div>
                                                            {repo.description && (
                                                                <p className="text-xs text-zinc-500 line-clamp-1 ml-5.5">
                                                                    {repo.description}
                                                                </p>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-3 text-xs text-zinc-500 flex-shrink-0">
                                                            {repo.language && (
                                                                <span className="flex items-center gap-1">
                                                                    <span className="w-2 h-2 rounded-full bg-indigo-400" />
                                                                    {repo.language}
                                                                </span>
                                                            )}
                                                            {repo.stargazers_count > 0 && (
                                                                <span className="flex items-center gap-1">
                                                                    <Star className="w-3 h-3" />
                                                                    {repo.stargazers_count}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </GlassCard>
        </motion.div>
    );
}
