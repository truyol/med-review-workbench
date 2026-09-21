import { Component, Suspense, useEffect, useRef, type ReactNode } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { Bounds, OrbitControls, useBounds } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { Button, Typography } from "antd";
import { assetModelUrl } from "../../shared/api/client";

type FitRef = { current: () => void };

export default function StlViewer({ assetId }: { assetId: string }) {
  const fitRef = useRef<() => void>(() => undefined);

  return (
    <ViewerErrorBoundary assetId={assetId}>
      <div className="stl-viewer">
        <Canvas camera={{ position: [0, 0, 260], fov: 45, near: 0.1, far: 100000 }}>
          <ambientLight intensity={0.85} />
          <directionalLight position={[140, 180, 220]} intensity={1.15} />
          <directionalLight position={[-160, -120, -140]} intensity={0.35} />
          <Suspense fallback={null}>
            <Bounds fit clip observe margin={1.25}>
              <FitController fitRef={fitRef} />
              <StlModel assetId={assetId} />
            </Bounds>
          </Suspense>
          <OrbitControls makeDefault enableDamping dampingFactor={0.08} />
        </Canvas>
        <div className="stl-toolbar">
          <Typography.Text type="secondary">拖动旋转 · 滚轮缩放 · 右键平移</Typography.Text>
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

function StlModel({ assetId }: { assetId: string }) {
  const geometry = useLoader(STLLoader, assetModelUrl(assetId));

  useEffect(() => {
    // Center the mesh so rotation feels natural, then rebuild normals for shading.
    geometry.center();
    geometry.computeVertexNormals();
  }, [geometry]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#4f9cf9" roughness={0.42} metalness={0.15} />
    </mesh>
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
