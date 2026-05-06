'use client';

import { useMemo, useRef } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import * as THREE from 'three';

// Free NASA-derived textures hosted on the three.js GitHub via jsdelivr CDN.
// Hosting these on a CDN offloads bandwidth from Railway and lets the browser
// cache them across visits.
const TEX_BASE = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r169/examples/textures/planets';
const URL_DAY      = `${TEX_BASE}/earth_atmos_2048.jpg`;
const URL_NORMAL   = `${TEX_BASE}/earth_normal_2048.jpg`;
const URL_SPECULAR = `${TEX_BASE}/earth_specular_2048.jpg`;
const URL_CLOUDS   = `${TEX_BASE}/earth_clouds_1024.png`;

// Fragment shader — photoreal Earth with day/night terminator, city lights,
// fresnel atmosphere rim, and Phong-style ocean specular.
const earthVert = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vViewDir;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vNormal = normalize(mat3(modelMatrix) * normal);
    vViewDir = normalize(cameraPosition - worldPos.xyz);
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

const earthFrag = /* glsl */ `
  uniform sampler2D dayMap;
  uniform sampler2D normalMap;
  uniform sampler2D specMap;
  uniform vec3 sunDir;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  varying vec2 vUv;

  void main() {
    vec3 baseColor = texture2D(dayMap, vUv).rgb;
    vec3 specMask = texture2D(specMap, vUv).rgb;

    // Light intensity (sun direction is in world space)
    float intensity = dot(normalize(vNormal), normalize(sunDir));

    // Smooth terminator
    float dayMix = smoothstep(-0.1, 0.25, intensity);

    // Day side — gentle ambient + diffuse
    vec3 day = baseColor * (0.15 + max(intensity, 0.0) * 1.05);

    // Ocean specular highlight (only where specular mask says water)
    vec3 reflectDir = reflect(-normalize(sunDir), normalize(vNormal));
    float spec = pow(max(dot(reflectDir, vViewDir), 0.0), 32.0);
    day += specMask * spec * 0.55;

    // Night side — city lights derived from inverse darkness of day map
    // Land tends to be brighter than ocean in day map, so we invert specMask
    // to find land, then sample brighter pockets as city glow.
    float landMask = 1.0 - clamp(specMask.r * 1.4, 0.0, 1.0);
    vec3 lightSrc = pow(baseColor, vec3(0.55)) * landMask;
    vec3 cityGlow = lightSrc * vec3(1.35, 0.85, 0.45) * 1.3;
    vec3 night = cityGlow * smoothstep(0.05, -0.25, intensity);

    vec3 surface = mix(night, day, dayMix);

    // Atmospheric rim (fresnel)
    float fres = 1.0 - max(dot(normalize(vNormal), normalize(vViewDir)), 0.0);
    fres = pow(fres, 2.2);
    vec3 atmosphere = vec3(0.28, 0.55, 1.0) * fres * (0.45 + max(intensity, 0.0) * 0.7);
    surface += atmosphere;

    gl_FragColor = vec4(surface, 1.0);
  }
`;

// Atmosphere fresnel halo — separate slightly-larger sphere with backside additive blending
const atmoVert = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vViewDir;
  void main() {
    vec4 worldPos = modelMatrix * vec4(position, 1.0);
    vNormal = normalize(mat3(modelMatrix) * normal);
    vViewDir = normalize(cameraPosition - worldPos.xyz);
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

const atmoFrag = /* glsl */ `
  uniform vec3 sunDir;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  void main() {
    float fres = 1.0 - max(dot(normalize(vNormal), normalize(vViewDir)), 0.0);
    fres = pow(fres, 3.5);
    float litSide = max(dot(normalize(vNormal), normalize(sunDir)), 0.0);
    float intensity = fres * (0.55 + litSide * 0.9);
    vec3 col = vec3(0.32, 0.62, 1.0) * intensity;
    gl_FragColor = vec4(col, intensity);
  }
`;

interface EarthProps {
  position?: [number, number, number];
  size?: number;
  sunPosition?: THREE.Vector3 | [number, number, number];
  rotationSpeed?: number;
  active?: boolean;
}

export default function Earth({
  position = [0, 0, -55],
  size = 9,
  sunPosition = [60, 25, 30],
  rotationSpeed = 0.012,
  active = true,
}: EarthProps) {
  const earthRef = useRef<THREE.Mesh>(null!);
  const cloudsRef = useRef<THREE.Mesh>(null!);
  const groupRef = useRef<THREE.Group>(null!);

  const [dayTex, normalTex, specTex, cloudTex] = useLoader(THREE.TextureLoader, [
    URL_DAY,
    URL_NORMAL,
    URL_SPECULAR,
    URL_CLOUDS,
  ]);

  // Configure texture sampling for sharper detail
  useMemo(() => {
    [dayTex, normalTex, specTex, cloudTex].forEach((t) => {
      t.anisotropy = 8;
      t.colorSpace = THREE.SRGBColorSpace;
    });
  }, [dayTex, normalTex, specTex, cloudTex]);

  const sunVec = useMemo(() => {
    const v = Array.isArray(sunPosition) ? new THREE.Vector3(...sunPosition) : sunPosition.clone();
    return v.clone().sub(new THREE.Vector3(...position)).normalize();
  }, [sunPosition, position]);

  // Custom Earth shader material
  const earthMat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: {
      dayMap:    { value: dayTex },
      normalMap: { value: normalTex },
      specMap:   { value: specTex },
      sunDir:    { value: sunVec },
    },
    vertexShader: earthVert,
    fragmentShader: earthFrag,
  }), [dayTex, normalTex, specTex, sunVec]);

  // Atmospheric halo material
  const atmoMat = useMemo(() => new THREE.ShaderMaterial({
    uniforms: { sunDir: { value: sunVec } },
    vertexShader: atmoVert,
    fragmentShader: atmoFrag,
    transparent: true,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  }), [sunVec]);

  // Cloud layer material — uses standard textured material with subtle transparency
  const cloudMat = useMemo(() => new THREE.MeshLambertMaterial({
    map: cloudTex,
    transparent: true,
    opacity: 0.42,
    depthWrite: false,
  }), [cloudTex]);

  useFrame((_, dt) => {
    if (!active) return;
    if (earthRef.current) earthRef.current.rotation.y += dt * rotationSpeed;
    if (cloudsRef.current) cloudsRef.current.rotation.y += dt * rotationSpeed * 1.35;
  });

  return (
    <group ref={groupRef} position={position}>
      {/* Earth surface */}
      <mesh ref={earthRef} material={earthMat}>
        <sphereGeometry args={[size, 96, 96]} />
      </mesh>
      {/* Cloud layer */}
      <mesh ref={cloudsRef} material={cloudMat}>
        <sphereGeometry args={[size * 1.012, 64, 64]} />
      </mesh>
      {/* Atmospheric halo */}
      <mesh material={atmoMat} scale={1.08}>
        <sphereGeometry args={[size, 48, 48]} />
      </mesh>
      {/* Outer haze */}
      <mesh scale={1.2}>
        <sphereGeometry args={[size, 32, 32]} />
        <meshBasicMaterial
          color="#3B82F6"
          transparent
          opacity={0.05}
          side={THREE.BackSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}
