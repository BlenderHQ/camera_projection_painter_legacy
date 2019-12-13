# <pep8 compliant>

import bpy
import gpu
import bgl
from mathutils import Matrix
from gpu_extras.batch import batch_for_shader

from ..shaders import shaders
from .. import __package__ as addon_pkg

import struct


def generate_preview(image):
    if not image:
        return -1

    if not image.preview.is_image_custom:
        image.preview.reload()
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

            buffer = bgl.Buffer(bgl.GL_BYTE, sx * sy * 4)
            bgl.glReadBuffer(bgl.GL_BACK)
            bgl.glReadPixels(0, 0, sx, sy, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

        image.buffers_free()
        offscreen.free()

        image.preview.image_size = sx, sy
        pixels = [n / 255 for n in buffer]
        image.preview.image_pixels_float = pixels


def get_image_metadata_from_bytesio(input, st_size):
    size_x, size_y = 0, 0

    data = input.read(24)

    if (st_size >= 24) and data.startswith(b'\x89PNG\r\n\x1a\n') and (data[12:16] == b'IHDR'):
        # PNG
        w, h = struct.unpack(">LL", data[16:24])
        size_x = int(w)
        size_y = int(h)

        #print("PNG")

    elif (st_size >= 2) and data.startswith(b'\377\330'):
        # JPEG
        input.seek(0)
        input.read(2)
        b = input.read(1)
        try:
            w, h = 0, 0
            while b and ord(b) != 0xDA:
                while ord(b) != 0xFF:
                    b = input.read(1)
                while ord(b) == 0xFF:
                    b = input.read(1)
                if 0xC0 <= ord(b) <= 0xC3:
                    input.read(3)
                    h, w = struct.unpack(">HH", input.read(4))
                    break
                else:
                    input.read(
                        int(struct.unpack(">H", input.read(2))[0]) - 2)
                b = input.read(1)
            if w and h:
                size_x = int(w)
                size_y = int(h)
        except:
            pass

        #print("JPEG")
    else:
        print("WHAT HAPPENING?)))")  # TODO: Remove this)

    return size_x, size_y
