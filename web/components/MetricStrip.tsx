'use client';

import { motion } from 'framer-motion';
import type { Health } from '@/lib/types';
import { fmtMoney } from '@/lib/format';

export default function MetricStrip({ health }: { health: Health }) {
  const m = health.metrics;
  const tiles = [
    { label: 'Income', value: fmtMoney(m.income), color: '#34D399' },
    { label: 'Expenses', value: fmtMoney(m.expenses), color: '#F43F5E' },
    { label: 'Net', value: fmtMoney(m.net), color: m.net >= 0 ? '#22D3EE' : '#F43F5E' },
    { label: 'Monthly Burn', value: fmtMoney(m.monthly_expense), color: '#A78BFA' },
    { label: 'Savings Rate', value: `${(m.savings_rate * 100).toFixed(1)}%`, color: '#FBBF24' },
    { label: 'Buffer', value: `${m.buffer_months.toFixed(1)} mo`, color: '#67E8F9' },
  ];
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {tiles.map((t, i) => (
        <motion.div
          key={t.label}
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 + i * 0.08, duration: 0.5 }}
          className="hud-panel hud-corners p-3 relative overflow-hidden"
        >
          <div className="text-[0.62rem] font-mono uppercase tracking-widest text-cosmic-dim">
            {t.label}
          </div>
          <div
            className="font-display font-extrabold text-lg sm:text-xl mt-1"
            style={{ color: t.color, textShadow: `0 0 12px ${t.color}55` }}
          >
            {t.value}
          </div>
          <div
            className="absolute bottom-0 left-0 h-[2px] w-full"
            style={{ background: `linear-gradient(90deg, transparent, ${t.color}, transparent)` }}
          />
        </motion.div>
      ))}
    </div>
  );
}
