/* eslint-disable react-hooks/immutability -- three.js camera/controls are mutable objects by design */
import { Component, Suspense, useEffect, useMemo, useRef, type ReactNode } from "react";
import { Canvas, useLoader, useThree, type ThreeEvent } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { Button, Spin, Typography } from "antd";
import type { Annotation } from "../../shared/api/client";
import { assetModelUrl } from "../../shared/api/client";
import { markerColor } from "../../shared/markerColors";

export type MarkerPoint = { x: number; y: number; z: number };
type FitRef = { current: () => void };

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
        <Canvas camera={{ position: [0, 0, 1], fov: 45, near: 0.0001, far: 100000 }}>
          <ambientLight intensity={0.85} />
          <directionalLight position={[140, 180, 220]} intensity={1.15} />
          <directionalLight position={[-160, -120, -140]} intensity={0.35} />
          <Suspense
            fallback={
              <Html center>
                <Spin tip="正在加载模型" />
              </Html>
            }
          >
            <StlModel
              assetId={assetId}
              markers={markers}
              onPlaceMarker={onPlaceMarker}
              fitRef={fitRef}
            />
          </Suspense>
          <OrbitControls makeDefault enableDamping dampingFactor={0.08} />
        </Canvas>
        <div className="stl-toolbar">
          <Typography.Text type="secondary">
            拖动旋转 · 滚轮缩放 · 右键平移 · 点击模型放置结构标记
          </Typography.Text>
          <Button size="small" onClick={() => fitRef.current()}>
            视角复位
          </Button>
        </div>
      </div>
    </ViewerErrorBoundary>
  );
}

function StlModel({
  assetId,
  markers,
  onPlaceMarker,
  fitRef,
}: {
  assetId: string;
  markers: Annotation[];
  onPlaceMarker: (point: MarkerPoint) => void;
  fitRef: FitRef;
}) {
  const geometry = useLoader(STLLoader, assetModelUrl(assetId));
  const camera = useThree((state) => state.camera);
  const controls = useThree((state) => state.controls) as OrbitControlsImpl | null;
  const meshRef = useRef<THREE.Mesh>(null);
  const pointerDown = useRef<{ x: number; y: number } | null>(null);

  // Normalize the geometry and derive its scale once per loaded model. Models
  // can use very different coordinate units (this STL is ~0.14 units across),
  // so the camera is fitted from the bounding box instead of fixed numbers.
  const modelSize = useMemo(() => {
    geometry.center();
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    const size = new THREE.Vector3();
    geometry.boundingBox?.getSize(size);
    return Math.max(size.x, size.y, size.z, 1e-6);
  }, [geometry]);

  const markerRadius = Math.max(modelSize * 0.018, 1e-6);

  useEffect(() => {
    const perspective = camera as THREE.PerspectiveCamera;
    const fit = () => {
      const fov = (perspective.fov * Math.PI) / 180;
      const distance = (modelSize / 2 / Math.tan(fov / 2)) * 1.15;
      perspective.position.set(0, 0, distance);
      perspective.near = distance / 1000;
      perspective.far = distance * 1000;
      perspective.updateProjectionMatrix();
      perspective.lookAt(0, 0, 0);
      if (controls) {
        controls.target.set(0, 0, 0);
        controls.update();
      }
    };
    fit();
    fitRef.current = fit;
  }, [camera, controls, modelSize, fitRef]);

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
