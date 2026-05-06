'use client';

import { useMemo, useRef } from 'react';
import { useFrame, invalidate } from '@react-three/fiber';
import * as THREE from 'three';

// ===========================================================================
// Procedural deep-space nebula — supermassive black hole explosion remnant
// Reference look: Hubble deep-field / Pillars of Creation / Veil Nebula —
// mostly dark void with structured filaments, stars dominate, no blow-outs.
// ===========================================================================

const vert = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vDir = normalize(wp.xyz);
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;

const frag = /* glsl */ `
  precision highp float;
  varying vec3 vDir;
  uniform float uTime;

  // ---------- Cheap value noise + 6-octave FBM ----------
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
    for (int i = 0; i < 6; i++) {
      v += a * noise(p);
      p = p * 2.07 + vec3(0.13, 0.71, 1.24);
      a *= 0.5;
    }
    return v;
  }

  // Domain-warped FBM — produces swirling filamentary dust lanes
  float swirl(vec3 p){
    vec3 q = vec3(
      fbm(p + vec3(0.00, 0.00, 0.00)),
      fbm(p + vec3(5.20, 1.30, 9.20)),
      fbm(p + vec3(8.70, 3.70, 2.80))
    );
    return fbm(p + 1.6 * q);
  }

  // ---------- Sparse 3D star sparkles ----------
  // Returns 0..1 brightness for a tiny pinpoint at a hashed cell centre.
  float starField(vec3 d, float scale, float threshold){
    vec3 c = floor(d * scale);
    float h = hash(c);
    if (h < threshold) return 0.0;
    vec3 f = fract(d * scale) - 0.5;
    float r = length(f);
    float bri = (h - threshold) / (1.0 - threshold);
    return smoothstep(0.06, 0.0, r) * bri;
  }

  void main() {
    vec3 d = normalize(vDir);

    // ---------- Sample filament density at two scales ----------
    float t = uTime * 0.012;
    vec3 p = d * 2.6 + vec3(t, -t * 0.5, t * 0.3);
    float coarse = swirl(p);
    float fine   = fbm(p * 5.5);
    float density = coarse * 0.72 + fine * 0.28;

    // Sharpen + threshold so most of the sky is true dark void.
    // Anything below 0.42 becomes empty space; anything above 0.78
    // is a bright filament. Smoothstep keeps soft edges.
    density = smoothstep(0.42, 0.78, density);
    density = pow(density, 1.35);

    // ---------- Photo-realistic nebula colour ramp ----------
    // Inspired by Hubble narrowband palettes: void → indigo → magenta dust →
    // warm hydrogen-alpha → soft pink ionised core. Brightness stays in the
    // 0.0–0.7 range — we let bloom on the rare bright stars do the punch.
    vec3 voidCol = vec3(0.005, 0.008, 0.022);   // near-black with cool tint
    vec3 deepCol = vec3(0.040, 0.025, 0.110);   // indigo gas
    vec3 dustCol = vec3(0.32,  0.10,  0.34);    // magenta dust lane
    vec3 warmCol = vec3(0.55,  0.28,  0.22);    // warm hydrogen
    vec3 hotCol  = vec3(0.85,  0.55,  0.62);    // pink ionised — soft, NOT white

    vec3 col = voidCol;
    col = mix(col, deepCol, smoothstep(0.00, 0.25, density));
    col = mix(col, dustCol, smoothstep(0.25, 0.55, density));
    col = mix(col, warmCol, smoothstep(0.55, 0.80, density));
    col = mix(col, hotCol,  smoothstep(0.80, 0.97, density));

    // Density-driven brightness modulation — most of frame stays dim.
    col *= 0.32 + density * 0.55;

    // ---------- Subtle cyan-blue ambient haze in the voids ----------
    col += vec3(0.012, 0.020, 0.040) * (1.0 - density);

    // ---------- Stars: three layers of pinpoint detail ----------
    // Tiny background stars — very dense field, very faint
    float s1 = starField(d, 360.0, 0.992);
    col += vec3(0.85, 0.88, 1.00) * s1 * 0.55;

    // Mid-distance white stars
    float s2 = starField(d, 140.0, 0.996);
    col += vec3(1.0, 0.96, 0.88) * s2 * 1.1;

    // Rare close bright stars with colour temperature variation
    vec3 cb = floor(d * 60.0);
    float s3h = hash(cb + vec3(7.0, 3.0, 1.0));
    if (s3h > 0.9985) {
      vec3 fp = fract(d * 60.0) - 0.5;
      float r = length(fp);
      float bri = (s3h - 0.9985) / 0.0015;
      // colour by another hash — blue, white, or amber
      float cHash = hash(cb + vec3(11.0, 5.0, 2.0));
      vec3 starCol = cHash < 0.33 ? vec3(0.7, 0.85, 1.0)
                  : cHash < 0.67 ? vec3(1.0, 0.97, 0.92)
                                 : vec3(1.0, 0.78, 0.55);
      col += starCol * smoothstep(0.05, 0.0, r) * bri * 1.6;
    }

    // ---------- Slight film grain (deterministic, per-fragment) ----------
    float grain = (hash(d * 4096.0 + uTime) - 0.5) * 0.012;
    col += grain;

    gl_FragColor = vec4(max(col, 0.0), 1.0);
  }
`;

interface NebulaProps {
  /** Slow internal rotation of the entire skybox sphere */
  rotationSpeed?: number;
  /** When false, skip uTime advance + invalidate (saves GPU during dashboard) */
  active?: boolean;
}

export default function Nebula({
  rotationSpeed = 0.004,
  active = true,
}: NebulaProps) {
  const groupRef = useRef<THREE.Group>(null!);
  const startRef = useRef<number>(performance.now() / 1000);

  const mat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0.0 } },
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
        {/* Geometry cost is irrelevant — every fragment is shaded procedurally. */}
        <sphereGeometry args={[600, 48, 32]} />
      </mesh>
    </group>
  );
}
