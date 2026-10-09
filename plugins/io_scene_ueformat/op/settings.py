"""AddonPreferences + scene property install/uninstall.

UFSettings (the per-scene import configuration) lives in
importer/options.py. This module only handles the plugin-level
preferences and the scene property lifecycle.
"""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences

from ..importer.options import UFSettings


def _armature_only(self, obj):
    return obj is not None and obj.type == "ARMATURE"


def _root_bone_poll(self, bone):
    armature = getattr(self, "ueformat_pose_skeleton", None)
    if armature is None or armature.type != "ARMATURE":
        return False
    return bone.id_data == armature.data


def _on_pose_skeleton_changed(self, context):
    root = getattr(self, "ueformat_pose_root_bone", None)
    if root is None:
        return
    armature = getattr(self, "ueformat_pose_skeleton", None)
    if armature is None or root.id_data != armature.data:
        self.ueformat_pose_root_bone = None


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
    for name, prop in _SCENE_PROPS.items():
        if hasattr(bpy.types.Scene, name):
            continue
        try:
            setattr(bpy.types.Scene, name, prop)
        except Exception as e:
            print(f"[UEFORMAT] failed to install scene prop {name}: {e}")


def uninstall_scene_props() -> None:
    for name in _SCENE_PROPS:
        if hasattr(bpy.types.Scene, name):
            try:
                delattr(bpy.types.Scene, name)
            except Exception:
                pass


class UEFormatPreferences(AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]

    show_import_popup: BoolProperty(
        name="Show Import Time Popup",
        description=(
            "Show a popup with the import duration after each import. "
            "Intended for measuring performance; leave off for normal use"
        ),
        default=False,
    )
    profile_import: BoolProperty(
        name="Log Import Profile",
        description=(
            "Print a per-step timing breakdown to the console after each "
            "import. Intended for diagnosing slow imports"
        ),
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Diagnostics", icon="CONSOLE")
        box.prop(self, "show_import_popup")
        box.prop(self, "profile_import")


def get_diagnostics() -> tuple[bool, bool]:
    try:
        prefs = bpy.context.preferences.addons[
            __package__.rsplit(".", 1)[0]
        ].preferences
    except Exception:
        return False, False
    try:
        return bool(prefs.show_import_popup), bool(prefs.profile_import)
    except Exception:
        return False, False