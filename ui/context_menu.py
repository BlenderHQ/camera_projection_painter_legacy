# <pep8 compliant>

import importlib

import bpy

from . import template
from .. import operators
from .. import icons

if "_rc" in locals(): # In case of module reloading
    importlib.reload(template)
    importlib.reload(operators)
    importlib.reload(icons)

_rc = None


class CPP_MT_camera_pie(bpy.types.Menu):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        col = pie.column(align = True)
        scene = context.scene
        wm = context.window_manager

        camera_object = wm.cpp_current_selected_camera_ob

        if not camera_object:
            return
        
        col.label(text = "Camera:")
        col.emboss = 'RADIAL_MENU'
        col.label(text = camera_object.name)
        col.emboss = 'NORMAL'
        col = col.column(align = True)

        scene = context.scene
        
        template.camera_image(col, camera_object, mode = 'TMP')

        col.emboss = 'RADIAL_MENU'
        props = pie.operator(
            operator = operators.CPP_OT_bind_camera_image.bl_idname,
            icon_value = icons.get_icon_id("bind_image"))
        props.mode = 'TMP'

        state = not camera_object.cpp.initial_hide_viewport
        if state:
            text = "Disable"
            icon = 'HIDE_ON'
        else:
            text = "Enable"
            icon = 'HIDE_OFF'

        pie.operator(
            operator = operators.CPP_OT_toggle_camera_usage.bl_idname,
            text = text, icon = icon
        )

        text = None
        if scene.camera == camera_object:
            text = "Already active"
        
        pie.operator(
            operator = operators.CPP_OT_set_tmp_camera_active.bl_idname,
            text = text, icon_value = icons.get_icon_id("set_active"))
