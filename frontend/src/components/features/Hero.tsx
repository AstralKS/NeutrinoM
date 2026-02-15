import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Button } from "../ui/Button";
import { ArrowRight } from "lucide-react";

const HERO_VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260207_050933_33e2620d-09cd-43a2-80ef-4cdbb42f4194.mp4";

const FLOATING_FEATURES = [
  {
    title: "Connect GitHub Repository",
    desc: "Paste a public or private repo URL to start analysis.",
  },
  {
    title: "AI-Powered Stack Detection",
    desc: "Automatically detects architecture, tools, and frameworks.",
  },
  {
    title: "Risk & Gap Identification",
    desc: "Security, testing, and scalability issues highlighted instantly.",
  },
  {
    title: "Actionable Roadmap",
    desc: "Get prioritized technical and executive recommendations.",
  },
] as const;

export function Hero() {
  return (
    <section className="relative min-h-screen w-full overflow-hidden flex flex-col items-center justify-center text-center bg-black lg:pb-64">
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-black/60 z-10" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-transparent to-black z-10" />
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover scale-[1.5] origin-top-left opacity-60"
        >
          <source src={HERO_VIDEO_SRC} type="video/mp4" />
        </video>
      </div>

      <div className="container relative z-20 px-6 pt-24 pb-40">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="max-w-4xl mx-auto flex flex-col items-center"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-xs font-mono text-indigo-200 tracking-wide uppercase">
              Real-Time Repository Intelligence
            </span>
          </motion.div>

          <h1 className="text-6xl md:text-8xl font-clash font-bold tracking-tight text-white mb-8 leading-[1.08]">
            Understand Any <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-200 to-white text-glow">
              Codebase in Minutes
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-zinc-400 max-w-2xl mb-12 leading-relaxed font-light">
            Turn complex repositories into clear technical and executive insights powered by AI.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <Link to="/dashboard">
              <Button size="lg" className="group rounded-full pl-8 pr-6">
                Analyze a Repository
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform inline-block" />
              </Button>
            </Link>
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="absolute bottom-[20vh] left-0 right-0 z-20 hidden lg:block shrink-0"
      >
        <div className="container mx-auto px-6 min-w-0">
          <div
            className="grid gap-4 p-4 rounded-2xl glass border border-white/10 w-full"
            style={{ gridTemplateColumns: "repeat(4, minmax(200px, 1fr))" }}
          >
            {FLOATING_FEATURES.map((item, i) => (
              <div
                key={i}
                className="flex min-w-0 flex-col p-4 border-r border-white/10 last:border-0 hover:bg-white/5 transition-colors rounded-lg"
              >
                <h3 className="text-white font-semibold text-base mb-1.5">{item.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none z-0 mix-blend-screen" />
    </section>
  );
}
