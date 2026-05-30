// Sidecar lifecycle helper — deliberately Electron-free so it can be driven
// from a plain-node headless smoke (dist/smoke.js) as well as from the
// Electron main process (main.ts). Covers risks R2 (spawn), R3 (ready-race
// via the TOUCH_READY sentinel), R4 (ephemeral port read off stdout).

import { spawn, type ChildProcess } from "node:child_process";
import { createInterface } from "node:readline";
import * as path from "node:path";

export interface SidecarHandle {
  proc: ChildProcess;
  /** Resolves with the port parsed from `TOUCH_READY <port>`, or rejects. */
  port: Promise<number>;
}

export interface SidecarSpec {
  command: string;
  args: string[];
  cwd: string;
}

const READY_RE = /^TOUCH_READY (\d+)$/;
const READY_TIMEOUT_MS = 10_000;

export function spawnSidecar(spec: SidecarSpec): SidecarHandle {
  // stdout piped (we parse the sentinel); stderr inherited so failures are
  // visible; stdin ignored.
  const proc = spawn(spec.command, spec.args, {
    cwd: spec.cwd,
    stdio: ["ignore", "pipe", "inherit"],
  });

  const port = new Promise<number>((resolve, reject) => {
    const rl = createInterface({ input: proc.stdout! });
    const timer = setTimeout(() => {
      reject(new Error(`sidecar: no TOUCH_READY within ${READY_TIMEOUT_MS} ms`));
    }, READY_TIMEOUT_MS);

    rl.on("line", (line) => {
      const m = READY_RE.exec(line.trim());
      if (m) {
        clearTimeout(timer);
        resolve(Number(m[1]));
      }
    });
    proc.on("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`sidecar exited (code ${code}) before TOUCH_READY`));
    });
    proc.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
  });

  return { proc, port };
}

/**
 * Dev (Linux, pre-PyInstaller): run the editable sidecar from its venv.
 * `shellRoot` is the spike/shell directory; the sidecar lives at ../sidecar.
 */
export function devSidecarSpec(shellRoot: string): SidecarSpec {
  const sidecarDir = path.resolve(shellRoot, "..", "sidecar");
  const py = path.join(sidecarDir, ".venv", "bin", "python");
  return { command: py, args: ["-m", "touch_sidecar"], cwd: sidecarDir };
}
