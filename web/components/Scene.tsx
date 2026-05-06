'use client';

import { Canvas, useFrame, useThree, invalidate } from '@react-three/fiber';
import { Stars, AdaptiveDpr, AdaptiveEvents } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { KernelSize } from 'postprocessing';
import { Suspense, useRef, useEffect, useState, Component, ReactNode } from 'react';
import * as THREE from 'three';
import { useStore } from '@/lib/store';
import Earth from './Earth';
import Moon from './Moon';

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
// Sun — bright sphere off-camera that creates rim lighting on Earth
// ===========================================================================
function Sun({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[3.2, 32, 32]} />
        <meshBasicMaterial color="#FFF7E0" toneMapped={false} />
      </mesh>
      {/* Soft glow shell */}
      <mesh scale={1.8}>
        <sphereGeometry args={[3.2, 24, 24]} />
        <meshBasicMaterial
          color="#FDE68A"
          transparent
          opacity={0.18}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      <directionalLight color="#FFFAF0" intensity={2.6} position={[0, 0, 0]} target-position={[0, 0, -50]} />
    </group>
  );
}

// ===========================================================================
// Camera rig — pointer parallax (rAF-throttled), invalidates on demand only
// ===========================================================================
function CameraRig({ tier }: { tier: Tier }) {
  const { camera } = useThree();
  const stage = useStore((s) => s.stage);
  const targetLook = useRef(new THREE.Vector3(0, 0, -50));
  const desired = useRef(new THREE.Vector3(0, 0, -50));
  const startTime = useRef<number | null>(null);
  const exteriorClock = useRef(0);
  const wakeStop = useRef(0);

  // Throttled pointer / touch / tilt → updates desired look-at vector only
  useEffect(() => {
    let raf = 0;
    let pendingX = 0;
    let pendingY = 0;
    const flush = () => {
      const range = tier === 'mobile' ? 4 : 8;
      desired.current.set(pendingX * range, -pendingY * (range / 2) + 1, -50);
      raf = 0;
      // Wake the render loop for ~250ms after input
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

  // Reset cinematic timer when stage changes; wake renderer
  useEffect(() => {
    startTime.current = null;
    wakeStop.current = performance.now() + 1000;
    invalidate();
  }, [stage]);

  useFrame((state, dt) => {
    if (stage === 'exterior') {
      // Slow orbit around the Earth in preflight
      exteriorClock.current += dt * 0.12;
      const t = exteriorClock.current;
      camera.position.set(Math.cos(t) * 16, 4 + Math.sin(t * 0.5) * 1.2, Math.sin(t) * 16);
      camera.lookAt(0, 0, -50);
      invalidate();
      return;
    }
    if (stage === 'flying-in') {
      if (startTime.current === null) startTime.current = state.clock.elapsedTime;
      const elapsed = state.clock.elapsedTime - startTime.current;
      const k = Math.min(1, elapsed / 2.0);
      const eased = 1 - Math.pow(1 - k, 3);
      camera.position.lerp(new THREE.Vector3(0, 0.5, 0), eased * 0.15);
      camera.lookAt(0, 0.5, -50);
      if (k < 1) invalidate();
      return;
    }
    // Cockpit (free look)
    camera.position.set(0, 0.5, 0);
    targetLook.current.lerp(desired.current, Math.min(1, dt * 4));
    camera.lookAt(targetLook.current);
    // Keep render alive briefly after input, then sleep
    if (performance.now() < wakeStop.current) {
      invalidate();
    }
  });

  return null;
}

// ===========================================================================
// Earth + Moon system — keeps a tiny per-frame rotation; the rotation lives
// inside Earth.tsx itself and gates on `active`. Here we only mount.
// ===========================================================================
function EarthSystem({ tier, active }: { tier: Tier; active: boolean }) {
  const earthPos: [number, number, number] = [0, 0, -50];
  const sunPos: [number, number, number] = [60, 22, -10];
  const earthSize = tier === 'mobile' ? 7.5 : 9.5;

  // Drive a lazy ~12fps invalidation so Earth rotates in demand mode without
  // hammering the GPU. Cleared when not active.
  useEffect(() => {
    if (!active) return;
    const id = window.setInterval(() => invalidate(), 80);
    return () => window.clearInterval(id);
  }, [active]);

  return (
    <>
      <Sun position={sunPos} />
      <Suspense fallback={null}>
        <Earth position={earthPos} size={earthSize} sunPosition={sunPos} active={active} />
        <Moon earthPosition={earthPos} size={earthSize * 0.18} orbitRadius={earthSize * 2.4} active={active} />
      </Suspense>
    </>
  );
}

// ===========================================================================
// Scene contents
// ===========================================================================
function SceneContents({ tier }: { tier: Tier }) {
  const stage = useStore((s) => s.stage);
  const data = useStore((s) => s.data);
  const panelOpen = useStore((s) => s.panelOpen);
  // Stop continuous orbit/rotation work when the dashboard is fully covering Earth
  const heavy = !(stage === 'cockpit' && !!data && panelOpen);

  // Tiered counts — kept low; Bloom does the heavy lifting visually
  const starsFar  = tier === 'mobile' ? 1800 : tier === 'tablet' ? 3500 : 5500;
  const starsNear = tier === 'mobile' ?  500 : tier === 'tablet' ? 1000 : 1600;

  return (
    <>
      <color attach="background" args={['#020410']} />

      {/* Tiny ambient + cool fill so Earth's night side isn't pitch black */}
      <ambientLight intensity={0.05} color="#1E3A8A" />
      <hemisphereLight args={['#22D3EE', '#020410', 0.12]} />

      {/* Two starfield layers — fade is built-in to drei Stars */}
      <Stars radius={400} depth={140} count={starsFar} factor={4.5} saturation={0.3} fade speed={heavy ? 0.25 : 0} />
      <Stars radius={120} depth={50}  count={starsNear} factor={2.5} saturation={0}    fade speed={heavy ? 0.45 : 0} />

      <EarthSystem tier={tier} active={heavy} />

      <CameraRig tier={tier} />

      {/* Single bloom pass — cheap and gives the photoreal rim glow */}
      <EffectComposer multisampling={tier === 'mobile' ? 0 : 2}>
        <Bloom
          intensity={1.0}
          luminanceThreshold={0.4}
          luminanceSmoothing={0.6}
          mipmapBlur
          kernelSize={tier === 'mobile' ? KernelSize.MEDIUM : KernelSize.LARGE}
        />
      </EffectComposer>
    </>
  );
}

// ===========================================================================
// Error boundary — if WebGL crashes or shaders fail to compile, fall back to
// a CSS cosmos so the app is still usable
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
              'radial-gradient(ellipse at 30% 50%, rgba(34,211,238,0.12) 0%, transparent 50%),' +
              'radial-gradient(ellipse at 70% 30%, rgba(124,58,237,0.18) 0%, transparent 55%),' +
              '#020410',
          }}
        />
      );
    }
    return this.props.children;
  }
}

// ===========================================================================
// Main Scene — frameloop="demand" everywhere. Frames only render when
// invalidate() is called: by camera animation, pointer input, or the
// 80ms Earth-rotation tick.
// ===========================================================================
export default function Scene() {
  const tier = useDeviceTier();
  const stage = useStore((s) => s.stage);
  const panelOpen = useStore((s) => s.panelOpen);

  // Wake renderer whenever scene state changes
  useEffect(() => { invalidate(); }, [stage, panelOpen]);

  const fov = tier === 'mobile' ? 72 : tier === 'tablet' ? 68 : 65;
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
        camera={{ position: [0, 4, 18], fov, near: 0.1, far: 2000 }}
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
