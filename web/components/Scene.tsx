'use client';

import { Canvas, useFrame, useThree, invalidate } from '@react-three/fiber';
import {
  Stars,
  Trail,
  Sparkles,
  AdaptiveDpr,
  AdaptiveEvents,
  PerformanceMonitor,
} from '@react-three/drei';
import {
  EffectComposer,
  Bloom,
  ChromaticAberration,
  Vignette,
  Noise,
} from '@react-three/postprocessing';
import { BlendFunction, KernelSize } from 'postprocessing';
import { Suspense, useRef, useMemo, useEffect, useState } from 'react';
import * as THREE from 'three';
import { useStore } from '@/lib/store';
import Earth from './Earth';
import Moon from './Moon';

// ===========================================================================
// Device tier
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
// The Sun — bright sphere off-camera that drives bloom rim-light
// ===========================================================================
function Sun({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[2.6, 32, 32]} />
        <meshBasicMaterial color="#FFF1C2" toneMapped={false} />
      </mesh>
      {/* Inner corona */}
      <mesh scale={2.4}>
        <sphereGeometry args={[2.6, 24, 24]} />
        <meshBasicMaterial color="#FDE68A" transparent opacity={0.15} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
      {/* Outer corona */}
      <mesh scale={6}>
        <sphereGeometry args={[2.6, 24, 24]} />
        <meshBasicMaterial color="#FBBF24" transparent opacity={0.04} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
      <pointLight color="#FFF7E0" intensity={2.4} distance={400} decay={1} />
      <directionalLight color="#FFFAF0" intensity={1.6} position={[0, 0, 0]} />
    </group>
  );
}

// ===========================================================================
// Comet streak (interactive cosmos ambience)
// ===========================================================================
function Comet({ orbit = 60, speed = 0.12, offset = 0, active = true }: { orbit?: number; speed?: number; offset?: number; active?: boolean }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (!active || !ref.current) return;
    const t = state.clock.elapsedTime * speed + offset;
    ref.current.position.set(Math.cos(t) * orbit, Math.sin(t * 0.6) * 10, Math.sin(t) * orbit - 30);
  });
  return (
    <Trail width={1.6} length={7} color={'#67E8F9'} attenuation={(t) => t * t}>
      <mesh ref={ref}>
        <sphereGeometry args={[0.16, 12, 12]} />
        <meshBasicMaterial color="#F1F5F9" toneMapped={false} />
      </mesh>
    </Trail>
  );
}

// ===========================================================================
// Cockpit canopy — kept minimal so Earth dominates the framing
// ===========================================================================
function CockpitCanopy({ tier }: { tier: Tier }) {
  const segs = tier === 'mobile' ? 32 : 64;
  return (
    <group>
      {[-1.05, -0.5, 0, 0.5, 1.05].map((angle, i) => (
        <mesh key={i} rotation={[0, angle, 0]}>
          <torusGeometry args={[18, 0.15, 10, 80, Math.PI * 0.95]} />
          <meshPhysicalMaterial color="#1F2937" metalness={0.95} roughness={0.22} clearcoat={0.7} />
        </mesh>
      ))}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[17.9, 0.18, 10, 96]} />
        <meshPhysicalMaterial color="#0F172A" metalness={0.92} roughness={0.28} clearcoat={0.6} />
      </mesh>
      <mesh position={[0, -8, -6]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[18, 5, 8]} />
        <meshPhysicalMaterial color="#0E1330" metalness={0.8} roughness={0.4} emissive="#22d3ee" emissiveIntensity={0.05} clearcoat={0.5} />
      </mesh>
      <mesh position={[0, -5.7, -2.2]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[16, 0.04, 0.06]} />
        <meshBasicMaterial color="#22d3ee" toneMapped={false} />
      </mesh>
      <mesh position={[0, -5.0, -1.2]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[14, 0.04, 0.06]} />
        <meshBasicMaterial color="#7C3AED" toneMapped={false} />
      </mesh>
    </group>
  );
}

