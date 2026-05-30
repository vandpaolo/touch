// Headless FE<->BE wire-parity check: connect to a running sidecar, decode
// the binary frame with the SAME decoder the viewport uses, assert the cube
// shape. Does NOT exercise three.js rendering/hover (that's a visual browser
// check) — it proves the frontend reads the backend frame correctly.
//
// Run via verify_day2.sh, or: node --experimental-strip-types verify_day2.ts <port>
import { decodeMesh } from "./src/wire.ts";

const port = Number(process.argv[2]);
if (!Number.isInteger(port)) {
  console.error("usage: verify_day2.ts <port>");
  process.exit(2);
}

const ws = new WebSocket(`ws://127.0.0.1:${port}`);
ws.binaryType = "arraybuffer";

const timer = setTimeout(() => {
  console.error("FAIL: no frame within 5s");
  process.exit(1);
}, 5000);

ws.onerror = () => {
  console.error(`FAIL: WS error (port ${port})`);
  process.exit(1);
};

ws.onmessage = (ev: MessageEvent) => {
  clearTimeout(timer);
  const mesh = decodeMesh(ev.data as ArrayBuffer);
  const verts = mesh.vertices.length / 3;
  const tris = mesh.faceTagPerTriangle.length;
  const faces = new Set(mesh.faceTagPerTriangle);
  console.log(`version: ${mesh.version}`);
  console.log(`vertices: ${verts}`);
  console.log(`triangles: ${tris}`);
  console.log(`distinct face tags: [${[...faces].sort((a, b) => a - b).join(", ")}]`);
  const ok = mesh.version === 1 && verts === 8 && tris === 12 && faces.size === 6;
  console.log(ok ? "PASS" : "FAIL");
  ws.close();
  process.exit(ok ? 0 : 1);
};
