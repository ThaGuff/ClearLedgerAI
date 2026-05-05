'use client';

import dynamic from 'next/dynamic';
import PreflightPanel from '@/components/PreflightPanel';
import HUDFrame from '@/components/HUDFrame';
import Dashboard from '@/components/Dashboard';

// R3F scene must be client-only — no SSR for WebGL
const Scene = dynamic(() => import('@/components/Scene'), { ssr: false });

export default function HomePage() {
  return (
    <main className="relative w-screen h-screen overflow-hidden bg-space-deep">
      {/* 3D background — fills the viewport */}
      <div className="absolute inset-0 z-0">
        <Scene />
      </div>

      {/* Cockpit canopy mask + HUD strips */}
      <HUDFrame />

      {/* Pre-flight upload panel (only when stage === 'exterior') */}
      <PreflightPanel />

      {/* Cockpit dashboard (only when stage === 'cockpit' && data loaded) */}
      <Dashboard />

      {/* Powered-by footer */}
      <div className="absolute bottom-2 right-4 z-40 hud-mono text-[0.55rem] text-cosmic-dim/70 tracking-[0.3em] pointer-events-none">
        POWERED BY PLEX AUTOMATION
      </div>
    </main>
  );
}
