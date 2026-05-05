'use client';

import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  Stars,
  Trail,
  Float,
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
import { useRef, useMemo, useEffect, useState } from 'react';
import * as THREE from 'three';
import { useStore } from '@/lib/store';

// ===========================================================================
// Device tier detection (drives FOV, DPR cap, geometry segment counts)
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
// Planet — procedural with physical material + atmospheric scattering shells
// ===========================================================================
function Planet({
  position,
  size = 2,
  color = '#22d3ee',
  emissive = '#0e1330',
  speed = 0.05,
  rings = false,
  segments = 64,
  active = true,
}: {
  position: [number, number, number];
  size?: number;
  color?: string;
  emissive?: string;
  speed?: number;
  rings?: boolean;
  segments?: number;
  active?: boolean;
}) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((_, dt) => {
    if (active && ref.current) ref.current.rotation.y += dt * speed;
  });
  return (
    <Float speed={active ? 1.2 : 0} rotationIntensity={active ? 0.2 : 0} floatIntensity={active ? 0.4 : 0}>
      <group position={position}>
        <mesh ref={ref}>
          <sphereGeometry args={[size, segments, segments]} />
          <meshPhysicalMaterial
            color={color}
            emissive={emissive}
            emissiveIntensity={0.32}
            roughness={0.55}
            metalness={0.18}
            clearcoat={0.6}
            clearcoatRoughness={0.25}
          />
        </mesh>
        {/* Inner atmospheric scattering */}
        <mesh scale={1.04}>
          <sphereGeometry args={[size, Math.max(24, segments / 2), Math.max(24, segments / 2)]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.18}
            side={THREE.BackSide}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
        {/* Outer halo */}
        <mesh scale={1.12}>
          <sphereGeometry args={[size, 24, 24]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.07}
            side={THREE.BackSide}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
        {rings && (
          <mesh rotation={[Math.PI / 2.4, 0, 0]}>
            <ringGeometry args={[size * 1.4, size * 2.1, 96]} />
            <meshBasicMaterial color="#FBBF24" transparent opacity={0.4} side={THREE.DoubleSide} />
          </mesh>
        )}
      </group>
    </Float>
  );
}

function Nebula({ position, color, scale = 80 }: { position: [number, number, number]; color: string; scale?: number }) {
  return (
    <mesh position={position}>
      <planeGeometry args={[scale, scale]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.18}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}

function Comet({ orbit = 30, speed = 0.3, offset = 0, active = true }: { orbit?: number; speed?: number; offset?: number; active?: boolean }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    if (!active) return;
    const t = state.clock.elapsedTime * speed + offset;
    if (ref.current) {
      ref.current.position.set(
        Math.cos(t) * orbit,
        Math.sin(t * 0.6) * 8,
        Math.sin(t) * orbit,
      );
    }
  });
  return (
    <Trail width={1.4} length={6} color={'#67E8F9'} attenuation={(t) => t * t}>
      <mesh ref={ref}>
        <sphereGeometry args={[0.18, 12, 12]} />
        <meshBasicMaterial color="#F1F5F9" toneMapped={false} />
      </mesh>
    </Trail>
  );
}

// ===========================================================================
// Cockpit canopy — glass dome + ribs + console with physical materials
// ===========================================================================
function CockpitCanopy({ tier }: { tier: Tier }) {
  const segs = tier === 'mobile' ? 32 : 64;
  return (
    <group>
      {/* Glass dome */}
      <mesh>
        <sphereGeometry args={[18, segs, segs, 0, Math.PI * 2, 0, Math.PI / 1.6]} />
        <meshPhysicalMaterial
          color="#22d3ee"
          transparent
          opacity={0.05}
          transmission={0.92}
          roughness={0.04}
          metalness={0}
          ior={1.45}
          thickness={0.5}
          clearcoat={1}
          clearcoatRoughness={0.05}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Vertical structural ribs */}
      {[-1.05, -0.5, 0, 0.5, 1.05].map((angle, i) => (
        <mesh key={i} rotation={[0, angle, 0]}>
          <torusGeometry args={[18, 0.18, 12, 96, Math.PI * 0.95]} />
          <meshPhysicalMaterial color="#1F2937" metalness={0.95} roughness={0.22} clearcoat={0.7} />
        </mesh>
      ))}

      {/* Equator ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[17.9, 0.2, 12, 128]} />
        <meshPhysicalMaterial color="#0F172A" metalness={0.92} roughness={0.28} clearcoat={0.6} />
      </mesh>

      {/* Lower console */}
      <mesh position={[0, -8, -6]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[18, 5, 8]} />
        <meshPhysicalMaterial
          color="#0E1330"
          metalness={0.8}
          roughness={0.4}
          emissive="#22d3ee"
          emissiveIntensity={0.05}
          clearcoat={0.5}
        />
      </mesh>

      {/* Glowing console accent strips */}
      <mesh position={[0, -5.7, -2.2]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[16, 0.04, 0.06]} />
        <meshBasicMaterial color="#22d3ee" toneMapped={false} />
      </mesh>
      <mesh position={[0, -5.0, -1.2]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[14, 0.04, 0.06]} />
        <meshBasicMaterial color="#7C3AED" toneMapped={false} />
      </mesh>

      {/* Holographic side panel gauges (skip on mobile to save fragment fill) */}
      {tier !== 'mobile' && (
        <>
          <mesh position={[-5.5, -4.2, -3]} rotation={[-Math.PI / 6, 0.5, 0]}>
            <planeGeometry args={[2.2, 1.4]} />
            <meshBasicMaterial color="#22d3ee" transparent opacity={0.18} blending={THREE.AdditiveBlending} depthWrite={false} />
          </mesh>
          <mesh position={[5.5, -4.2, -3]} rotation={[-Math.PI / 6, -0.5, 0]}>
            <planeGeometry args={[2.2, 1.4]} />
            <meshBasicMaterial color="#A78BFA" transparent opacity={0.18} blending={THREE.AdditiveBlending} depthWrite={false} />
          </mesh>
        </>
      )}
    </group>
  );
}

