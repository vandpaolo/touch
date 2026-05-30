"""Real OCCT self-check — the actual point of Day 4 (risk R1).

Day 1's cube is hand-authored and imports nothing native. To prove the
PyInstaller bundle ships OCP's native OCCT libraries *and that they load and
run after packaging*, the sidecar performs one genuine kernel computation at
startup (build a box, measure its volume). If the native libs (libTKBRep,
libTKMath, libTKernel, …) are missing from the bundle, this import/compute
fails immediately — which is exactly the failure mode Day 4 exists to catch.
"""

from __future__ import annotations


def ocp_selfcheck() -> str:
    """Build a unit box via OCCT and return a one-line summary.

    Raises on any import/compute failure (caller decides how loud to be).
    """
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.GProp import GProp_GProps

    box = BRepPrimAPI_MakeBox(10.0, 10.0, 10.0).Shape()
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(box, props)
    volume = props.Mass()
    return f"OCCT box volume={volume:.1f} (expected 1000.0)"
