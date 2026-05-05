'use client';

import { motion } from 'framer-motion';
import { useStore } from '@/lib/store';

export default function HUDFrame() {
  const stage = useStore((s) => s.stage);
  if (stage === 'exterior') return null;

  return (
    <>
      {/* Cockpit canopy vignette overlay */}
      <div className="cockpit-vignette" />

      {/* Top HUD strip — telemetry */}
      <motion.div
        initial={{ y: -40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1.6, duration: 0.6 }}
        className="fixed top-0 inset-x-0 z-10 px-6 py-3 flex justify-between text-[0.68rem] font-mono uppercase tracking-widest text-cosmic-cyan/80 bg-gradient-to-b from-space-deep/90 to-transparent pointer-events-none"
      >
        <span>★ IRON STAR LEDGER · NAV-COM ACTIVE</span>
        <span className="hidden sm:inline">SECTOR 7G · TRANSIT VECTOR 0.42c</span>
        <span>POWERED BY <span className="text-cosmic-gold">PLEX AUTOMATION</span></span>
      </motion.div>

      {/* Bottom HUD strip — status */}
      <motion.div
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 1.8, duration: 0.6 }}
        className="fixed bottom-0 inset-x-0 z-10 px-6 py-3 flex justify-between text-[0.68rem] font-mono uppercase tracking-widest text-cosmic-cyan/70 bg-gradient-to-t from-space-deep/90 to-transparent pointer-events-none"
      >
        <span>HULL · NOMINAL</span>
        <span className="hidden md:inline">SHIELDS · ENCRYPTED · IN-MEMORY</span>
        <span>FUEL · ∞ · STARDATE 2026.05</span>
      </motion.div>

      {/* Side scanline effect on right edge */}
      <div className="fixed right-0 top-0 h-screen w-32 pointer-events-none z-[6] overflow-hidden opacity-25">
        <div className="absolute inset-0 scanline-bg" />
        <div className="absolute inset-x-0 h-12 bg-gradient-to-b from-transparent via-cosmic-cyan/20 to-transparent animate-scanline" />
      </div>
    </>
  );
}
