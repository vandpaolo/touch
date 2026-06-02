// web/viewport — three.js scene + render loop (F3). Builds a BufferGeometry
// from the decoded DocStore mesh and renders it; fits the camera to the model.
// Day 7 uses default OrbitControls; Day 8 rebinds them NX-style.
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { pickFace, type PickHit } from '../picking'
import type { MeshData } from '../transport'

export class Viewport {
  private readonly scene = new THREE.Scene()
  private readonly camera: THREE.PerspectiveCamera
  private readonly renderer: THREE.WebGLRenderer
  private controls?: OrbitControls
  private mesh?: THREE.Mesh
  private meshData?: MeshData
  private container?: HTMLElement
  private resizeObserver?: ResizeObserver
  private raf = 0

  // Hover picking (N1: local raycast, zero round-trip).
  private readonly raycaster = new THREE.Raycaster()
  private readonly pointer = new THREE.Vector2()
  private readonly hoverMaterial = new THREE.MeshBasicMaterial({
    color: 0x4aa3ff,
    transparent: true,
    opacity: 0.35,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1,
  })
  private hoverObj?: THREE.Mesh
  private hoverTag: number | null = null
  private onPointerMove?: (e: PointerEvent) => void
  private onPointerLeave?: () => void

  // Click selection (left-click; distinguished from a left-drag).
  private readonly selectedMaterial = new THREE.MeshBasicMaterial({
    color: 0xffa733,
    transparent: true,
    opacity: 0.5,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
  })
  private selectedObj?: THREE.Mesh
  private selectedTag: number | null = null
  private downPos: { x: number; y: number } | null = null
  private faceClickCb?: (hit: PickHit | null, screen: { x: number; y: number }) => void
  private onPointerDown?: (e: PointerEvent) => void
  private onPointerUp?: (e: PointerEvent) => void

  constructor() {
    this.scene.background = new THREE.Color(0x1e1e1e)

    this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100_000)
    this.camera.position.set(120, 90, 120)

    this.renderer = new THREE.WebGLRenderer({ antialias: true })
    this.renderer.setPixelRatio(window.devicePixelRatio)

