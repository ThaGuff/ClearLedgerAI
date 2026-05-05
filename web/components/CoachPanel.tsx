'use client';

import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { useStore } from '@/lib/store';
import { fetchCoach } from '@/lib/api';

export default function CoachPanel() {
  const data = useStore((s) => s.data);
  const coachText = useStore((s) => s.coachText);
  const coachLoading = useStore((s) => s.coachLoading);
  const setCoachText = useStore((s) => s.setCoachText);
  const setCoachLoading = useStore((s) => s.setCoachLoading);

  async function engage() {
    if (!data) return;
    setCoachLoading(true);
    try {
      const text = await fetchCoach(data.transactions);
      setCoachText(text);
    } catch (e: any) {
      setCoachText(`_Coach unavailable: ${e?.message || 'unknown error'}_`);
    } finally {
      setCoachLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cosmic-purpleHi" />
          <div className="hud-mono text-[0.7rem] text-cosmic-dim">AI COACH · CFP-LEVEL ANALYSIS</div>
        </div>
        <button
          onClick={engage}
          disabled={coachLoading || !data}
          className="btn-plasma text-xs px-4 py-2 disabled:opacity-40"
        >
          {coachLoading ? 'TRANSMITTING…' : coachText ? 'RE-ENGAGE COACH' : 'ENGAGE COACH'}
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="hud-panel hud-corners p-5 min-h-[260px] coach-md"
      >
        {!coachText && !coachLoading && (
          <div className="text-cosmic-dim text-sm font-mono">
            <div className="mb-2 text-cosmic-cyan">// awaiting transmission</div>
            Press <span className="text-cosmic-purpleHi">ENGAGE COACH</span> to receive a personalized financial briefing
            generated from your transaction signal.
          </div>
        )}
        {coachLoading && (
          <div className="flex items-center gap-3 text-cosmic-cyan font-mono text-sm">
            <div className="w-2 h-2 rounded-full bg-cosmic-cyan animate-pulse" />
            decoding signal…
          </div>
        )}
        {coachText && <ReactMarkdown>{coachText}</ReactMarkdown>}
      </motion.div>
    </div>
  );
}
