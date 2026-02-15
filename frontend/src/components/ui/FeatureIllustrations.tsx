import { motion } from "framer-motion";

/* ------------------------------------------------------------------ */
/*  1. Code Analysis Illustration – file-tree → AI → outputs          */
/* ------------------------------------------------------------------ */
export function CodeAnalysisIllustration({ className = "" }: { className?: string }) {
  return (
    <div className={`relative w-full h-full flex items-center justify-center ${className}`}>
      <svg viewBox="0 0 400 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="ca-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#22D3EE" />
          </linearGradient>
          <filter id="ca-glow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Background grid dots */}
        {[...Array(8)].map((_, i) =>
          [...Array(5)].map((_, j) => (
            <circle key={`dot-${i}-${j}`} cx={50 * (i + 1)} cy={44 * (j + 0.5)} r="1.5" fill="white" opacity="0.08" />
          ))
        )}

        {/* Left: Code file blocks */}
        <motion.g initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.1 }}>
          <rect x="30" y="25" width="95" height="70" rx="8" fill="#1E1B4B" stroke="#6366F1" strokeOpacity="0.4" strokeWidth="1.5" />
          <rect x="42" y="40" width="50" height="4" rx="2" fill="#818CF8" opacity="0.9" />
          <rect x="42" y="50" width="65" height="4" rx="2" fill="white" opacity="0.25" />
          <rect x="42" y="60" width="35" height="4" rx="2" fill="white" opacity="0.18" />
          <rect x="42" y="70" width="55" height="4" rx="2" fill="#22D3EE" opacity="0.6" />
          <rect x="42" y="80" width="40" height="4" rx="2" fill="white" opacity="0.15" />
        </motion.g>

        <motion.g initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.25 }}>
          <rect x="30" y="115" width="95" height="70" rx="8" fill="#1E1B4B" stroke="#6366F1" strokeOpacity="0.3" strokeWidth="1.5" />
          <rect x="42" y="130" width="55" height="4" rx="2" fill="#818CF8" opacity="0.8" />
          <rect x="42" y="140" width="42" height="4" rx="2" fill="white" opacity="0.22" />
          <rect x="42" y="150" width="68" height="4" rx="2" fill="white" opacity="0.18" />
          <rect x="42" y="160" width="30" height="4" rx="2" fill="#22D3EE" opacity="0.5" />
          <rect x="42" y="170" width="50" height="4" rx="2" fill="white" opacity="0.12" />
        </motion.g>

        {/* Connection lines to center */}
        <motion.path d="M125 60 L175 105" stroke="url(#ca-grad)" strokeWidth="2" strokeDasharray="6 4" filter="url(#ca-glow)"
          initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }} transition={{ duration: 0.8, delay: 0.5 }} />
        <motion.path d="M125 150 L175 115" stroke="url(#ca-grad)" strokeWidth="2" strokeDasharray="6 4" filter="url(#ca-glow)"
          initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1 }} transition={{ duration: 0.8, delay: 0.6 }} />

        {/* Central: AI processing node */}
        <motion.g initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7, type: "spring" }}>
          <circle cx="200" cy="110" r="32" fill="#1E1B4B" stroke="url(#ca-grad)" strokeWidth="2" />
          <circle cx="200" cy="110" r="16" fill="#6366F1" opacity="0.35" filter="url(#ca-glow)" />
          {/* AI sparkle */}
          <motion.path d="M200 96 L203 106 L213 109 L203 112 L200 122 L197 112 L187 109 L197 106 Z"
            fill="#C7D2FE" opacity="0.9"
            animate={{ scale: [1, 1.15, 1], opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }} />
        </motion.g>
        <motion.text x="186" y="144" fill="#A5B4FC" fontSize="9" fontWeight="600" fontFamily="system-ui"
          initial={{ opacity: 0 }} animate={{ opacity: 0.8 }} transition={{ delay: 0.9 }}>AI Core</motion.text>

        {/* Output lines */}
        <motion.path d="M232 105 L280 60" stroke="url(#ca-grad)" strokeWidth="2" filter="url(#ca-glow)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.6, delay: 0.9 }} />
        <motion.path d="M232 110 L280 110" stroke="url(#ca-grad)" strokeWidth="2" filter="url(#ca-glow)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.6, delay: 1 }} />
        <motion.path d="M232 115 L280 160" stroke="url(#ca-grad)" strokeWidth="2" filter="url(#ca-glow)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.6, delay: 1.1 }} />

        {/* Right: Output insight cards */}
        <motion.g initial={{ opacity: 0, x: 25 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.1, duration: 0.5 }}>
          <rect x="280" y="38" width="95" height="42" rx="8" fill="#1E1B4B" stroke="#818CF8" strokeOpacity="0.45" strokeWidth="1.5" />
          <text x="294" y="57" fill="#C7D2FE" fontSize="9" fontWeight="600" fontFamily="system-ui">Architecture</text>
          <rect x="294" y="64" width="60" height="4" rx="2" fill="#818CF8" opacity="0.45" />
        </motion.g>

        <motion.g initial={{ opacity: 0, x: 25 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.2, duration: 0.5 }}>
          <rect x="280" y="88" width="95" height="42" rx="8" fill="#0F172A" stroke="#22D3EE" strokeOpacity="0.4" strokeWidth="1.5" />
          <text x="294" y="107" fill="#A5F3FC" fontSize="9" fontWeight="600" fontFamily="system-ui">Dependencies</text>
          <rect x="294" y="114" width="52" height="4" rx="2" fill="#22D3EE" opacity="0.4" />
        </motion.g>

        <motion.g initial={{ opacity: 0, x: 25 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.3, duration: 0.5 }}>
          <rect x="280" y="138" width="95" height="42" rx="8" fill="#1E1B4B" stroke="#818CF8" strokeOpacity="0.35" strokeWidth="1.5" />
          <text x="294" y="157" fill="#C7D2FE" fontSize="9" fontWeight="600" fontFamily="system-ui">Frameworks</text>
          <rect x="294" y="164" width="58" height="4" rx="2" fill="#818CF8" opacity="0.35" />
        </motion.g>
      </svg>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  2. Executive Intelligence – dashboard mockup                      */
