import { motion } from "framer-motion";
import { GlassCard } from "../ui/GlassCard";
import { Shield, Zap, Layout, Code2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Feature = {
  title: string;
  description: string;
  icon: LucideIcon;
  align: "left" | "right";
};

const features: Feature[] = [
  {
    title: "Deep Technical Analysis",
    description:
      "Our AI agents parse every file, dependency, and configuration to build a complete mental model of your architecture. No more guessing how services interact.",
    icon: Code2,
    align: "left",
  },
  {
    title: "Executive Intelligence",
    description:
      "Translate complex technical debt into business risk. Get automated reports that explain the why behind the what for non-technical stakeholders.",
    icon: Layout,
    align: "right",
  },
  {
    title: "Security & Scalability",
    description:
      "Identify vulnerabilities and bottlenecks before they become incidents. We benchmark your repo against industry standards for performance and safety.",
    icon: Shield,
    align: "left",
  },
  {
    title: "Instant Roadmap",
    description:
      "Turn analysis into action with prioritized tickets and refactoring plans that your team can execute immediately.",
    icon: Zap,
    align: "right",
  },
];

export function FeaturesSection() {
  return (
    <section className="relative py-32 bg-black overflow-hidden">
      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-24"
        >
          <h2 className="text-4xl md:text-5xl font-clash font-bold text-white mb-6">
            Beyond Static Analysis
          </h2>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
            Most tools just lint your code. We understand it.
          </p>
        </motion.div>

        <div className="flex flex-col gap-24">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8 }}
                className={`flex flex-col md:flex-row items-center gap-12 ${
                  feature.align === "right" ? "md:flex-row-reverse" : ""
                }`}
              >
                <div className="flex-1">
                  <GlassCard className="p-12 md:p-16 relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <Icon className="w-16 h-16 text-indigo-400 mb-8" />
                    <div className="h-40 w-full bg-white/5 rounded-lg border border-white/5 backdrop-blur-sm" />
                  </GlassCard>
                </div>
                <div className="flex-1 space-y-6">
                  <h3 className="text-3xl font-bold text-white">{feature.title}</h3>
                  <p className="text-lg text-zinc-400 leading-relaxed">
                    {feature.description}
                  </p>
                  <span className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-2 group cursor-default">
                    Learn more <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
