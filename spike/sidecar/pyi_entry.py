"""PyInstaller entry point for the bundled sidecar.

PyInstaller analyses a real script, not `python -m pkg`. This thin shim just
calls the same `main()` that `python -m touch_sidecar` does, so the frozen
binary and the dev invocation share one code path.
"""

from touch_sidecar.server import main

if __name__ == "__main__":
    main()
