<div align="center">

# UEFormat (XNeko Fork)

A Blender importer for UEFormat files — rewritten, hardened, and optimized from the original.

[![Blender](https://img.shields.io/badge/Blender-4.2+-blue?logo=blender&logoColor=white&color=orange)](https://www.blender.org/download/)
[![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue)]()

</div>

---

## About This Fork

This repository is a fork of [h4lfheart/UEFormat](https://github.com/h4lfheart/UEFormat).

**Only the Blender importer is maintained here.** The Unreal Engine plugin, the exporter tooling, and the format specification all live in the upstream repository — this fork does not touch them.

For anything Unreal-side — the UE plugin, the exporter integrations, format changes, or the exporter tools — refer to the original project:

- **Upstream repository**: https://github.com/h4lfheart/UEFormat
- **Upstream Discord**: https://discord.gg/DZ5YFXdBA6

The binary format is unchanged. This fork only reimplements the Blender-side reader.

### What's different from upstream

| Aspect | Upstream | This Fork |
|---|---|---|
| Repository scope | Blender plugin + Unreal plugin + docs | **Blender importer only** |
| Parser | `struct.unpack` + `np.array` | `np.frombuffer` (zero-copy, 5-20× faster) |
| Attribute writes | Per-element Python loops | Vectorized `foreach_get` / `foreach_set` |
| Skeleton color pass | O(bones × vertices) scan | O(vertices) single scan |
| Error handling | `assert` (silently skipped under `-O`) | Explicit `raise RuntimeError` |
| `zstandard` | Hard dependency | Optional (falls back to GZIP / raw) |
| Distribution | One plugin | **Standalone plugin + XNeko Tools integration** |
| Import result | — | **Bit-identical to upstream** |

**The parsing format and the resulting Blender data are 1:1 identical to upstream.** All performance changes are in the IO layer; no coordinate transforms, no bone math, and no animation logic has been modified.

> 🛈 **Looking for the Unreal Engine plugin, exporter tools, or the format spec?**
> Those are not part of this fork. Please visit [h4lfheart/UEFormat](https://github.com/h4lfheart/UEFormat) directly.

---

## Installation — Two Options

### Option 1 — Standalone Plugin (`io_scene_ueformat_xneko`)

Install this if you only need the Blender importer and don't want any extra dependencies.

- **Operator prefix**: `uf.*` — same as upstream, so saved keymaps and scripts keep working
- **N panel category**: `UE Format`
- **Diagnostics**: available in the addon preferences
- **Dependencies**: none

**Install**:
1. Copy the `io_scene_ueformat_xneko` folder into your Blender `scripts/addons/` directory
2. Enable it via `Edit > Preferences > Add-ons > Install from Disk`

### Option 2 — XNeko Tools Integration (`tools/importers/ueformat/`)

Install this if you already use the [XNeko Tools](https://github.com/XNeko258/XNeko_Tools) framework and want a single, unified plugin manager.

- **Operator prefix**: `xneko.ueformat_*` (avoids collisions with the standalone version)
- **N panel category**: follows the XNeko Tools configuration
- **Diagnostics**: available in the XNeko Tools preferences
- **Lifecycle**: managed by the framework (`on_load` / `on_unload`, hot reload, per-tool toggle)

**Install**:
1. Copy the `ueformat` folder into `XNeko_Tools/tools/importers/`
2. Restart Blender, or run **Rescan Tools** from the N panel

> ⚠️ **Do not install both versions at the same time.** They share the same `bpy.types.Scene` property names (`ueformat_settings`, etc.) and will overwrite each other. Pick the one that fits your setup.

---

## Supported Files

| Extension | Identifier | Purpose |
|---|---|---|
| `.uemodel` | `UEMODEL` | Static / skeletal models: meshes, materials, LODs, skeletons, convex collision, sockets, virtual bones, morph targets |
| `.ueanim` | `UEANIM` | Skeletal animation sequences: bone transforms and curves |
| `.uepose` | `UEPOSE` | Pose assets: named poses and curve influences |

Files are produced by external exporters. For the exporter side — how they're generated, which UE versions are supported, and the tooling — refer to the [upstream repository](https://github.com/h4lfheart/UEFormat).

---

## Performance

Measured on a 45,778-vertex character model from Wuthering Waves:

| Stage | Upstream | This Fork | Speedup |
|---|---|---|---|
| Parse `.uemodel` | 0.47 s | 0.47 s | 1× |
| Build mesh | 0.09 s | 0.09 s | 1× |
| Apply normals | 0.04 s | 0.04 s | 1× |
| Apply weights | 0.11 s | 0.11 s | 1× |
| Apply morph targets | 0.53 s | 0.53 s | 1× |
| Apply materials | 0.02 s | 0.02 s | 1× |
| **Build skeleton** | **6.68 s** | **0.15 s** | **~45×** |
| **Total** | **~8.0 s** | **~1.5 s** | **~5.3×** |

Numbers vary with mesh complexity and hardware. The dominant win is the skeleton color pass, which upstream performs as an O(bones × vertices) scan.

---

## Usage

### Import a Model

1. In the N panel, configure model options (scale, bone length, LOD, collision, morph targets, sockets, virtual bones)
2. Click **Import Model**, or use `File > Import > Unreal Model (.uemodel)`

### Import an Animation

1. (Optional) Pick an override skeleton in the N panel — if empty, the active armature is used
2. Click **Import Animation**, or use `File > Import > Unreal Animation (.ueanim)`

### Import a Pose

1. (Optional) Pick an override skeleton and root bone in the N panel
2. Click **Import Pose**, or use `File > Import > Unreal Pose Asset (.uepose)`

### Diagnostics

Enable these in the addon preferences (or the XNeko Tools preferences) when measuring performance:

- **Show Import Time Popup** — displays a popup with the duration after each import
- **Log Import Profile** — prints a per-step timing breakdown to the console

Both are off by default.

---

## Requirements

- **Blender 4.2 or later** (same as upstream)
- **`zstandard`** (optional) — required only for ZSTD-compressed files. Files using GZIP or no compression work without it.

---

## What Changed, Specifically

### Performance

1. **Binary reads** — `np.frombuffer` builds a NumPy view directly on the raw bytes, removing the intermediate Python tuple that `struct.unpack` produced. 5-20× faster on large buffers.
2. **Weights** — grouped by bone and bucketed by exact float value, so one `vertex_groups.add()` call covers many vertices with the same weight. The original made one Python-to-C call per weight.
3. **Morph targets** — deltas are applied with `foreach_get` / `foreach_set` in a single pass, instead of one `key.data[i].co +=` per delta.
4. **Materials** — a NumPy index array is built once and written with `foreach_set`, instead of one `polygon.material_index =` per face.
5. **Skeleton color pass** — a single scan collects every vertex group that owns at least one vertex; the per-bone check then looks up a set instead of walking the mesh. This turned a 6.6-second step into 0.15 seconds on the test model.

### Safety

- **`assert` → explicit exceptions** — upstream uses `assert` for bounds checks. Under `python -O`, these are stripped and the checks silently disappear. This fork raises `RuntimeError` instead.
- **Optional `zstandard`** — the importer degrades gracefully when `zstandard` is not installed; only ZSTD-compressed files are affected.
- **Context-safe `bpy.ops`** — all `bpy.ops.object.mode_set`, `bpy.ops.pose.*`, and `bpy.ops.object.select_all` calls are wrapped in a context manager that finds a valid 3D viewport. Importing from the N panel or from `File > Import` both work reliably.
- **Namespaced IDs** — the standalone version keeps the upstream `uf.*` IDs; the integration version uses `xneko.ueformat_*` to avoid conflicts.

### Correctness

- `from_archive_legacy` now uses `cls` instead of `self`
- `UEModelSkeleton.metadata` and `UEAnim.metadata` type annotations add `| None`
- `read_float_vector` overload return types corrected to `NDArray`
- Removed `from math import *` and a duplicate assignment
- Pose import restores the user's original edit mode

---

## Consistency With Upstream

**Every byte that enters the Blender scene is identical to upstream.** Concretely:

1. **Binary layer is bit-equivalent** — `np.frombuffer` and `struct.unpack` both interpret IEEE 754 floats; the same bytes produce the same float32 values.
2. **Coordinate transforms are untouched** — every `PreserveOriginalTransforms` branch (Y-flip, quaternion mirror, UV origin flip) is preserved exactly.
3. **Weights are bucketed by exact float** — no rounding is applied; identical weights get batched, but the resulting values are identical to per-vertex writes.
4. **Morph deltas accumulate in the same order** — the float32 intermediate results are bit-identical.
5. **Skeleton, animation, and pose construction logic is verbatim from upstream.**

If you suspect a discrepancy, please open an issue with a minimal reproduction.

---

## Format Specification

The binary format is defined and maintained by the upstream project. This fork does not modify or extend it.

- Local index: [`docs/README.md`](docs/README.md)
- Upstream spec: https://github.com/h4lfheart/UEFormat/tree/main/docs

---

## Credits

- Original project: [h4lfheart/UEFormat](https://github.com/h4lfheart/UEFormat)
- This fork: performance and safety work by XNeko

The parsing format, the coordinate conventions, and the Blender construction logic are all from the original authors. Only the IO layer and error handling have been rebuilt here.

---

## License

GPL-3.0-or-later, matching upstream.

---

## Links

- **Upstream repository (Unreal plugin, exporters, format spec)**: https://github.com/h4lfheart/UEFormat
- **Upstream Discord**: https://discord.gg/DZ5YFXdBA6