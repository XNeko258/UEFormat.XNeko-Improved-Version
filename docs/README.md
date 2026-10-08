# Format Specification

The UEFormat binary specification is defined and maintained by the upstream project.

**This fork does not modify the format.** It only reimplements the Blender-side reader for performance and safety. The files it reads conform to the upstream spec exactly.

For the full specification, see the upstream docs:

- [Generic](https://github.com/h4lfheart/UEFormat/blob/main/docs/generic.md)
- [UEModel](https://github.com/h4lfheart/UEFormat/blob/main/docs/uemodel.md)
- [UEAnim](https://github.com/h4lfheart/UEFormat/blob/main/docs/ueanim.md)
- [UEPose](https://github.com/h4lfheart/UEFormat/blob/main/docs/uepose.md)

## Where these formats come from

`.uemodel`, `.ueanim`, and `.uepose` files are produced by external exporters. For the exporter side — the tooling, the Unreal Engine plugin, and version support — refer to the upstream repository:

- https://github.com/h4lfheart/UEFormat

## Why this fork exists

See the [main README](../README.md) for a detailed comparison with upstream. In short:

- **Performance**: the skeleton color pass went from O(bones × vertices) to O(vertices). Measured 8.0 s → 1.5 s on a 45,778-vertex model.
- **Safety**: `assert`-based bounds checks replaced with explicit exceptions; `zstandard` made optional; `bpy.ops` calls wrapped in a context manager.
- **Consistency**: the parsing format and the resulting Blender data are bit-identical to upstream.