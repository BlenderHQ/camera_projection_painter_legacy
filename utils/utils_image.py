import bpy
import gpu
import bgl
from mathutils import Matrix
from gpu_extras.presets import draw_texture_2d

from ..constants import PREVIEW_CHECK_MASK
from .. import __package__ as addon_pkg

import struct

FILE_UNKNOWN = "Unknown File"


class UnknownImageFormat(Exception):
    pass


def generate_preview(image):
    preferences = bpy.context.preferences.addons[addon_pkg].preferences
    preview_size = preferences.render_preview_size  # bpy.app.render_preview_size

    size_x, size_y = image.cpp.static_size

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

    offscreen = gpu.types.GPUOffScreen(sx, sy)

    with offscreen.bind():
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        with gpu.matrix.push_pop():
            gpu.matrix.load_matrix(Matrix.Identity(4))
            gpu.matrix.load_projection_matrix(Matrix.Identity(4))

            if image.gl_load():
                return -1
            draw_texture_2d(texture_id = image.bindcode, position = (-1.0, -1.0), width = 2.0, height = 2.0)
            image.buffers_free()

        buffer = bgl.Buffer(bgl.GL_BYTE, sx * sy * 4)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, sx, sy, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

    offscreen.free()

    image.preview.image_size = sx, sy
    pixels = [n / 255 for n in buffer]
    pixels[0:len(PREVIEW_CHECK_MASK)] = PREVIEW_CHECK_MASK
    image.preview.image_pixels_float = pixels


def get_image_metadata_from_bytesio(input, size):
    """
    GIFs, PNGs, older PNGs, JPEG, BMP, TIFF,
    """
    height = -1
    width = -1
    data = input.read(26)
    msg = " raised while trying to decode as JPEG."

    if (size >= 10) and data[:6] in (b'GIF87a', b'GIF89a'):
        # GIFs
        w, h = struct.unpack("<HH", data[6:10])
        width = int(w)
        height = int(h)
    elif ((size >= 24) and data.startswith(b'\211PNG\r\n\032\n')
          and (data[12:16] == b'IHDR')):
        # PNGs
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)
    elif (size >= 16) and data.startswith(b'\211PNG\r\n\032\n'):
        # older PNGs
        w, h = struct.unpack(">LL", data[8:16])
        width = int(w)
        height = int(h)
    elif (size >= 2) and data.startswith(b'\377\330'):
        # JPEG
        input.seek(0)
        input.read(2)
        b = input.read(1)
        try:
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
            width = int(w)
            height = int(h)
        except struct.error:
            raise UnknownImageFormat("StructError" + msg)
        except ValueError:
            raise UnknownImageFormat("ValueError" + msg)
        except Exception as e:
            raise UnknownImageFormat(e.__class__.__name__ + msg)
    elif (size >= 26) and data.startswith(b'BM'):
        # BMP
        headersize = struct.unpack("<I", data[14:18])[0]
        if headersize == 12:
            w, h = struct.unpack("<HH", data[18:22])
            width = int(w)
            height = int(h)
        elif headersize >= 40:
            w, h = struct.unpack("<ii", data[18:26])
            width = int(w)
            # as h is negative when stored upside down
            height = abs(int(h))
        else:
            raise UnknownImageFormat(
                "Unkown DIB header size:" +
                str(headersize))
    elif (size >= 8) and data[:4] in (b"II\052\000", b"MM\000\052"):
        # Standard TIFF, big- or little-endian
        # BigTIFF and other different but TIFF-like formats are not
        # supported currently
        byte_order = data[:2]
        bo_char = ">" if byte_order == "MM" else "<"
        # maps TIFF type id to size (in bytes)
        # and python format char for struct
        tiff_types = {
            1: (1, bo_char + "B"),  # BYTE
            2: (1, bo_char + "c"),  # ASCII
            3: (2, bo_char + "H"),  # SHORT
            4: (4, bo_char + "L"),  # LONG
            5: (8, bo_char + "LL"),  # RATIONAL
            6: (1, bo_char + "b"),  # SBYTE
            7: (1, bo_char + "c"),  # UNDEFINED
            8: (2, bo_char + "h"),  # SSHORT
            9: (4, bo_char + "l"),  # SLONG
            10: (8, bo_char + "ll"),  # SRATIONAL
            11: (4, bo_char + "f"),  # FLOAT
            12: (8, bo_char + "d")  # DOUBLE
        }
        ifd_offset = struct.unpack(bo_char + "L", data[4:8])[0]
        try:
            count_size = 2
            input.seek(ifd_offset)
            ec = input.read(count_size)
            ifd_entry_count = struct.unpack(bo_char + "H", ec)[0]
            # 2 bytes: TagId + 2 bytes: type + 4 bytes: count of values + 4
            # bytes: value offset
            ifd_entry_size = 12
            for i in range(ifd_entry_count):
                entry_offset = ifd_offset + count_size + i * ifd_entry_size
                input.seek(entry_offset)
                tag = input.read(2)
                tag = struct.unpack(bo_char + "H", tag)[0]
                if tag in (256, 257):
                    # if type indicates that value fits into 4 bytes, value
                    # offset is not an offset but value itself
                    t_type = input.read(2)
                    t_type = struct.unpack(bo_char + "H", t_type)[0]
                    if t_type not in tiff_types:
                        raise UnknownImageFormat(
                            "Unkown TIFF field type:" +
                            str(t_type))
                    type_size = tiff_types[t_type][0]
                    type_char = tiff_types[t_type][1]
                    input.seek(entry_offset + 8)
                    value = input.read(type_size)
                    value = int(struct.unpack(type_char, value)[0])
                    if tag == 256:
                        width = value
                    else:
                        height = value
                if width > -1 and height > -1:
                    break
        except Exception as e:
            raise UnknownImageFormat(str(e))
    else:
        raise UnknownImageFormat(FILE_UNKNOWN)

    return width, height
