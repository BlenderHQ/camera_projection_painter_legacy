# <pep8 compliant>

import bpy

from . import operators

_keymaps = []


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new("Image Paint")

    kmi = km.keymap_items.new(
        idname = operators.CPP_OT_image_paint.bl_idname,
        type = 'LEFTMOUSE',
        value = 'PRESS',
        head = True
    )
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new(
        idname = operators.CPP_OT_set_camera_by_view.bl_idname,
        type = 'X',
        value = 'PRESS',
        alt = True)
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new(idname = "view3d.view_center_pick", type = 'SPACE', value = 'PRESS', alt = True)
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new(idname = "wm.context_toggle", type = 'I', value = 'PRESS')
    kmi.properties.data_path = "scene.cpp.use_camera_image_previews"
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new(idname = "wm.context_toggle", type = 'O', value = 'PRESS')
    kmi.properties.data_path = "scene.cpp.use_projection_preview"
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new(idname = "wm.context_toggle", type = 'P', value = 'PRESS')
    kmi.properties.data_path = "scene.cpp.use_current_image_preview"
    _keymaps.append((km, kmi))


def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
