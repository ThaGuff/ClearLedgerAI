'use client';

import { motion } from 'framer-motion';
import type { Health } from '@/lib/types';

const RADIUS = 70;
const CIRC = 2 * Math.PI * RADIUS;

function bandColor(band: string) {
  if (band === 'Critical') return '#F43F5E';
  if (band === 'Fair') return '#FBBF24';
  return '#34D399';
}

export default function HealthGauge({ health }: { health: Health }) {
  const score = Math.max(0, Math.min(100, health.score));
  const offset = CIRC * (1 - score / 100);
  const color = bandColor(health.band);

  return (
    <div className="hud-panel hud-corners p-5 flex flex-col items-center">
      <div className="hud-mono text-cosmic-cyan mb-2">FINANCIAL HEALTH</div>
      <div className="relative w-[180px] h-[180px]">
        <svg viewBox="0 0 180 180" className="w-full h-full -rotate-90">
          <defs>
            <linearGradient id="ring-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.4" />
              <stop offset="100%" stopColor={color} />
            </linearGradient>
            <filter id="ring-glow">
              <feGaussianBlur stdDeviation="3.2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle
            cx="90" cy="90" r={RADIUS}
            stroke="rgba(34,211,238,0.15)" strokeWidth="8" fill="none"
          />
          <motion.circle
            cx="90" cy="90" r={RADIUS}
            stroke="url(#ring-grad)" strokeWidth="8" fill="none"
            strokeLinecap="round"
            strokeDasharray={CIRC}
            initial={{ strokeDashoffset: CIRC }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.4, ease: 'easeOut', delay: 0.3 }}
            filter="url(#ring-glow)"
          />
          {/* Tick marks */}
          {Array.from({ length: 24 }).map((_, i) => {
            const angle = (i / 24) * Math.PI * 2;
            const x1 = 90 + Math.cos(angle) * 84;
            const y1 = 90 + Math.sin(angle) * 84;
            const x2 = 90 + Math.cos(angle) * 88;
            const y2 = 90 + Math.sin(angle) * 88;
            return (
              <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="rgba(34,211,238,0.35)" strokeWidth="1" />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            className="font-display font-extrabold text-4xl"
            style={{ color, textShadow: `0 0 22px ${color}80` }}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, type: 'spring' }}
          >
            {score.toFixed(0)}
          </motion.div>
          <div className="font-mono text-[0.7rem] text-cosmic-dim mt-0.5">/100</div>
          <div
            className="mt-1 px-2 py-0.5 rounded-full text-[0.62rem] font-mono uppercase tracking-widest"
            style={{ background: `${color}22`, color, border: `1px solid ${color}55` }}
          >
            {health.band}
          </div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 w-full text-[0.7rem] font-mono">
        {health.reasoning.map((r) => (
          <div
            key={r.name}
            className="flex flex-col px-2 py-1.5 rounded border border-cosmic-cyan/15 bg-space-deep/40"
          >
            <span className="text-cosmic-dim text-[0.62rem] uppercase tracking-wider">{r.name}</span>
            <span className="text-cosmic-starlight font-semibold">{r.metric}</span>
            <span className="text-cosmic-cyan/60 text-[0.6rem]">w {r.weight}% · ideal {r.ideal}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
