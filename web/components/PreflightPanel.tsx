'use client';

import { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Rocket, FileSpreadsheet } from 'lucide-react';
import { useStore } from '@/lib/store';
import { analyzeFiles, fetchDemo } from '@/lib/api';

export default function PreflightPanel() {
  const stage = useStore((s) => s.stage);
  const setData = useStore((s) => s.setData);
  const setLoading = useStore((s) => s.setLoading);
  const setError = useStore((s) => s.setError);
  const flyToCockpit = useStore((s) => s.flyToCockpit);
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const fileRef = useRef<HTMLInputElement>(null);
  const [pickedNames, setPickedNames] = useState<string[]>([]);

  if (stage !== 'exterior') return null;

  async function onDemo() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDemo();
      setData(data);
      flyToCockpit();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load demo data.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function onFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const arr = Array.from(files);
    setPickedNames(arr.map((f) => f.name));
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeFiles(arr);
      setData(data);
      flyToCockpit();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to analyze files.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        key="preflight"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="fixed left-1/2 top-1/2 z-20 w-[min(560px,92vw)] -translate-x-1/2 -translate-y-1/2"
      >
        <div className="hud-panel hud-corners p-7 sm:p-9">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-3xl">🪐</span>
            <span className="hud-mono text-cosmic-cyan animate-flicker">SYSTEM ONLINE · STARDATE 2026.05</span>
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-extrabold tracking-wide bg-gradient-to-br from-cosmic-cyan via-cosmic-purpleHi to-cosmic-gold bg-clip-text text-transparent mb-2">
            IRON STAR LEDGER
          </h1>
          <p className="text-cosmic-dim text-sm sm:text-base font-mono mb-6">
            Approach the cockpit. Beam up your statements to chart your financial galaxy.
          </p>

          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".csv,.xlsx,.xls,.ofx,.qfx,.qbo"
            className="hidden"
            onChange={(e) => onFiles(e.target.files)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={loading}
              className="btn-plasma flex items-center justify-center gap-2"
            >
              <Upload size={16} /> Upload Statements
            </button>
            <button
              type="button"
              onClick={onDemo}
              disabled={loading}
              className="btn-ghost flex items-center justify-center gap-2"
            >
              <Rocket size={16} /> Launch Demo
            </button>
          </div>

          {pickedNames.length > 0 && (
            <div className="mt-4 text-xs text-cosmic-dim font-mono flex items-start gap-2">
              <FileSpreadsheet size={14} className="mt-0.5 text-cosmic-cyan" />
              <span>{pickedNames.join(' · ')}</span>
            </div>
          )}

          {loading && (
            <div className="mt-5 flex items-center gap-3 text-cosmic-cyan font-mono text-xs">
              <div className="w-2 h-2 rounded-full bg-cosmic-cyan animate-ping" />
              <span>SCANNING CARGO BAY · PARSING TRANSACTIONS…</span>
            </div>
          )}

          {error && (
            <div className="mt-4 text-cosmic-danger font-mono text-xs border border-cosmic-danger/40 rounded p-3 bg-cosmic-danger/5">
              ⚠ {error}
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-cosmic-cyan/15 text-[0.68rem] text-cosmic-dim font-mono tracking-wider uppercase">
            Supported · CSV · Excel · OFX · QFX · QBO &nbsp;·&nbsp; Bank-grade · in-memory only
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