/* ------------------------------------------------------------------ */
export function ExecutiveIllustration({ className = "" }: { className?: string }) {
  return (
    <div className={`relative w-full h-full flex items-center justify-center ${className}`}>
      <svg viewBox="0 0 400 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="ei-area" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#6366F1" stopOpacity="0" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0.35" />
          </linearGradient>
          <linearGradient id="ei-line" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#22D3EE" />
          </linearGradient>
          <filter id="ei-glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Dashboard outer frame */}
        <motion.rect x="25" y="15" width="350" height="190" rx="12" fill="#0F0F1A" stroke="white" strokeOpacity="0.1" strokeWidth="1.5"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }} />

        {/* Title bar */}
        <motion.rect x="25" y="15" width="350" height="28" rx="12" fill="white" fillOpacity="0.06"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} />
        <circle cx="44" cy="29" r="4.5" fill="#EF4444" opacity="0.7" />
        <circle cx="58" cy="29" r="4.5" fill="#F59E0B" opacity="0.7" />
        <circle cx="72" cy="29" r="4.5" fill="#22C55E" opacity="0.7" />
        <text x="160" y="33" fill="white" fillOpacity="0.3" fontSize="8" fontFamily="system-ui" textAnchor="middle">Executive Report</text>

        {/* KPI Card 1 - Risk Score */}
        <motion.g initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.5 }}>
          <rect x="40" y="55" width="100" height="68" rx="8" fill="white" fillOpacity="0.06" stroke="white" strokeOpacity="0.08" />
          <text x="54" y="72" fill="white" fillOpacity="0.45" fontSize="8" fontFamily="system-ui">Risk Score</text>
          <text x="54" y="100" fill="#4ADE80" fontSize="26" fontWeight="800" fontFamily="system-ui">Low</text>
          <rect x="54" y="110" width="72" height="5" rx="2.5" fill="white" fillOpacity="0.12" />
          <motion.rect x="54" y="110" width="22" height="5" rx="2.5" fill="#4ADE80"
            initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 0.7, duration: 0.6 }} style={{ transformOrigin: "54px 112px" }} />
        </motion.g>

        {/* KPI Card 2 - Tech Debt */}
        <motion.g initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45, duration: 0.5 }}>
          <rect x="150" y="55" width="100" height="68" rx="8" fill="white" fillOpacity="0.06" stroke="white" strokeOpacity="0.08" />
          <text x="164" y="72" fill="white" fillOpacity="0.45" fontSize="8" fontFamily="system-ui">Tech Debt</text>
          <text x="164" y="100" fill="#FBBF24" fontSize="26" fontWeight="800" fontFamily="system-ui">42%</text>
          <rect x="164" y="110" width="72" height="5" rx="2.5" fill="white" fillOpacity="0.12" />
          <motion.rect x="164" y="110" width="30" height="5" rx="2.5" fill="#FBBF24"
            initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 0.8, duration: 0.6 }} style={{ transformOrigin: "164px 112px" }} />
        </motion.g>

        {/* KPI Card 3 - Mini bar chart */}
        <motion.g initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55, duration: 0.5 }}>
          <rect x="260" y="55" width="100" height="68" rx="8" fill="white" fillOpacity="0.06" stroke="white" strokeOpacity="0.08" />
          <text x="274" y="72" fill="white" fillOpacity="0.45" fontSize="8" fontFamily="system-ui">Complexity</text>
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const heights = [22, 38, 28, 44, 32, 40];
            const h = heights[i];
            return (
              <motion.rect
                key={`bar-${i}`}
                x={274 + i * 13}
                y={115 - h}
                width="8"
                height={h}
                rx="3"
                fill={i % 2 === 0 ? "#818CF8" : "#22D3EE"}
                opacity={0.75}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ delay: 0.8 + i * 0.08, duration: 0.4 }}
                style={{ transformOrigin: `${274 + i * 13 + 4}px 115px` }}
              />
            );
          })}
        </motion.g>

        {/* Bottom trend area chart */}
        <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>
          <rect x="40" y="135" width="320" height="58" rx="8" fill="white" fillOpacity="0.04" stroke="white" strokeOpacity="0.06" />
          <text x="54" y="150" fill="white" fillOpacity="0.35" fontSize="8" fontFamily="system-ui">Health Trend</text>
          <motion.path
            d="M55 178 Q100 162, 135 170 T210 156 T280 164 T345 148"
            stroke="url(#ei-line)" strokeWidth="2.5" fill="none" filter="url(#ei-glow)"
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1, duration: 1.5, ease: "easeOut" }} />
          <motion.path
            d="M55 178 Q100 162, 135 170 T210 156 T280 164 T345 148 L345 188 L55 188 Z"
            fill="url(#ei-area)"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8, duration: 0.8 }} />
        </motion.g>
      </svg>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  3. Security Shield – scanning shield motif                        */
