import React from 'react';
import { motion } from 'framer-motion';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer,
} from 'recharts';
import { AlertTriangle, Shield, Clock, Lightbulb, Activity, CheckCircle2, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArchitectureDiagram } from './ArchitectureDiagram';
import type { ExecutiveStats } from '../../types';

interface ExecutiveViewProps {
  summary: string;
  stats?: ExecutiveStats;
}

const COLORS = {
  cyan: '#06b6d4',
  emerald: '#10b981',
  yellow: '#eab308',
  red: '#ef4444',
};

const getVerdict = (score: number) => {
  if (score >= 80) return { title: "Healthy", desc: "No immediate critical actions required. System is stable.", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", glow: "shadow-[0_0_30px_rgba(16,185,129,0.15)]", Icon: CheckCircle2 };
  if (score >= 60) return { title: "Needs Attention", desc: "Moderate tech debt and potential risks detected.", color: "text-yellow-400", bg: "bg-yellow-500/10", border: "border-yellow-500/20", glow: "shadow-[0_0_30px_rgba(234,179,8,0.15)]", Icon: Activity };
  return { title: "Critical Risk", desc: "Immediate action recommended to address structural issues.", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20", glow: "shadow-[0_0_30px_rgba(239,68,68,0.15)]", Icon: AlertTriangle };
};

function TldrStrip({ data }: { data: Record<string, string> }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="grid grid-cols-1 md:grid-cols-2 gap-4"
    >
      {Object.entries(data).map(([key, value]) => {
        const isOpportunity = key.toLowerCase().includes('opportunity');
        const theme = isOpportunity 
          ? { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400', Icon: Zap }
          : { bg: 'bg-violet-500/10', border: 'border-violet-500/30', text: 'text-violet-400', Icon: Lightbulb };

        return (
          <div
            key={key}
            className={`flex items-start gap-4 rounded-2xl border ${theme.border} ${theme.bg} p-6 backdrop-blur-sm shadow-xl`}
          >
            <div className={`p-3 rounded-xl bg-white/5 ${theme.text}`}>
              <theme.Icon className="w-6 h-6" />
            </div>
            <div>
              <h4 className={`text-xs font-bold tracking-wider uppercase mb-1.5 ${theme.text}`}>
                {key.replace(/_/g, ' ')}
              </h4>
              <p className="text-sm font-medium text-slate-200 leading-relaxed">
                {value}
              </p>
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}

const ExecutiveView: React.FC<ExecutiveViewProps> = ({ summary, stats }) => {
  const radarData = stats
    ? Object.entries(stats.radar_metrics).map(([key, value]) => ({
      subject: key,
      A: value,
      fullMark: 100,
    }))
    : [];

  const filteredTldr = stats?.tldr_strip
    ? Object.fromEntries(
        Object.entries(stats.tldr_strip).filter(
          ([k]) => !['health', 'debt', 'risk'].some(skip => k.toLowerCase().includes(skip))
        )
      )
    : {};

  const verdict = stats ? getVerdict(stats.overall_health_score) : null;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      
      {/* 1. HERO VERDICT */}
      {stats && verdict && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`relative overflow-hidden rounded-3xl border ${verdict.border} bg-slate-900/80 backdrop-blur-xl ${verdict.glow}`}
        >
          {/* Subtle gradient background */}
          <div className={`absolute inset-0 opacity-20 bg-gradient-to-br from-transparent to-current ${verdict.color}`} />
          
          <div className="relative p-8 md:p-10 flex flex-col md:flex-row items-center gap-10">
            {/* Health Score Circular Display */}
            <div className="flex-shrink-0 flex flex-col items-center justify-center w-48 h-48 rounded-full border-4 border-white/5 bg-slate-950/50 shadow-inner relative">
              <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                <circle cx="96" cy="96" r="88" stroke="currentColor" strokeWidth="8" fill="none" className="text-slate-800" />
                <circle 
                  cx="96" cy="96" r="88" 
                  stroke="currentColor" 
                  strokeWidth="8" 
                  fill="none" 
                  strokeDasharray="552.92" 
                  strokeDashoffset={552.92 - (552.92 * stats.overall_health_score) / 100}
                  className={`${verdict.color} transition-all duration-1000 ease-out`} 
                />
              </svg>
              <span className={`text-6xl font-bold tracking-tighter ${verdict.color}`}>{stats.overall_health_score}</span>
              <span className="text-xs font-medium tracking-widest text-slate-500 uppercase mt-1">Health</span>
            </div>

            {/* Verdict Info */}
            <div className="flex-grow space-y-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <verdict.Icon className={`w-8 h-8 ${verdict.color}`} />
                  <h2 className={`text-4xl font-black tracking-tight ${verdict.color}`}>{verdict.title}</h2>
                </div>
                <p className="text-lg text-slate-300 font-medium">{verdict.desc}</p>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-3 bg-slate-950/50 border border-white/10 rounded-2xl px-5 py-3">
                  <div className={`p-2 rounded-full ${stats.risk_level === 'Low' ? 'bg-emerald-500/20 text-emerald-400' : stats.risk_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                    {stats.risk_level === 'Low' ? <Shield className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-0.5">Risk Level</p>
                    <p className="text-lg font-bold text-white leading-none">{stats.risk_level}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 bg-slate-950/50 border border-white/10 rounded-2xl px-5 py-3">
                  <div className="p-2 rounded-full bg-violet-500/20 text-violet-400">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-0.5">Est. Tech Debt</p>
                    <p className="text-lg font-bold text-white leading-none">{stats.tech_debt_estimate_days} <span className="text-sm font-medium text-slate-400">days</span></p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* 2. STRATEGIC INSIGHTS (BENTO ROW) */}
      {Object.keys(filteredTldr).length > 0 && (
        <TldrStrip data={filteredTldr} />
      )}

      {/* 3. BLUEPRINT & BALANCE SPLIT */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Architecture Diagram (Left 2/3) */}
          {stats.architecture_diagram && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-3xl p-1 overflow-hidden backdrop-blur-md shadow-xl"
            >
              <div className="bg-slate-950/50 rounded-[28px] h-full flex flex-col overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800/50 flex items-center justify-between bg-slate-900/50">
                  <h3 className="text-slate-300 font-semibold tracking-wide text-sm">System Blueprint</h3>
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/30 border border-red-500/50" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/30 border border-yellow-500/50" />
                    <div className="w-3 h-3 rounded-full bg-green-500/30 border border-green-500/50" />
                  </div>
                </div>
                <div className="flex-grow p-4 min-h-[300px]">
                  <ArchitectureDiagram
                    chart={stats.architecture_diagram}
                    className="h-full border-0 bg-transparent rounded-xl"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {/* Technical Balance (Right 1/3) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className={`bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-md flex flex-col items-center justify-center shadow-xl ${!stats.architecture_diagram ? 'lg:col-span-3' : 'lg:col-span-1'}`}
          >
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">Technical Balance</h3>
            <div className="w-full h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 500 }} />
                  <Radar
                    name="Project"
                    dataKey="A"
                    stroke={COLORS.cyan}
                    strokeWidth={2}
                    fill={COLORS.cyan}
                    fillOpacity={0.25}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        </div>
      )}

      {/* 4. NARRATIVE SUMMARY */}
      {summary && summary !== "*No executive summary available.*" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h3 className="text-slate-400 text-sm font-bold uppercase tracking-widest mb-6 px-2">Executive Briefing</h3>
          <div className="bg-slate-900/30 border border-slate-800/60 rounded-3xl p-8 md:p-12 backdrop-blur-md shadow-2xl">
            <div className="report-prose max-w-none text-lg">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {summary}
              </ReactMarkdown>
            </div>
          </div>
        </motion.div>
      )}

    </div>
  );
};

export { ExecutiveView };
