# <pep8 compliant>

import importlib

import bpy
import gpu
import bgl
from mathutils import Vector
from mathutils.geometry import intersect_point_quad_2d
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

from .. import __package__ as addon_pkg
from .. import poll
from .. import shaders

if "_rc" in locals():  # In case of module reloading
    importlib.reload(poll)
    importlib.reload(shaders)

_rc = None

def f_lerp(value0: float, value1: float, factor: float):
    """Linear interpolate float value"""
    return (value0 * (1.0 - factor)) + (value1 * factor)


def get_curr_img_pos_from_context(context: bpy.types.Context):
    """
    Returns the absolute position in pixels, the size of the square of the image,
    and the ability to draw (only if the image frame does not go beyond the frame of the viewer)
    relative to the square from the edge of the n-panel to the edge of the t-panel horizontally
    and from the top to the bottom edge of the 3D view with the specified empty space tolerance
    """
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    image = image_paint.clone_image

    if image and image.cpp.valid:
        preferences = context.preferences.addons[addon_pkg].preferences
        empty_space = preferences.border_empty_space

        area = context.area

        tools_width = [n for n in area.regions if n.type == 'TOOLS'][-1].width  # N-panel width
        ui_width = [n for n in area.regions if n.type == 'UI'][-1].width  # T-panel width
        area_size = Vector([area.width - ui_width - tools_width - empty_space, area.height - empty_space])

        image_size = Vector(image.cpp.aspect_scale) * scene.cpp.current_image_size
        possible = True
        if image_size.x > area_size.x - empty_space or image_size.y > area_size.y - empty_space:
            possible = False

        image_rel_pos = scene.cpp.current_image_position
        rpx, rpy = image_rel_pos
        apx = f_lerp(empty_space, area_size.x - image_size.x, rpx) + tools_width
        apy = f_lerp(empty_space, area_size.y - image_size.y, rpy)

        return Vector((apx, apy)), image_size, possible


class CPP_GT_current_image_preview(bpy.types.Gizmo):
    bl_idname = "CPP_GT_current_image_preview"

    image_batch: gpu.types.GPUBatch
    pixel_pos: Vector
    pixel_size: Vector
    rel_offset: Vector
    restore_show_brush: bool

    __slots__ = (
        "image_batch",
        "pixel_pos",
        "pixel_size",
        "rel_offset",
        "restore_show_brush",
    )

    @staticmethod
    def _get_image_rel_pos(context, event):
        area = context.area
        return Vector([(event.mouse_x - area.x) / area.width, (event.mouse_y - area.y) / area.height])

    def setup(self):
        self.image_batch = batch_for_shader(
            shaders.shader.current_image, 'TRI_FAN',
            {"pos": ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
             "uv": ((0, 0), (1, 0), (1, 1), (0, 1))})

    def draw(self, context):
        scene = context.scene
        rv3d = context.region_data
        camera_ob = scene.camera
        image_paint = scene.tool_settings.image_paint
        image = image_paint.clone_image

        if not image or (not image.cpp.valid):
            return

        shader = shaders.shader.current_image
        batch = self.image_batch

        curr_img_pos = get_curr_img_pos_from_context(context)
        if not curr_img_pos:
            return

        self.pixel_pos, self.pixel_size, possible = curr_img_pos

        if rv3d.view_perspective == 'CAMERA':
            view_frame = [camera_ob.matrix_world @ v for v in camera_ob.data.view_frame(scene = scene)]
            p0 = view3d_utils.location_3d_to_region_2d(context.region, rv3d, coord = view_frame[2])
            p1 = view3d_utils.location_3d_to_region_2d(context.region, rv3d, coord = view_frame[0])
            pos = p0
            size = p1.x - p0.x, p1.y - p0.y
        else:
            pos = self.pixel_pos
            size = self.pixel_size

        if not possible:
            return

        self.alpha = scene.cpp.current_image_alpha

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_POLYGON_SMOOTH)

        with gpu.matrix.push_pop():
            gpu.matrix.translate(pos)
            gpu.matrix.scale(size)

            if image.gl_load():
                raise Exception()

            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

            shader.bind()
            shader.uniform_int("image", 0)

            alpha = self.alpha_highlight if self.is_highlight else scene.cpp.current_image_alpha
            shader.uniform_float("alpha", alpha)
            shader.uniform_bool("colorspace_srgb", (image.colorspace_settings.name == 'sRGB',))

            batch.draw(shader)

        bgl.glDisable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_POLYGON_SMOOTH)

    def test_select(self, context, location):
        rv3d = context.region_data

        if rv3d.view_perspective == 'CAMERA':
            return -1
        curr_img_pos = get_curr_img_pos_from_context(context)
        if not curr_img_pos:
            return -1
        pos, size, possible = curr_img_pos
        if not possible:
            return -1

        mouse_pos = Vector(location)
        mpr_pos = self.pixel_pos
        quad_p1 = mpr_pos
        quad_p2 = mpr_pos + Vector((0.0, self.pixel_size.y))
        quad_p3 = mpr_pos + self.pixel_size
        quad_p4 = mpr_pos + Vector((self.pixel_size.x, 0.0))
        res = intersect_point_quad_2d(mouse_pos, quad_p1, quad_p2, quad_p3, quad_p4)
        if res == -1:
            return 0
        return -1

    def invoke(self, context, event):
        wm = context.window_manager
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        self.restore_show_brush = bool(image_paint.show_brush)
        image_paint.show_brush = False
        self.rel_offset = Vector(scene.cpp.current_image_position) - self._get_image_rel_pos(context, event)
        wm.cpp_suspended = True
        return {'RUNNING_MODAL'}

    def modal(self, context, event, tweak):
        scene = context.scene
        rel_pos = self._get_image_rel_pos(context, event) + self.rel_offset
        snap_points = [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (0.0, 1.0), (0.5, 1.0), (1.0, 1.0), (0.0, 0.5), (1.0, 0.5)]
        if 'PRECISE' in tweak:
            pass  # Maybe, some another action for precise?
        elif 'SNAP' in tweak:
            rel_pos = Vector((sorted(snap_points, key = lambda dist: (Vector(dist) - rel_pos).length)[0]))
        scene.cpp.current_image_position = rel_pos
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        wm = context.window_manager
        wm.cpp_suspended = False
        image_paint = context.scene.tool_settings.image_paint
        image_paint.show_brush = self.restore_show_brush


class CPP_GGT_image_preview_gizmo_group(bpy.types.GizmoGroup):
    bl_idname = "CPP_GGT_image_preview_gizmo_group"
    bl_label = "Image Preview Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    mpr: bpy.types.Gizmo
    mpr_scale: bpy.types.Gizmo

    @classmethod
    def poll(cls, context):
        if not poll.full_poll(context):
            return False
        scene = context.scene
        return scene.cpp.use_current_image_preview and scene.cpp.current_image_alpha

    def setup(self, context):
        mpr = self.gizmos.new(CPP_GT_current_image_preview.bl_idname)
        mpr.use_draw_scale = True
        mpr.alpha_highlight = 1.0
        mpr.use_draw_modal = True
        mpr.use_select_background = True
        mpr.use_grab_cursor = True

        self.mpr = mpr
