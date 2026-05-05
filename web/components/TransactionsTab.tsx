'use client';

import { useMemo, useState } from 'react';
import type { Transaction } from '@/lib/types';
import { fmtMoney, fmtDate } from '@/lib/format';

type SortKey = 'date' | 'amount' | 'payee' | 'category';
type SortDir = 'asc' | 'desc';

export default function TransactionsTab({ txns }: { txns: Transaction[] }) {
  const [q, setQ] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let rows = !needle
      ? txns
      : txns.filter(
          (t) =>
            t.payee.toLowerCase().includes(needle) ||
            (t.category || '').toLowerCase().includes(needle) ||
            t.source.toLowerCase().includes(needle)
        );
    rows = [...rows].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortKey === 'amount') return (a.amount - b.amount) * dir;
      if (sortKey === 'payee') return a.payee.localeCompare(b.payee) * dir;
      if (sortKey === 'category') return (a.category || '').localeCompare(b.category || '') * dir;
      return (new Date(a.date).getTime() - new Date(b.date).getTime()) * dir;
    });
    return rows;
  }, [txns, q, sortKey, sortDir]);

  function header(label: string, key: SortKey) {
    const active = key === sortKey;
    return (
      <button
        onClick={() => {
          if (active) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
          else {
            setSortKey(key);
            setSortDir('desc');
          }
        }}
        className={`uppercase tracking-wider text-[0.62rem] font-mono ${
          active ? 'text-cosmic-cyan' : 'text-cosmic-dim'
        } hover:text-cosmic-cyan transition`}
      >
        {label} {active ? (sortDir === 'asc' ? '↑' : '↓') : ''}
      </button>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="filter merchant / category / source"
          className="bg-space-panel/60 border border-cosmic-cyan/20 rounded-md px-3 py-1.5 text-xs font-mono w-full max-w-md text-cosmic-starlight placeholder:text-cosmic-dim/60 focus:outline-none focus:border-cosmic-cyan"
        />
        <div className="hud-mono text-[0.65rem] text-cosmic-dim whitespace-nowrap">
          {filtered.length.toLocaleString()} / {txns.length.toLocaleString()} ROWS
        </div>
      </div>

      <div className="hud-panel hud-corners p-3">
        <div className="grid grid-cols-12 gap-2 border-b border-cosmic-cyan/15 pb-2 mb-1">
          <div className="col-span-2">{header('Date', 'date')}</div>
          <div className="col-span-4">{header('Payee', 'payee')}</div>
          <div className="col-span-3">{header('Category', 'category')}</div>
          <div className="col-span-2 text-right">{header('Amount', 'amount')}</div>
          <div className="col-span-1 text-right">
            <span className="uppercase tracking-wider text-[0.62rem] font-mono text-cosmic-dim">Src</span>
          </div>
        </div>
        <div className="max-h-[480px] overflow-auto hud-scroll">
          {filtered.slice(0, 500).map((t, i) => {
            const isIncome = t.amount > 0;
            return (
              <div
                key={i}
                className="grid grid-cols-12 gap-2 py-1.5 border-b border-cosmic-cyan/8 text-sm"
              >
                <div className="col-span-2 font-mono text-xs text-cosmic-dim">
                  {fmtDate(t.date)}
                </div>
                <div className="col-span-4 text-cosmic-starlight truncate">{t.payee}</div>
                <div className="col-span-3 text-cosmic-cyan/80 font-mono text-xs truncate">
                  {t.category}
                </div>
                <div
                  className={`col-span-2 text-right font-mono font-semibold ${
                    isIncome ? 'text-cosmic-mint' : 'text-cosmic-gold'
                  }`}
                >
                  {fmtMoney(t.amount)}
                </div>
                <div className="col-span-1 text-right text-[0.65rem] font-mono text-cosmic-dim truncate">
                  {t.source.split('.')[0].slice(0, 6)}
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-cosmic-dim text-xs font-mono p-6 text-center">
              No transactions match the filter.
            </div>
          )}
          {filtered.length > 500 && (
            <div className="text-cosmic-dim text-[0.65rem] font-mono p-3 text-center">
              showing first 500 of {filtered.length.toLocaleString()} matches
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
