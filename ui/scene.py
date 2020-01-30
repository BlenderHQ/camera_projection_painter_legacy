# <pep8 compliant>

import importlib
import os

import bpy

from . import template
from .. import poll
from .. import icons
from .. import operators

if "_rc" in locals():  # In case of module reloading
    importlib.reload(template)
    importlib.reload(poll)
    importlib.reload(icons)
    importlib.reload(operators)

_rc = None


class SceneOptions:
    """Base class for interface elements in the scene tab"""
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}


class CPP_PT_camera_painter_scene(bpy.types.Panel, SceneOptions):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)

        scene = context.scene

        row = col.row(align=True)
        row.prop(scene.cpp, "source_images_path", icon='IMAGE')
        srow = row.row()
        srow.enabled = False
        if os.path.isdir(scene.cpp.source_images_path):
            srow.enabled = True
        props = srow.operator(
            operator="wm.path_open",
            text="",
            icon='EXTERNAL_DRIVE'
        )
        props.filepath = scene.cpp.source_images_path
        # col.prop(scene.cpp, "calibration_source_file", icon_id = 'FILE_CACHE')

        col.separator()

        scol = col.column()
        scol.enabled = scene.cpp.has_camera_objects_selected
        props = scol.operator(
            operator=operators.CPP_OT_bind_camera_image.bl_idname,
            text="Bind Selected Camera Images",
            text_ctxt="CPP",
            icon_value=icons.get_icon_id("bind_image")
        )
        props.mode = 'SELECTED'

        scol = col.column()
        scol.enabled = scene.cpp.has_camera_objects
        props = scol.operator(
            operator=operators.CPP_OT_bind_camera_image.bl_idname,
            text="Bind All Camera Images",
            text_ctxt="CPP",
            icon_value=icons.get_icon_id("bind_image")
        )
        props.mode = 'ALL'

        # scol = col.column()
        # scol.operator(
        #              operator = CPP_OT_set_camera_calibration_from_file.bl_idname,
        #              icon_value = get_icon_id("calibration"))


class CPP_PT_enter_context(bpy.types.Panel, SceneOptions):
    bl_label = "Quick Start"
    bl_parent_id = "CPP_PT_camera_painter_scene"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if not ob:
            return False
        if ob.type != 'MESH':
            return False
        return True

    def draw_header(self, context):
        layout = self.layout
        layout.template_icon(icon_value=icons.get_icon_id("run"))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)

        col.separator()
        row = col.row(align=True)
        row.operator(operator=operators.CPP_OT_enter_context.bl_idname,
                     icon_value=icons.get_icon_id("run"))

        template.missing_context(col, context)

        col.separator()

        scene = context.scene
        ob = context.active_object

        if ob.active_material:
            col.label(text="Material:")
        else:
            col.label(text="Object have no active material", icon='INFO')

        props = col.operator(
            operator=operators.CPP_OT_canvas_to_diffuse.bl_idname,
            text="Canvas Image To Diffuse"
        )
        props.reverse = False

        props = col.operator(
            operator=operators.CPP_OT_canvas_to_diffuse.bl_idname,
            text="Diffuse To Canvas Image"
        )
        props.reverse = True

        col.prop(scene.cpp, "use_bind_canvas_diffuse")

        col.label(text="Experimental:")
        col.operator(operator=operators.CPP_OT_set_all_cameras_sensor.bl_idname)
