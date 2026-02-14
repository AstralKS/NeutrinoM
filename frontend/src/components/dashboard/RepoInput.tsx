import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "../ui/Button";
import { GlassCard } from "../ui/GlassCard";
import { Github, Lock, Search } from "lucide-react";

interface RepoInputProps {
  onAnalyze: (url: string, token?: string) => void;
  isLoading: boolean;
}

export function RepoInput({ onAnalyze, isLoading }: RepoInputProps) {
  const [url, setUrl] = useState("");
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url) onAnalyze(url, token);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto"
    >
      <GlassCard className="p-8">
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center mb-4">
            <Github className="w-6 h-6 text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Analyze a Repository</h2>
          <p className="text-zinc-400">
            Enter a public or private GitHub repository URL to generate insights.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
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
        </form>
      </GlassCard>
    </motion.div>
  );
}
