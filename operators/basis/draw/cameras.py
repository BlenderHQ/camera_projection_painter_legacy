# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(shaders)

    del importlib
else:
    from .... import shaders
    from .... import __package__ as addon_pkg

import bpy
import bgl
import gpu

from gpu_extras.batch import batch_for_shader

_image_previews = {}
_image_icons = {}
_image_skip_free = set({})

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

    shader_camera = shaders.shader.camera
    shader_camera_image_preview = shaders.shader.camera_image_preview

    camera_wire_batch = batch_for_shader(
        shader_camera, 'LINES',
        {"pos": vertices},
        indices = wire_indices,
    )

    vertices = (
        (0.5, 0.5, -1.0),
        (0.5, -0.5, -1.0),
        (-0.5, -0.5, -1.0),
        (-0.5, 0.5, -1.0)
    )

    image_rect_uv = (
        (1.0, 1.0), (1.0, 0.0), (0.0, 0.0), (0.0, 1.0),
    )

    image_rect_batch = batch_for_shader(
        shader_camera_image_preview, 'TRI_FAN',
        {"pos": vertices, "uv": image_rect_uv}
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

def check_image_previews(self, context):
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

    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image

    if clone_image not in _image_skip_free:
        _image_skip_free.add(clone_image)

    # Shaders
    shader_camera = shaders.shader.camera
    shader_camera_image_preview = shaders.shader.camera_image_preview
    shader_axes = shaders.shader.axes

    # Batches
    axes_batch = self.axes_batch
    camera_wire_batch = self.camera_batch
    image_rect_batch = self.image_rect_batch

    # OpenGL setup
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_MULTISAMPLE)

    for camera_ob in scene.cpp.initial_visible_camera_objects:
        camera = camera_ob.data

        bgl.glLineWidth(preferences.camera_line_width)

        model_matrix = camera_ob.matrix_world
        camera_lens_size = camera.lens / camera.sensor_width

        image = camera.cpp.image

        image_has_data = False
        image_aspect_scale = 1.0, 1.0

        if image and (not image.cpp.invalid):
            image_aspect_scale = image.cpp.aspect_scale
            image_has_data = image.has_data

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