// Electron main process for the T0 spike.
//
// Flow: spawn the Python sidecar -> wait for TOUCH_READY <port> on its stdout
// (R3: no naive setTimeout race) -> open a BrowserWindow loading the
// Vite-built viewport with ?port=<port> injected -> supervise both directions
// (sidecar dies -> app quits; window closes -> sidecar killed).

import { app, BrowserWindow } from "electron";
import * as path from "node:path";
import { spawnSidecar, devSidecarSpec, type SidecarHandle, type SidecarSpec } from "./sidecar.js";

let sidecar: SidecarHandle | null = null;
let quitting = false;

// Packaged (Day 5): the PyInstaller --onedir output is shipped under
// resources/sidecar/ (asarUnpack'd), resolved via process.resourcesPath (R2).
function packagedSidecarSpec(): SidecarSpec {
  const dir = path.join(process.resourcesPath, "sidecar");
  return { command: path.join(dir, "touch_sidecar"), args: [], cwd: dir };
}

function resolveIndexHtml(): string {
  return app.isPackaged
    ? path.join(process.resourcesPath, "web", "index.html")
    : path.join(__dirname, "..", "..", "web", "dist", "index.html");
}

async function main(): Promise<void> {
  await app.whenReady();

  const shellRoot = path.join(__dirname, ".."); // dist/ -> spike/shell
  const spec = app.isPackaged ? packagedSidecarSpec() : devSidecarSpec(shellRoot);
  sidecar = spawnSidecar(spec);

  sidecar.proc.on("exit", (code) => {
    if (!quitting) {
      console.error(`[shell] sidecar exited (code ${code}); quitting`);
      app.quit();
    }
  });

  let port: number;
  try {
    port = await sidecar.port;
  } catch (err) {
    console.error(`[shell] ${(err as Error).message}`);
    app.quit();
    return;
  }
  console.log(`[shell] sidecar ready on port ${port}`);

  const win = new BrowserWindow({
    width: 1100,
    height: 800,
    backgroundColor: "#1e1e1e",
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  await win.loadFile(resolveIndexHtml(), { query: { port: String(port) } });
}

// Window closed -> quit the app; quitting -> kill the sidecar.
app.on("window-all-closed", () => app.quit());
app.on("before-quit", () => {
  quitting = true;
  sidecar?.proc.kill();
});

main();
