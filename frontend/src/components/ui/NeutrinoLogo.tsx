import { motion } from "framer-motion";

interface NeutrinoLogoProps {
  size?: number;
  className?: string;
  animate?: boolean;
}

export function NeutrinoLogo({ size = 32, className = "", animate = true }: NeutrinoLogoProps) {
  const orbitVariants = {
    animate: {
      rotate: 360,
      transition: { duration: 8, repeat: Infinity, ease: "linear" as const },
    },
  };

  const orbitVariants2 = {
    animate: {
      rotate: -360,
      transition: { duration: 12, repeat: Infinity, ease: "linear" as const },
    },
  };

  const pulseVariants = {
    animate: {
      scale: [1, 1.2, 1],
      opacity: [0.8, 1, 0.8],
      transition: { duration: 2, repeat: Infinity, ease: "easeInOut" as const },
    },
  };

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id="core-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#818CF8" stopOpacity="1" />
            <stop offset="50%" stopColor="#6366F1" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#4F46E5" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="orbit1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366F1" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#22D3EE" stopOpacity="0.3" />
          </linearGradient>
          <linearGradient id="orbit2" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#22D3EE" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0.2" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer glow */}
        <circle cx="32" cy="32" r="20" fill="url(#core-glow)" opacity="0.15" />

        {/* Orbit rings */}
        {animate ? (
          <>
            <motion.g
              variants={orbitVariants}
              animate="animate"
              style={{ originX: "32px", originY: "32px", transformOrigin: "32px 32px" }}
            >
              <ellipse
                cx="32"
                cy="32"
                rx="22"
                ry="10"
                stroke="url(#orbit1)"
                strokeWidth="1.5"
                fill="none"
                opacity="0.6"
                transform="rotate(-30 32 32)"
              />
              <circle cx="54" cy="32" r="2.5" fill="#818CF8" filter="url(#glow)" transform="rotate(-30 32 32)" />
            </motion.g>

            <motion.g
              variants={orbitVariants2}
              animate="animate"
              style={{ originX: "32px", originY: "32px", transformOrigin: "32px 32px" }}
            >
              <ellipse
                cx="32"
                cy="32"
                rx="22"
                ry="10"
                stroke="url(#orbit2)"
                strokeWidth="1.5"
                fill="none"
                opacity="0.5"
                transform="rotate(60 32 32)"
              />
              <circle cx="54" cy="32" r="2" fill="#22D3EE" filter="url(#glow)" transform="rotate(60 32 32)" />
            </motion.g>
          </>
        ) : (
          <>
            <ellipse
              cx="32"
              cy="32"
              rx="22"
              ry="10"
              stroke="url(#orbit1)"
              strokeWidth="1.5"
              fill="none"
              opacity="0.6"
              transform="rotate(-30 32 32)"
            />
            <ellipse
              cx="32"
              cy="32"
              rx="22"
              ry="10"
              stroke="url(#orbit2)"
              strokeWidth="1.5"
              fill="none"
              opacity="0.5"
              transform="rotate(60 32 32)"
            />
          </>
        )}

        {/* Core particle */}
        {animate ? (
          <motion.circle
            cx="32"
            cy="32"
            r="5"
            fill="url(#core-glow)"
            filter="url(#glow)"
            variants={pulseVariants}
            animate="animate"
          />
        ) : (
          <circle cx="32" cy="32" r="5" fill="url(#core-glow)" filter="url(#glow)" />
        )}

        {/* Inner bright dot */}
        <circle cx="32" cy="32" r="2" fill="#C7D2FE" />
      </svg>
    </div>
  );
}
