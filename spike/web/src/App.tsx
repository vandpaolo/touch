import { Viewport } from "./Viewport";

// The sidecar binds an ephemeral port and prints it on stdout; in the real
// app Electron injects ?port=<port>. For browser-tab dev, append it yourself:
//   http://localhost:5173/?port=40879
function readPort(): number | null {
  const raw = new URLSearchParams(window.location.search).get("port");
  if (!raw) return null;
  const port = Number(raw);
  return Number.isInteger(port) && port > 0 && port < 65536 ? port : null;
}

export function App() {
  const port = readPort();

  if (port === null) {
    return (
      <div
        style={{
          color: "#ddd",
          font: "14px/1.5 system-ui, sans-serif",
          padding: "2rem",
        }}
      >
        <h2>Touch spike viewport</h2>
        <p>
          No sidecar port given. Start the sidecar (<code>python -m touch_sidecar</code>),
          note the <code>TOUCH_READY &lt;port&gt;</code> line, then open this page with{" "}
          <code>?port=&lt;port&gt;</code>.
        </p>
      </div>
    );
  }

  return <Viewport port={port} />;
}
