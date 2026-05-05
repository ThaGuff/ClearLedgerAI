'use client';

import type { Subscription } from '@/lib/types';
import { fmtMoney, fmtDate } from '@/lib/format';

export default function SubscriptionsTab({ subs }: { subs: Subscription[] }) {
  const totalAnnual = subs.reduce((a, b) => a + b.annual_cost, 0);
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="hud-panel p-3">
          <div className="hud-mono text-[0.6rem] text-cosmic-dim">DETECTED</div>
          <div className="font-display font-extrabold text-2xl text-cosmic-cyan">{subs.length}</div>
        </div>
        <div className="hud-panel p-3">
          <div className="hud-mono text-[0.6rem] text-cosmic-dim">MONTHLY</div>
          <div className="font-display font-extrabold text-2xl text-cosmic-purpleHi">{fmtMoney(totalAnnual / 12)}</div>
        </div>
        <div className="hud-panel p-3">
          <div className="hud-mono text-[0.6rem] text-cosmic-dim">ANNUAL</div>
          <div className="font-display font-extrabold text-2xl text-cosmic-gold">{fmtMoney(totalAnnual)}</div>
        </div>
      </div>

      <div className="hud-panel hud-corners p-3">
        <div className="grid grid-cols-12 gap-2 text-[0.62rem] font-mono uppercase tracking-wider text-cosmic-dim border-b border-cosmic-cyan/15 pb-2 mb-1">
          <div className="col-span-4">Merchant</div>
          <div className="col-span-2">Cadence</div>
          <div className="col-span-2 text-right">Avg Charge</div>
          <div className="col-span-2 text-right">Annual</div>
          <div className="col-span-2">Detected</div>
        </div>
        <div className="max-h-[400px] overflow-auto hud-scroll">
          {subs.map((s, i) => (
            <div key={i} className="grid grid-cols-12 gap-2 py-2 border-b border-cosmic-cyan/8 text-sm">
              <div className="col-span-4 text-cosmic-starlight font-medium truncate">{s.merchant}</div>
              <div className="col-span-2 text-cosmic-cyan/80 font-mono text-xs">{s.cadence}</div>
              <div className="col-span-2 text-right font-mono text-cosmic-starlight">{fmtMoney(s.avg_charge)}</div>
              <div className="col-span-2 text-right font-mono text-cosmic-gold font-semibold">{fmtMoney(s.annual_cost)}</div>
              <div className="col-span-2 text-cosmic-dim font-mono text-[0.7rem]">{s.detected_by}</div>
            </div>
          ))}
          {subs.length === 0 && (
            <div className="text-cosmic-dim text-xs font-mono p-6 text-center">
              No recurring charges detected yet — try uploading 2+ months of data.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
