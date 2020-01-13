# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(common)
    importlib.reload(shaders)

    del importlib
else:
    from . import common
    from .. import shaders
    from .. import __package__ as addon_pkg

import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy.types import SpaceView3D

import numpy as np

_image_previews = {}
_image_icons = {}
_image_skip_free = set({})


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
    if self.draw_handler_cameras:
        SpaceView3D.draw_handler_remove(self.draw_handler_cameras, 'WINDOW')


# Base utils

def update_brush_texture_bindcode(self, context):
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    brush = image_paint.brush
    pixel_width = scene.tool_settings.unified_paint_settings.size

    check_steps = 10  # Check curve values for every 10% to check any updates. Its biased, but fast.
    check_tuple = tuple((n for n in common.iter_curve_values(brush.curve, check_steps))) + (pixel_width,)

    if self.check_brush_curve_updated(check_tuple):
        pixels = [int(n * 255) for n in common.iter_curve_values(brush.curve, pixel_width)]

        id_buff = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenTextures(1, id_buff)

        bindcode = id_buff.to_list()[0]

        bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
        image_buffer = bgl.Buffer(bgl.GL_INT, len(pixels), pixels)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER | bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RED,
                         pixel_width, 1, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, image_buffer)

        self.brush_texture_bindcode = bindcode



def get_batch_attributes(bm):
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


def draw_projection_preview(self, context):
    wm = context.window_manager
    if wm.cpp_suspended:
        return

    scene = context.scene

    use_projection_preview = scene.cpp.use_projection_preview
    use_projection_outline = scene.cpp.use_projection_outline
    use_normal_highlight = scene.cpp.use_normal_highlight
    use_warnings = scene.cpp.use_warnings
    use_warning_action_draw = scene.cpp.use_warning_action_draw
    full_draw = self.full_draw

    ob = context.image_paint_object
    preferences = context.preferences.addons[addon_pkg].preferences

    if not (use_projection_preview or (use_warnings and use_warning_action_draw)):
        return

    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image

    if clone_image.gl_load():
        return

    if clone_image.cpp.invalid:
        return

    batch = self.mesh_batch
    if not batch:
        return

    if clone_image not in _image_skip_free:
        _image_skip_free.add(clone_image)

    # openGL setup
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    bgl.glEnable(bgl.GL_MULTISAMPLE)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    # bind textures
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S | bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_BORDER)
    # bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S | bgl.GL_TEXTURE_WRAP_T, bgl.GL_REPEAT)

    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, clone_image.bindcode)
    bgl.glActiveTexture(bgl.GL_TEXTURE0 + 1)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.brush_texture_bindcode)

    shader = shaders.shader.mesh_preview
    shader.bind()

    # shader uniforms
    shader.uniform_int("clone_image", 0)
    shader.uniform_int("brush_img", 1)

    colorspace_srgb = clone_image.colorspace_settings.name == 'sRGB'
    shader.uniform_bool("colorspace_srgb", (colorspace_srgb,))

    shader.uniform_bool("use_projection_preview", (use_projection_preview,))
    shader.uniform_bool("use_normal_highlight", (use_normal_highlight,))
    shader.uniform_bool("use_warnings", (use_warnings,))
    shader.uniform_bool("use_warning_action_draw", (use_warning_action_draw,))
    shader.uniform_bool("full_draw", (full_draw,))

    model_matrix = ob.matrix_world
    shader.uniform_float("model_matrix", model_matrix)
    projector_position, projector_forward, projector_up_axis = common.get_camera_attributes(scene.camera)
    shader.uniform_float("projector_position", projector_position)
    shader.uniform_float("projector_forward", projector_forward)
    shader.uniform_float("projector_up_axis", projector_up_axis)
    aspect = clone_image.cpp.aspect
    shader.uniform_float("aspect", aspect)

    # normal highlight
    if use_normal_highlight:
        normal_highlight_color = preferences.normal_highlight_color
        shader.uniform_float("normal_highlight_color", normal_highlight_color)

    # outline
    outline_type = 0
    if use_projection_outline:
        outline_type = {'NO_OUTLINE': 0, 'FILL': 1, 'CHECKER': 2, 'LINES': 3}[preferences.outline_type]

        outline_color = preferences.outline_color
        shader.uniform_float("outline_color", outline_color)
        outline_scale = preferences.outline_scale
        shader.uniform_float("outline_scale", outline_scale)
        outline_width = preferences.outline_width * 0.1
        shader.uniform_float("outline_width", outline_width)
    shader.uniform_int("outline_type", outline_type)

    # warnings
    warning_status = False
    if use_warnings and use_warning_action_draw:
        warning_status = common.get_warning_status(context, wm.cpp_mouse_pos)
        shader.uniform_float("warning_color", preferences.warning_color)
    shader.uniform_bool("warning_status", (warning_status,))

    # multiple viewports support
    mouse_position = wm.cpp_mouse_pos
    active_rv3d = common.get_hovered_region_3d(context, mouse_position)
    current_rv3d = context.area.spaces.active.region_3d
    active_view = False
    if active_rv3d == current_rv3d:
        active_view = True
        mx, my = mouse_position
        mx -= context.area.x
        my -= context.area.y
        shader.uniform_float("mouse_pos", (mx, my))
        brush_radius = scene.tool_settings.unified_paint_settings.size
        shader.uniform_float("brush_radius", brush_radius)
        brush_strength = image_paint.brush.strength
        shader.uniform_float("brush_strength", brush_strength)

    if self.suspended_brush and (not warning_status):
        active_view = False
    shader.uniform_int("active_view", active_view)

    # finally, draw
    batch.draw(shader)


