import bpy
import bgl
import gpu
from mathutils import Vector
from gpu_extras.batch import batch_for_shader

from . import utils_state

from .utils_warning import get_warning_status
from .utils_poll import full_poll_decorator
from .utils_camera import get_camera_attributes
from .common import get_hovered_region_3d, iter_curve_values, flerp

from ..shaders import shaders
from .. import __package__ as addon_pkg


class CameraProjectionPainterDrawUtils:
    mesh_batch: gpu.types.GPUBatch
    brush_texture_bindcode: int

    def generate_mesh_batch(self, context):
        ob = context.active_object
        vertices, normals, indices = ob.cpp.generate_batch_attr(context)
        shader = shaders.mesh_preview
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices, "normal": normals}, indices = indices)
        self.mesh_batch = batch

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
    if self.suspended:
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

    if scene.cpp.use_warnings and scene.cpp.use_warning_action_draw:
        danger_zone = get_warning_status(context, active_rv3d)
        shader.uniform_int("warning", danger_zone)
        shader.uniform_float("warningColor", preferences.warning_color)
    else:
        shader.uniform_int("warning", 0)

    # Finally, draw
    batch.draw(shader)
