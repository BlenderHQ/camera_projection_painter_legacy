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


camera_lens_model_items = [
    ('perspective', "No lens distortion", ""),
    ('division', "Division", ""),
    ('brown3', "Brown 3", ""),
    ('brown4', "Brown 4", ""),
    ('brown3t2', "Brown 3 with tangential distortion", ""),
    ('brown4t2', "Brown 4 with tangential distortion", "")
]


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
        items=camera_lens_model_items,
        name="Lens Model",
        default=camera_lens_model_items[0][0],
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
            shader.uniform_float("UND_image_width", width)
            shader.uniform_float("UND_image_height", height)
            shader.uniform_float("UND_lens", self.id_data.lens)

            uniforms_seq = ["principal_point_x", "principal_point_y", "skew", "aspect_ratio"]

            for i, item in enumerate(camera_lens_model_items):
                if self.camera_lens_model == item[0]:
                    shader.uniform_int("UND_lens_distortion_model", i)

            if self.camera_lens_model == 'division':
                uniforms_seq.extend(["k1"])

            elif self.camera_lens_model == 'brown3':
                uniforms_seq.extend(["k1", "k2", "k3"])

            elif self.camera_lens_model == 'brown4':
                uniforms_seq.extend(["k1", "k2", "k3", "k4"])

            elif self.camera_lens_model == 'brown3t2':
                uniforms_seq.extend(["k1", "k2", "k3", "t1", "t2"])

            elif self.camera_lens_model == 'brown4t2':
                uniforms_seq.extend(["k1", "k2", "k3", "k4", "t1", "t2"])

            for uname in uniforms_seq:
                value = getattr(self, uname)
                if isinstance(value, float):
                    shader.uniform_float(f"UND_{uname}", value)
