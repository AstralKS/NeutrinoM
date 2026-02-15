import { motion } from "framer-motion";
import { GlassCard } from "../ui/GlassCard";

import codeAnalysisImg from "../../assets/image.png";
import executiveIntelImg from "../../assets/image2.png";
import securityScaleImg from "../../assets/image1.png";
import instantRoadmapImg from "../../assets/image4.png";

type Feature = {
  title: string;
  description: string;
  image: string;
  align: "left" | "right";
  accentGradient: string;
  glowColor: string;
};

const features: Feature[] = [
  {
    title: "Deep Technical Analysis",
    description:
      "Our AI agents parse every file, dependency, and configuration to build a complete mental model of your architecture. No more guessing how services interact.",
    image: codeAnalysisImg,
    align: "left",
    accentGradient: "from-indigo-500/20 via-purple-500/10 to-transparent",
    glowColor: "shadow-indigo-500/20",
  },
  {
    title: "Executive Intelligence",
    description:
      "Translate complex technical debt into business risk. Get automated reports that explain the why behind the what for non-technical stakeholders.",
    image: executiveIntelImg,
    align: "right",
    accentGradient: "from-cyan-500/20 via-blue-500/10 to-transparent",
    glowColor: "shadow-cyan-500/20",
  },
  {
    title: "Security & Scalability",
    description:
      "Identify vulnerabilities and bottlenecks before they become incidents. We benchmark your repo against industry standards for performance and safety.",
    image: securityScaleImg,
    align: "left",
    accentGradient: "from-emerald-500/20 via-teal-500/10 to-transparent",
    glowColor: "shadow-emerald-500/20",
  },
  {
    title: "Instant Roadmap",
    description:
      "Turn analysis into action with prioritized tickets and refactoring plans that your team can execute immediately.",
    image: instantRoadmapImg,
    align: "right",
    accentGradient: "from-violet-500/20 via-fuchsia-500/10 to-transparent",
    glowColor: "shadow-violet-500/20",
  },
];

export function FeaturesSection() {
  return (
    <section className="relative py-32 bg-black overflow-hidden">
      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-28"
        >
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-mono text-indigo-200 tracking-wide uppercase mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            Capabilities
          </motion.span>

          <h2 className="text-5xl md:text-7xl font-clash font-bold text-white mb-6 leading-tight">
            Beyond Static Analysis
          </h2>
          <p className="text-xl md:text-2xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Most tools just lint your code. We understand it.
          </p>
        </motion.div>

        {/* Feature Rows */}
        <div className="flex flex-col gap-32">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.7, ease: "easeOut" }}
              className={`flex flex-col md:flex-row items-center gap-14 ${
                feature.align === "right" ? "md:flex-row-reverse" : ""
              }`}
            >
              {/* Image Card */}
              <div className="flex-1 w-full">
                <GlassCard className="p-6 relative overflow-hidden group hover:border-white/10 transition-all duration-500">
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${feature.accentGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                  />
                  <div className="relative z-10">
                    <motion.img
                      src={feature.image}
                      alt={feature.title}
                      className={`w-full h-auto rounded-xl object-cover shadow-2xl ${feature.glowColor} group-hover:shadow-3xl transition-shadow duration-500`}
                      whileHover={{ scale: 1.02 }}
                      transition={{ duration: 0.4, ease: "easeOut" }}
                      loading="lazy"
                    />
                  </div>
                </GlassCard>
              </div>

              {/* Text Content */}
              <div className="flex-1 space-y-6">
                <h3 className="text-3xl md:text-5xl font-clash font-bold text-white leading-tight">
                  {feature.title}
                </h3>
                <p className="text-lg md:text-xl text-zinc-400 leading-relaxed max-w-lg">
                  {feature.description}
                </p>
                <span className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-2 group/link cursor-default text-base">
                  Learn more{" "}
                  <span className="group-hover/link:translate-x-1.5 transition-transform duration-300">
                    →
                  </span>
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Decorative blurred glows */}
      <div className="absolute top-[20%] -left-40 w-[500px] h-[500px] bg-indigo-600/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[15%] -right-40 w-[400px] h-[400px] bg-cyan-600/5 rounded-full blur-[120px] pointer-events-none" />
    </section>
  );
}
