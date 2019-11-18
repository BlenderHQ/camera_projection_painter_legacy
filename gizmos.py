# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


import bpy
import gpu
import bgl

from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_point_quad_2d
from bpy.types import Gizmo, GizmoGroup

from .utils import utils_poll, utils_state, utils_draw
from .shaders import shaders

_preview_bindcodes = {}


def open_gl_draw(func):
    def wrapper(self, context):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
        bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
        bgl.glPolygonOffset(0.1, 0.9)
        bgl.glPointSize(3.0)

        ret = func(self, context)

        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)
        bgl.glPointSize(1.0)
        return ret

    return wrapper


def generate_preview_bincodes(self, context):
    images = bpy.data.images
    count = len(images)

    if not count:
        return

    id_buff = bgl.Buffer(bgl.GL_INT, count)
    bgl.glGenTextures(count, id_buff)

    for image in images:
        preview = image.preview
        pixels = list(preview.image_pixels)

        if not len(pixels):
            context.window.cursor_set('WAIT')
            bpy.ops.wm.previews_ensure('INVOKE_DEFAULT')
            # self.report(type = {'INFO'}, message = "Data previews refreshed, save a file to store")
            context.window.cursor_set('DEFAULT')
            break

    for i, image in enumerate(images):
        bindcode = id_buff.to_list()[i]
        preview = image.preview
        pixels = list(preview.image_pixels)
        if not len(pixels):
            continue

        width, height = preview.image_size
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
        image_buffer = bgl.Buffer(bgl.GL_INT, len(pixels), pixels)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER | bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA,
                         width, height, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, image_buffer)

        _preview_bindcodes[image] = bindcode


class CPP_GT_camera_gizmo(Gizmo):
    shape: object
    camera_object: bpy.types.Object
    batch_image_preview: gpu.types.GPUBatch

    bl_idname = "CPP_GT_camera_gizmo"

    __slots__ = (
        "shape",
        "camera_object",
        "batch_image_preview",
    )

    def setup(self):
        if not hasattr(self, "point_shape"):
            self.shape = self.new_custom_shape('POINTS', ((0.0, 0.0, 0.0),))
        self.camera_object = None

    def invoke(self, context, event):
        return {'RUNNING_MODAL'}

    def modal(self, context, event, tweak):
        utils_state.state.tmp_camera = self.camera_object
        bpy.ops.wm.call_menu_pie(name = "CPP_MT_camera_pie")
        return {'FINISHED'}

    def test_select(self, context, location):
        return -1

    @open_gl_draw
    def draw(self, context):
        cpp_data = self.camera_object.data.cpp
        preferences = context.preferences.addons[__package__].preferences

        if not preferences.always_draw_gizmo_point:
            if self.is_highlight:
                self.draw_custom_shape(self.shape)
        else:
            self.draw_custom_shape(self.shape)
        if cpp_data.available:
            self.color = preferences.gizmo_color
            if cpp_data.image in _preview_bindcodes:
                shader = shaders.camera_image_preview

                shader.bind()
                shader.uniform_float("modelMatrix", self.matrix_basis)

                bindcode = _preview_bindcodes[cpp_data.image]
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
                shader.uniform_int("image", 0)
                self.batch_image_preview.draw(shader)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.shape, select_id = select_id)

    def update_camera(self, context):
        camera = self.camera_object.data
        view_frame = camera.view_frame(scene = context.scene)
        display_size = camera.display_size
        asp = view_frame[0].y
        view_frame = [n * display_size for n in view_frame]

        self.batch_image_preview = batch_for_shader(
            shaders.camera_image_preview, 'TRI_FAN',
            {"pos": view_frame,
             "texCoord": ((1, 0.5 + asp), (1, 0.5 - asp), (0, 0.5 - asp), (0, 0.5 + asp))})


class CPP_GGT_camera_gizmo_group(GizmoGroup):
    bl_idname = "CPP_GGT_camera_gizmo_group"
    bl_label = "Camera Painter Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'DEPTH_3D', 'SCALE'}

    @classmethod
    def poll(cls, context):
        return utils_poll.tool_setup_poll(context)

    def setup(self, context):
        preferences = context.preferences.addons[__package__].preferences

        for ob in context.scene.cpp.visible_camera_objects:
            mpr = self.gizmos.new(CPP_GT_camera_gizmo.bl_idname)

            mpr.matrix_basis = ob.matrix_world.normalized()
            mpr.camera_object = ob
            mpr.color = preferences.gizmo_color
            mpr.alpha = preferences.gizmo_alpha
            mpr.alpha_highlight = preferences.gizmo_alpha

            mpr.use_draw_scale = True
            mpr.scale_basis = preferences.gizmo_scale_basis
            #mpr.use_draw_modal = False
            mpr.use_select_background = True
            mpr.use_event_handle_all = False
            mpr.use_grab_cursor = True
            mpr.update_camera(context)

    def refresh(self, context):
        for mpr in self.gizmos:
            try:
                mpr.matrix_basis = mpr.camera_object.matrix_world.normalized() @ Matrix.Translation((0.0, 0.0, 0.1))
                mpr.update_camera(context)
            except ReferenceError:
                self.gizmos.remove(mpr)
                continue


class CPP_GT_current_image_preview(Gizmo):
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
            shaders.current_image, 'TRI_FAN',
            {"pos": ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
             "uv": ((0, 0), (1, 0), (1, 1), (0, 1))})

    @open_gl_draw
    def draw(self, context):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        image = image_paint.clone_image

        shader = shaders.current_image
        batch = self.image_batch

        pos, size, possible = utils_draw.get_curr_img_pos_from_context(context)

        if not possible:
            return

        self.pixel_pos = pos
        self.pixel_size = size
        self.alpha = scene.cpp.current_image_alpha

        bgl.glEnable(bgl.GL_BLEND)
        with gpu.matrix.push_pop():
            gpu.matrix.translate(self.pixel_pos)
            gpu.matrix.scale(self.pixel_size)

            if image.gl_load():
                raise Exception()

            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

            shader.bind()
            shader.uniform_int("image", 0)

            alpha = self.alpha_highlight if self.is_highlight else scene.cpp.current_image_alpha
            shader.uniform_float("alpha", alpha)

            batch.draw(shader)

    def test_select(self, context, location):
        pos, size, possible = utils_draw.get_curr_img_pos_from_context(context)
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
            utils_state.state.operator.suspended = True
            return 0
        utils_state.state.operator.suspended = False
        return -1

    def invoke(self, context, event):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        self.restore_show_brush = bool(image_paint.show_brush)
        image_paint.show_brush = False
        utils_state.state.operator.suspended = True
        self.rel_offset = Vector(scene.cpp.current_image_position) - self._get_image_rel_pos(context, event)
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
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        image_paint = context.scene.tool_settings.image_paint
        image_paint.show_brush = self.restore_show_brush
        utils_state.state.operator.suspended = False


class CPP_GGT_image_preview_gizmo_group(GizmoGroup):
    bl_idname = "CPP_GGT_image_preview_gizmo_group"
    bl_label = "Image Preview Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    mpr: Gizmo
    mpr_scale: Gizmo

    @classmethod
    def poll(cls, context):
        if not utils_poll.full_poll(context):
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


_classes = [
    CPP_GT_camera_gizmo,
    CPP_GGT_camera_gizmo_group,
    CPP_GT_current_image_preview,
    CPP_GGT_image_preview_gizmo_group
]

register, unregister = bpy.utils.register_classes_factory(_classes)
