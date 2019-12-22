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


def get_curr_img_pos_from_context(context):
    area = context.area
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    image = image_paint.clone_image

    if not image:
        return
    size_x, size_y = image.cpp.static_size
    if not (size_x and size_y):
        return

    preferences = context.preferences.addons[addon_pkg].preferences
    empty_space = preferences.border_empty_space

    tools_width = [n for n in area.regions if n.type == 'TOOLS'][-1].width  # N-panel width
    ui_width = [n for n in area.regions if n.type == 'UI'][-1].width  # T-panel width
    area_size = Vector([area.width - ui_width - tools_width - empty_space, area.height - empty_space])

    image_size = Vector([1.0, size_y / size_x]) * scene.cpp.current_image_size
    possible = True
    if image_size.x > area_size.x - empty_space or image_size.y > area_size.y - empty_space:
        possible = False

    image_rel_pos = scene.cpp.current_image_position
    rpx, rpy = image_rel_pos
    apx = common.f_lerp(empty_space, area_size.x - image_size.x, rpx) + tools_width
    apy = common.f_lerp(empty_space, area_size.y - image_size.y, rpy)

    return Vector((apx, apy)), image_size, possible


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

    if self.suspended_mouse and (not warning_status):
        active_view = False
    shader.uniform_int("active_view", active_view)

    # finally, draw
    batch.draw(shader)


def gen_camera_batch(camera):
    shader_camera = shaders.shader.camera
    shader_camera_image_preview = shaders.shader.camera_image_preview

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

    return batch_frame, batch_image


def get_camera_batches(context):
    res = {}
    scene = context.scene
    for ob in scene.cpp.camera_objects:
        camera = ob.data
        batch_frame, batch_image = gen_camera_batch(camera)
        res[ob] = batch_frame, batch_image
    return res


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
    # glTexSubImage2d
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
    scene = context.scene
    shader_camera = shaders.shader.camera
    shader_camera_image_preview = shaders.shader.camera_image_preview

    preferences = context.preferences.addons[addon_pkg].preferences

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    bgl.glEnable(bgl.GL_MULTISAMPLE)

    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glLineWidth(preferences.camera_line_width)

    bgl.glEnable(bgl.GL_DEPTH_TEST)

    for ob in scene.cpp.camera_objects:
        batches = None
        if ob in self.camera_batches.keys():
            batches = self.camera_batches[ob]
        if not batches:
            continue

        batch_frame, batch_image = batches

        mat = ob.matrix_world
        display_size = scene.cpp.cameras_viewport_size
        image = ob.data.cpp.image

        has_data = False
        size_x, size_y = (1, 1)
        if image:
            static_size = image.cpp.static_size
            if static_size[0] and static_size[1]:
                size_x, size_y = static_size
                has_data = image.has_data

        if size_x > size_y:
            aspect_x = 1.0
            aspect_y = size_y / size_x
        elif size_y > size_x:
            aspect_x = 1.0
            aspect_y = size_y / size_x
        else:
            aspect_x = 1.0
            aspect_y = 1.0

        rv3d = context.region_data
        if image and scene.cpp.use_camera_image_previews:
            if rv3d.view_perspective != 'CAMERA':
                if image in _image_previews.keys():
                    bindcode = _image_previews[image]
                    bgl.glActiveTexture(bgl.GL_TEXTURE0)
                    bgl.glBindTexture(bgl.GL_TEXTURE_2D, bindcode)

                    shader_camera_image_preview.bind()
                    shader_camera_image_preview.uniform_int("image", 0)
                    shader_camera_image_preview.uniform_float("display_size", display_size)
                    shader_camera_image_preview.uniform_float("scale", (aspect_x, aspect_y))
                    shader_camera_image_preview.uniform_float("modelMatrix", mat)
                    batch_image.draw(shader_camera_image_preview)

        shader_camera.bind()
        if has_data:
            color = preferences.camera_color_loaded_data
        else:
            color = preferences.camera_color
        if ob == scene.camera:
            color = preferences.camera_color_highlight

        shader_camera.uniform_float("color", color)
        shader_camera.uniform_float("scale", (aspect_x, aspect_y))
        shader_camera.uniform_float("display_size", display_size)
        shader_camera.uniform_float("modelMatrix", mat)

        batch_frame.draw(shader_camera)
