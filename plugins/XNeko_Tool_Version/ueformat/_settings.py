"""UFSettings PropertyGroup + option dataclasses + tool preference props.

UFSettings lives on bpy.types.Scene. It is installed explicitly by
this module via install_scene_props() / uninstall_scene_props(),
called from the tool's on_load / on_unload. This avoids depending on
the framework's scene_props mechanism, which requires a matching
core.py version.

Scene property names are prefixed with "ueformat_" to avoid
colliding with other tools that may also register scene-level
properties.

Diagnostics toggles (show_import_popup, profile_import) are declared
in preference_props instead of on UFSettings: they are plugin-level
debug switches, not per-file import settings, and they live in the
addon preferences panel rather than the N panel. get_diagnostics()
reads their current values for the import operators.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup


class UFSettings(PropertyGroup):
    scale_factor: FloatProperty(name="Scale", default=0.01, min=0.01)

    bone_length: FloatProperty(name="Bone Length", default=4.0, min=0.1)
    reorient_bones: BoolProperty(name="Reorient Bones", default=False)
    target_lod: IntProperty(name="Level of Detail", default=0, min=0)
    import_collision: BoolProperty(name="Import Collision", default=False)
    import_morph_targets: BoolProperty(name="Import Morph Targets", default=True)
    import_sockets: BoolProperty(name="Import Sockets", default=True)
    import_virtual_bones: BoolProperty(name="Import Virtual Bones", default=False)

    rotation_only: BoolProperty(name="Rotation Only", default=False)
    import_curves: BoolProperty(name="Import Curves", default=True)

    def get_props(self) -> dict:
        return {
            key: getattr(self, key)
            for key in type(self).__annotations__.keys()
        }


# ============================================================
# Scene-level property polls and callbacks
# ============================================================
def _armature_only(self, obj):
    return obj is not None and obj.type == "ARMATURE"


def _root_bone_poll(self, bone):
    """Only allow bones that belong to the currently selected armature."""
    armature = getattr(self, "ueformat_pose_skeleton", None)
    if armature is None or armature.type != "ARMATURE":
        return False
    return bone.id_data == armature.data


def _on_pose_skeleton_changed(self, context):
    """Clear the root bone picker if it no longer matches the skeleton."""
    root = getattr(self, "ueformat_pose_root_bone", None)
    if root is None:
        return
    armature = getattr(self, "ueformat_pose_skeleton", None)
    if armature is None or root.id_data != armature.data:
        self.ueformat_pose_root_bone = None


# ============================================================
# Scene property definitions
# ============================================================
_SCENE_PROPS = {
    "ueformat_settings": bpy.props.PointerProperty(type=UFSettings),

    "ueformat_anim_skeleton": bpy.props.PointerProperty(
        name="Override Skeleton",
        description="Armature to apply the animation to",
        type=bpy.types.Object,
        poll=_armature_only,
    ),
    "ueformat_pose_skeleton": bpy.props.PointerProperty(
        name="Override Skeleton",
        description="Armature to apply the pose to",
        type=bpy.types.Object,
        poll=_armature_only,
        update=_on_pose_skeleton_changed,
    ),
    "ueformat_pose_root_bone": bpy.props.PointerProperty(
        name="Root Bone",
        description="Leave empty to use the armature's first bone",
        type=bpy.types.Bone,
        poll=_root_bone_poll,
    ),
}


def install_scene_props() -> None:
    """Attach the scene properties to bpy.types.Scene.

    Idempotent: properties already present on Scene are skipped, so
    repeated on_load calls do not log spurious errors or attempt to
    reassign bound descriptors.
    """
    for name, prop in _SCENE_PROPS.items():
        if hasattr(bpy.types.Scene, name):
            continue
        try:
            setattr(bpy.types.Scene, name, prop)
        except Exception as e:
            print(f"[XNeko/UEFORMAT] failed to install scene prop "
                  f"{name}: {e}")


def uninstall_scene_props() -> None:
    """Remove the scene properties from bpy.types.Scene."""
    for name in _SCENE_PROPS:
        if hasattr(bpy.types.Scene, name):
            try:
                delattr(bpy.types.Scene, name)
            except Exception:
                pass


# ============================================================
# Addon preference properties (diagnostics)
# ============================================================
preference_props = {
    "show_import_popup": BoolProperty(
        name="Show Import Time Popup",
        description=(
            "Show a popup with the import duration after each import. "
            "Intended for measuring performance; leave off for normal use"
        ),
        default=False,
    ),
    "profile_import": BoolProperty(
        name="Log Import Profile",
        description=(
            "Print a per-step timing breakdown to the console after each "
            "import. Intended for diagnosing slow imports"
        ),
        default=False,
    ),
}


def draw_preferences(layout, context, prefs) -> None:
    """Draw the tool's diagnostics UI in the addon preferences panel.

    `prefs` is the framework's per-tool preference namespace, through
    which preference_props values are read and drawn.
    """
    box = layout.box()
    box.label(text="Diagnostics", icon="CONSOLE")
    prefs.prop(box, "show_import_popup")
    prefs.prop(box, "profile_import")


def get_diagnostics() -> tuple[bool, bool]:
    """Return (show_popup, profile_import) from the tool preferences.

    Falls back to (False, False) when the framework or the tool
    preference namespace is not available yet. Never raises.
    """
    try:
        from ....preferences import get_tool_prefs
        prefs = get_tool_prefs("ueformat")
    except Exception:
        return False, False
    if prefs is None:
        return False, False
    try:
        return bool(prefs.show_import_popup), bool(prefs.profile_import)
    except Exception:
        return False, False


# ============================================================
# Option dataclasses
# ============================================================
@dataclass(slots=True)
class UEFormatOptions:
    link: bool = True
    scale_factor: float = 0.01
    profile_import: bool = False

    @classmethod
    def from_settings(cls, settings: UFSettings):
        return cls(**{
            k: v for k, v in settings.get_props().items()
            if k in inspect.signature(cls).parameters
        })


@dataclass(slots=True)
class UEModelOptions(UEFormatOptions):
    bone_length: float = 4.0
    reorient_bones: bool = False
    import_collision: bool = False
    import_sockets: bool = True
    import_morph_targets: bool = True
    import_virtual_bones: bool = False
    target_lod: int = 0
    allowed_reorient_children: dict | None = None


@dataclass(slots=True)
class UEAnimOptions(UEFormatOptions):
    rotation_only: bool = False
    import_curves: bool = True
    override_skeleton: bpy.types.Object | None = None


@dataclass(slots=True)
class UEPoseOptions(UEFormatOptions):
    root_bone: str = ""
    override_skeleton: bpy.types.Object | None = None