/* ------------------------------------------------------------------ */
export function SecurityIllustration({ className = "" }: { className?: string }) {
  return (
    <div className={`relative w-full h-full flex items-center justify-center ${className}`}>
      <svg viewBox="0 0 400 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="sh-grad" x1="50%" y1="0%" x2="50%" y2="100%">
            <stop offset="0%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#22D3EE" />
          </linearGradient>
          <linearGradient id="sh-scan" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#6366F1" stopOpacity="0" />
            <stop offset="50%" stopColor="#6366F1" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
          </linearGradient>
          <filter id="sh-glow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Scan line */}
        <motion.rect x="0" y="0" width="400" height="5" fill="url(#sh-scan)" rx="2"
          animate={{ y: [0, 215, 0] }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }} />

        {/* Decorative rings around shield */}
        <motion.ellipse cx="200" cy="110" rx="120" ry="95" stroke="white" strokeOpacity="0.04" strokeWidth="1" fill="none"
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2, duration: 1 }} />
        <motion.ellipse cx="200" cy="110" rx="140" ry="105" stroke="white" strokeOpacity="0.03" strokeWidth="1" fill="none"
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4, duration: 1 }} />

        {/* Shield shape */}
        <motion.path
          d="M200 28 L245 52 L245 118 Q245 152 200 178 Q155 152 155 118 L155 52 Z"
          fill="#1E1B4B" fillOpacity="0.6" stroke="url(#sh-grad)" strokeWidth="2.5"
          initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.7, type: "spring" }} />
        <motion.path
          d="M200 42 L235 62 L235 115 Q235 142 200 165 Q165 142 165 115 L165 62 Z"
          fill="url(#sh-grad)" fillOpacity="0.12"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} />

        {/* Checkmark */}
        <motion.path
          d="M183 107 L195 121 L222 86"
          stroke="#4ADE80" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" fill="none" filter="url(#sh-glow)"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.9, duration: 0.6 }} />

        {/* Left: Vulnerability scan items */}
        {[0, 1, 2, 3].map((i) => {
          const colors = ["#4ADE80", "#4ADE80", "#FBBF24", "#4ADE80"];
          const labels = ["Auth", "XSS", "CSRF", "SQL"];
          const widths = [55, 48, 62, 42];
          return (
            <motion.g key={`vuln-${i}`}
              initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 + i * 0.12, duration: 0.4 }}>
              <circle cx="38" cy={48 + i * 38} r="5" fill={colors[i]} opacity="0.7" />
              <text x="50" y={52 + i * 38} fill="white" fillOpacity="0.5" fontSize="9" fontFamily="system-ui">{labels[i]}</text>
              <rect x="50" y={56 + i * 38} width={widths[i]} height="3.5" rx="1.5" fill="white" fillOpacity="0.12" />
            </motion.g>
          );
        })}

        {/* Right: Security metrics */}
        {[0, 1, 2].map((i) => {
          const labels = ["CVEs Found", "Dependencies", "Grade"];
          const values = ["0", "147", "A+"];
          const clrs = ["#4ADE80", "#A5B4FC", "#22D3EE"];
          return (
            <motion.g key={`metric-${i}`}
              initial={{ opacity: 0, x: 15 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + i * 0.12, duration: 0.4 }}>
              <rect x="290" y={40 + i * 52} width="90" height="42" rx="8" fill="white" fillOpacity="0.05" stroke="white" strokeOpacity="0.1" />
              <text x="304" y={56 + i * 52} fill="white" fillOpacity="0.4" fontSize="8" fontFamily="system-ui">{labels[i]}</text>
              <text x="304" y={74 + i * 52} fill={clrs[i]} fontSize="16" fontWeight="800" fontFamily="system-ui">{values[i]}</text>
            </motion.g>
          );
        })}
      </svg>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  4. Roadmap – timeline with phase cards                            */
