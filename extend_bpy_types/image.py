import numpy as np

import bpy
from bpy.props import IntVectorProperty
import bgl


class EvalItemData:
    __slots__ = (
        "has_icon_generated",
        "has_prev_generated",
        "preview_bindcode"
    )

    def __init__(self):
        self.has_icon_generated = False
        self.has_prev_generated = False
        self.preview_bindcode = 0


class ImageCache:
    __slots__ = ()

    cache = {}
    gl_load_order = []

    icon_flat_arr = np.zeros(0, dtype=np.int32)
    prev_flat_arr = np.zeros(0, dtype=np.int32)

    @classmethod
    def clear(cls):
        cls.cache.clear()
        cls.gl_load_order.clear()


class ImageProperties(bpy.types.PropertyGroup):
    """
    Serves for storing property methods associated with images
    """

    static_size: IntVectorProperty(
        name="Size",
        size=2,
        default=(0, 0)
    )

    @property
    def valid(self):
        return self.static_size[0]

    def gl_load(self, context):
        """
        Images cached with max_loaded_images limit
        @return: int
        """
        image = self.id_data
        try:
            getattr(image, "name")
        except ReferenceError:
            del ImageCache.cache[image]
            return 0

        gll = image.gl_load()

        if not gll:
            if image in ImageCache.gl_load_order:
                ImageCache.gl_load_order.remove(image)
            ImageCache.gl_load_order.insert(0, image)
            if len(ImageCache.gl_load_order) > context.scene.cpp.max_loaded_images:
                last_image = ImageCache.gl_load_order[-1]
                last_image.gl_free()
                last_image.buffers_free()
                ImageCache.gl_load_order.remove(last_image)
            return 0
        elif image in ImageCache.gl_load_order:
            ImageCache.gl_load_order.remove(image)
        return gll

    @property
    def preview_bindcode(self):
        image = self.id_data

        try:
            getattr(image, "name")
        except ReferenceError:
            del ImageCache.cache[image]
            return 0

        item = ImageCache.cache.get(image, None)
        if item is None:
            ImageCache.cache[image] = EvalItemData()
        assert image in ImageCache.cache
        item = ImageCache.cache[image]

        if item.has_icon_generated and item.has_prev_generated and item.preview_bindcode:
            return item.preview_bindcode

        image_paint = bpy.context.scene.tool_settings.image_paint
        skip_buff_free = (image_paint.canvas, image_paint.clone_image)

        if (not item.has_icon_generated) and image.preview.icon_id and len(image.preview.icon_pixels):
            ImageCache.icon_flat_arr = np.resize(ImageCache.icon_flat_arr, len(image.preview.icon_pixels))
            image.preview.icon_pixels.foreach_get(ImageCache.icon_flat_arr)
            item.has_icon_generated = np.any(ImageCache.icon_flat_arr)
            if image.has_data and (image not in ImageCache.gl_load_order) and (image not in skip_buff_free):
                image.buffers_free()

        if (not item.has_prev_generated) and len(image.preview.image_pixels):
            ImageCache.prev_flat_arr = np.resize(ImageCache.prev_flat_arr, len(image.preview.image_pixels))
            image.preview.image_pixels.foreach_get(ImageCache.prev_flat_arr)
            item.has_prev_generated = np.any(ImageCache.prev_flat_arr)
            if image.has_data and (image not in ImageCache.gl_load_order) and (image not in skip_buff_free):
                image.buffers_free()

        if (not item.preview_bindcode) and item.has_prev_generated:
            id_buff = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenTextures(1, id_buff)

            item.preview_bindcode = id_buff.to_list()[0]

            bgl.glBindTexture(bgl.GL_TEXTURE_2D, item.preview_bindcode)
            image_buffer = bgl.Buffer(
                bgl.GL_INT,
                len(ImageCache.prev_flat_arr),
                ImageCache.prev_flat_arr
            )
            bgl.glTexParameteri(
                bgl.GL_TEXTURE_2D,
                bgl.GL_TEXTURE_MAG_FILTER | bgl.GL_TEXTURE_MIN_FILTER,
                bgl.GL_LINEAR
            )
            bgl.glTexImage2D(
                bgl.GL_TEXTURE_2D, 0, bgl.GL_RGBA,
                image.preview.image_size[0], image.preview.image_size[1],
                0, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, image_buffer
            )
        return item.preview_bindcode
