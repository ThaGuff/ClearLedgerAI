'use client';

import { useMemo, useRef } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import * as THREE from 'three';

const URL_MOON = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r169/examples/textures/planets/moon_1024.jpg';

interface MoonProps {
  earthPosition?: [number, number, number];
  orbitRadius?: number;
  orbitSpeed?: number;
  size?: number;
  active?: boolean;
}

export default function Moon({
  earthPosition = [0, 0, -55],
  orbitRadius = 18,
  orbitSpeed = 0.06,
  size = 1.6,
  active = true,
}: MoonProps) {
  const ref = useRef<THREE.Mesh>(null!);
  const moonTex = useLoader(THREE.TextureLoader, URL_MOON);

  useMemo(() => {
    moonTex.anisotropy = 8;
    moonTex.colorSpace = THREE.SRGBColorSpace;
  }, [moonTex]);

  useFrame((state, dt) => {
    if (!active || !ref.current) return;
    const t = state.clock.elapsedTime * orbitSpeed;
    ref.current.position.set(
      earthPosition[0] + Math.cos(t) * orbitRadius,
      earthPosition[1] + Math.sin(t * 0.4) * 3,
      earthPosition[2] + Math.sin(t) * orbitRadius * 0.6,
    );
    ref.current.rotation.y += dt * 0.05;
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[size, 48, 48]} />
      <meshStandardMaterial map={moonTex} roughness={0.95} metalness={0.0} />
    </mesh>
  );
}
