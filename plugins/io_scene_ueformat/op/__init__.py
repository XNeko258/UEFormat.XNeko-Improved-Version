"""UE Format plugin registration entry point."""

import bpy

from .import_helpers import (
    UFImportUEModel,
    UFImportUEAnim,
    UFImportUEPose,
    UFShowImportTime,
    IO_FH_uemodel,
    IO_FH_ueanim,
    IO_FH_uepose,
    register_import_menu,
    unregister_import_menu,
)
from .panels import UEFORMAT_PT_Panel
from .settings import (
    UEFormatPreferences,
    install_scene_props,
    uninstall_scene_props,
)
from ..importer.options import UFSettings


_blender_classes = (
    UEFormatPreferences,
    UFSettings,
    UEFORMAT_PT_Panel,
    UFImportUEModel,
    UFImportUEAnim,
    UFImportUEPose,
    UFShowImportTime,
    IO_FH_uemodel,
    IO_FH_ueanim,
    IO_FH_uepose,
)


def register() -> None:
    for cls in _blender_classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"[UEFORMAT] failed to register {cls.__name__}: {e}")

    install_scene_props()
    register_import_menu()


def unregister() -> None:
    unregister_import_menu()
    uninstall_scene_props()

    for cls in reversed(_blender_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass