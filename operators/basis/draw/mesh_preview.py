# <pep8 compliant>

import importlib
import numpy as np

import bpy
import bgl
import gpu
from mathutils import Vector

from ... import utils
from .... import constants
from .... import shaders
from .... import __package__ as addon_pkg

if "_rc" in locals():
    importlib.reload(utils)
    importlib.reload(constants)
    importlib.reload(shaders)

_rc = None


def iter_curve_values(curve_mapping, steps: int):
    curve_mapping.initialize()
    curve = list(curve_mapping.curves)[0]
    clip_min_x = curve_mapping.clip_min_x
    clip_min_y = curve_mapping.clip_min_y
    clip_max_x = curve_mapping.clip_max_x
    clip_max_y = curve_mapping.clip_max_y

    for i in range(steps):
        fac = i / steps
        pos = utils.common.f_lerp(clip_min_x, clip_max_x, fac)

        value = 1.0
        #value = curve.evaluate(pos)
        yield utils.common.f_clamp(value, clip_min_y, clip_max_y)

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


def get_camera_attributes(ob):
    camera_size = ob.data.sensor_width
    matrix_world = ob.matrix_world
    camera_pos = ob.matrix_world.translation
    camera_forward = (
        camera_pos + (Vector(
            [0.0, 0.0, -ob.data.lens / camera_size]
        ) @ matrix_world.inverted().normalized())
    )
    camera_up = Vector([0.0, 1.0, 0.0]) @ matrix_world.inverted()

    return camera_pos, camera_forward, camera_up


def get_object_batch(context, ob):
    """Returns object batch from evaluated depsgraph"""

    depsgraph = context.evaluated_depsgraph_get()

    # Get the modified version of the mesh from the depsgraph
    mesh = depsgraph.id_eval_get(ob).data
    mesh.calc_loop_triangles()

    vertices_count = len(mesh.vertices)
    loop_tris_count = len(mesh.loop_triangles)

    vertices_shape = (vertices_count, 3)
    loop_tris_shape = (loop_tris_count, 3)

    # Required attributes
    vertices_positions = np.empty(vertices_shape, dtype = np.float32)
    vertices_normals = np.empty(vertices_shape, dtype = np.float32)
    indices = np.empty(loop_tris_shape, dtype = np.int32)

    vertices_newshape = vertices_count * 3
    loop_tris_newshape = loop_tris_count * 3

    # 'foreach_get' is the fastest method
    mesh.vertices.foreach_get(
        "co", np.reshape(vertices_positions, vertices_newshape))
    mesh.vertices.foreach_get(
        "normal", np.reshape(vertices_normals, vertices_newshape))
    mesh.loop_triangles.foreach_get(
        "vertices", np.reshape(indices, loop_tris_newshape))

    # Batch generation
    buffer_type = 'TRIS'

    format_attributes = (
        ("pos", vertices_positions),
        ("normal", vertices_normals)
    )
    # Structure of a vertex buffer
    vert_format = gpu.types.GPUVertFormat()
    for format_attr in format_attributes:
        vert_format.attr_add(id = format_attr[0], comp_type = 'F32', len = 3, fetch_mode = 'FLOAT')

    # Index buffer
    ibo = gpu.types.GPUIndexBuf(type = buffer_type, seq = indices)

    # Vertex buffer
    vbo = gpu.types.GPUVertBuf(len = vertices_count, format = vert_format)
    for attr_id, attr in format_attributes:
        vbo.attr_fill(id = attr_id, data = attr)

    # Batch
    batch = gpu.types.GPUBatch(type = buffer_type, buf = vbo, elem = ibo)

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
    if not ob:
        return
    
    if not (use_projection_preview or (use_warnings and use_warning_action_draw)):
        return

    preferences = context.preferences.addons[addon_pkg].preferences
    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image

    if utils.warnings.gl_load(context, clone_image):
        return

    if not clone_image.cpp.valid:
        return

    batch = self.mesh_batch
    if not batch:
        return

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
    projector_position, projector_forward, projector_up_axis = get_camera_attributes(scene.camera)
    shader.uniform_float("projector_position", projector_position)
    shader.uniform_float("projector_forward", projector_forward)
    shader.uniform_float("projector_up_axis", projector_up_axis)

    width, height = clone_image.cpp.static_size
    wh_div = width / height

    shader.uniform_float("wh_div", wh_div)

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
        warning_status = utils.warnings.get_warning_status(context, wm.cpp_mouse_pos)
        shader.uniform_float("warning_color", preferences.warning_color)
    shader.uniform_bool("warning_status", (warning_status,))

    # multiple viewports support
    mouse_position = wm.cpp_mouse_pos
    active_rv3d = utils.screen.get_hovered_region_3d(context, mouse_position)
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