def get_camera_batches():
    # Camera and binded image batches
    vertices = (
        (0.0, 0.0, 0.0),
        (0.5, 0.5, -1.0),
        (0.5, -0.5, -1.0),
        (-0.5, -0.5, -1.0),
        (-0.5, 0.5, -1.0)
    )

    wire_indices = (
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (2, 3), (3, 4), (1, 4)
    )

    image_rect_indices = (
        (1, 2, 3), (3, 4, 1)
    )

    image_rect_uv = (
        (0.0, 0.0),
        (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0),
    )

    shader_camera = shaders.shader.camera
    shader_camera_image_preview = shaders.shader.camera_image_preview

    camera_wire_batch = batch_for_shader(
        shader_camera, 'LINES',
        {"pos": vertices},
        indices = wire_indices,
    )

    image_rect_batch = batch_for_shader(
        shader_camera_image_preview, 'TRIS',
        {"pos": vertices, "uv": image_rect_uv},
        indices = image_rect_indices,
    )

    return camera_wire_batch, image_rect_batch


def get_axes_batch():
    vertices = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0)
    )

    vertex_colors = (
        (0.5, 0.5, 0.5, 0.0),
        (1.0, 0.0, 0.0, 0.6),
        (0.0, 1.0, 0.0, 0.6),
        (0.0, 0.0, 1.0, 0.6)
    )

    indices = ((0, 1), (0, 2), (0, 3))

    shader_axes = shaders.shader.axes

    batch_axes = batch_for_shader(
        shader_axes, 'LINES',
        {"pos": vertices, "color": vertex_colors},
        indices = indices,
    )

    return batch_axes


def gen_buffer_preview(preview):
    id_buff = bgl.Buffer(bgl.GL_INT, 1)
    bgl.glGenTextures(1, id_buff)

    bindcode = id_buff.to_list()[0]
    pixels = preview.image_pixels[:]

    width, height = preview.image_size
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)
    image_buffer = bgl.Buffer(bgl.GL_INT, len(pixels), pixels)
    bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER | bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
    bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA,
                     width, height, 0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, image_buffer)

    return bindcode


def get_loaded_images_count():
    return len([image for image in bpy.data.images if image.has_data])


