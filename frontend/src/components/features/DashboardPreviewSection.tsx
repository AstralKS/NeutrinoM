import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FileText, Briefcase, Clock } from "lucide-react";
import { GlassCard } from "../ui/GlassCard";

const MOCK_CARDS = [
  {
    title: "Technical Summary",
    desc: "Architecture, stack, and code quality insights at a glance.",
    icon: FileText,
  },
  {
    title: "Executive Summary",
    desc: "Business risk and opportunity in plain language.",
    icon: Briefcase,
  },
  {
    title: "Timeline & Insights",
    desc: "Phase-by-phase analysis and actionable recommendations.",
    icon: Clock,
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
          <h2 className="text-4xl md:text-5xl font-clash font-bold text-white mb-6">
            From Analysis to Action
          </h2>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
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
              <GlassCard key={index} className="p-8 relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center mb-6">
                    <Icon className="w-6 h-6 text-indigo-400" />
                  </div>
                  <h3 className="text-xl font-clash font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-zinc-400">{item.desc}</p>
                </div>
              </GlassCard>
            );
          })}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mt-12"
        >
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-8 py-4 transition-colors shadow-lg shadow-indigo-500/20 border border-indigo-500/50"
          >
            Open Dashboard
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
