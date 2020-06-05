import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
    PointerProperty
)


class BindImageHistoryItem(PropertyGroup):
    """
    Used to store a palette of previously used images
    """
    image: PointerProperty(
        type=bpy.types.Image, name="Image",
        options={'HIDDEN'})

    favorite: BoolProperty(
        name="Favorite",
        default=False,
        description="Mark image as favorite"
    )


class CameraProperties(PropertyGroup):
    """
    Serves for storing the properties associated with the data of each individual camera,
    the main here is the image binded to the camera
    """

    # Update methods
    def _image_update(self, context):
        if self.image and self.image.cpp.valid:
            camera = self.id_data
            bind_history = camera.cpp_bind_history
            bind_history_images = []
            for item in bind_history:
                if item.image and item.image.cpp.valid:
                    bind_history_images.append(item.image)

            if self.image in bind_history_images:
                check_index = bind_history_images.index(self.image)
            else:
                item = camera.cpp_bind_history.add()
                item.image = self.image
                check_index = len(camera.cpp_bind_history) - 1

            if self.active_bind_index <= len(bind_history) - 1:
                item = bind_history[self.active_bind_index]
                if item.image != self.image:
                    self.active_bind_index = check_index

            width, height = self.image.cpp.static_size
            if width > height:
                camera.sensor_fit = 'VERTICAL'
            else:
                camera.sensor_fit = 'HORIZONTAL'

    def _active_bind_index_update(self, context):
        camera = self.id_data
        bind_history = camera.cpp_bind_history
        item = bind_history[self.active_bind_index]
        if item.image and item.image.cpp.valid and (item.image != self.image):
            self.image = item.image

    # Properties
    active_bind_index: IntProperty(
        name="Active Bind History Index",
        default=0,
        update=_active_bind_index_update)

    image: PointerProperty(
        type=bpy.types.Image, name="Image",
        options={'HIDDEN'},
        description="An image binded to a camera for use as a Clone Image in Texture Paint mode",
        update=_image_update)

    # Calibration properties
    xmp_filepath: StringProperty(
        name="XMP File",
        subtype='FILE_PATH',
        description="Path to third-party application *.xmp file."
    )

    skew: FloatProperty(
        name="Skew", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Camera skew"
    )

    aspect_ratio: FloatProperty(
        name="Aspect Ratio", default=1.0, min=0.0, soft_min=0.5, soft_max=2.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Camera aspect ratio correction factor"
    )

    principal_point_x: FloatProperty(
        name="Principal Point X [mm]", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Deviation of the camera principal point in millimeters w.r.t 35mm film format"
    )

    principal_point_y: FloatProperty(
        name="Principal Point Y [mm]", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Deviation of the camera principal point in millimeters w.r.t 35mm film format"
    )

    camera_lens_model: EnumProperty(
        items=[
            ('perspective', "No lens distortion", ""),
            ('division', "Division", ""),
            ('brown3', "Brown 3", ""),
            ('brown4', "Brown 4", ""),
            ('brown3t2', "Brown 3 with tangential distortion", ""),
            ('brown4t2', "Brown 4 with tangential distortion", ""),
        ],
        name="Lens Model",
        default='brown3t2',
        options={'HIDDEN'},
        description="Camera projection and distortion mathematical model"
    )

    k1: FloatProperty(
        name="Radial 1", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=12,
        options={'HIDDEN'},
        description="Brown's model radial coefficient x^2"
    )

    k2: FloatProperty(
        name="Radial 2", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Brown's model radial coefficient x^4"
    )

    k3: FloatProperty(
        name="Radial 3", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Brown's model radial coefficient x^6"
    )

    k4: FloatProperty(
        name="Radial 4", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Brown's model radial coefficient x^8"
    )

    t1: FloatProperty(
        name="Tangential 1", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Brown's model tangential coefficient 1"
    )

    t2: FloatProperty(
        name="Tangential 2", default=0.0, soft_min=-1.0, soft_max=1.0,
        subtype='FACTOR',
        precision=6,
        options={'HIDDEN'},
        description="Brown's model tangential coefficient 2"
    )

    def set_shader_calibration(self, shader):
        image = self.image
        if image and image.cpp.valid:
            width, height = image.cpp.static_size
            shader.uniform_float("image_width", width)
            shader.uniform_float("image_height", height)

            shader.uniform_float("lens", self.id_data.lens)
            shader.uniform_float("shiftx", self.principal_point_x)
            shader.uniform_float("shifty", self.principal_point_y)
            shader.uniform_float("skew", self.skew)
            shader.uniform_float("aspect_ratio", self.aspect_ratio)

            lens_distortion_model = [2]

            if self.camera_lens_model == 'perspective':
                lens_distortion_model = [0]

            elif self.camera_lens_model == 'division':
                lens_distortion_model = [1]
                shader.uniform_float("k1", self.k1)

            elif self.camera_lens_model == 'brown3':
                shader.uniform_float("k1", self.k1)
                shader.uniform_float("k2", self.k2)
                shader.uniform_float("k3", self.k3)

            elif self.camera_lens_model == 'brown3t2':
                shader.uniform_float("k1", self.k1)
                shader.uniform_float("k2", self.k2)
                shader.uniform_float("k3", self.k3)
                shader.uniform_float("t1", self.t1)
                shader.uniform_float("t2", self.t2)

            elif self.camera_lens_model == 'brown4':
                shader.uniform_float("k1", self.k1)
                shader.uniform_float("k2", self.k2)
                shader.uniform_float("k3", self.k3)
                shader.uniform_float("k4", self.k4)

            elif self.camera_lens_model == 'brown4t2':
                shader.uniform_float("k1", self.k1)
                shader.uniform_float("k2", self.k2)
                shader.uniform_float("k3", self.k3)
                shader.uniform_float("k4", self.k4)
                shader.uniform_float("t1", self.t1)
                shader.uniform_float("t2", self.t2)

            shader.uniform_int("lens_distortion_model", lens_distortion_model)
