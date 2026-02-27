import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { ProStat } from '../../types';

interface ProStatCardProps {
  stat: ProStat;
}

const getTrendConfig = (direction: 'up' | 'down' | 'neutral') => {
  switch (direction) {
    case 'up':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/20',
        icon: TrendingUp,
      };
    case 'down':
      return {
        bg: 'bg-red-500/10',
        text: 'text-red-400',
        border: 'border-red-500/20',
        icon: TrendingDown,
      };
    case 'neutral':
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        icon: Minus,
      };
  }
};

const ProStatCard: React.FC<ProStatCardProps> = ({ stat }) => {
  const trendConfig = getTrendConfig(stat.trend_direction);
  const TrendIcon = trendConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm shadow-xl flex items-center justify-between print:border-gray-200 print:shadow-none print:break-inside-avoid print:bg-white"
    >
      <div>
        <p className="text-slate-400 text-sm font-medium tracking-wide">
          {stat.label}
        </p>
        <p className="text-4xl font-bold tracking-tight text-white mt-1 print:text-black">
          {stat.value}
        </p>
      </div>

      <div
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border ${trendConfig.bg} ${trendConfig.text} ${trendConfig.border}`}
      >
        <TrendIcon className="h-4 w-4" />
        <span className="text-xs font-semibold">{stat.trend}</span>
      </div>
    </motion.div>
  );
};

export { ProStatCard };
