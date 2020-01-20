# <pep8 compliant>

import importlib

import bpy

from . import operators

if "_rc" in locals():
    importlib.reload(operators)

_rc = None


_keymaps = []

ADDON_KEYMAP = {
    operators.CPP_OT_image_paint.bl_idname: (
        (
            {"type": 'LEFTMOUSE', "value": 'PRESS', "head": True},
            None
        ),
    ),

    operators.CPP_OT_set_camera_by_view.bl_idname: (
        (
            {"type": 'X', "value": 'PRESS', "alt": True},
            None
        ),
    ),

    operators.CPP_OT_enable_all_cameras.bl_idname: (
        (
            {"type": 'H', "value": 'PRESS', "alt": True},
            None
        ),
    ),

    operators.CPP_OT_set_camera_radial.bl_idname: (
        (
            {"type": 'LEFT_ARROW', "value": 'PRESS'},
            {"order": 'PREV'}
        ),

        (
            {"type": 'RIGHT_ARROW', "value": 'PRESS'},
            {"order": 'NEXT'}
        )
    ),

    "view3d.view_center_pick": (
        (
            {"type": 'SPACE', "value": 'PRESS'},
            None
        ),
    ),

    "wm.context_toggle": (
        (
            {"type": 'I', "value": 'PRESS'},
            {"data_path": "scene.cpp.use_camera_image_previews"}
        ),

        (
            {"type": 'O', "value": 'PRESS'},
            {"data_path": "scene.cpp.use_projection_preview"}
        ),

        (
            {"type": 'P', "value": 'PRESS'},
            {"data_path": "scene.cpp.use_current_image_preview"}
        )
    ),
}


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new("Image Paint")

    for idname, data in ADDON_KEYMAP.items():
        for variance in data:
            key_data, properties = variance

            key_data["idname"] = idname

            kmi = km.keymap_items.new(**key_data)

            if properties:
                for attr, value in properties.items():
                    if hasattr(kmi.properties, attr):
                        setattr(kmi.properties, attr, value)
                    else:
                        print(attr, value)
                        print(kmi.properties.bl_rna)

            _keymaps.append((km, kmi))


def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
