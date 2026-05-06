'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, PieChart, Repeat2, Sparkles, ListChecks, X } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useStore } from '@/lib/store';
import HealthGauge from './HealthGauge';
import MetricStrip from './MetricStrip';
import InsightsList from './InsightsList';

// Code-split heavy Recharts/Markdown bundles so the cockpit paints fast.
const CashflowChart      = dynamic(() => import('./Charts').then(m => m.CashflowChart),      { ssr: false });
const CategoryDonut      = dynamic(() => import('./Charts').then(m => m.CategoryDonut),      { ssr: false });
const TopCategoriesBar   = dynamic(() => import('./Charts').then(m => m.TopCategoriesBar),   { ssr: false });
const RunningBalance     = dynamic(() => import('./Charts').then(m => m.RunningBalance),     { ssr: false });
const TopExpensesList    = dynamic(() => import('./Charts').then(m => m.TopExpensesList),    { ssr: false });
const SubscriptionsTab   = dynamic(() => import('./SubscriptionsTab'),                       { ssr: false });
const CoachPanel         = dynamic(() => import('./CoachPanel'),                             { ssr: false });
const TransactionsTab    = dynamic(() => import('./TransactionsTab'),                        { ssr: false });

const TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'spend', label: 'Spend', icon: PieChart },
  { id: 'subs', label: 'Subscriptions', icon: Repeat2 },
  { id: 'coach', label: 'AI Coach', icon: Sparkles },
  { id: 'tx', label: 'Transactions', icon: ListChecks },
] as const;

export default function Dashboard() {
  const stage = useStore((s) => s.stage);
  const data = useStore((s) => s.data);
  const panelOpen = useStore((s) => s.panelOpen);
  const setPanelOpen = useStore((s) => s.setPanelOpen);
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);

  if (stage !== 'cockpit' || !data) return null;

  return (
    <AnimatePresence>
      {panelOpen && (
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="absolute inset-x-0 bottom-0 top-12 sm:top-16 z-30 px-2 sm:px-6 pb-4 sm:pb-10 pt-2 sm:pt-4 pointer-events-none"
        >
          <div className="mx-auto max-w-[1400px] h-full pointer-events-auto">
            <div className="hud-panel hud-corners p-3 sm:p-5 h-full overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between mb-3 sm:mb-4 gap-2">
                <div className="min-w-0">
                  <div className="hud-mono text-[0.55rem] sm:text-[0.62rem] text-cosmic-cyan tracking-[0.25em] sm:tracking-[0.3em] truncate">
                    NAV-COM · LEDGER INTERFACE
                  </div>
                  <div className="font-display text-lg sm:text-2xl font-extrabold text-cosmic-starlight tracking-wide truncate">
                    Iron Star Ledger
                  </div>
                </div>
                <button
                  onClick={() => setPanelOpen(false)}
                  className="btn-ghost text-[0.65rem] sm:text-xs flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 shrink-0"
                  aria-label="Minimize panel"
                >
                  <X className="w-3.5 h-3.5" /> <span className="hidden sm:inline">MINIMIZE</span>
                </button>
              </div>

              {/* Tabs */}
              <div className="flex items-center gap-1 mb-3 sm:mb-4 border-b border-cosmic-cyan/15 overflow-x-auto hud-scroll-x">
                {TABS.map((t) => {
                  const Icon = t.icon;
                  const active = activeTab === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setActiveTab(t.id as any)}
                      className={`flex items-center gap-1.5 px-2 sm:px-3 py-2 text-[0.65rem] sm:text-xs font-mono uppercase tracking-wider transition relative shrink-0 ${
                        active
                          ? 'text-cosmic-cyan'
                          : 'text-cosmic-dim hover:text-cosmic-starlight'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span className="hidden xs:inline sm:inline">{t.label}</span>
                      {active && (
                        <motion.div
                          layoutId="tab-underline"
                          className="absolute -bottom-px left-0 right-0 h-[2px] bg-cosmic-cyan shadow-[0_0_10px_rgba(34,211,238,0.7)]"
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Body */}
              <div className="flex-1 overflow-auto hud-scroll pr-1">
                {activeTab === 'overview' && <OverviewView />}
                {activeTab === 'spend' && <SpendView />}
                {activeTab === 'subs' && <SubscriptionsTab subs={data.subscriptions} />}
                {activeTab === 'coach' && <CoachPanel />}
                {activeTab === 'tx' && <TransactionsTab txns={data.transactions} />}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {!panelOpen && stage === 'cockpit' && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setPanelOpen(true)}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 z-30 btn-plasma px-6 py-3 text-xs"
        >
          ⌃ RE-ENGAGE LEDGER
        </motion.button>
      )}
    </AnimatePresence>
  );
}

function OverviewView() {
  const data = useStore((s) => s.data)!;
  return (
    <div className="space-y-4">
      <MetricStrip health={data.health} />
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5">
          <HealthGauge health={data.health} />
        </div>
        <div className="col-span-12 lg:col-span-7 h-[220px] sm:h-[300px]">
          <CashflowChart data={data.time_series} />
        </div>
      </div>
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-7 h-[200px] sm:h-[280px]">
          <RunningBalance data={data.time_series} />
        </div>
        <div className="col-span-12 lg:col-span-5">
          <InsightsList insights={data.insights} />
        </div>
      </div>
    </div>
  );
}

function SpendView() {
  const data = useStore((s) => s.data)!;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5 h-[260px] sm:h-[340px]">
          <CategoryDonut data={data.by_category} />
        </div>
        <div className="col-span-12 lg:col-span-7 h-[260px] sm:h-[340px]">
          <TopCategoriesBar data={data.by_category} />
        </div>
      </div>
      <TopExpensesList rows={data.top_expenses} />
    </div>
  );
}
