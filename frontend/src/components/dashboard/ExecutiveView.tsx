import React from 'react';
import { motion } from 'framer-motion';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip
} from 'recharts';
import { AlertTriangle, Shield, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArchitectureDiagram } from './ArchitectureDiagram';

interface ExecutiveStats {
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

interface ExecutiveViewProps {
  summary: string;
  stats?: ExecutiveStats;
}

const COLORS = {
  cyan: '#06b6d4',
  violet: '#8b5cf6',
  red: '#ef4444',
  yellow: '#eab308',
  green: '#22c55e',
  slate: '#94a3b8'
};

const ExecutiveView: React.FC<ExecutiveViewProps> = ({ summary, stats }) => {
  // Parsing radar data for Recharts
  const radarData = stats ? Object.entries(stats.radar_metrics).map(([key, value]) => ({
    subject: key,
    A: value,
    fullMark: 100,
  })) : [];

  // Health Score Color
  const getHealthColor = (score: number) => {
    if (score >= 80) return COLORS.green;
    if (score >= 60) return COLORS.yellow;
    return COLORS.red;
  };

  const healthColor = stats ? getHealthColor(stats.overall_health_score) : COLORS.slate;

  // Donut Chart Data
  const healthData = stats ? [
    { name: 'Score', value: stats.overall_health_score },
    { name: 'Remaining', value: 100 - stats.overall_health_score }
  ] : [];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">

      {/* Top Section: Visual Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Health Score Donut */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-900/50 border border-slate-800 p-6 rounded-xl flex flex-col items-center justify-center relative backdrop-blur-sm"
          >
            <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">Overall Health</h3>
            <div className="h-48 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={healthData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    startAngle={180}
                    endAngle={0}
                    paddingAngle={0}
                    dataKey="value"
                    stroke="none"
                  >
                    <Cell key="score" fill={healthColor} />
                    <Cell key="remaining" fill="#1e293b" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pt-8">
                <span className="text-4xl font-bold text-white">{stats.overall_health_score}</span>
                <span className="text-xs text-slate-500">/ 100</span>
              </div>
            </div>
          </motion.div>

          {/* Architecture Diagram */}
          {stats.architecture_diagram && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="col-span-1 lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-xl p-0 overflow-hidden backdrop-blur-sm shadow-xl shadow-cyan-900/5"
            >
              <ArchitectureDiagram
                chart={stats.architecture_diagram}
                className="h-full border-0 bg-transparent"
              />
            </motion.div>
          )}

          {/* Radar Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-slate-900/50 border border-slate-800 p-6 rounded-xl flex flex-col items-center justify-center backdrop-blur-sm"
          >
            <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-2">Technical Balance</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar
                    name="Project"
                    dataKey="A"
                    stroke={COLORS.cyan}
                    strokeWidth={2}
                    fill={COLORS.cyan}
                    fillOpacity={0.2}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f1f5f9' }}
                    itemStyle={{ color: COLORS.cyan }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Key Metrics Cards */}
          <div className="grid grid-rows-2 gap-6">

            {/* Risk Level */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-slate-900/50 border border-slate-800 p-6 rounded-xl flex items-center justify-between backdrop-blur-sm"
            >
              <div>
                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-1">Risk Level</h3>
                <span className={`text-2xl font-bold ${stats.risk_level === 'Critical' ? 'text-red-500' :
                  stats.risk_level === 'High' ? 'text-orange-500' :
                    stats.risk_level === 'Medium' ? 'text-yellow-500' : 'text-green-500'
                  }`}>
                  {stats.risk_level}
                </span>
              </div>
              <div className={`p-3 rounded-full bg-slate-800/50 ${stats.risk_level === 'Critical' ? 'text-red-500' :
                stats.risk_level === 'High' ? 'text-orange-500' :
                  stats.risk_level === 'Medium' ? 'text-yellow-500' : 'text-green-500'
                }`}>
                {stats.risk_level === 'Low' ? <Shield size={24} /> : <AlertTriangle size={24} />}
              </div>
            </motion.div>

            {/* Tech Debt Estimate */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-slate-900/50 border border-slate-800 p-6 rounded-xl flex items-center justify-between backdrop-blur-sm"
            >
              <div>
                <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-1">Tech Debt</h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-white">{stats.tech_debt_estimate_days}</span>
                  <span className="text-sm text-slate-500">days est.</span>
                </div>
              </div>
              <div className="p-3 rounded-full bg-slate-800/50 text-violet-500">
                <Clock size={24} />
              </div>
            </motion.div>

          </div>
        </div>
      )}

      {/* Text Content */}
      <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-8 backdrop-blur-sm">
        <div className="prose prose-invert max-w-none prose-headings:text-cyan-400 prose-a:text-violet-400">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {summary}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export { ExecutiveView };
