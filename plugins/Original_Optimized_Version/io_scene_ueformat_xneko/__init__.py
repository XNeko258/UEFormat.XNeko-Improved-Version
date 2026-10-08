bl_info = {
    "name": "UE Format (XNeko fork)",
    "author": "Half (original), XNeko fork",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > UE Format; File > Import",
    "description": (
        "Importer for UEFormat files (.uemodel / .ueanim / .uepose). "
        "Fork of the original UE Format addon with performance and "
        "robustness fixes."
    ),
    "category": "Import-Export",
}

import bpy

from . import _operators
from . import _panel
from . import _settings
from . import _zstd


classes = (
    _settings.UEFormatPreferences,
    _settings.UFSettings,
    _panel.UEFORMAT_PT_Panel,
    _operators.UFImportUEModel,
    _operators.UFImportUEAnim,
    _operators.UFImportUEPose,
    _operators.UFShowImportTime,
    _operators.IO_FH_uemodel,
    _operators.IO_FH_ueanim,
    _operators.IO_FH_uepose,
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"[UEFORMAT] failed to register {cls.__name__}: {e}")

    _settings.install_scene_props()
    _operators.register_import_menu()
    _zstd.reset_cache()


def unregister():
    _operators.unregister_import_menu()
    _settings.uninstall_scene_props()
    _zstd.reset_cache()

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass