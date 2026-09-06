import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export type BreathingPhase = 'idle' | 'inhale' | 'hold_in' | 'exhale' | 'hold_out';

interface BreathingSphereProps {
  phase: BreathingPhase;
  progressInPhase: number; // 0.0 to 1.0 progress within the current phase
  isActive: boolean;
}

export const BreathingSphere: React.FC<BreathingSphereProps> = ({
  phase,
  progressInPhase,
  isActive,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const coreMeshRef = useRef<THREE.Mesh | null>(null);
  const wireMeshRef = useRef<THREE.Mesh | null>(null);
  const particlesRef = useRef<THREE.Points | null>(null);
  const targetScaleRef = useRef<number>(1.0);
  const currentScaleRef = useRef<number>(1.0);

  // Compute target scale based on phase and progress
  useEffect(() => {
    if (!isActive || phase === 'idle') {
      targetScaleRef.current = 1.0;
      return;
    }

    const minScale = 1.0;
    const maxScale = 1.85;

    // Smooth sinusoidal easing
    const easeInOut = (t: number) => 0.5 * (1 - Math.cos(Math.PI * t));

    if (phase === 'inhale') {
      targetScaleRef.current = minScale + (maxScale - minScale) * easeInOut(progressInPhase);
    } else if (phase === 'hold_in') {
      // Subtle pulse during hold
      targetScaleRef.current = maxScale + 0.03 * Math.sin(progressInPhase * Math.PI * 4);
    } else if (phase === 'exhale') {
      targetScaleRef.current = maxScale - (maxScale - minScale) * easeInOut(progressInPhase);
    } else if (phase === 'hold_out') {
      targetScaleRef.current = minScale + 0.02 * Math.sin(progressInPhase * Math.PI * 4);
    }
  }, [phase, progressInPhase, isActive]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 320;
    const height = container.clientHeight || 320;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 5.5;

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    rendererRef.current = renderer;

    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLightCyan = new THREE.PointLight(0x00dbe7, 2.5, 50);
    pointLightCyan.position.set(4, 4, 4);
    scene.add(pointLightCyan);

    const pointLightPurple = new THREE.PointLight(0xd0bcff, 2.0, 50);
    pointLightPurple.position.set(-4, -4, 4);
    scene.add(pointLightPurple);

    // 4. Core glowing sphere
    const coreGeometry = new THREE.IcosahedronGeometry(1.0, 4);
    const coreMaterial = new THREE.MeshStandardMaterial({
      color: 0x00363a,
      emissive: 0x00696f,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.8,
      wireframe: false,
    });
    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    scene.add(coreMesh);
    coreMeshRef.current = coreMesh;

    // 5. Outer Wireframe Cage
    const wireGeometry = new THREE.IcosahedronGeometry(1.22, 2);
    const wireMaterial = new THREE.MeshBasicMaterial({
      color: 0x00dbe7,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const wireMesh = new THREE.Mesh(wireGeometry, wireMaterial);
    scene.add(wireMesh);
    wireMeshRef.current = wireMesh;

    // 6. Floating ambient particles
    const particleCount = 200;
    const particleGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      const radius = 2.0 + Math.random() * 1.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      particlePositions[i] = radius * Math.sin(phi) * Math.cos(theta);
      particlePositions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePositions[i + 2] = radius * Math.cos(phi);
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0x74f5ff,
      size: 0.035,
      transparent: true,
      opacity: 0.6,
    });

    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
    particlesRef.current = particles;

    // 7. Animation Loop
    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Smooth scale interpolation towards target
      currentScaleRef.current += (targetScaleRef.current - currentScaleRef.current) * 0.1;
      const s = currentScaleRef.current;

      if (coreMeshRef.current) {
        coreMeshRef.current.scale.set(s, s, s);
        coreMeshRef.current.rotation.y += 0.005;
        coreMeshRef.current.rotation.x += 0.002;
      }

      if (wireMeshRef.current) {
        const wireScale = s * 1.15;
        wireMeshRef.current.scale.set(wireScale, wireScale, wireScale);
        wireMeshRef.current.rotation.y -= 0.004;
        wireMeshRef.current.rotation.z += 0.003;
      }

      if (particlesRef.current) {
        particlesRef.current.rotation.y += 0.001;
        particlesRef.current.rotation.x += 0.0005;
      }

      renderer.render(scene, camera);
    };

    animate();

    // 8. Resize Handler
    const handleResize = () => {
      if (!container || !rendererRef.current) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      if (rendererRef.current && rendererRef.current.domElement && container) {
        container.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
      coreGeometry.dispose();
      coreMaterial.dispose();
      wireGeometry.dispose();
      wireMaterial.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-72 sm:h-80 flex items-center justify-center cursor-default select-none pointer-events-none"
    />
  );
};
