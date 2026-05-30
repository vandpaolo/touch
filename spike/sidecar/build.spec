# PyInstaller spec for the Touch spike sidecar — the heart of Day 4 (risk R1)
# and reused unchanged on the Day-5 Windows CI runner.
#
# OCP ships as a repaired wheel: the Python extension lives at
# site-packages/OCP/ and its ~200 native OCCT shared libraries live in a
# SIBLING dir whose name is derived from the *distribution* name — for the
# `cadquery-ocp` wheel that is `cadquery_ocp.libs/` (NOT `OCP.libs/`), with
# hash-suffixed files (libTKMath-…​.so.7.8.1 on Linux, TKMath-….dll on
# Windows). PyInstaller's automatic analysis does not reliably pull the full
# set, so we collect them explicitly. cadquery-ocp also depends on vtk, whose
# native libs live in a `vtkmodules/` sibling. This is exactly the "PyInstaller
# misses OCP's native libs" failure mode Day 4 exists to prove out.
#
# We DISCOVER the native-lib dirs by globbing the wheel-vendored sibling
# directories, which keeps this CROSS-PLATFORM. Both Linux (auditwheel) and
# Windows (delvewheel) vendor native deps into a "<distribution>.libs" sibling
# of the package (here `cadquery_ocp.libs`), and vtk vendors its libs under
# `vtkmodules`. Globbing `*.libs` + `vtkmodules` works on both and survives a
# wheel rename. (An earlier ldd-based version was Linux-only and would have
# failed on the Day-5 Windows runner.)
#
# --onedir (NOT --onefile): onefile unpacks to a temp dir at every launch,
# which is slow for ~400 MB of libs and trips some AV heuristics (R11).
#
# Build:  pyinstaller build.spec --noconfirm
# Output: dist/touch_sidecar/  (a directory with the `touch_sidecar[.exe]`
#         binary + all libs)

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# --- locate the installed OCP package ---------------------------------------
import OCP  # noqa: E402

ocp_pkg_dir = Path(OCP.__file__).resolve().parent          # .../site-packages/OCP
site_packages = ocp_pkg_dir.parent

_LIB_MARKERS = (".so", ".dll", ".dylib", ".pyd")


def _is_shared_lib(name: str) -> bool:
    return any(marker in name for marker in _LIB_MARKERS)


# Sibling native-lib dirs: "<dist>.libs" (auditwheel/delvewheel) + vtkmodules.
candidate_dirs = [d for d in site_packages.glob("*.libs") if d.is_dir()]
vtk_dir = site_packages / "vtkmodules"
if vtk_dir.is_dir():
    candidate_dirs.append(vtk_dir)

if not candidate_dirs:
    raise SystemExit(
        f"No '*.libs' / vtkmodules native-lib dirs under {site_packages}; "
        "the OCP packaging layout changed — re-audit (R1)."
    )

# Collect every shared lib from each dir, preserving the dir name in the bundle
# so the OCP extension's $ORIGIN/../<libdir> (Linux) or DLL-search (Windows)
# still resolves at runtime.
ocp_binaries = []
collected_tk = 0
for d in candidate_dirs:
    dest = d.name  # e.g. "cadquery_ocp.libs" or "vtkmodules"
    for f in d.iterdir():
        if f.is_file() and _is_shared_lib(f.name):
            ocp_binaries.append((str(f), dest))
            if "TK" in f.name:  # libTKMath…so (Linux) / TKMath…dll (Windows)
                collected_tk += 1

if collected_tk == 0:
    raise SystemExit(
        f"Found native-lib dirs {sorted(d.name for d in candidate_dirs)} but no "
        "TK* (OCCT) libs — re-audit the OCP layout (R1)."
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