/* ------------------------------------------------------------------ */
export function RoadmapIllustration({ className = "" }: { className?: string }) {
  return (
    <div className={`relative w-full h-full flex items-center justify-center ${className}`}>
      <svg viewBox="0 0 400 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
        <defs>
          <linearGradient id="rm-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#22D3EE" />
          </linearGradient>
          <filter id="rm-glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Progress badge */}
        <motion.g initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.5 }}>
          <rect x="145" y="8" width="110" height="24" rx="12" fill="#1E1B4B" stroke="#818CF8" strokeOpacity="0.4" />
          <text x="170" y="24" fill="#A5B4FC" fontSize="10" fontFamily="system-ui" fontWeight="700">50% Complete</text>
        </motion.g>

        {/* Timeline main line */}
        <motion.line x1="55" y1="110" x2="345" y2="110" stroke="url(#rm-grad)" strokeWidth="2.5" strokeOpacity="0.35"
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1 }} />

        {/* Timeline nodes and cards */}
        {[0, 1, 2, 3].map((i) => {
          const x = 85 + i * 78;
          const done = i < 2;
          const active = i === 2;
          const labels = ["Setup & Config", "Core Analysis", "AI Integration", "Production"];
          const above = i % 2 === 0;

          return (
            <motion.g key={`phase-${i}`}
              initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3 + i * 0.18, type: "spring" }}>
              {/* Connector to card */}
              <line x1={x} y1={above ? 80 : 126} x2={x} y2={above ? 100 : 120}
                stroke={done ? "#4ADE80" : active ? "#818CF8" : "white"} strokeOpacity={done ? 0.4 : active ? 0.5 : 0.1} strokeWidth="1.5" />

              {/* Node circle */}
              <circle cx={x} cy={110} r="12" fill="#0F0F1A"
                stroke={done ? "#4ADE80" : active ? "#818CF8" : "white"} strokeOpacity={done ? 0.7 : active ? 0.7 : 0.15} strokeWidth="2" />
              {done && <circle cx={x} cy={110} r="5.5" fill="#4ADE80" opacity="0.75" filter="url(#rm-glow)" />}
              {active && (
                <motion.circle cx={x} cy={110} r="5.5" fill="#818CF8" filter="url(#rm-glow)"
                  animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }} />
              )}

              {/* Phase card */}
              <rect
                x={x - 40} y={above ? 40 : 130}
                width="80" height="40" rx="8"
                fill={active ? "#1E1B4B" : "white"} fillOpacity={active ? 0.8 : 0.04}
                stroke={done ? "#4ADE80" : active ? "#818CF8" : "white"}
                strokeOpacity={done ? 0.35 : active ? 0.5 : 0.08}
                strokeWidth={active ? 1.5 : 1}
                strokeDasharray={i === 3 ? "5 4" : "none"}
              />
              <text x={x - 28} y={above ? 56 : 148} fill="white" fillOpacity={i === 3 ? 0.3 : 0.55} fontSize="7" fontFamily="system-ui">Phase {i + 1}</text>
              <text x={x - 28} y={above ? 68 : 160} fill={done ? "#4ADE80" : active ? "#A5B4FC" : "white"}
                fillOpacity={i === 3 ? 0.2 : 0.45} fontSize="6.5" fontFamily="system-ui">{labels[i]}</text>
            </motion.g>
          );
        })}
      </svg>
    </div>
  );
}
