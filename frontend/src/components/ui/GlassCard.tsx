import { cn } from "../../lib/utils";
import { type HTMLMotionProps, motion } from "framer-motion";

interface GlassProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  variant?: "card" | "panel" | "heavy";
}

export function GlassCard({ children, className, variant = "card", ...props }: GlassProps) {
  const variants = {
    card: "glass-card",
    panel: "glass-panel",
    heavy: "backdrop-blur-2xl bg-zinc-950/90 border border-white/10",
  };

  return (
    <motion.div
      className={cn(
        "rounded-2xl p-6 transition-all duration-300",
        variants[variant],
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      {...props}
    >
      <div className="relative z-10">{children}</div>
      {/* Optional: Add subtle gradient or noise overlay here if needed */}
    </motion.div>
  );
}
