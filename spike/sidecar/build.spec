# PyInstaller spec for the Touch spike sidecar — the heart of Day 4 (risk R1).
#
# OCP is shipped as a manylinux/auditwheel wheel: the Python extension lives at
# site-packages/OCP/ and its ~200 native OCCT shared libraries live in a
# SIBLING auditwheel dir whose name is derived from the *distribution* name —
# for the `cadquery-ocp` wheel that is `cadquery_ocp.libs/` (NOT `OCP.libs/`),
# with hash-suffixed files (e.g. libTKMath-150e51f6.so.7.8.1). The OCP
# extension's RPATH is `$ORIGIN/../cadquery_ocp.libs`, so PyInstaller's
# automatic analysis does not reliably pull the full set — we collect them
# explicitly. cadquery-ocp also depends on vtk, whose native libs live in a
# `vtkmodules/` sibling. This is exactly the "PyInstaller misses OCP's native
# libs" failure mode Day 4 exists to prove out.
#
# We DISCOVER the libs dir from the OCP extension's actual ldd output rather
# than hardcoding its name, so a wheel rename (cadquery-ocp vs ocp vs a future
# repack) doesn't silently ship a broken bundle.
#
# --onedir (NOT --onefile): onefile unpacks to a temp dir at every launch,
# which is slow for ~400 MB of libs and trips some AV heuristics (R11).
#
# Build:  pyinstaller build.spec --noconfirm
# Output: dist/touch_sidecar/  (a directory containing the `touch_sidecar`
#         binary + all libs; run dist/touch_sidecar/touch_sidecar)

import subprocess
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# --- locate the installed OCP extension -------------------------------------
import OCP  # noqa: E402

ocp_pkg_dir = Path(OCP.__file__).resolve().parent          # .../site-packages/OCP
site_packages = ocp_pkg_dir.parent
ocp_ext = next(ocp_pkg_dir.glob("OCP.*.so"))               # the compiled extension


def _resolved_lib_dirs(ext: Path) -> set[Path]:
    """Directories ldd actually resolves the extension's TK/vtk deps from."""
    out = subprocess.run(
        ["ldd", str(ext)], capture_output=True, text=True, check=True
    ).stdout
    dirs: set[Path] = set()
    for line in out.splitlines():
        if "=>" not in line:
            continue
        target = line.split("=>", 1)[1].strip().split(" (", 1)[0].strip()
        if not target or target == "not found":
            continue
        p = Path(target).resolve()
        name = p.name
        if name.startswith("libTK") or name.startswith("libvtk"):
            dirs.add(p.parent)
    return dirs


lib_dirs = _resolved_lib_dirs(ocp_ext)
if not lib_dirs:
    raise SystemExit(
        "Could not resolve any libTK*/libvtk* deps from the OCP extension via "
        f"ldd ({ocp_ext}); the OCP packaging layout changed — re-audit (R1)."
    )

# Collect every .so* from each resolved lib dir, preserving the dir's name in
# the bundle so the OCP extension's $ORIGIN/../<libdir> RPATH still resolves.
ocp_binaries = []
collected_tk = 0
for d in lib_dirs:
    dest = d.name  # e.g. "cadquery_ocp.libs" or "vtkmodules"
    for so in d.iterdir():
        if ".so" in so.name:
            ocp_binaries.append((str(so), dest))
            if so.name.startswith("libTK"):
                collected_tk += 1

if collected_tk == 0:
    raise SystemExit(
        f"Resolved lib dirs {sorted(map(str, lib_dirs))} but found no libTK* "
        "files — re-audit the OCP layout (R1)."
    )

# numpy / OCP can lazily import submodules PyInstaller's static analysis misses.
hidden = collect_submodules("OCP") + collect_submodules("numpy")

block_cipher = None

a = Analysis(
    ["pyi_entry.py"],
    pathex=[],
    binaries=ocp_binaries,
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # The spike sidecar does not render via vtk/matplotlib; excluding the
        # GUI-heavy bits trims the bundle. Keep vtk's native libs (above) in
        # case OCP touches them transitively, but drop matplotlib backends.
        "tkinter",
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="touch_sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # UPX-compressing 400 MB of OCCT libs is slow and AV-suspicious (R11)
    console=True,         # the sidecar talks over stdout (TOUCH_READY) — keep a console
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="touch_sidecar",
)
