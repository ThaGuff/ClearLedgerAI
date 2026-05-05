'use client';

import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import type { Insight } from '@/lib/types';

const STYLE: Record<Insight['type'], { icon: any; ring: string; bg: string; text: string; label: string }> = {
  warn: {
    icon: AlertTriangle,
    ring: 'border-cosmic-danger/40',
    bg: 'bg-cosmic-danger/8',
    text: 'text-cosmic-danger',
    label: 'RISK',
  },
  good: {
    icon: CheckCircle2,
    ring: 'border-cosmic-mint/40',
    bg: 'bg-cosmic-mint/8',
    text: 'text-cosmic-mint',
    label: 'WIN',
  },
  info: {
    icon: Info,
    ring: 'border-cosmic-cyan/40',
    bg: 'bg-cosmic-cyan/8',
    text: 'text-cosmic-cyan',
    label: 'INTEL',
  },
};

export default function InsightsList({ insights }: { insights: Insight[] }) {
  if (!insights.length) {
    return (
      <div className="hud-panel p-4 text-cosmic-dim text-xs font-mono">
        No insights generated yet.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {insights.map((ins, i) => {
        const s = STYLE[ins.type] || STYLE.info;
        const Icon = s.icon;
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`hud-panel border ${s.ring} ${s.bg} p-3 flex items-start gap-3`}
          >
            <Icon className={`w-4 h-4 mt-0.5 ${s.text}`} />
            <div className="flex-1">
              <div className={`hud-mono text-[0.6rem] ${s.text} mb-0.5`}>{s.label}</div>
              <div className="text-sm text-cosmic-starlight leading-snug font-semibold">{ins.title}</div>
              <div className="text-xs text-cosmic-dim mt-1 leading-snug">{ins.body}</div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
