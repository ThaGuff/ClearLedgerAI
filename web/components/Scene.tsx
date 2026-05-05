'use client';

import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  Stars,
  Sphere,
  Trail,
  Float,
  PerspectiveCamera,
} from '@react-three/drei';
import { EffectComposer, Bloom, ChromaticAberration, Vignette } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import { useRef, useMemo, useEffect } from 'react';
import * as THREE from 'three';
import { useStore } from '@/lib/store';

// ===========================================================================
// Planet — procedural, no textures required (works offline)
// ===========================================================================
function Planet({
  position,
  size = 2,
  color = '#22d3ee',
  emissive = '#0e1330',
  speed = 0.05,
  rings = false,
}: {
  position: [number, number, number];
  size?: number;
  color?: string;
  emissive?: string;
  speed?: number;
  rings?: boolean;
}) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((_, dt) => {
    if (ref.current) ref.current.rotation.y += dt * speed;
  });
  return (
    <Float speed={1.2} rotationIntensity={0.2} floatIntensity={0.4}>
      <group position={position}>
        <mesh ref={ref}>
          <sphereGeometry args={[size, 64, 64]} />
          <meshStandardMaterial
            color={color}
            emissive={emissive}
            emissiveIntensity={0.25}
            roughness={0.7}
            metalness={0.15}
          />
        </mesh>
        {/* Atmospheric glow shell */}
        <mesh scale={1.06}>
          <sphereGeometry args={[size, 32, 32]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.12}
            side={THREE.BackSide}
          />
        </mesh>
        {rings && (
          <mesh rotation={[Math.PI / 2.4, 0, 0]}>
            <ringGeometry args={[size * 1.4, size * 2.1, 96]} />
            <meshBasicMaterial color="#FBBF24" transparent opacity={0.35} side={THREE.DoubleSide} />
          </mesh>
        )}
      </group>
    </Float>
  );
}

// ===========================================================================
// Distant nebula clouds (textureless billboards)
// ===========================================================================
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

// ===========================================================================
// Comet streaks
// ===========================================================================
function Comet({ orbit = 30, speed = 0.3, offset = 0 }: { orbit?: number; speed?: number; offset?: number }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
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
        <meshBasicMaterial color="#F1F5F9" />
      </mesh>
    </Trail>
  );
}

// ===========================================================================
// Cockpit canopy frame — a giant inverted hemisphere with a metallic frame
// ===========================================================================
function CockpitCanopy() {
  // Tinted canopy glass (very faint, only visible from interior)
  return (
    <group>
      {/* Glass dome — see-through with a subtle blue tint */}
      <mesh>
        <sphereGeometry args={[18, 64, 64, 0, Math.PI * 2, 0, Math.PI / 1.6]} />
        <meshPhysicalMaterial
          color="#22d3ee"
          transparent
          opacity={0.04}
          transmission={0.92}
          roughness={0.05}
          metalness={0}
          ior={1.45}
          thickness={0.5}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Canopy structural frame — vertical ribs */}
      {[-1.05, -0.5, 0, 0.5, 1.05].map((angle, i) => (
        <mesh key={i} rotation={[0, angle, 0]}>
          <torusGeometry args={[18, 0.18, 12, 96, Math.PI * 0.95]} />
          <meshStandardMaterial color="#1F2937" metalness={0.95} roughness={0.25} />
        </mesh>
      ))}

      {/* Horizontal frame ring at viewport equator */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[17.9, 0.2, 12, 128]} />
        <meshStandardMaterial color="#0F172A" metalness={0.92} roughness={0.3} />
      </mesh>

      {/* Lower console — dashboard panel that reads as the front of cockpit */}
      <mesh position={[0, -8, -6]} rotation={[-Math.PI / 6, 0, 0]}>
        <boxGeometry args={[18, 5, 8]} />
        <meshStandardMaterial
          color="#0E1330"
          metalness={0.8}
          roughness={0.45}
          emissive="#22d3ee"
          emissiveIntensity={0.04}
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
    </group>
  );
}

