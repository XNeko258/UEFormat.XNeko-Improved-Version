bl_info = {
    "name": "UE Format (.uemodel / .ueanim / .uepose)",
    "author": "Half, XNeko",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > UE Format; File > Import",
    "description": (
        "Importer for UEFormat files. "
        "XNeko fork with performance and robustness improvements."
    ),
    "category": "Import-Export",
}

from . import op  # noqa: F401


def register():
    op.register()


def unregister():
    op.unregister()


if __name__ == "__main__":
    register()