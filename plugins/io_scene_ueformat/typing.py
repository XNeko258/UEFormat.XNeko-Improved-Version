"""Type aliases for the UE Format importer.

Mirrors the upstream layout. These subclasses exist only to give
type checkers accurate information about runtime objects; they are
never instantiated.

The entire class body is guarded by TYPE_CHECKING so that no runtime
subclass of bpy.types.Scene or bpy.types.Context is ever created.
Subclassing Blender's built-in types at import time adds permanent
entries to Scene.__subclasses__() and Context.__subclasses__(),
which can confuse tools that walk those hierarchies.

Nothing in this fork imports UFormatScene or UFormatContext directly;
they exist purely for the public type surface.
"""

from typing import TYPE_CHECKING

from bpy.types import Context, Scene

if TYPE_CHECKING:
    from .importer.options import UFSettings

    class UFormatScene(Scene):
        ueformat_settings: "UFSettings"

    class UFormatContext(Context):
        scene: UFormatScene