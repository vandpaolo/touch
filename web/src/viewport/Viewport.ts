// web/viewport — three.js scene + render loop (F3). Builds a BufferGeometry
// from the decoded DocStore mesh and renders it; fits the camera to the model.
// Day 7 uses default OrbitControls; Day 8 rebinds them NX-style.
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { MeshData } from '../transport'

export class Viewport {
  private readonly scene = new THREE.Scene()
  private readonly camera: THREE.PerspectiveCamera
  private readonly renderer: THREE.WebGLRenderer
  private controls?: OrbitControls
  private mesh?: THREE.Mesh
  private container?: HTMLElement
  private resizeObserver?: ResizeObserver
  private raf = 0

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

    const loop = () => {
      this.raf = requestAnimationFrame(loop)
      this.controls?.update()
      this.renderer.render(this.scene, this.camera)
    }
    loop()
  }

  /** Replace the displayed geometry from a decoded mesh frame. */
  setMesh(data: MeshData): void {
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

  private resize(): void {
    if (!this.container) return
    const w = this.container.clientWidth
    const h = this.container.clientHeight
    if (w === 0 || h === 0) return
    this.renderer.setSize(w, h)
    this.camera.aspect = w / h
    this.camera.updateProjectionMatrix()
  }

  dispose(): void {
    cancelAnimationFrame(this.raf)
    this.resizeObserver?.disconnect()
    this.controls?.dispose()
    this.mesh?.geometry.dispose()
    this.renderer.dispose()
    this.renderer.domElement.remove()
  }
}
