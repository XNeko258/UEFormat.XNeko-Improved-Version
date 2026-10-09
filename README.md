<div align="center">

# UEFormat

A Blender importer for UEFormat files — rewritten, hardened, and optimized from the original.

[![Blender](https://img.shields.io/badge/Blender-4.2+-blue?logo=blender&logoColor=white&color=orange)](https://www.blender.org/download/)
[![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue)]()

</div>

---

## About This Fork

This repository is a fork of [h4lfheart/UEFormat](https://github.com/h4lfheart/UEFormat).

**Only the Blender importer is maintained here.** The Unreal Engine plugin, the exporter tooling, and the format specification all live in the upstream repository — this fork does not touch them.

For anything Unreal-side, refer to:

- **Upstream repository**: https://github.com/h4lfheart/UEFormat
- **Upstream Discord**: https://discord.gg/DZ5YFXdBA6

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

---

## ⚠️ Pick one — do not install both

This repository ships the importer in two forms. They are **alternatives, not complements**.

| Form | Where it goes | Operator prefix |
|---|---|---|
| **Standalone plugin** | Blender's `scripts/addons/` directory | `uf.*` |
| **XNeko Tools module** | Inside the XNeko_Tools framework's `tools/` directory | `xneko.ueformat_*` |

Both register Blender classes with the same identifiers (`UEFORMAT_PT_Panel`, `UFSettings`). **Enabling both in the same Blender installation will raise a registration error** — this is expected, not a bug. Pick the one that matches where you're installing:

| Your situation | Install |
|---|---|
| Only need the importer | Standalone plugin |
| Already using XNeko Tools | Toolbox module |
| Migrating from upstream UEFormat | Standalone plugin (`uf.*` operator prefix is preserved) |

---

## Installation

### Standalone Plugin

1. Copy the `io_scene_ueformat` folder into your Blender `scripts/addons/` directory
2. Enable it via `Edit > Preferences > Add-ons`

- **Operator prefix**: `uf.*` — same as upstream
- **N panel category**: `UE Format`
- **Dependencies**: none (install `zstandard` separately for ZSTD-compressed files)

### XNeko Tools Module

1. Copy the `tools/importers/ueformat` folder into `XNeko_Tools/tools/importers/`
2. Restart Blender, or run **Rescan Tools** from the N panel

- **Operator prefix**: `xneko.ueformat_*`
- **N panel category**: follows the XNeko Tools configuration
- **Dependencies**: the XNeko Tools framework

---

## Supported Files

| Extension | Identifier | Purpose |
|---|---|---|
| `.uemodel` | `UEMODEL` | Static / skeletal models |
| `.ueanim` | `UEANIM` | Skeletal animation sequences |
| `.uepose` | `UEPOSE` | Pose assets |

Files are produced by external exporters. Refer to the [upstream repository](https://github.com/h4lfheart/UEFormat) for the exporter side.

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

The dominant win is the skeleton color pass, which upstream performs as an O(bones × vertices) scan.

---

## Usage

### Import a Model
1. In the N panel, configure model options
2. Click **Import Model**, or use `File > Import > Unreal Model (.uemodel)`

### Import an Animation
1. (Optional) Pick an override skeleton in the N panel
2. Click **Import Animation**, or use `File > Import > Unreal Animation (.ueanim)`

### Import a Pose
1. (Optional) Pick an override skeleton and root bone in the N panel
2. Click **Import Pose**, or use `File > Import > Unreal Pose Asset (.uepose)`

### Diagnostics

Enable in addon preferences:
- **Show Import Time Popup** — displays a popup with the duration
- **Log Import Profile** — prints a per-step timing breakdown

Both are off by default.

---

## Requirements

- **Blender 4.2 or later**
- **`zstandard`** (optional) — required only for ZSTD-compressed files

---

## What Changed

### Performance
1. **Binary reads** — `np.frombuffer` removes the intermediate Python tuple that `struct.unpack` produced
2. **Weights** — bucketed by exact float value, one `add()` per group
3. **Morph targets** — `foreach_get` / `foreach_set` instead of per-delta `+=`
4. **Materials** — NumPy index array + `foreach_set`
5. **Skeleton color pass** — O(vertices) scan instead of O(bones × vertices)

### Safety
- **`assert` → `raise`** — survives `python -O`
- **Optional `zstandard`** — graceful degradation
- **Context-safe `bpy.ops`** — works from N panel and File menu
- **Namespaced operator IDs**

### Correctness
- Fixed `from_archive_legacy` parameter name (`self` → `cls`)
- Fixed `metadata` type annotations (`| None`)
- Fixed `read_float_vector` overload return types
- Removed `from math import *` and duplicate assignment
- Pose import restores original edit mode

---

## Consistency With Upstream

Every byte that enters the Blender scene is identical to upstream:

1. Binary layer is bit-equivalent
2. Coordinate transforms untouched
3. Weights bucketed by exact float (no rounding)
4. Morph deltas accumulate in the same order
5. Skeleton, animation, pose construction verbatim

---

## Known Limitations

### Two distributions cannot coexist

The standalone plugin and the XNeko Tools module register classes with identical Blender identifiers (`UEFORMAT_PT_Panel`, `UFSettings`). They are meant for different environments and cannot be enabled simultaneously.

### `importer/` is duplicated

The `importer/` package is shipped in two places:
- `io_scene_ueformat/importer/`
- `tools/importers/ueformat/_importer/`

Both must stay byte-identical. Run `python sync_importer.py --check` to verify. CI checks on every push.

### Benchmark scope

The 5.3× figure describes one model on one machine. Actual speedup varies:
- Small models (<5k vertices): typically 1.5–2×
- Models without morph targets: the morph-target win does not apply
- Models with few bones: the skeleton color pass saves less

---

## Format Specification

Defined by upstream: https://github.com/h4lfheart/UEFormat/tree/main/docs

---

## Credits

- Original project: [h4lfheart/UEFormat](https://github.com/h4lfheart/UEFormat)
- This fork: performance and safety work by XNeko

---

## License

GPL-3.0-or-later, matching upstream.