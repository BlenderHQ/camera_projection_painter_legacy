import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import bmesh
from mathutils import Vector
from bpy.types import SpaceView3D

from . import utils_state

from .utils_warning import get_warning_status
from .utils_poll import full_poll_decorator
from .utils_camera import get_camera_attributes
from .common import get_hovered_region_3d, iter_curve_values, flerp

from ..constants import TEMP_DATA_NAME, PREVIEW_CHECK_MASK
from ..shaders import shaders
from .. import __package__ as addon_pkg

import numpy as np


# Operator cls specific func

def add_draw_handlers(self, context):
    args = (self, context)
    callback = draw_projection_preview
    self.draw_handler = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'POST_VIEW')
    callback = draw_cameras
    self.draw_handler_cameras = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'POST_VIEW')


def remove_draw_handlers(self):
    if self.draw_handler:
        SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
        SpaceView3D.draw_handler_remove(self.draw_handler_cameras, 'WINDOW')


# Base utils

def update_brush_texture_bindcode(self, context):
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


def base_update_preview(context):
    shader = shaders.mesh_preview
    scene = context.scene
    camera = scene.camera

    position, forward, up, scale = get_camera_attributes(context, camera)

    shader.bind()
    shader.uniform_float("projectorPosition", position)
    shader.uniform_float("projectorForward", forward)
    shader.uniform_float("projectorUpAxis", up)
    shader.uniform_float("sourceScale", scale)


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


def get_batch_attributes(bm):
    uv_layer = bm.loops.layers.uv.get(TEMP_DATA_NAME)
    if uv_layer:
        loop_triangles = bm.calc_loop_triangles()
        vertices = np.empty((len(bm.verts), 3), dtype = np.float32)
        normals = np.empty((len(bm.verts), 3), dtype = np.float32)
        indices = np.empty((len(loop_triangles), 3), dtype = np.int32)

        for index, vertex in enumerate(bm.verts):
            vertices[index] = vertex.co
            normals[index] = vertex.normal

        triangle_indices = np.empty(3, dtype = np.int32)
        for index, loop_triangles in enumerate(loop_triangles):
            for loop_index, loop in enumerate(loop_triangles):
                vertex_index = loop.vert.index
                triangle_indices[loop_index] = vertex_index

            indices[index] = triangle_indices

        return vertices, normals, indices


def get_bmesh_batch(bm):
    buf_type = 'TRIS'
    pos, normal, indices = get_batch_attributes(bm)
    fmt_attributes = (("pos", pos), ("normal", normal))

    fmt = gpu.types.GPUVertFormat()
    for fmt_attr in fmt_attributes:
        fmt.attr_add(id = fmt_attr[0], comp_type = 'F32', len = 3, fetch_mode = 'FLOAT')

    ibo = gpu.types.GPUIndexBuf(type = buf_type, seq = indices)

    vbo = gpu.types.GPUVertBuf(len = len(pos), format = fmt)
    for attr_id, attr in fmt_attributes:
        vbo.attr_fill(id = attr_id, data = attr)

    batch = gpu.types.GPUBatch(type = buf_type, buf = vbo, elem = ibo)

    return batch


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
    #current_rv3d = context.area.spaces.active.region_3d
    current_rv3d = context.region_data
    #print(current_rv3d)
    #print(active_rv3d)
    #return

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


def get_camera_batches(context):
    scene = context.scene
    shader_camera = shaders.camera
    shader_camera_image_preview = shaders.camera_image_preview

    res = {}
    for ob in scene.cpp.camera_objects:
        camera = ob.data
        view_frame = camera.view_frame()

        vertices = [Vector((0.0, 0.0, 0.0))]
        vertices.extend(view_frame)

        indices_frame = (
            (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 2), (2, 3), (3, 4), (1, 4)
        )

        indices_image = (
            (1, 2, 3), (3, 4, 1)
        )

        uv = (
            (0.0, 0.0),
            (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0),
        )

        batch_frame = batch_for_shader(
            shader_camera, 'LINES',
            {"pos": vertices},
            indices = indices_frame,
        )
        batch_image = batch_for_shader(
            shader_camera_image_preview, 'TRIS',
            {"pos": vertices, "uv": uv},
            indices = indices_image,
        )
        res[ob] = batch_frame, batch_image

    return res


_preview_bindcodes = {}


def clear_preview_bindcodes():
    global _preview_bindcodes
    _preview_bindcodes = {}


def get_preview_bincode(image):
    id_buff = bgl.Buffer(bgl.GL_INT, 1)
    bgl.glGenTextures(1, id_buff)

    bindcode = id_buff.to_list()[0]
    preview = image.preview
    pixels = list(preview.image_pixels)

    width, height = preview.image_size
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
    image_buffer = bgl.Buffer(bgl.GL_INT, len(pixels), pixels)
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER | bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
    bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA,
                     width, height, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, image_buffer)

    _preview_bindcodes[image] = bindcode
    return bindcode


def check_preview(image):
    return [round(n, 1) for n in image.preview.image_pixels_float[0:len(PREVIEW_CHECK_MASK)]] == PREVIEW_CHECK_MASK


@full_poll_decorator
def draw_cameras(self, context):
    scene = context.scene
    shader_camera = shaders.camera
    shader_camera_image_preview = shaders.camera_image_preview

    preferences = context.preferences.addons[addon_pkg].preferences

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    bgl.glEnable(bgl.GL_MULTISAMPLE)

    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glLineWidth(preferences.camera_line_width)

    for ob in scene.cpp.camera_objects:
        batches = self.camera_batches.get(ob)
        if not batches:
            continue
        batch_frame, batch_image = batches

        mat = ob.matrix_world.copy()
        display_size = scene.cpp.cameras_viewport_size

        shader_camera_image_preview.bind()

        image = ob.data.cpp.image

        size_x, size_y = image.cpp.static_size
        if size_x > size_y:
            aspect_x = 1.0
            aspect_y = size_y / size_x
        elif size_y > size_x:
            aspect_x = 1.0
            aspect_y = size_y / size_x
        else:
            aspect_x = 1.0
            aspect_y = 1.0

        if scene.cpp.use_camera_image_previews:
            if image not in _preview_bindcodes.keys():
                if check_preview(image):
                    bindcode = get_preview_bincode(image)
                    _preview_bindcodes[image] = bindcode

            if check_preview(image):
                if image in _preview_bindcodes.keys():
                    bindcode = _preview_bindcodes[image]

                    bgl.glActiveTexture(bgl.GL_TEXTURE0)
                    bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
                    shader_camera_image_preview.uniform_int("image", 0)
                    shader_camera_image_preview.uniform_float("display_size", display_size)
                    shader_camera_image_preview.uniform_float("scale", (aspect_x, aspect_y))
                    shader_camera_image_preview.uniform_float("modelMatrix", mat)
                    batch_image.draw(shader_camera_image_preview)

        shader_camera.bind()
        color = preferences.camera_color
        if ob == scene.camera:
            color = preferences.camera_color_highlight
        shader_camera.uniform_float("color", color)
        shader_camera.uniform_float("scale", (aspect_x, aspect_y))
        shader_camera.uniform_float("display_size", display_size)
        shader_camera.uniform_float("modelMatrix", mat)

        batch_frame.draw(shader_camera)
