# blender-mcp-testing

Testbed for building **interactive 3D models for websites** using natural language → [blender-mcp](https://github.com/ahujasid/blender-mcp) → Blender → `.glb` export.

Goal: rather than learn 3D modelling by hand, drive Blender from Claude (or any MCP client) with plain English, export the result as a web-ready `.glb`, and embed it on a page so visitors can rotate it, trigger animations on scroll, or hover to interact.

## Why this exists

Modern web design uses a lot of 3D — product viewers, animated logos, scroll-triggered scenes (Apple, Stripe, Linear, Vercel, etc.). The barrier was always *making* the 3D model. With blender-mcp, that step becomes a conversation. This repo collects working examples.

## Pipeline

```
plain English ──▶ Claude ──▶ blender-mcp (MCP server)
                                  │
                                  ▼  TCP :9876
                          Blender addon (bpy)
                                  │
                  ┌───────────────┼───────────────┐
                  ▼               ▼               ▼
              .blend          .glb           PNG/MP4
           (scene save)   (web-ready 3D)   (cinematic)
```

## Repo layout

```
blender-mcp-testing/
├── scripts/                   # Python source for each scene
│   └── build_matt_scene.py
├── scenes/                    # Blender binary saves (.blend)
│   └── matt_wave.blend
├── exports/                   # web-ready 3D (.glb / .gltf)
│   └── matt_wave.glb          # 233 KB, includes wave animation
├── web-examples/              # tiny HTML/React pages that embed the .glb
│   └── model-viewer.html
├── renders/                   # PNGs / MP4 (gitignored — see .gitignore)
└── README.md
```

## Three artifact types — what to commit

| File | What it is | Commit? |
|---|---|---|
| `.py` build script | Python that constructs the scene | **YES** — text, diffable, the canonical source |
| `.blend` | Blender's binary scene save | Optional — borderline; useful for resuming work in Blender, skip if it grows large |
| `.glb` | Browser-ready 3D model (geometry + materials + animation) | **YES if it's the deliverable** |
| `.png` / `.mp4` | Rendered output | **NO** — derived, regenerate from script |

## Reproducing any scene

1. Install Blender 4.x or 5.x
2. Install the [blender-mcp](https://github.com/ahujasid/blender-mcp) addon (`addon.py` from that repo → Blender Preferences → Add-ons → Install)
3. In Blender: open the script → Run, or talk to Claude with blender-mcp configured

## Using the `.glb` on a website (three options, easiest first)

### 1. `<model-viewer>` — one HTML tag, no build

```html
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js"></script>

<model-viewer
  src="matt_wave.glb"
  camera-controls
  auto-rotate
  autoplay
  exposure="1"
  style="width:600px;height:400px">
</model-viewer>
```

That's it. The user can drag to rotate, scroll to zoom, and the wave animation plays. See `web-examples/model-viewer.html` for the working file.

### 2. Three.js — direct control

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
new GLTFLoader().load('matt_wave.glb', gltf => scene.add(gltf.scene))
```

### 3. React Three Fiber — best for React/Next.js apps

```jsx
import { Canvas } from '@react-three/fiber'
import { useGLTF, OrbitControls } from '@react-three/drei'

function Matt() {
  const { scene } = useGLTF('/matt_wave.glb')
  return <primitive object={scene} />
}

export default () => (
  <Canvas camera={{ position: [0, 1, 6] }}>
    <ambientLight intensity={0.5} />
    <directionalLight position={[5, 5, 5]} />
    <Matt />
    <OrbitControls />
  </Canvas>
)
```

Scroll-triggered rotation comes from libraries like [`@react-three/drei`](https://github.com/pmndrs/drei) (`ScrollControls`) or pairing with [Framer Motion](https://www.framer.com/motion/).

## Quick browser test (no setup)

Drag any `.glb` from `exports/` onto:
- <https://modelviewer.dev/editor/>
- <https://gltf-viewer.donmccurdy.com/>

You'll see the interactive 3D version of the asset immediately.

## A note on visual fidelity

The `.glb` in the browser is **real-time WebGL** rendering — fast and interactive, but not photorealistic. The MP4 rendered out of Blender uses **Cycles raytracing** — gorgeous reflections, soft shadows, etc., but a flat recording.

Rule of thumb:
- **Hero animation / showreel** → render to MP4 from Cycles
- **Anything the user touches** → ship `.glb` and accept simpler shading

## Roadmap of experiments

- [ ] Hover-to-spin product icon
- [ ] Scroll-driven turntable
- [ ] Logo that explodes apart on click
- [ ] Materials sandbox: glass, gold, brushed metal, glass + caustics
- [ ] Lighter geometry baseline (Draco compression for tiny `.glb` sizes)
- [ ] Multiple animations in one `.glb` (idle + click + hover)

## How this was made

Claude drove Blender via the [blender-mcp](https://github.com/ahujasid/blender-mcp) server — stdio MCP → TCP socket on `127.0.0.1:9876` → Blender addon → `bpy` Python API. Every shape, material, keyframe, and camera move was a Python instruction sent over that socket.
