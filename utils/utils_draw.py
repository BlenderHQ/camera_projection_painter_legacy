import bpy
import bgl
from mathutils import Vector
from gpu_extras.batch import batch_for_shader

from .common import get_active_rv3d, iter_curve_values, flerp
from .utils_camera import get_camera_attributes
from .utils_poll import full_poll_decorator
from ..shaders import shaders

from .. import __package__ as addon_pkg


def gen_brush_texture(self, context):
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    brush = image_paint.brush
    pixel_width = scene.tool_settings.unified_paint_settings.size

    check_steps = 10  # Check curve values for every 10% to check any updates. Its biased, but fast.
    check_tuple = tuple((n for n in iter_curve_values(brush.curve, check_steps))) + (pixel_width,)

    if self.check_brush_curve_tuple != check_tuple:
        self.check_brush_curve_tuple = check_tuple

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


def gen_mesh_batch(self, context):
    ob = context.active_object
    if not self.mesh_batch:
        vertices, normals, indices = ob.cpp.generate_batch_attr(context)
        shader = shaders.mesh_preview
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, "normal": normals}, indices = indices)
        self.mesh_batch = batch
    return self.mesh_batch


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


@full_poll_decorator
def draw_projection_preview(self, context):
    scene = context.scene

    if not scene.cpp.use_projection_preview:
        return
    if not self.draw_preview:
        return

    preferences = context.preferences.addons[addon_pkg].preferences
    ob = context.image_paint_object
    image_paint = scene.tool_settings.image_paint
    image = image_paint.clone_image
    brush = image_paint.brush
    brush_radius = scene.tool_settings.unified_paint_settings.size

    if image.gl_load():
        raise Exception()

    shader = shaders.mesh_preview
    batch = self.mesh_batch
    if not batch:
        return

    mouse_position = self.mouse_position
    active_rv3d = get_active_rv3d(context, mouse_position)
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
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)
    bgl.glActiveTexture(bgl.GL_TEXTURE0 + 1)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.brush_texture_bindcode)

    # Set shader uniforms
    shader.bind()

    shader.uniform_float("ModelMatrix", ob.matrix_world)
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

    warning = 0
    if scene.cpp.use_warnings:
        view_distance = current_rv3d.view_distance
        sx, sy = image_paint.canvas.size
        canvas_size = (sx + sy) / 2
        distance_warning = scene.cpp.distance_warning
        brush_radius_warning = scene.cpp.brush_radius_warning
        canvas_size_warning = scene.cpp.canvas_size_warning
        dist_fac = abs((view_distance / distance_warning))
        brad_fac = (brush_radius / brush_radius_warning) - 1
        canv_fac = (canvas_size / canvas_size_warning) - 1
        warning_factor = (dist_fac + brad_fac + canv_fac)
        if warning_factor > 0.95:
            warning = 1
        shader.uniform_float("warningColor", preferences.warning_color)
    shader.uniform_int("warning", warning)

    # Finally, draw
    batch.draw(shader)
