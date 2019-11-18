import bpy
import bgl
import gpu
from mathutils import Vector
from bpy.types import SpaceView3D

from . import utils_state

from .utils_warning import get_warning_status
from .utils_poll import full_poll_decorator
from .common import get_hovered_region_3d, iter_curve_values, flerp

from ..constants import TEMP_DATA_NAME
from ..shaders import shaders
from .. import __package__ as addon_pkg

import time
import numpy as np


class CameraProjectionPainterDrawUtils:
    def add_draw_handlers(self, context):
        args = (self, context)
        callback = draw_projection_preview
        self.draw_handler = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'PRE_VIEW')

    def remove_draw_handlers(self):
        if self.draw_handler:
            SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')

    def generate_brush_texture(self, context):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        brush = image_paint.brush
        pixel_width = scene.tool_settings.unified_paint_settings.size

        check_steps = 10  # Check curve values for every 10% to check any updates. Its biased, but fast.
        check_tuple = tuple((n for n in iter_curve_values(brush.curve, check_steps))) + (pixel_width,)

        if self.check_brush_curve_updated(check_tuple):
            pixels = [int(n * 255) for n in iter_curve_values(brush.curve, pixel_width)]

            id_buff = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenTextures(1, id_buff)

            bindcode = id_buff.to_list()[0]

            bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
            image_buffer = bgl.Buffer(bgl.GL_INT, len(pixels), pixels)
            bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER | bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
            bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RED,
                             pixel_width, 1, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, image_buffer)

            self.brush_texture_bindcode = bindcode


def get_curr_img_pos_from_context(context):
    area = context.area
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    image = image_paint.clone_image

    preferences = context.preferences.addons[addon_pkg].preferences
    empty_space = preferences.border_empty_space

    tools_width = [n for n in area.regions if n.type == 'TOOLS'][-1].width  # N-panel width
    ui_width = [n for n in area.regions if n.type == 'UI'][-1].width  # T-panel width
    area_size = Vector([area.width - ui_width - tools_width - empty_space, area.height - empty_space])

    image_size = Vector([1.0, image.size[1] / image.size[0]]) * scene.cpp.current_image_size
    possible = True
    if image_size.x > area_size.x - empty_space or image_size.y > area_size.y - empty_space:
        possible = False

    image_rel_pos = scene.cpp.current_image_position
    rpx, rpy = image_rel_pos
    apx = flerp(empty_space, area_size.x - image_size.x, rpx) + tools_width
    apy = flerp(empty_space, area_size.y - image_size.y, rpy)

    return Vector((apx, apy)), image_size, possible


def generate_batch_attributes(bm):
    uv_layer = bm.loops.layers.uv.get(TEMP_DATA_NAME)
    if uv_layer:
        loop_triangles = bm.calc_loop_triangles()
        vertices = np.empty((len(bm.verts), 3), dtype = np.float32)
        normals = np.empty((len(bm.verts), 3), dtype = np.float32)
        unique_uv = np.zeros((len(bm.verts), 2), dtype = np.float32)
        indices = np.empty((len(loop_triangles), 3), dtype = np.int32)

        for index, vertex in enumerate(bm.verts):
            vertices[index] = vertex.co
            normals[index] = vertex.normal
        triangle_indices = np.empty(3, dtype = np.int32)
        zero_uv = np.zeros(2, dtype = np.float32)

        for index, loop_triangles in enumerate(loop_triangles):
            for loop_index, loop in enumerate(loop_triangles):
                vertex_index = loop.vert.index
                triangle_indices[loop_index] = vertex_index
                if (unique_uv[vertex_index] == zero_uv).all():
                    unique_uv[vertex_index] = loop[uv_layer].uv

            indices[index] = triangle_indices

        return vertices, normals, unique_uv, indices


def generate_updated_unique_uv(bm):
    uv_layer = bm.loops.layers.uv.get(TEMP_DATA_NAME)
    if uv_layer:
        loop_triangles = bm.calc_loop_triangles()
        unique_uv = np.empty((len(bm.verts), 2), dtype = np.float)

        skip_vert_indices = np.empty(len(bm.verts), dtype = np.bool)

        for loop_triangles in loop_triangles:
            for loop in loop_triangles:
                vertex_index = loop.vert.index
                if skip_vert_indices[vertex_index]:
                    continue

                skip_vert_indices[vertex_index] = True
                unique_uv[vertex_index] = loop[uv_layer].uv

        return unique_uv


