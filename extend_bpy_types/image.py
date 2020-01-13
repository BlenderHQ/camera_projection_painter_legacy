# <pep8 compliant>

# Image properties are expanded by the method of obtaining image size from its metadata.
# Such a method works much faster than bpy.types.Image.size

import bpy
from bpy.types import PropertyGroup

import os
import io
import struct

_image_size_cache = {}


def _get_image_metadata_size_from_bytesio(io_bytes, st_size):
    """
    Returns image size from io.Buffer. There is support of PNG and JPEG
    @param io_bytes: io.BytesIO
    @param st_size: int
    @return: tuple - (width, height)
    """
    width, height = 0, 0

    data = io_bytes.read(24)

    if (st_size >= 24) and data.startswith(b'\x89PNG\r\n\x1a\n') and (data[12:16] == b'IHDR'):
        # PNG
        w, h = struct.unpack(">LL", data[16:24])
        width = int(w)
        height = int(h)

    elif (st_size >= 2) and data.startswith(b'\377\330'):
        # JPEG
        io_bytes.seek(0)
        io_bytes.read(2)
        b = io_bytes.read(1)
        try:
            w, h = 0, 0
            while b and ord(b) != 0xDA:
                while ord(b) != 0xFF:
                    b = io_bytes.read(1)
                while ord(b) == 0xFF:
                    b = io_bytes.read(1)
                if 0xC0 <= ord(b) <= 0xC3:
                    io_bytes.read(3)
                    h, w = struct.unpack(">HH", io_bytes.read(4))
                    break
                else:
                    io_bytes.read(
                        int(struct.unpack(">H", io_bytes.read(2))[0]) - 2)
                b = io_bytes.read(1)
            if w and h:
                width = int(w)
                height = int(h)
        except:
            pass
    # else:
    # TODO: Other formats support

    return width, height


def get_image_static_size(image):
    """
    The method returns the size of the image from its metadata; size caching is used.
    If it is not possible to obtain the size using existing algorithms,
    returns the cached size obtained from bpy.types.Image.size
    @param image: bpy.types.Image
    @return: tuple - (width, height)
    """
    if image in _image_size_cache:
        return _image_size_cache[image]

    width, height = 0, 0

    if image.source == 'FILE':
        if image.packed_file:
            packed_data = image.packed_file.data
            st_size = image.packed_file.size
            with io.BytesIO(packed_data) as io_bytes:
                width, height = _get_image_metadata_size_from_bytesio(io_bytes, st_size)
        else:
            file_path = bpy.path.abspath(image.filepath)
            if os.path.isfile(file_path):
                st_size = os.path.getsize(file_path)
                with io.open(file_path, "rb") as io_bytes:
                    width, height = _get_image_metadata_size_from_bytesio(io_bytes, st_size)

    elif image.source == 'GENERATED':
        width, height = image.generated_width, image.generated_height

    if width and height:
        _image_size_cache[image] = width, height
        return width, height

    width, height = image.size[:]
    if width and height:
        _image_size_cache[image] = width, height
        return width, height
    return 0, 0


class ImageProperties(PropertyGroup):
    """
    Serves for storing property methods associated with images
    """

    @property
    def static_size(self):
        __doc__ = get_image_static_size.__doc__

        image = self.id_data
        width, height = get_image_static_size(image)
        return width, height

    @property
    def aspect(self):
        """
        Image aspect ratio
        @return: float
        """
        image = self.id_data
        width, height = image.cpp.static_size
        if width == height:
            return 1.0
        return height / width

    @property
    def aspect_scale(self):
        """
        Image aspect ratio as tuple
        @return: tuple (aspect_scale_x, aspect_scale_y)
        """
        image = self.id_data
        width, height = image.cpp.static_size
        if width > height:
            aspect_scale = 1.0, height / width
        elif width < height:
            aspect_scale = width / height, 1.0
        else:
            aspect_scale = 1.0, 1.0

        return aspect_scale

    @property
    def invalid(self):
        """
        Status that the image has data
        @return: bool
        """
        image = self.id_data
        size_x, size_y = image.cpp.static_size
        if size_x and size_y:
            return False
        return True
