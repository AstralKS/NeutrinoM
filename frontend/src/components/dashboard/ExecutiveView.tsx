import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip
} from 'recharts';
import { AlertTriangle, Shield, Clock, Loader2, DownloadCloud } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useReactToPrint } from 'react-to-print';
import { ArchitectureDiagram } from './ArchitectureDiagram';
import { ProStatCard } from './ProStatCard';
import type { ExecutiveStats, DeepSection } from '../../types';

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface ExecutiveViewProps {
  summary: string;
  stats?: ExecutiveStats;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const COLORS = {
  cyan: '#06b6d4',
  violet: '#8b5cf6',
  red: '#ef4444',
  yellow: '#eab308',
  green: '#22c55e',
  slate: '#94a3b8',
};

const getHealthColor = (score: number) => {
  if (score >= 80) return COLORS.green;
  if (score >= 60) return COLORS.yellow;
  return COLORS.red;
};

/* ------------------------------------------------------------------ */
/*  PDF Export Configuration                                           */
/* ------------------------------------------------------------------ */
// Handled via useReactToPrint hook inside the component.

/* ------------------------------------------------------------------ */
/*  TL;DR Strip                                                        */
/* ------------------------------------------------------------------ */

function TldrStrip({ data }: { data: Record<string, string> }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-2 md:grid-cols-4 gap-3"
    >
      {Object.entries(data).map(([key, value]) => (
        <div
          key={key}
          className="rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 backdrop-blur-sm"
        >
          <p className="text-[10px] font-medium uppercase tracking-widest text-slate-500">
            {key.replace(/_/g, ' ')}
          </p>
          <p className="mt-1 text-sm font-semibold text-white">{value}</p>
        </div>
      ))}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Interleaved Section Renderer                                       */
/* ------------------------------------------------------------------ */

function InterleavedSection({ section, index }: { section: DeepSection; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="space-y-6"
    >
      <h2 className="text-xl font-semibold text-cyan-400 print:text-cyan-600">{section.title}</h2>

      {section.associated_stat && (
        <div className="mt-2 text-slate-100">
          <ProStatCard stat={section.associated_stat} />
        </div>
      )}

      <div className="prose prose-invert prose-slate max-w-none text-slate-300 leading-relaxed print:prose-p:text-slate-800 print:text-slate-800">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {section.detailed_markdown}
        </ReactMarkdown>
      </div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

const ExecutiveView: React.FC<ExecutiveViewProps> = ({ summary, stats }) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  /* ---- Derived data ---- */
  const radarData = stats
    ? Object.entries(stats.radar_metrics).map(([key, value]) => ({
      subject: key,
      A: value,
      fullMark: 100,
    }))
    : [];

  const healthColor = stats ? getHealthColor(stats.overall_health_score) : COLORS.slate;

  const healthData = stats
    ? [
      { name: 'Score', value: stats.overall_health_score },
      { name: 'Remaining', value: 100 - stats.overall_health_score },
    ]
    : [];

  const hasSections = stats?.sections && stats.sections.length > 0;

  /* ---- PDF handler ---- */
  const generatePdf = useReactToPrint({
    contentRef: reportRef,
    documentTitle: `Executive_Report_${new Date().toISOString().split('T')[0]}`,
    onBeforePrint: () => {
      setExporting(true);
      return Promise.resolve();
    },
    onAfterPrint: () => {
      setExporting(false);
    },
    onPrintError: () => {
      setExporting(false);
    }
  });

  const handleExportPdf = () => {
    if (!exporting) {
      generatePdf();
    }
  };

  /* ---- Render ---- */
  return (
    <div className="space-y-6">
      {/* Download PDF button */}
      <div className="flex justify-end">
        <button
          onClick={handleExportPdf}
          disabled={exporting}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:border-cyan-500/40 hover:bg-cyan-500/10 hover:text-cyan-400 disabled:opacity-50"
        >
          {exporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <DownloadCloud className="h-4 w-4" />
          )}
          {exporting ? 'Generating PDF…' : 'Download PDF'}
        </button>
      </div>

      {/* ===== Exportable Report Container ===== */}
      <div id="executive-report-container" ref={reportRef} className="space-y-8 animate-in fade-in duration-500 pdf-container print:bg-white print:text-black print:p-8">

        {/* ---- Top Section: Visual Dashboard ---- */}
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

        {/* ---- TL;DR Strip ---- */}
        {stats?.tldr_strip && Object.keys(stats.tldr_strip).length > 0 && (
          <TldrStrip data={stats.tldr_strip} />
        )}

        {/* ---- Executive Report Markdown Content ---- */}
        {summary && summary !== "*No executive summary available.*" && (
          <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-8 backdrop-blur-sm">
            <div className="prose prose-invert max-w-none prose-headings:text-cyan-400 prose-a:text-violet-400 print:prose-p:text-slate-800 print:text-slate-800 text-slate-300 leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {summary}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* ---- Architecture Diagram (dedicated bottom section for PDF capture) ---- */}
        {stats?.architecture_diagram && (
          <div className="pdf-arch-section">
            <h2 className="text-lg font-semibold text-cyan-400 mb-4">System Architecture Map</h2>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
              <ArchitectureDiagram
                chart={stats.architecture_diagram}
                title="System Architecture"
                className="border-0 bg-transparent"
              />
            </div>
          </div>
        )}
      </div>

      {/* ===== Print / PDF Styles ===== */}
      <style dangerouslySetInnerHTML={{
        __html: `
        @media print {
          @page { margin: 20mm; size: A4 portrait; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .pdf-container { background: white !important; color: black !important; }
          .pdf-arch-section { display: block !important; page-break-inside: avoid; break-inside: avoid; }
          h2 { color: #0891b2 !important; } /* cyan-600 */
          p, span { color: #1e293b !important; } /* slate-800 */
          /* Hide the interactive upper dashboard in print to focus on the detailed markdown */
          .bg-slate-900\\/50 { background-color: #f1f5f9 !important; border: 1px solid #e2e8f0; } /* lighter slate */
          .text-white { color: #0f172a !important; }
          
          /* Recharts SVGs */
          .recharts-wrapper svg { background-color: transparent !important; }
          
          /* Mermaid Diagram SVGs */
          .mermaid-container svg { background-color: transparent !important; }
        }

        .pdf-container .pdf-arch-section {
          display: none;
        }
      `}} />
    </div>
  );
};

export { ExecutiveView };