// ===========================================================================
// External starship (visible only in 'exterior' stage)
// ===========================================================================
function Starship({ visible }: { visible: boolean }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame((_, dt) => {
    if (ref.current && visible) {
      ref.current.rotation.y += dt * 0.05;
    }
  });
  if (!visible) return null;
  return (
    <group ref={ref} position={[0, 0, 0]}>
      {/* Hull — elongated capsule */}
      <mesh>
        <capsuleGeometry args={[1.2, 4, 16, 32]} />
        <meshStandardMaterial color="#475569" metalness={0.92} roughness={0.3} />
      </mesh>
      {/* Cockpit window glow */}
      <mesh position={[0, 0, 1.6]}>
        <sphereGeometry args={[0.55, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshBasicMaterial color="#22d3ee" transparent opacity={0.85} toneMapped={false} />
      </mesh>
      {/* Engine glow */}
      <mesh position={[0, -2.6, 0]}>
        <coneGeometry args={[0.5, 1.2, 24]} />
        <meshBasicMaterial color="#A78BFA" toneMapped={false} />
      </mesh>
      <pointLight position={[0, -3, 0]} color="#7C3AED" intensity={6} distance={8} />
      {/* Wing fins */}
      <mesh position={[1.2, -0.6, 0]} rotation={[0, 0, -0.4]}>
        <boxGeometry args={[1.6, 0.1, 0.6]} />
        <meshStandardMaterial color="#334155" metalness={0.88} roughness={0.4} />
      </mesh>
      <mesh position={[-1.2, -0.6, 0]} rotation={[0, 0, 0.4]}>
        <boxGeometry args={[1.6, 0.1, 0.6]} />
        <meshStandardMaterial color="#334155" metalness={0.88} roughness={0.4} />
      </mesh>
    </group>
  );
}

// ===========================================================================
// Cinematic camera rig — fly from exterior into cockpit interior
// ===========================================================================
function CameraRig() {
  const { camera, gl } = useThree();
  const stage = useStore((s) => s.stage);
  const targetPos = useRef(new THREE.Vector3(0, 6, 28));
  const targetLook = useRef(new THREE.Vector3(0, 0, 0));
  const mouse = useRef({ x: 0, y: 0 });
  const startTime = useRef<number | null>(null);

  // Track mouse for parallax look in cockpit stage
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = (e.clientY / window.innerHeight) * 2 - 1;
      mouse.current.x = x;
      mouse.current.y = y;
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  useEffect(() => {
    startTime.current = null;
  }, [stage]);

  useFrame((state, dt) => {
    if (stage === 'exterior') {
      // Slow orbit around the starship from outside
      const t = state.clock.elapsedTime * 0.15;
      targetPos.current.set(Math.cos(t) * 14, 4 + Math.sin(t * 0.6) * 1.2, Math.sin(t) * 14);
      targetLook.current.set(0, 0, 0);
    } else if (stage === 'flying-in') {
      // Cinematic dolly: from current position into the cockpit window
      if (startTime.current === null) startTime.current = state.clock.elapsedTime;
      const elapsed = state.clock.elapsedTime - startTime.current;
      const k = Math.min(1, elapsed / 2.2);
      const eased = 1 - Math.pow(1 - k, 3); // easeOutCubic
      // Travel to cockpit interior position (inside the canopy)
      const startVec = new THREE.Vector3(camera.position.x, camera.position.y, camera.position.z);
      const endVec = new THREE.Vector3(0, 0.5, 0); // interior origin
      targetPos.current.copy(startVec).lerp(endVec, eased);
      // Look forward (out the canopy window)
      targetLook.current.set(0, 1, -10);
    } else {
      // Cockpit stage — anchored interior with mouse-parallax 360 look
      targetPos.current.set(0, 0.5, 0);
      // Look direction follows mouse for "head movement"
      const lx = mouse.current.x * 8;
      const ly = -mouse.current.y * 4 + 1;
      targetLook.current.set(lx, ly, -12);
    }

    // Smoothly interpolate camera + look-at
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
// Main Scene
// ===========================================================================
export default function Scene() {
  const stage = useStore((s) => s.stage);

  // Procedural distant stars + planets
  const planets = useMemo(() => ([
    { pos: [-22, 4, -42] as [number, number, number], size: 4.2, color: '#3B82F6', emissive: '#1E40AF', rings: true, speed: 0.04 },
    { pos: [28, -6, -55] as [number, number, number], size: 6.5, color: '#F472B6', emissive: '#9D174D', speed: 0.025 },
    { pos: [-35, 12, -70] as [number, number, number], size: 3.0, color: '#FBBF24', emissive: '#92400E', speed: 0.06 },
    { pos: [12, 18, -38] as [number, number, number], size: 1.8, color: '#A78BFA', emissive: '#5B21B6', speed: 0.08 },
    { pos: [40, 2, -90] as [number, number, number], size: 8.0, color: '#22D3EE', emissive: '#0E7490', speed: 0.02 },
  ]), []);

  return (
    <Canvas
      gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      dpr={[1, 2]}
      camera={{ position: [0, 6, 28], fov: 65, near: 0.1, far: 2000 }}
    >
      <color attach="background" args={['#020410']} />
      <fog attach="fog" args={['#020410', 60, 350]} />

      {/* Lights */}
      <ambientLight intensity={0.18} />
      <directionalLight position={[20, 10, 5]} intensity={1.2} color="#67E8F9" />
      <directionalLight position={[-15, -8, -10]} intensity={0.5} color="#F472B6" />
      <pointLight position={[0, 0, 0]} intensity={0.8} color="#22D3EE" distance={40} />

      {/* Deep starfield */}
      <Stars radius={300} depth={120} count={9000} factor={5} saturation={0.4} fade speed={0.4} />
      <Stars radius={120} depth={50} count={2500} factor={3} saturation={0} fade speed={0.6} />

      {/* Nebula clouds */}
      <Nebula position={[-60, 20, -120]} color="#7C3AED" scale={140} />
      <Nebula position={[80, -30, -140]} color="#22D3EE" scale={160} />
      <Nebula position={[0, 60, -180]} color="#F472B6" scale={120} />

      {/* Planets */}
      {planets.map((p, i) => (
        <Planet key={i} position={p.pos} size={p.size} color={p.color} emissive={p.emissive} speed={p.speed} rings={p.rings} />
      ))}

      {/* Comets */}
      <Comet orbit={45} speed={0.18} offset={0} />
      <Comet orbit={60} speed={0.12} offset={Math.PI} />
      <Comet orbit={38} speed={0.25} offset={Math.PI / 2} />

      {/* Starship (visible only outside) */}
      <Starship visible={stage === 'exterior' || stage === 'flying-in'} />

      {/* Cockpit canopy (visible inside) */}
      {(stage === 'cockpit' || stage === 'flying-in') && <CockpitCanopy />}

      {/* Camera control rig */}
      <CameraRig />

      {/* Postprocessing — bloom + chromatic + vignette */}
      <EffectComposer multisampling={0}>
        <Bloom intensity={0.85} luminanceThreshold={0.55} luminanceSmoothing={0.4} mipmapBlur />
        <ChromaticAberration
          blendFunction={BlendFunction.NORMAL}
          offset={new THREE.Vector2(0.0008, 0.0008)}
          radialModulation={false}
          modulationOffset={0}
        />
        <Vignette eskil={false} offset={0.1} darkness={0.85} />
      </EffectComposer>
    </Canvas>
  );
}
