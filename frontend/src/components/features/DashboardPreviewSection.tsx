import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FileText, Briefcase, Clock, ArrowRight, CheckCircle2 } from "lucide-react";
import { GlassCard } from "../ui/GlassCard";

const MOCK_CARDS = [
  {
    title: "Technical Summary",
    desc: "Architecture, stack, and code quality insights at a glance.",
    icon: FileText,
    highlights: ["Stack detection", "Dependency graph", "Code patterns"],
    accentColor: "from-indigo-500/20 to-purple-500/10",
  },
  {
    title: "Executive Summary",
    desc: "Business risk and opportunity in plain language.",
    icon: Briefcase,
    highlights: ["Risk assessment", "Tech debt score", "Investment ROI"],
    accentColor: "from-cyan-500/20 to-indigo-500/10",
  },
  {
    title: "Timeline & Insights",
    desc: "Phase-by-phase analysis and actionable recommendations.",
    icon: Clock,
    highlights: ["Sprint roadmap", "Priority actions", "Trend analysis"],
    accentColor: "from-purple-500/20 to-cyan-500/10",
  },
] as const;

export function DashboardPreviewSection() {
  return (
    <section className="relative py-32 bg-black overflow-hidden">
      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-mono text-indigo-200 tracking-wide uppercase mb-6"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            Dashboard
          </motion.span>
          <h2 className="text-4xl md:text-6xl font-clash font-bold text-white mb-6">
            From Analysis to Action
          </h2>
          <p className="text-xl md:text-2xl text-zinc-400 max-w-2xl mx-auto">
            Your dashboard surfaces technical and executive insights in one place.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {MOCK_CARDS.map((item, index) => {
            const Icon = item.icon;
            return (
              <GlassCard
                key={index}
                className="p-8 relative overflow-hidden group hover:border-indigo-500/20 transition-all duration-500"
                whileHover={{ y: -4, transition: { duration: 0.3 } }}
              >
                {/* Hover gradient */}
                <div className={`absolute top-0 left-0 w-full h-full bg-gradient-to-br ${item.accentColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                
                <div className="relative z-10">
                  {/* Icon */}
                  <div className="w-14 h-14 rounded-2xl bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center mb-6 group-hover:bg-indigo-500/25 transition-colors">
                    <Icon className="w-7 h-7 text-indigo-400" />
                  </div>

                  {/* Title & Description */}
                  <h3 className="text-2xl font-clash font-bold text-white mb-3">{item.title}</h3>
                  <p className="text-base text-zinc-400 leading-relaxed mb-6">{item.desc}</p>

                  {/* Highlight checklist */}
                  <div className="space-y-2.5 pt-4 border-t border-white/5">
                    {item.highlights.map((h, i) => (
                      <div key={i} className="flex items-center gap-2.5 text-sm text-zinc-300">
                        <CheckCircle2 className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                        <span>{h}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mt-16"
        >
          <Link
            to="/dashboard"
            className="group inline-flex items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-10 py-4 text-lg transition-all shadow-lg shadow-indigo-500/20 border border-indigo-500/50 hover:shadow-indigo-500/40"
          >
            Open Dashboard
            <ArrowRight className="ml-2.5 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      </div>

      {/* Decorative glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-600/5 rounded-full blur-[120px] pointer-events-none" />
    </section>
  );
}
