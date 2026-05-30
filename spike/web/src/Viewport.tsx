import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { decodeMesh, type Mesh } from "./wire";

// Base (un-hovered) face colour, and a distinct highlight colour per face
// tag so mousing over each of the 6 cube faces reads differently (the Day-2
// "done when"). Indexed by face tag (0..5).
const BASE_COLOR = new THREE.Color(0x6a6a72);
const HIGHLIGHT_BY_TAG = [
  new THREE.Color(0xe6584d), // +X red
  new THREE.Color(0x4db8e6), // -X cyan
  new THREE.Color(0x6fd06f), // +Y green
  new THREE.Color(0xe6c84d), // -Y yellow
  new THREE.Color(0xb784e6), // +Z purple
  new THREE.Color(0xe69a4d), // -Z orange
];

// Expand an indexed mesh into a non-indexed BufferGeometry so each triangle
// owns its 3 vertices — required for crisp per-face colouring and flat
// normals. With non-indexed geometry the raycaster's `faceIndex` is exactly
// the triangle index, so face_tag_per_triangle[faceIndex] is an O(1) lookup
// (the picking pattern T1b reuses against the real tessellator).
function buildGeometry(mesh: Mesh): THREE.BufferGeometry {
  const triCount = mesh.faceTagPerTriangle.length;
  const positions = new Float32Array(triCount * 3 * 3);
  const colors = new Float32Array(triCount * 3 * 3);

  for (let t = 0; t < triCount; t++) {
    for (let c = 0; c < 3; c++) {
      const vi = mesh.indices[t * 3 + c];
      const po = (t * 3 + c) * 3;
      positions[po] = mesh.vertices[vi * 3];
      positions[po + 1] = mesh.vertices[vi * 3 + 1];
      positions[po + 2] = mesh.vertices[vi * 3 + 2];
      colors[po] = BASE_COLOR.r;
      colors[po + 1] = BASE_COLOR.g;
      colors[po + 2] = BASE_COLOR.b;
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geo.computeVertexNormals(); // flat normals (non-indexed) — faceted cube
  return geo;
}

export function Viewport({ port }: { port: number }) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState("connecting…");

  useEffect(() => {
    const mount = mountRef.current!;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1e1e1e);

    const camera = new THREE.PerspectiveCamera(
      50,
      mount.clientWidth / mount.clientHeight,
      0.1,
      100,
    );
    camera.position.set(4, 3, 5);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 0.9);
    dir.position.set(5, 8, 6);
    scene.add(dir);

    let mesh: Mesh | null = null;
    let object: THREE.Mesh | null = null;
    let colorAttr: THREE.BufferAttribute | null = null;
    let hoveredTag = -1;

    // Recolour every vertex: triangles whose face tag == `tag` get that
    // tag's highlight colour, everything else the base colour.
    function applyHighlight(tag: number) {
      if (!mesh || !colorAttr) return;
      const arr = colorAttr.array as Float32Array;
      for (let t = 0; t < mesh.faceTagPerTriangle.length; t++) {
        const c =
          mesh.faceTagPerTriangle[t] === tag
            ? HIGHLIGHT_BY_TAG[tag % HIGHLIGHT_BY_TAG.length]
            : BASE_COLOR;
        for (let k = 0; k < 3; k++) {
          const po = (t * 3 + k) * 3;
          arr[po] = c.r;
          arr[po + 1] = c.g;
          arr[po + 2] = c.b;
        }
      }
      colorAttr.needsUpdate = true;
    }

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let havePointer = false;

    function onPointerMove(e: PointerEvent) {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      havePointer = true;
    }
    renderer.domElement.addEventListener("pointermove", onPointerMove);

    // --- transport -------------------------------------------------------
    const ws = new WebSocket(`ws://127.0.0.1:${port}`);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => setStatus("connected — waiting for mesh…");
    ws.onerror = () => setStatus(`WS error (port ${port})`);
    ws.onclose = () => setStatus((s) => (mesh ? s : "disconnected"));
    ws.onmessage = (ev) => {
      if (!(ev.data instanceof ArrayBuffer)) return;
      mesh = decodeMesh(ev.data);
      const geo = buildGeometry(mesh);
      colorAttr = geo.getAttribute("color") as THREE.BufferAttribute;
      const mat = new THREE.MeshStandardMaterial({
        vertexColors: true,
        flatShading: true,
        metalness: 0.0,
        roughness: 0.85,
      });
      object = new THREE.Mesh(geo, mat);
      scene.add(object);
      setStatus(
        `mesh: ${mesh.vertices.length / 3} verts, ` +
          `${mesh.faceTagPerTriangle.length} tris, ` +
          `${new Set(mesh.faceTagPerTriangle).size} faces — hover a face`,
      );
    };

    // --- render loop -----------------------------------------------------
    let raf = 0;
    function tick() {
      raf = requestAnimationFrame(tick);
      controls.update();

      if (object && havePointer) {
        raycaster.setFromCamera(pointer, camera);
        const hit = raycaster.intersectObject(object)[0];
        const tag =
          hit && hit.faceIndex != null && mesh
            ? mesh.faceTagPerTriangle[hit.faceIndex]
            : -1;
        if (tag !== hoveredTag) {
          hoveredTag = tag;
          applyHighlight(tag); // tag === -1 → all base (clears highlight)
        }
      }
      renderer.render(scene, camera);
    }
    tick();

    function onResize() {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    }
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      renderer.domElement.removeEventListener("pointermove", onPointerMove);
      ws.close();
      controls.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [port]);

  return (
    <div ref={mountRef} style={{ position: "fixed", inset: 0 }}>
      <div
        style={{
          position: "absolute",
          top: 8,
          left: 12,
          color: "#bbb",
          font: "12px/1.4 system-ui, sans-serif",
          pointerEvents: "none",
        }}
      >
        {status}
      </div>
    </div>
  );
}
