import { Component, Suspense, useEffect, useMemo, useRef, type ReactNode } from "react";
import { Canvas, useLoader, type ThreeEvent } from "@react-three/fiber";
import { Bounds, OrbitControls, useBounds } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";
import { Button, Typography } from "antd";
import type { Annotation } from "../../shared/api/client";
import { assetModelUrl } from "../../shared/api/client";
import { markerColor } from "../../shared/markerColors";

type FitRef = { current: () => void };

export type MarkerPoint = { x: number; y: number; z: number };

export default function StlViewer({
  assetId,
  markers,
  onPlaceMarker,
}: {
  assetId: string;
  markers: Annotation[];
  onPlaceMarker: (point: MarkerPoint) => void;
}) {
  const fitRef = useRef<() => void>(() => undefined);

  return (
    <ViewerErrorBoundary assetId={assetId}>
      <div className="stl-viewer">
        <Canvas camera={{ position: [0, 0, 260], fov: 45, near: 0.1, far: 100000 }}>
          <ambientLight intensity={0.85} />
          <directionalLight position={[140, 180, 220]} intensity={1.15} />
          <directionalLight position={[-160, -120, -140]} intensity={0.35} />
          <Suspense fallback={null}>
            <Bounds fit observe margin={1.2}>
              <FitController fitRef={fitRef} />
              <StlModel assetId={assetId} markers={markers} onPlaceMarker={onPlaceMarker} />
            </Bounds>
          </Suspense>
          <OrbitControls makeDefault enableDamping dampingFactor={0.08} />
        </Canvas>
        <div className="stl-toolbar">
          <Typography.Text type="secondary">拖动旋转 · 滚轮缩放 · 右键平移 · 点击模型放置结构标记</Typography.Text>
          <Button size="small" onClick={() => fitRef.current()}>
            视角复位
          </Button>
        </div>
      </div>
    </ViewerErrorBoundary>
  );
}

function FitController({ fitRef }: { fitRef: FitRef }) {
  const bounds = useBounds();
  useEffect(() => {
    fitRef.current = () => {
      bounds.refresh().clip().fit();
    };
  }, [bounds, fitRef]);
  return null;
}

function StlModel({
  assetId,
  markers,
  onPlaceMarker,
}: {
  assetId: string;
  markers: Annotation[];
  onPlaceMarker: (point: MarkerPoint) => void;
}) {
  const geometry = useLoader(STLLoader, assetModelUrl(assetId));
  const meshRef = useRef<THREE.Mesh>(null);
  const pointerDown = useRef<{ x: number; y: number } | null>(null);

  // Normalize the geometry once per loaded model and derive a marker size that
  // scales with the model. Both operations are idempotent.
  const markerRadius = useMemo(() => {
    geometry.center();
    geometry.computeVertexNormals();
    geometry.computeBoundingSphere();
    return Math.max((geometry.boundingSphere?.radius ?? 100) * 0.012, 0.005);
  }, [geometry]);

  const handlePointerDown = (event: ThreeEvent<PointerEvent>) => {
    pointerDown.current = { x: event.clientX, y: event.clientY };
  };

  const handlePointerUp = (event: ThreeEvent<PointerEvent>) => {
    const start = pointerDown.current;
    pointerDown.current = null;
    if (!start || !meshRef.current) {
      return;
    }
    // Ignore orbit drags: only a near-stationary press places a marker.
    const moved = Math.hypot(event.clientX - start.x, event.clientY - start.y);
    if (moved > 4) {
      return;
    }
    event.stopPropagation();
    // Convert the world-space hit point back into the centered model space so the
    // stored marker stays aligned with the geometry on reload.
    const local = meshRef.current.worldToLocal(event.point.clone());
    onPlaceMarker({ x: local.x, y: local.y, z: local.z });
  };

  return (
    <>
      <mesh
        ref={meshRef}
        geometry={geometry}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
      >
        <meshStandardMaterial color="#4f9cf9" roughness={0.42} metalness={0.15} />
      </mesh>
      {markers.map((marker, index) => {
        const color = markerColor(index);
        return (
          <mesh
            key={marker.id}
            position={[marker.data.x ?? 0, marker.data.y ?? 0, marker.data.z ?? 0]}
          >
            <sphereGeometry args={[markerRadius, 20, 20]} />
            <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.35} />
          </mesh>
        );
      })}
    </>
  );
}

type ViewerErrorBoundaryState = { failed: boolean };

class ViewerErrorBoundary extends Component<
  { assetId: string; children: ReactNode },
  ViewerErrorBoundaryState
> {
  state: ViewerErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): ViewerErrorBoundaryState {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) {
      return this.props.children;
    }
    return (
      <div className="viewer-fallback">
        <Typography.Text>3D 模型加载失败</Typography.Text>
        <Button size="small" onClick={() => this.setState({ failed: false })}>
          重试
        </Button>
      </div>
    );
  }
}