// ===========================================================================
// Starship (only visible in exterior preflight stage)
// ===========================================================================
function Starship({ visible }: { visible: boolean }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame((_, dt) => {
    if (ref.current && visible) ref.current.rotation.y += dt * 0.05;
  });
  if (!visible) return null;
  return (
    <group ref={ref}>
      <mesh>
        <capsuleGeometry args={[1.2, 4, 16, 32]} />
        <meshPhysicalMaterial color="#475569" metalness={0.92} roughness={0.28} clearcoat={0.8} />
      </mesh>
      <mesh position={[0, 0, 1.6]}>
        <sphereGeometry args={[0.55, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshBasicMaterial color="#22d3ee" transparent opacity={0.85} toneMapped={false} />
      </mesh>
      <mesh position={[0, -2.6, 0]}>
        <coneGeometry args={[0.5, 1.2, 24]} />
        <meshBasicMaterial color="#A78BFA" toneMapped={false} />
      </mesh>
      <pointLight position={[0, -3, 0]} color="#7C3AED" intensity={6} distance={8} />
      <mesh position={[1.2, -0.6, 0]} rotation={[0, 0, -0.4]}>
        <boxGeometry args={[1.6, 0.1, 0.6]} />
        <meshPhysicalMaterial color="#334155" metalness={0.88} roughness={0.4} clearcoat={0.6} />
      </mesh>
      <mesh position={[-1.2, -0.6, 0]} rotation={[0, 0, 0.4]}>
        <boxGeometry args={[1.6, 0.1, 0.6]} />
        <meshPhysicalMaterial color="#334155" metalness={0.88} roughness={0.4} clearcoat={0.6} />
      </mesh>
    </group>
  );
}

// ===========================================================================
// Camera rig — pointer / touch / tilt parallax with rAF coalescing.
// Calls invalidate() so frameloop="demand" wakes only when needed.
// ===========================================================================
function CameraRig({ tier, demand }: { tier: Tier; demand: boolean }) {
  const { camera } = useThree();
  const stage = useStore((s) => s.stage);
  const targetPos = useRef(new THREE.Vector3(0, 6, 28));
  const targetLook = useRef(new THREE.Vector3(0, 0, 0));
  const pointer = useRef({ x: 0, y: 0 });
  const startTime = useRef<number | null>(null);
  const settled = useRef(false);

  useEffect(() => {
    let raf = 0;
    let pendingX = 0;
    let pendingY = 0;
    const flush = () => {
      pointer.current.x = pendingX;
      pointer.current.y = pendingY;
      raf = 0;
      settled.current = false;
      if (demand) invalidate(); // wake render loop
    };
    const updateFromXY = (clientX: number, clientY: number) => {
      pendingX = (clientX / window.innerWidth) * 2 - 1;
      pendingY = (clientY / window.innerHeight) * 2 - 1;
      if (!raf) raf = requestAnimationFrame(flush);
    };
    const onMouse = (e: MouseEvent) => updateFromXY(e.clientX, e.clientY);
    const onTouch = (e: TouchEvent) => {
      if (e.touches[0]) updateFromXY(e.touches[0].clientX, e.touches[0].clientY);
    };
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
  }, [tier, demand]);

  useEffect(() => {
    startTime.current = null;
    settled.current = false;
    if (demand) invalidate();
  }, [stage, demand]);

  useFrame((state, dt) => {
    if (stage === 'exterior') {
      const t = state.clock.elapsedTime * 0.15;
      targetPos.current.set(Math.cos(t) * 14, 4 + Math.sin(t * 0.6) * 1.2, Math.sin(t) * 14);
      targetLook.current.set(0, 0, 0);
      // Always animating in exterior stage — don't settle
      settled.current = false;
    } else if (stage === 'flying-in') {
      if (startTime.current === null) startTime.current = state.clock.elapsedTime;
      const elapsed = state.clock.elapsedTime - startTime.current;
      const k = Math.min(1, elapsed / 2.2);
      const eased = 1 - Math.pow(1 - k, 3);
      const startVec = new THREE.Vector3(camera.position.x, camera.position.y, camera.position.z);
      const endVec = new THREE.Vector3(0, 0.5, 0);
      targetPos.current.copy(startVec).lerp(endVec, eased);
      targetLook.current.set(0, 1, -10);
      if (k < 1) settled.current = false;
    } else {
      targetPos.current.set(0, 0.5, 0);
      const range = tier === 'mobile' ? 4 : 8;
      const lx = pointer.current.x * range;
      const ly = -pointer.current.y * (range / 2) + 1;
      targetLook.current.set(lx, ly, -12);
    }

    const prevPos = camera.position.clone();
    camera.position.lerp(targetPos.current, Math.min(1, dt * 3));
    const currentLook = new THREE.Vector3();
    camera.getWorldDirection(currentLook);
    const desiredLook = targetLook.current.clone().sub(camera.position).normalize();
    const newLook = currentLook.lerp(desiredLook, Math.min(1, dt * 4)).normalize();
    const lookTarget = camera.position.clone().add(newLook.multiplyScalar(20));
    camera.lookAt(lookTarget);

    // In demand mode: stop requesting frames once camera is essentially still.
    if (demand) {
      const moved = prevPos.distanceTo(camera.position) > 0.0008;
      if (moved) {
        settled.current = false;
        invalidate();
      } else {
        settled.current = true;
      }
    }
  });

  return null;
}

// ===========================================================================
// Earth that auto-orbits the Earth-Moon system slightly when active
// ===========================================================================
function EarthSystem({ tier, active, demand }: { tier: Tier; active: boolean; demand: boolean }) {
  const groupRef = useRef<THREE.Group>(null!);
  const earthPos: [number, number, number] = tier === 'mobile' ? [0, 0, -52] : [0, 0, -50];
  const sunPos: [number, number, number] = [70, 28, -10];
  const earthSize = tier === 'mobile' ? 7.5 : 9;

  useFrame((_, dt) => {
    if (!active || !groupRef.current) return;
    groupRef.current.rotation.y += dt * 0.008; // slow drift
    if (demand) invalidate();
  });

  return (
    <group ref={groupRef}>
      <Sun position={sunPos} />
      <Suspense fallback={null}>
        <Earth position={earthPos} size={earthSize} sunPosition={sunPos} active={active} />
        <Moon earthPosition={earthPos} size={earthSize * 0.18} orbitRadius={earthSize * 2.1} active={active} />
      </Suspense>
    </group>
  );
}

// ===========================================================================
// Scene contents
// ===========================================================================
function SceneContents({ tier, demand }: { tier: Tier; demand: boolean }) {
  const stage = useStore((s) => s.stage);
  const data = useStore((s) => s.data);
  const panelOpen = useStore((s) => s.panelOpen);
  // Pause non-essential motion when the panel is fully covering Earth
  const heavyAnimate = !(stage === 'cockpit' && !!data && panelOpen);

  // Tiered counts
  const starsFar  = tier === 'mobile' ? 3000 : tier === 'tablet' ? 6500 : 10000;
  const starsNear = tier === 'mobile' ?  900 : tier === 'tablet' ? 1800 :  2800;

  return (
    <>
      <color attach="background" args={['#020410']} />
      <fog attach="fog" args={['#020410', 90, 600]} />

      {/* Soft ambient + cool fill so the night side of Earth isn't pitch black */}
      <ambientLight intensity={0.06} color="#1E3A8A" />
      <hemisphereLight args={['#22D3EE', '#020410', 0.18]} />

      <Stars radius={420} depth={160} count={starsFar} factor={5.5} saturation={0.35} fade speed={heavyAnimate ? 0.35 : 0} />
      <Stars radius={140} depth={60}  count={starsNear} factor={3.0} saturation={0.0} fade speed={heavyAnimate ? 0.55 : 0} />

      {/* Distant nebulae — pure additive billboards, very cheap */}
      <mesh position={[-90, 30, -200]}>
        <planeGeometry args={[180, 180]} />
        <meshBasicMaterial color="#7C3AED" transparent opacity={0.16} depthWrite={false} blending={THREE.AdditiveBlending} />
      </mesh>
      <mesh position={[110, -40, -240]}>
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial color="#22D3EE" transparent opacity={0.13} depthWrite={false} blending={THREE.AdditiveBlending} />
      </mesh>

      {/* Floating dust / small foreground stars (skip on mobile) */}
      {tier !== 'mobile' && heavyAnimate && (
        <Sparkles count={tier === 'desktop' ? 140 : 80} scale={[80, 40, 80]} size={2.6} speed={0.3} color="#9DD7FF" opacity={0.7} />
      )}

      <EarthSystem tier={tier} active={heavyAnimate} demand={demand} />

      {heavyAnimate && (
        <>
          <Comet orbit={70} speed={0.12} offset={0} active={heavyAnimate} />
          {tier !== 'mobile' && <Comet orbit={55} speed={0.18} offset={Math.PI} active={heavyAnimate} />}
        </>
      )}

      <Starship visible={stage === 'exterior' || stage === 'flying-in'} />
      {(stage === 'cockpit' || stage === 'flying-in') && <CockpitCanopy tier={tier} />}

      <CameraRig tier={tier} demand={demand} />

      <EffectComposer multisampling={tier === 'mobile' ? 0 : 2}>
        <Bloom intensity={1.2} luminanceThreshold={0.35} luminanceSmoothing={0.5} mipmapBlur kernelSize={KernelSize.LARGE} />
        <ChromaticAberration
          blendFunction={BlendFunction.NORMAL}
          offset={new THREE.Vector2(0.0006, 0.0006)}
          radialModulation={false}
          modulationOffset={0}
        />
        <Noise opacity={tier === 'mobile' ? 0.02 : 0.035} blendFunction={BlendFunction.OVERLAY} />
        <Vignette eskil={false} offset={0.15} darkness={0.9} />
      </EffectComposer>
    </>
  );
}

// ===========================================================================
// Main Scene — switches frameloop to "demand" once cockpit is reached AND
// dashboard panel is open. This is the main offload: the GPU stops rendering
// entirely when the cosmos isn't changing, freeing CPU/GPU for the dashboard.
// ===========================================================================
export default function Scene() {
  const tier = useDeviceTier();
  const stage = useStore((s) => s.stage);
  const panelOpen = useStore((s) => s.panelOpen);

  // Demand mode kicks in only when nothing meaningful is animating
  const demand = stage === 'cockpit' && panelOpen;

  // Whenever stage/panel changes, prod the renderer
  useEffect(() => { invalidate(); }, [stage, panelOpen]);

  const fov = tier === 'mobile' ? 72 : tier === 'tablet' ? 68 : 65;
  const dprMax = tier === 'mobile' ? 1.25 : tier === 'tablet' ? 1.6 : 2;

  return (
    <Canvas
      gl={{ antialias: tier !== 'mobile', alpha: false, powerPreference: 'high-performance' }}
      dpr={[1, dprMax]}
      camera={{ position: [0, 6, 28], fov, near: 0.1, far: 2500 }}
      frameloop={demand ? 'demand' : 'always'}
      onCreated={({ gl }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = 1.05;
      }}
    >
      <PerformanceMonitor onDecline={() => { /* AdaptiveDpr handles downscale */ }} />
      <AdaptiveDpr pixelated />
      <AdaptiveEvents />
      <Suspense fallback={null}>
        <SceneContents tier={tier} demand={demand} />
      </Suspense>
    </Canvas>
  );
}
