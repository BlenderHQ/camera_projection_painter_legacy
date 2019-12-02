import bpy
import gpu
import bgl
from mathutils import Matrix
from gpu_extras.batch import batch_for_shader

from ..shaders import shaders
from ..constants import PREVIEW_CHECK_MASK
from .. import __package__ as addon_pkg

import struct


def generate_preview(image):
    if not image:
        return -1
    if image.gl_load():
        return -1

    size_x, size_y = image.cpp.static_size
    if not (size_x and size_y):
        return

    preferences = bpy.context.preferences.addons[addon_pkg].preferences
    preview_size = preferences.render_preview_size  # bpy.app.render_preview_size

    if size_x > size_y:
        aspect_x = size_x / size_y
        aspect_y = 1.0
    elif size_y > size_x:
        aspect_x = 1.0
        aspect_y = size_x / size_y
    else:
        aspect_x = 1.0
        aspect_y = 1.0

    sx, sy = int(preview_size * aspect_x), int(preview_size * aspect_y)

    coords = ((0, 0), (1, 0), (1, 1), (0, 1))

    shader = shaders.current_image
    batch = batch_for_shader(shader, 'TRI_FAN',
                             {"pos": coords,
                              "uv": coords})

    offscreen = gpu.types.GPUOffScreen(sx, sy)
    with offscreen.bind():
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        with gpu.matrix.push_pop():
            gpu.matrix.load_matrix(Matrix.Identity(4))
            gpu.matrix.load_projection_matrix(Matrix.Identity(4))

            gpu.matrix.translate((-1.0, -1.0))
            gpu.matrix.scale((2.0, 2.0))

            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

            shader.bind()
            shader.uniform_int("image", 0)
            shader.uniform_float("alpha", 1.0)
            shader.uniform_bool("colorspace_srgb", (image.colorspace_settings.name == 'sRGB',))
            batch.draw(shader)

            image.buffers_free()

        buffer = bgl.Buffer(bgl.GL_BYTE, sx * sy * 4)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, sx, sy, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

    offscreen.free()

    image.preview.image_size = sx, sy
    pixels = [n / 255 for n in buffer]
    pixels[0:len(PREVIEW_CHECK_MASK)] = PREVIEW_CHECK_MASK
    image.preview.image_pixels_float = pixels


def get_image_metadata_from_bytesio(input, st_size):
    """PNGs  only"""
    size_x = 0
    size_y = 0

    data = input.read(24)

    if (st_size >= 24) and data.startswith(b'\x89PNG\r\n\x1a\n') and (data[12:16] == b'IHDR'):
        # PNGs
        w, h = struct.unpack(">LL", data[16:24])
        size_x = int(w)
        size_y = int(h)
    else:
        print("PREFERED TO USE PNGs)))")  # TODO: Remove this)

    return size_x, size_y
