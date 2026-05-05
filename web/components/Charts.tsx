'use client';

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, LineChart, Line, Cell, PieChart, Pie,
} from 'recharts';
import type { TimeSeriesPoint, CategoryAgg, Transaction } from '@/lib/types';
import { fmtDate, fmtMoney } from '@/lib/format';

const PALETTE = ['#22D3EE', '#7C3AED', '#FBBF24', '#3B82F6', '#F472B6', '#10B981', '#A78BFA', '#FB923C', '#67E8F9', '#F87171'];

const tooltipStyle = {
  background: 'rgba(7,10,31,0.92)',
  border: '1px solid rgba(34,211,238,0.4)',
  borderRadius: 8,
  fontSize: 12,
  color: '#F1F5F9',
  fontFamily: 'JetBrains Mono, monospace',
  padding: '8px 10px',
  boxShadow: '0 0 18px rgba(34,211,238,0.25)',
};

function chartFrame(title: string, kicker: string, children: React.ReactNode) {
  return (
    <div className="hud-panel hud-corners p-4 h-full flex flex-col">
      <div className="flex items-baseline justify-between mb-2">
        <div className="font-display text-cosmic-starlight text-sm font-bold tracking-wide">
          {title}
        </div>
        <div className="hud-mono text-[0.6rem] text-cosmic-cyan">{kicker}</div>
      </div>
      <div className="flex-1 min-h-[180px]">{children}</div>
    </div>
  );
}

export function CashflowChart({ data }: { data: TimeSeriesPoint[] }) {
  const formatted = data.map((d) => ({
    ...d,
    label: fmtDate(d.date, { short: true }),
  }));
  return chartFrame('CASHFLOW · INCOME vs EXPENSES', 'TEMPORAL TRACE',
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={formatted} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="g-inc" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34D399" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#34D399" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="g-exp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F43F5E" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#F43F5E" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(34,211,238,0.08)" strokeDasharray="2 4" />
        <XAxis dataKey="label" stroke="#64748B" fontSize={10} tickLine={false} />
        <YAxis stroke="#64748B" fontSize={10} tickLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(v: number) => fmtMoney(v)}
        />
        <Area type="monotone" dataKey="income" stroke="#34D399" strokeWidth={2} fill="url(#g-inc)" />
        <Area type="monotone" dataKey="expenses" stroke="#F43F5E" strokeWidth={2} fill="url(#g-exp)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function CategoryDonut({ data }: { data: CategoryAgg[] }) {
  const top = data.slice(0, 8);
  const total = top.reduce((a, b) => a + b.total, 0);
  return chartFrame('SPEND BY CATEGORY', `TOTAL · ${fmtMoney(total)}`,
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={top}
          dataKey="total"
          nameKey="category"
          innerRadius={50}
          outerRadius={85}
          stroke="#020410"
          strokeWidth={2}
          paddingAngle={2}
        >
          {top.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(v: number, n: string) => [fmtMoney(v), n]}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function TopCategoriesBar({ data }: { data: CategoryAgg[] }) {
  const top = data.slice(0, 6);
  return chartFrame('TOP 6 CATEGORIES', 'BARS · ABSOLUTE',
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={top} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
        <CartesianGrid stroke="rgba(34,211,238,0.06)" strokeDasharray="2 4" horizontal={false} />
        <XAxis type="number" stroke="#64748B" fontSize={10}
          tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`} />
        <YAxis dataKey="category" type="category" stroke="#94A3B8" fontSize={10} width={84} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => fmtMoney(v)} cursor={{ fill: 'rgba(34,211,238,0.05)' }} />
        <Bar dataKey="total" radius={[0, 6, 6, 0]}>
          {top.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function RunningBalance({ data }: { data: TimeSeriesPoint[] }) {
  const formatted = data.map((d) => ({
    ...d,
    label: fmtDate(d.date, { short: true }),
  }));
  return chartFrame('CUMULATIVE CASH POSITION', 'WARP-FUEL RESERVE',
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={formatted} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="g-bal" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#7C3AED" />
            <stop offset="100%" stopColor="#22D3EE" />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(34,211,238,0.08)" strokeDasharray="2 4" />
        <XAxis dataKey="label" stroke="#64748B" fontSize={10} tickLine={false} />
        <YAxis stroke="#64748B" fontSize={10} tickLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => fmtMoney(v)} />
        <Line type="monotone" dataKey="running_balance"
          stroke="url(#g-bal)" strokeWidth={2.5} dot={false}
          activeDot={{ r: 5, fill: '#22D3EE', stroke: '#F1F5F9' }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function TopExpensesList({ rows }: { rows: Transaction[] }) {
  return (
    <div className="hud-panel hud-corners p-4 h-full flex flex-col">
      <div className="flex items-baseline justify-between mb-2">
        <div className="font-display text-cosmic-starlight text-sm font-bold tracking-wide">
          TOP 10 EXPENSES
        </div>
        <div className="hud-mono text-[0.6rem] text-cosmic-cyan">LARGEST OUTFLOWS</div>
      </div>
      <div className="flex-1 overflow-auto hud-scroll">
        {rows.map((r, i) => (
          <div key={i} className="flex items-center justify-between py-1.5 border-b border-cosmic-cyan/10">
            <div className="flex flex-col min-w-0">
              <span className="text-cosmic-starlight text-sm truncate max-w-[180px]">{r.payee}</span>
              <span className="text-cosmic-dim text-[0.65rem] font-mono">
                {fmtDate(r.date, { short: true })} · {r.category}
              </span>
            </div>
            <span className="text-cosmic-danger font-mono font-semibold text-sm">
              {fmtMoney(r.amount)}
            </span>
          </div>
        ))}
        {rows.length === 0 && (
          <div className="text-cosmic-dim text-xs font-mono p-4 text-center">No expenses detected.</div>
        )}
      </div>
    </div>
  );
}