def generate_fmt():
    fmt = gpu.types.GPUVertFormat()
    fmt.attr_add(id = "pos", comp_type = 'F32', len = 3, fetch_mode = 'FLOAT')
    fmt.attr_add(id = "normal", comp_type = 'F32', len = 3, fetch_mode = 'FLOAT')
    fmt.attr_add(id = "unique_uv", comp_type = 'F32', len = 2, fetch_mode = 'FLOAT')
    return fmt


def generate_ibo(indices):
    return gpu.types.GPUIndexBuf(type = 'TRIS', seq = indices)


def generate_vbo(fmt, vertices, normals, unique_uv):
    vbo = gpu.types.GPUVertBuf(len = len(vertices), format = fmt)
    vbo.attr_fill(id = "pos", data = vertices)
    vbo.attr_fill(id = "normal", data = normals)
    vbo.attr_fill(id = "unique_uv", data = unique_uv)
    return vbo


def generate_batch(vbo, ibo):
    return gpu.types.GPUBatch(type = 'TRIS', buf = vbo, elem = ibo)


@full_poll_decorator
def draw_projection_preview(self, context):
    scene = context.scene

    if not scene.cpp.use_projection_preview:
        return
    if self.suspended:
        return

    preferences = context.preferences.addons[addon_pkg].preferences
    ob = context.image_paint_object
    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image
    brush = image_paint.brush
    brush_radius = scene.tool_settings.unified_paint_settings.size

    if clone_image.gl_load():
        raise Exception()

    shader = shaders.mesh_preview
    batch = self.mesh_batch
    if not batch:
        return

    mouse_position = utils_state.event.mouse_position
    active_rv3d = get_hovered_region_3d(context)
    current_rv3d = context.area.spaces.active.region_3d

    outline_type = 0
    if scene.cpp.use_projection_outline:
        outline_type = {
            'NO_OUTLINE': 0,
            'FILL': 1,
            'CHECKER': 2
        }[preferences.outline_type]

    outline_width = preferences.outline_width * 0.1
    outline_scale = preferences.outline_scale
    outline_color = preferences.outline_color
    normal_highlight_color = preferences.normal_highlight_color

    # OpenGL setup
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    bgl.glEnable(bgl.GL_MULTISAMPLE)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    # Bind textures
    bgl.glTexParameteri(
        bgl.GL_TEXTURE_2D,
        bgl.GL_TEXTURE_WRAP_S | bgl.GL_TEXTURE_WRAP_T,
        bgl.GL_REPEAT)  # GL_CLAMP_TO_BORDER

    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, clone_image.bindcode)
    bgl.glActiveTexture(bgl.GL_TEXTURE0 + 1)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.brush_texture_bindcode)

    # Set shader uniforms
    shader.bind()

    shader.uniform_float("ModelMatrix", ob.matrix_world)
    # shader.uniform_float("projectorForward", Vector((0.0, 0.0, 1.0)) @ scene.camera.matrix_world.inverted())
    shader.uniform_int("sourceImage", 0)
    shader.uniform_int("brushImage", 1)
    shader.uniform_int("outlineType", outline_type)
    shader.uniform_float("outlineWidth", outline_width)
    shader.uniform_float("outlineScale", outline_scale)
    shader.uniform_float("outlineColor", outline_color)
    shader.uniform_int("useNormalInspection", scene.cpp.use_normal_highlight)
    shader.uniform_float("normalHighlightColor", normal_highlight_color)

    use_brush = False
    if active_rv3d == current_rv3d:
        use_brush = True
        mx, my = mouse_position
        mx -= context.area.x
        my -= context.area.y
        shader.uniform_float("mousePos", (mx, my))
        shader.uniform_float("brushRadius", brush_radius)
        shader.uniform_float("brushStrength", brush.strength)

    shader.uniform_int("useBrush", use_brush)

    if scene.cpp.use_warnings and scene.cpp.use_warning_action_draw:
        danger_zone = get_warning_status(context, active_rv3d)
        shader.uniform_int("warning", danger_zone)
        shader.uniform_float("warningColor", preferences.warning_color)
    else:
        shader.uniform_int("warning", 0)

    shader.uniform_bool("colorspace_srgb", (clone_image.colorspace_settings.name == 'sRGB',))

    # Finally, draw
    batch.draw(shader)