    const key = new THREE.DirectionalLight(0xffffff, 2.2)
    key.position.set(1, 1.5, 1)
    const fill = new THREE.DirectionalLight(0xffffff, 0.8)
    fill.position.set(-1, -0.5, -1)
    this.scene.add(key, fill, new THREE.AmbientLight(0xffffff, 0.5))
  }

  /** Attach the renderer to a container and start the render loop. */
  mount(container: HTMLElement): void {
    this.container = container
    container.appendChild(this.renderer.domElement)

    this.controls = new OrbitControls(this.camera, this.renderer.domElement)
    this.controls.enableDamping = true
    this.controls.zoomToCursor = true

    // Camera bindings (user's scheme, 2026-06-01): middle-mouse (scroll-wheel)
    // drag orbits; scroll zooms toward the cursor. Left and right are left
    // unbound here — left-click is select+prompt and right-click is the
    // context menu, both wired in T3 (see docs/notes/interaction.md).
    this.controls.mouseButtons = { MIDDLE: THREE.MOUSE.ROTATE }

    this.resize()
    this.resizeObserver = new ResizeObserver(() => this.resize())
    this.resizeObserver.observe(container)

    this.onPointerMove = (e: PointerEvent) => this.handleHover(e)
    this.onPointerLeave = () => this.setHoverHighlight(null)
    this.onPointerDown = (e: PointerEvent) => {
      if (e.button === 0) this.downPos = { x: e.clientX, y: e.clientY }
    }
    this.onPointerUp = (e: PointerEvent) => this.handleClick(e)
    this.renderer.domElement.addEventListener('pointermove', this.onPointerMove)
    this.renderer.domElement.addEventListener('pointerleave', this.onPointerLeave)
    this.renderer.domElement.addEventListener('pointerdown', this.onPointerDown)
    this.renderer.domElement.addEventListener('pointerup', this.onPointerUp)

    const loop = () => {
      this.raf = requestAnimationFrame(loop)
      this.controls?.update()
      this.renderer.render(this.scene, this.camera)
    }
    loop()
  }

  /** Register a left-click handler; fires with the picked face (or null on a
   *  miss) and the click's screen coords. */
  onFaceClick(cb: (hit: PickHit | null, screen: { x: number; y: number }) => void): void {
    this.faceClickCb = cb
  }

  /** Persistently highlight the selected face, or clear (null). */
  setSelectedFace(faceTag: number | null): void {
    if (faceTag === this.selectedTag) return
    this.selectedTag = faceTag
    if (this.selectedObj) {
      this.scene.remove(this.selectedObj)
      this.selectedObj.geometry.dispose()
      this.selectedObj = undefined
    }
    if (faceTag === null || !this.meshData) return
    const geometry = this.faceGeometry(faceTag, this.meshData)
    if (!geometry) return
    this.selectedObj = new THREE.Mesh(geometry, this.selectedMaterial)
    this.selectedObj.renderOrder = 2
    this.scene.add(this.selectedObj)
  }

  /** Replace the displayed geometry from a decoded mesh frame. */
  setMesh(data: MeshData): void {
    this.setHoverHighlight(null)
    this.setSelectedFace(null)
    this.meshData = data
    if (this.mesh) {
      this.scene.remove(this.mesh)
      this.mesh.geometry.dispose()
      ;(this.mesh.material as THREE.Material).dispose()
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(data.vertices, 3))
    geometry.setAttribute('normal', new THREE.BufferAttribute(data.normals, 3))
    geometry.setIndex(new THREE.BufferAttribute(data.indices, 1))

    const material = new THREE.MeshStandardMaterial({
      color: 0x9aa0a6,
      metalness: 0.1,
      roughness: 0.6,
    })
    this.mesh = new THREE.Mesh(geometry, material)
    this.scene.add(this.mesh)
    this.frameToObject(geometry)
  }

  /** Point the camera at the model and back off to fit it in view. */
  private frameToObject(geometry: THREE.BufferGeometry): void {
    geometry.computeBoundingSphere()
    const sphere = geometry.boundingSphere
    if (!sphere || !this.controls) return

    const { center, radius } = sphere
    const fitDist = (radius * 1.6) / Math.sin((this.camera.fov * Math.PI) / 360)
    const dir = new THREE.Vector3(1, 0.8, 1).normalize()
    this.camera.position.copy(center).addScaledVector(dir, fitDist)
    this.camera.near = Math.max(radius / 100, 0.1)
    this.camera.far = fitDist + radius * 10
    this.camera.updateProjectionMatrix()
    this.controls.target.copy(center)
    this.controls.update()
  }

  private handleHover(e: PointerEvent): void {
    if (!this.mesh || !this.meshData) return
    const rect = this.renderer.domElement.getBoundingClientRect()
    this.pointer.set(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1,
    )
    const hit = pickFace(
      this.raycaster,
      this.camera,
      this.mesh,
      this.meshData.faceTagPerTriangle,
      this.pointer,
    )
    this.setHoverHighlight(hit ? hit.faceTag : null)
  }

  private handleClick(e: PointerEvent): void {
    if (e.button !== 0 || !this.downPos) return
    const moved = Math.hypot(e.clientX - this.downPos.x, e.clientY - this.downPos.y)
    this.downPos = null
    if (moved > 5) return // a drag, not a click
    if (!this.faceClickCb) return
    const screen = { x: e.clientX, y: e.clientY }
    if (!this.mesh || !this.meshData) {
      this.faceClickCb(null, screen)
      return
    }
    const rect = this.renderer.domElement.getBoundingClientRect()
    this.pointer.set(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1,
    )
    const hit = pickFace(
      this.raycaster,
      this.camera,
      this.mesh,
      this.meshData.faceTagPerTriangle,
      this.pointer,
    )
    this.faceClickCb(hit, screen)
  }

  /** Overlay-highlight every triangle of `faceTag`, or clear (null). */
  private setHoverHighlight(faceTag: number | null): void {
    if (faceTag === this.hoverTag) return
    this.hoverTag = faceTag

    if (this.hoverObj) {
      this.scene.remove(this.hoverObj)
      this.hoverObj.geometry.dispose()
      this.hoverObj = undefined
    }
    if (faceTag === null || !this.meshData) return

    const geometry = this.faceGeometry(faceTag, this.meshData)
    if (!geometry) return
    this.hoverObj = new THREE.Mesh(geometry, this.hoverMaterial)
    this.hoverObj.renderOrder = 1
    this.scene.add(this.hoverObj)
  }

  /** Build a non-indexed geometry of just the triangles tagged `faceTag`. */
  private faceGeometry(faceTag: number, data: MeshData): THREE.BufferGeometry | null {
    const positions: number[] = []
    for (let t = 0; t < data.faceTagPerTriangle.length; t++) {
      if (data.faceTagPerTriangle[t] !== faceTag) continue
      for (let k = 0; k < 3; k++) {
        const vi = data.indices[t * 3 + k]
        positions.push(data.vertices[vi * 3], data.vertices[vi * 3 + 1], data.vertices[vi * 3 + 2])
      }
    }
    if (positions.length === 0) return null
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
    return geometry
  }

  private resize(): void {
    if (!this.container) return
    const w = this.container.clientWidth
    const h = this.container.clientHeight
    if (w === 0 || h === 0) return
    this.renderer.setSize(w, h)
    this.camera.aspect = w / h
    this.camera.updateProjectionMatrix()
  }

  /** Remove all geometry + highlights (e.g. on a new/empty document). */
  clear(): void {
    this.setHoverHighlight(null)
    this.setSelectedFace(null)
    this.meshData = undefined
    if (this.mesh) {
      this.scene.remove(this.mesh)
      this.mesh.geometry.dispose()
      ;(this.mesh.material as THREE.Material).dispose()
      this.mesh = undefined
    }
  }

  dispose(): void {
    cancelAnimationFrame(this.raf)
    if (this.onPointerMove) {
      this.renderer.domElement.removeEventListener('pointermove', this.onPointerMove)
    }
    if (this.onPointerLeave) {
      this.renderer.domElement.removeEventListener('pointerleave', this.onPointerLeave)
    }
    if (this.onPointerDown) {
      this.renderer.domElement.removeEventListener('pointerdown', this.onPointerDown)
    }
    if (this.onPointerUp) {
      this.renderer.domElement.removeEventListener('pointerup', this.onPointerUp)
    }
    this.hoverObj?.geometry.dispose()
    this.hoverMaterial.dispose()
    this.selectedObj?.geometry.dispose()
    this.selectedMaterial.dispose()
    this.resizeObserver?.disconnect()
    this.controls?.dispose()
    this.mesh?.geometry.dispose()
    this.renderer.dispose()
    this.renderer.domElement.remove()
  }
}
