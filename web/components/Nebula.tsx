'use client';

import { useMemo, useRef } from 'react';
import { useFrame, invalidate } from '@react-three/fiber';
import * as THREE from 'three';

// ===========================================================================
// Procedural nebula — supermassive black hole explosion remnant
// Rendered as a large back-faced sphere (skybox-style) so it fills every
// pixel of the camera frustum regardless of look direction.
// ===========================================================================

const vert = /* glsl */ `
  varying vec3 vDir;
  void main() {
    // Pass world-space direction from origin (camera centre) to fragment.
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vDir = normalize(wp.xyz);
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;

const frag = /* glsl */ `
  precision highp float;
  varying vec3 vDir;
  uniform float uTime;
  uniform vec3  uEpi;     // direction of the explosion epicentre
  uniform vec3  uTintA;   // hot inner colour
  uniform vec3  uTintB;   // mid filament colour
  uniform vec3  uTintC;   // cool outer colour

  // Cheap value noise + FBM in 3D — good enough for a wispy nebula.
  float hash(vec3 p){ return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453123); }

  float noise(vec3 p){
    vec3 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(mix(hash(i + vec3(0,0,0)), hash(i + vec3(1,0,0)), f.x),
          mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
      mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
          mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y),
      f.z);
  }

  float fbm(vec3 p){
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
    return v;
  }

  void main() {
    vec3 d   = normalize(vDir);
    vec3 epi = normalize(uEpi);

    // Angular distance from epicentre (0 at centre → ~2 on opposite side)
    float ang = 1.0 - dot(d, epi);

    // Slow swirl of the fbm sample point
    float t = uTime * 0.025;
    vec3 p1 = d * 2.4  + vec3( t, -t * 0.6,  t * 0.4);
    vec3 p2 = d * 5.2  + vec3(-t * 0.7, t,  -t * 0.5) + fbm(p1);
    vec3 p3 = d * 11.0 + vec3( t * 0.3, t * 0.2, t * 0.8);

    float bigDust   = fbm(p1);
    float midDust   = fbm(p2);
    float fineDust  = noise(p3);

    // Combined "cloud density"
    float dust = pow(0.55 * bigDust + 0.35 * midDust + 0.15 * fineDust, 1.7);

    // Radial brightness: hot near epicentre, falling off with angle
    float core   = exp(-ang * 5.5);                                  // white-hot remnant
    float shock  = exp(-pow((ang - 0.45) * 3.2, 2.0));               // shockwave ring
    float halo   = exp(-ang * 1.2);                                  // wide outer glow

    // Hot accretion-core colour (white → orange) tinted by uTintA
    vec3 hot = mix(vec3(1.0, 0.95, 0.85), uTintA, 0.4);

    // Build colour from cool background → mid filaments → shock → core
    vec3 col = uTintC * 0.18;                       // deep ambient void
    col += uTintB * dust * halo * 1.05;             // wide colourful gas
    col += mix(uTintA, uTintB, dust) * shock * dust * 1.6; // ring filaments
    col += hot * core * 1.6;                        // bright epicentre
    col += hot * pow(core, 3.0) * 3.5;              // hyper-bright pinpoint (bloom-eligible)

    // Star sparkle field — sparse but bright, derived from cell hash
    vec3 sc = floor(d * 320.0);
    float s = hash(sc);
    float star = smoothstep(0.9965, 1.0, s);
    col += vec3(star) * 1.4;

    // Subtle vignette toward the anti-epicentre so the eye is drawn in
    col *= 1.0 - smoothstep(1.4, 2.0, ang) * 0.55;

    gl_FragColor = vec4(col, 1.0);
  }
`;

interface NebulaProps {
  /** Slow internal rotation of the whole sphere — adds gentle motion */
  rotationSpeed?: number;
  /** Whether per-frame time advance + invalidate ticks fire */
  active?: boolean;
}

export default function Nebula({
  rotationSpeed = 0.005,
  active = true,
}: NebulaProps) {
  const groupRef = useRef<THREE.Group>(null!);
  const startRef = useRef<number>(performance.now() / 1000);

  const mat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: {
      uTime:  { value: 0.0 },
      // Explosion epicentre roughly forward + slightly up — feels framed
      uEpi:   { value: new THREE.Vector3(0.05, 0.15, -1.0).normalize() },
      // Plasma palette — magenta core, electric cyan filaments, indigo void
      uTintA: { value: new THREE.Color('#FF4FB0') },     // hot pink
      uTintB: { value: new THREE.Color('#22D3EE') },     // cyan
      uTintC: { value: new THREE.Color('#0B0E2A') },     // deep indigo void
    },
    vertexShader: vert,
    fragmentShader: frag,
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: false,
    toneMapped: true,
  }), []);

  useFrame(() => {
    if (!active) return;
    mat.uniforms.uTime.value = performance.now() / 1000 - startRef.current;
    if (groupRef.current) groupRef.current.rotation.y += rotationSpeed * 0.016;
    invalidate();
  });

  return (
    <group ref={groupRef}>
      <mesh material={mat} renderOrder={-10}>
        {/* Large enough to sit beyond all foreground geometry, segments low
            because every fragment is shaded procedurally — the geometry
            cost is irrelevant. */}
        <sphereGeometry args={[600, 48, 32]} />
      </mesh>
    </group>
  );
}