def check_image_previews(context):
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image
    canvas = image_paint.canvas
    for image in bpy.data.images:
        preview = image.preview

        if image not in _image_previews:
            if image.has_data:
                if any(preview.image_pixels[:]):
                    bindcode = gen_buffer_preview(preview)
                    _image_previews[image] = bindcode
                if image not in (clone_image, canvas):
                    if image not in _image_skip_free:
                        image.buffers_free()
            else:
                if any(preview.image_pixels[:]):
                    bindcode = gen_buffer_preview(preview)
                    _image_previews[image] = bindcode
        if image not in _image_icons:
            if image.has_data:
                if any(preview.icon_pixels[:]):
                    _image_icons[image] = True
                if image not in (clone_image, canvas):
                    if image not in _image_skip_free:
                        image.buffers_free()


def clear_image_previews():
    global _image_previews
    global _image_icons
    global _image_skip_free
    _image_previews = {}
    _image_icons = {}
    _image_skip_free = set({})


def get_ready_preview_count():
    return len(_image_previews)


def draw_cameras(self, context):
    preferences = context.preferences.addons[addon_pkg].preferences
    scene = context.scene
    cameras_viewport_size = scene.cpp.cameras_viewport_size

    # Shaders
    shader_camera = shaders.shader.camera
    shader_camera_image_preview = shaders.shader.camera_image_preview
    shader_axes = shaders.shader.axes

    # Batches
    axes_batch = self.axes_batch
    camera_wire_batch = self.camera_batch
    image_rect_batch = self.image_rect_batch

    # OpenGL setup
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    bgl.glEnable(bgl.GL_MULTISAMPLE)

    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glEnable(bgl.GL_DEPTH_TEST)

    for camera_ob in scene.cpp.camera_objects:
        camera = camera_ob.data

        bgl.glLineWidth(preferences.camera_line_width)

        model_matrix = camera_ob.matrix_world
        camera_lens_size = camera.lens / camera.sensor_width

        image = camera.cpp.image

        image_has_data = False
        image_aspect_scale = 1.0, 1.0

        if image and (not image.cpp.invalid):
            image_aspect_scale = image.cpp.aspect_scale

            if (scene.cpp.use_camera_image_previews and
                    context.region_data.view_perspective != 'CAMERA' and
                    image in _image_previews):
                bindcode = _image_previews[image]
                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)

                shader_camera_image_preview.bind()

                shader_camera_image_preview.uniform_int("image", 0)
                shader_camera_image_preview.uniform_float("cameras_viewport_size", cameras_viewport_size)
                shader_camera_image_preview.uniform_float("image_aspect_scale", image_aspect_scale)
                shader_camera_image_preview.uniform_float("camera_lens_size", camera_lens_size)
                shader_camera_image_preview.uniform_float("model_matrix", model_matrix)

                image_rect_batch.draw(shader_camera_image_preview)

        shader_camera.bind()
        if image_has_data:
            wire_color = preferences.camera_color_loaded_data
        else:
            wire_color = preferences.camera_color
        if camera_ob == scene.camera:
            wire_color = preferences.camera_color_highlight

        shader_camera.uniform_float("wire_color", wire_color)
        shader_camera.uniform_float("image_aspect_scale", image_aspect_scale)
        shader_camera.uniform_float("cameras_viewport_size", cameras_viewport_size)
        shader_camera.uniform_float("camera_lens_size", camera_lens_size)
        shader_camera.uniform_float("model_matrix", model_matrix)

        camera_wire_batch.draw(shader_camera)

        # Display the axes of the camera object
        if scene.cpp.use_camera_axes:
            camera_axes_size = scene.cpp.camera_axes_size

            bgl.glLineWidth(2.0)
            shader_axes.bind()
            shader_axes.uniform_float("modelMatrix", model_matrix)
            shader_axes.uniform_float("camera_axes_size", camera_axes_size)
            axes_batch.draw(shader_axes)

    # OpenGL restore defaults
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_MULTISAMPLE)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_DEPTH_TEST)
    bgl.glLineWidth(1.0)