function Starship({ visible }: { visible: boolean }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame((_, dt) => {
    if (ref.current && visible) ref.current.rotation.y += dt * 0.05;
  });
  if (!visible) return null;
  return (
    <group ref={ref} position={[0, 0, 0]}>
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
// Camera rig — supports mouse + touch + device-tilt parallax (rAF throttled)
// ===========================================================================
function CameraRig({ tier }: { tier: Tier }) {
  const { camera } = useThree();
  const stage = useStore((s) => s.stage);
  const targetPos = useRef(new THREE.Vector3(0, 6, 28));
  const targetLook = useRef(new THREE.Vector3(0, 0, 0));
  const pointer = useRef({ x: 0, y: 0 });
  const startTime = useRef<number | null>(null);

  useEffect(() => {
    let raf = 0;
    let pendingX = 0;
    let pendingY = 0;
    const flush = () => {
      pointer.current.x = pendingX;
      pointer.current.y = pendingY;
      raf = 0;
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
      // gamma: -90..90 (left-right), beta: -180..180 (front-back)
      const g = (e.gamma ?? 0) / 45; // -1..1
      const b = ((e.beta ?? 0) - 30) / 45;
      pendingX = Math.max(-1, Math.min(1, g));
      pendingY = Math.max(-1, Math.min(1, b));
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
    startTime.current = null;
  }, [stage]);

  useFrame((state, dt) => {
    if (stage === 'exterior') {
      const t = state.clock.elapsedTime * 0.15;
      targetPos.current.set(Math.cos(t) * 14, 4 + Math.sin(t * 0.6) * 1.2, Math.sin(t) * 14);
      targetLook.current.set(0, 0, 0);
    } else if (stage === 'flying-in') {
      if (startTime.current === null) startTime.current = state.clock.elapsedTime;
      const elapsed = state.clock.elapsedTime - startTime.current;
      const k = Math.min(1, elapsed / 2.2);
      const eased = 1 - Math.pow(1 - k, 3);
      const startVec = new THREE.Vector3(camera.position.x, camera.position.y, camera.position.z);
      const endVec = new THREE.Vector3(0, 0.5, 0);
      targetPos.current.copy(startVec).lerp(endVec, eased);
      targetLook.current.set(0, 1, -10);
    } else {
      targetPos.current.set(0, 0.5, 0);
      // Reduce parallax range on mobile so head movement isn't dizzying
      const range = tier === 'mobile' ? 4 : 8;
      const lx = pointer.current.x * range;
      const ly = -pointer.current.y * (range / 2) + 1;
      targetLook.current.set(lx, ly, -12);
    }

    camera.position.lerp(targetPos.current, Math.min(1, dt * 3));
    const currentLook = new THREE.Vector3();
    camera.getWorldDirection(currentLook);
    const desiredLook = targetLook.current.clone().sub(camera.position).normalize();
    const newLook = currentLook.lerp(desiredLook, Math.min(1, dt * 4)).normalize();
    const lookTarget = camera.position.clone().add(newLook.multiplyScalar(20));
    camera.lookAt(lookTarget);
  });

  return null;
}

// ===========================================================================
// Scene contents — wrapped so PerformanceMonitor can adjust counts live
// ===========================================================================
function SceneContents({ tier }: { tier: Tier }) {
  const stage = useStore((s) => s.stage);
  const data = useStore((s) => s.data);
  // When the dashboard panel is fully visible, pause expensive background motion
  const animateBackground = !(stage === 'cockpit' && !!data);

  // Tiered counts
  const starsFar = tier === 'mobile' ? 2500 : tier === 'tablet' ? 5500 : 9000;
  const starsNear = tier === 'mobile' ? 800 : tier === 'tablet' ? 1500 : 2500;
  const planetSegs = tier === 'mobile' ? 32 : 64;

  const planets = useMemo(() => ([
    { pos: [-22, 4, -42] as [number, number, number], size: 4.2, color: '#3B82F6', emissive: '#1E40AF', rings: true, speed: 0.04 },
    { pos: [28, -6, -55] as [number, number, number], size: 6.5, color: '#F472B6', emissive: '#9D174D', speed: 0.025 },
    { pos: [-35, 12, -70] as [number, number, number], size: 3.0, color: '#FBBF24', emissive: '#92400E', speed: 0.06 },
    { pos: [12, 18, -38] as [number, number, number], size: 1.8, color: '#A78BFA', emissive: '#5B21B6', speed: 0.08 },
    { pos: [40, 2, -90] as [number, number, number], size: 8.0, color: '#22D3EE', emissive: '#0E7490', speed: 0.02 },
  ]), []);

  return (
    <>
      <color attach="background" args={['#020410']} />
      <fog attach="fog" args={['#020410', 60, 350]} />

      <ambientLight intensity={0.18} />
      <directionalLight position={[20, 10, 5]} intensity={1.2} color="#67E8F9" />
      <directionalLight position={[-15, -8, -10]} intensity={0.5} color="#F472B6" />
      <pointLight position={[0, 0, 0]} intensity={0.8} color="#22D3EE" distance={40} />

      <Stars radius={300} depth={120} count={starsFar} factor={5} saturation={0.4} fade speed={animateBackground ? 0.4 : 0} />
      <Stars radius={120} depth={50} count={starsNear} factor={3} saturation={0} fade speed={animateBackground ? 0.6 : 0} />

      {/* Floating dust sparkles (cheap, big perceptual win) */}
      {tier !== 'mobile' && (
        <Sparkles count={tier === 'desktop' ? 160 : 90} scale={[60, 30, 60]} size={2.4} speed={animateBackground ? 0.35 : 0} color="#67E8F9" opacity={0.7} />
      )}

      <Nebula position={[-60, 20, -120]} color="#7C3AED" scale={140} />
      <Nebula position={[80, -30, -140]} color="#22D3EE" scale={160} />
      <Nebula position={[0, 60, -180]} color="#F472B6" scale={120} />

      {planets.map((p, i) => (
        <Planet key={i} position={p.pos} size={p.size} color={p.color} emissive={p.emissive} speed={p.speed} rings={p.rings} segments={planetSegs} active={animateBackground} />
      ))}

      <Comet orbit={45} speed={0.18} offset={0} active={animateBackground} />
      <Comet orbit={60} speed={0.12} offset={Math.PI} active={animateBackground} />
      {tier !== 'mobile' && <Comet orbit={38} speed={0.25} offset={Math.PI / 2} active={animateBackground} />}

      <Starship visible={stage === 'exterior' || stage === 'flying-in'} />
      {(stage === 'cockpit' || stage === 'flying-in') && <CockpitCanopy tier={tier} />}

      <CameraRig tier={tier} />

      <EffectComposer multisampling={tier === 'mobile' ? 0 : 2}>
        <Bloom intensity={1.1} luminanceThreshold={0.5} luminanceSmoothing={0.4} mipmapBlur kernelSize={KernelSize.LARGE} />
        <ChromaticAberration
          blendFunction={BlendFunction.NORMAL}
          offset={new THREE.Vector2(0.0008, 0.0008)}
          radialModulation={false}
          modulationOffset={0}
        />
        <Noise opacity={tier === 'mobile' ? 0.025 : 0.04} blendFunction={BlendFunction.OVERLAY} />
        <Vignette eskil={false} offset={0.1} darkness={0.85} />
      </EffectComposer>
    </>
  );
}

// ===========================================================================
// Main Scene — adapts FOV, DPR, and quality tier to the device
// ===========================================================================
export default function Scene() {
  const tier = useDeviceTier();
  const [perfTier, setPerfTier] = useState(2); // 0=lowest, 2=highest

  const fov = tier === 'mobile' ? 72 : tier === 'tablet' ? 68 : 65;
  const dprMax = tier === 'mobile' ? 1.25 : tier === 'tablet' ? 1.6 : 2;

  return (
    <Canvas
      gl={{ antialias: tier !== 'mobile', alpha: false, powerPreference: 'high-performance' }}
      dpr={[1, dprMax]}
      camera={{ position: [0, 6, 28], fov, near: 0.1, far: 2000 }}
      frameloop="always"
    >
      <PerformanceMonitor
        onIncline={() => setPerfTier((t) => Math.min(2, t + 1))}
        onDecline={() => setPerfTier((t) => Math.max(0, t - 1))}
      />
      <AdaptiveDpr pixelated />
      <AdaptiveEvents />
      <SceneContents tier={perfTier === 0 ? 'mobile' : tier} />
    </Canvas>
  );
}
