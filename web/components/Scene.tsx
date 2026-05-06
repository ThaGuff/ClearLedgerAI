'use client';

import { Canvas, useFrame, useThree, invalidate } from '@react-three/fiber';
import { Stars, AdaptiveDpr, AdaptiveEvents } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { KernelSize } from 'postprocessing';
import { Suspense, useRef, useEffect, useState, Component, ReactNode } from 'react';
import * as THREE from 'three';
import { useStore } from '@/lib/store';
import Nebula from './Nebula';

// ===========================================================================
// Device tier detection
// ===========================================================================
type Tier = 'mobile' | 'tablet' | 'desktop';
function useDeviceTier(): Tier {
  const [tier, setTier] = useState<Tier>('desktop');
  useEffect(() => {
    const detect = () => {
      const w = window.innerWidth;
      const touch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      if (w < 640 || (touch && w < 820)) setTier('mobile');
      else if (w < 1280) setTier('tablet');
      else setTier('desktop');
    };
    detect();
    window.addEventListener('resize', detect);
    return () => window.removeEventListener('resize', detect);
  }, []);
  return tier;
}

// ===========================================================================
// Camera rig — pointer parallax (rAF-throttled), invalidates on demand only.
// Camera lives at the origin since the nebula surrounds it; we only rotate
// the look direction so the player feels embedded inside the explosion remnant.
// ===========================================================================
function CameraRig({ tier }: { tier: Tier }) {
  const { camera } = useThree();
  const stage = useStore((s) => s.stage);
  const desired = useRef(new THREE.Vector2(0, 0));
  const current = useRef(new THREE.Vector2(0, 0));
  const wakeStop = useRef(0);

  useEffect(() => {
    let raf = 0;
    let pendingX = 0;
    let pendingY = 0;
    const flush = () => {
      desired.current.set(pendingX, pendingY);
      raf = 0;
      wakeStop.current = performance.now() + 250;
      invalidate();
    };
    const upd = (cx: number, cy: number) => {
      pendingX = (cx / window.innerWidth) * 2 - 1;
      pendingY = (cy / window.innerHeight) * 2 - 1;
      if (!raf) raf = requestAnimationFrame(flush);
    };
    const onMouse = (e: MouseEvent) => upd(e.clientX, e.clientY);
    const onTouch = (e: TouchEvent) => { if (e.touches[0]) upd(e.touches[0].clientX, e.touches[0].clientY); };
    const onTilt = (e: DeviceOrientationEvent) => {
      pendingX = Math.max(-1, Math.min(1, (e.gamma ?? 0) / 45));
      pendingY = Math.max(-1, Math.min(1, ((e.beta ?? 0) - 30) / 45));
      if (!raf) raf = requestAnimationFrame(flush);
    };
    window.addEventListener('mousemove', onMouse, { passive: true });
    window.addEventListener('touchmove', onTouch, { passive: true });
    if (tier !== 'desktop') window.addEventListener('deviceorientation', onTilt);
    return () => {
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('touchmove', onTouch);
      window.removeEventListener('deviceorientation', onTilt);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [tier]);

  useEffect(() => {
    wakeStop.current = performance.now() + 1200;
    invalidate();
  }, [stage]);

  useFrame((state, dt) => {
    current.current.lerp(desired.current, Math.min(1, dt * 4));

    const range = tier === 'mobile' ? 0.35 : 0.55;
    const drift = stage === 'exterior' ? state.clock.elapsedTime * 0.05 : 0;
    const yaw   = current.current.x * range + Math.sin(drift) * 0.25;
    const pitch = -current.current.y * (range * 0.55) + Math.cos(drift * 0.7) * 0.06;

    const target = new THREE.Vector3(
      Math.sin(yaw) * Math.cos(pitch),
      Math.sin(pitch),
      -Math.cos(yaw) * Math.cos(pitch),
    ).multiplyScalar(50);

    camera.position.set(0, 0, 0);
    camera.lookAt(target);

    if (stage === 'exterior' || performance.now() < wakeStop.current) {
      invalidate();
    }
  });

  return null;
}

// ===========================================================================
// Scene contents — nebula + parallax star layers + bloom
// ===========================================================================
function SceneContents({ tier }: { tier: Tier }) {
  const stage = useStore((s) => s.stage);
  const data = useStore((s) => s.data);
  const panelOpen = useStore((s) => s.panelOpen);
  // Stop continuous shader work when the dashboard fully covers the scene
  const heavy = !(stage === 'cockpit' && !!data && panelOpen);

  // Tiered star counts — kept low; bloom + nebula do the visual heavy lifting
  const starsFar  = tier === 'mobile' ? 1500 : tier === 'tablet' ? 3000 : 4800;
  const starsNear = tier === 'mobile' ?  400 : tier === 'tablet' ?  900 : 1400;

  return (
    <>
      <color attach="background" args={['#03061A']} />

      {/* Two starfield layers in front of the nebula for parallax depth */}
      <Stars radius={300} depth={120} count={starsFar}  factor={4.2} saturation={0.25} fade speed={heavy ? 0.2 : 0} />
      <Stars radius={90}  depth={40}  count={starsNear} factor={2.4} saturation={0}    fade speed={heavy ? 0.4 : 0} />

      {/* Procedural nebula — entire skybox is the explosion remnant */}
      <Nebula active={heavy} />

      <CameraRig tier={tier} />

      {/* Single bloom pass — gives the white-hot epicentre its glow */}
      <EffectComposer multisampling={tier === 'mobile' ? 0 : 2}>
        <Bloom
          intensity={1.15}
          luminanceThreshold={0.55}
          luminanceSmoothing={0.55}
          mipmapBlur
          kernelSize={tier === 'mobile' ? KernelSize.MEDIUM : KernelSize.LARGE}
        />
      </EffectComposer>
    </>
  );
}

// ===========================================================================
// Error boundary — if WebGL / shaders fail, fall back to a CSS cosmos
// ===========================================================================
class WebGLErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error) {
    // eslint-disable-next-line no-console
    console.warn('[Scene] WebGL render failed, falling back to CSS cosmos:', error?.message);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div
          className="fixed inset-0 -z-10"
          style={{
            background:
              'radial-gradient(ellipse at 50% 45%, rgba(255,180,220,0.35) 0%, transparent 30%),' +
              'radial-gradient(ellipse at 30% 50%, rgba(34,211,238,0.18) 0%, transparent 50%),' +
              'radial-gradient(ellipse at 70% 30%, rgba(255,79,176,0.22) 0%, transparent 55%),' +
              '#03061A',
          }}
        />
      );
    }
    return this.props.children;
  }
}

// ===========================================================================
// Main Scene — frameloop="demand". Frames render only when invalidate()
// fires: from camera animation, pointer input, or the nebula time tick.
// ===========================================================================
export default function Scene() {
  const tier = useDeviceTier();
  const stage = useStore((s) => s.stage);
  const panelOpen = useStore((s) => s.panelOpen);

  useEffect(() => { invalidate(); }, [stage, panelOpen]);

  const fov = tier === 'mobile' ? 78 : tier === 'tablet' ? 72 : 68;
  const dprMax = tier === 'mobile' ? 1.0 : tier === 'tablet' ? 1.4 : 1.75;

  return (
    <WebGLErrorBoundary>
      <Canvas
        gl={{
          antialias: tier !== 'mobile',
          alpha: false,
          powerPreference: 'high-performance',
          stencil: false,
          depth: true,
        }}
        dpr={[1, dprMax]}
        camera={{ position: [0, 0, 0], fov, near: 0.1, far: 2000 }}
        frameloop="demand"
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.05;
        }}
      >
        <AdaptiveDpr pixelated />
        <AdaptiveEvents />
        <Suspense fallback={null}>
          <SceneContents tier={tier} />
        </Suspense>
      </Canvas>
    </WebGLErrorBoundary>
  );
}
