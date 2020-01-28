# <pep8 compliant>


import importlib

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    StringProperty
)

from .. import icons
from .. import constants
from .. import operators

if "_rc" in locals():  # Case of module reloading
    importlib.reload(icons)
    importlib.reload(constants)
    importlib.reload(operators)

_rc = None


class SceneProperties(PropertyGroup):
    """
    Contains properties and methods related to the Scene
    """

    @property
    def _scene(self):
        return self.id_data

    @property
    def has_camera_objects(self):
        """
        True if there are camera objects in the scene
        @return: bool
        """
        for ob in self._scene.objects:
            if ob.type != 'CAMERA':
                continue
            return True
        return False

    @property
    def camera_objects(self):
        """
        Generates a generator of camera objects
        @return: generator
        """
        def check(ob: bpy.types.Object):
            if ob.type == 'CAMERA':
                camera = ob.data
                if camera.type == 'PERSP':
                    return True
            return False
        return (ob for ob in self._scene.objects if check(ob))

    @property
    def has_initial_visible_camera_objects(self):
        """
        True if there are initial visible camera objects in the scene
        @return: bool
        """
        for _ in self.initial_visible_camera_objects:
            return True
        return False

    @property
    def initial_visible_camera_objects(self):
        """
        Generates a generator of initial visible camera objects
        @return: generator
        """
        return (ob for ob in self.camera_objects if (not ob.cpp.initial_hide_viewport))

    @property
    def has_available_camera_objects(self):
        """
        True if there are cameras available for automation in the scene
        @return: bool
        """
        for _ in self.available_camera_objects:
            return True
        return False

    @property
    def available_camera_objects(self):
        """
        Generates a generator of available camera objects
        @return: generator
        """
        return (ob for ob in self.camera_objects if ob.data.cpp.available)

    @property
    def has_camera_objects_selected(self):
        """
        True if there are selected cameras in the scene
        @return: bool
        """
        for _ in self.selected_camera_objects:
            return True
        return False

    @property
    def selected_camera_objects(self):
        """
        Generates a generator of selected camera objects
        @return: generator
        """
        return (ob for ob in self._scene.cpp.camera_objects if ob.select_get())

    def cameras_hide_set(self, state):
        """
        Sets the visibility status of camera objects in the scene.
        @param state: bool
        """
        for camera_object in self.camera_objects:
            if state:
                camera_object.hide_set(True)
            else:
                camera_object.hide_set(camera_object.cpp.initial_hide_viewport)

    def ensure_objects_initial_hide_viewport(self, context):
        for ob in self._scene.objects:
            state = True
            if ob in context.visible_objects:
                state = False
            ob.cpp.initial_hide_viewport = state

    # Update methods
    def _use_auto_set_image_update(self, context):
        if self.use_auto_set_image:
            operators.utils.cameras.set_clone_image_from_camera_data(context)

    def _use_camera_image_previews_update(self, context):
        if self.use_camera_image_previews:
            operators.basis.draw.cameras.clear_image_previews()

    # Properties
    source_images_path: StringProperty(
        name="Source Images Directory",
        subtype='DIR_PATH',
        description="The path to the directory of the images used. "
                    "Used to automate image search for cameras by name"
    )

    calibration_source_file: StringProperty(
        name="Camera Calibration File",
        subtype='FILE_PATH',
        description="Path to third-party application *.csv file."
        "Used for automatic setup camera calibration parameters"
    )

    # Tool relative
    mapping: EnumProperty(
        items=[('UV', "UV", "Standard UV Mapping", '', 0),
               ('CAMERA', "Camera", "Camera Projection", '', 1)],
        name="Mapping",
        default='UV',
        options={'HIDDEN'},
        description="Source image mapping method"
    )

    # Camera section
    use_auto_set_camera: BoolProperty(
        name="Auto Camera Selection", default=False,
        options={'HIDDEN'},
        description="Automatically select a camera based on the direction and location of the viewer"
    )

    use_auto_set_image: BoolProperty(
        name="Auto Clone Image Selection", default=True,
        options={'HIDDEN'},
        description="Automatically set Clone Image to the image attached to the current camera",
        update=_use_auto_set_image_update)

    auto_set_camera_method: EnumProperty(
        items=[
            ('FULL', "Full",
             "Automatic dependent to world orientation and location",
             icons.get_icon_id("autocam_full"), 0),
            ('DIRECTION', "Direction",
             "Automatic dependent to view direction only",
             icons.get_icon_id("autocam_direction"), 1)
        ],
        name="Auto Camera Method",
        default='DIRECTION',
        options={'HIDDEN'},
        description="Method for camera selection"
    )

    tolerance_full: FloatProperty(
        name="Tolerance", default=0.92, soft_min=0.0, soft_max=1.0,
        subtype='FACTOR',
        options={'HIDDEN'},
        description="Tolerance in the difference between camera and viewer parameters"
    )

    tolerance_direction: FloatProperty(
        name="Tolerance", default=0.55, soft_min=0.0, soft_max=1.0,
        subtype='FACTOR',
        options={'HIDDEN'},
        description="Tolerance in the difference between camera and viewer parameters"
    )

    cameras_viewport_size: FloatProperty(
        name="Viewport Display Size",
        default=1.0, soft_min=1.0, soft_max=5.0, step=0.1,
        subtype='DISTANCE',
        options={'HIDDEN'},
        description="The size of the cameras to display in the viewport. Does not affect camera settings"
    )

    # Viewport draw
    use_projection_preview: BoolProperty(
        name="Brush Preview", default=True,
        options={'HIDDEN'},
        description="Display preview overlay projection clone image in brush"
    )

    use_projection_outline: BoolProperty(
        name="Outline", default=True,
        options={'HIDDEN'},
        description="Display the stroke around the borders of the projected image"
    )

    use_normal_highlight: BoolProperty(
        name="Normal Highlight", default=False,
        options={'HIDDEN'},
        description="Visualization of the angle between"
        "the direction of the projector and the normal of the mesh in the current fragment"
    )

    use_camera_image_previews: BoolProperty(
        name="Camera Images", default=False,
        options={'HIDDEN'},
        description="Display previews of images binded to cameras in the viewport. Uses standard image previews.",
        update=_use_camera_image_previews_update
    )

    use_camera_axes: BoolProperty(
        name="Axes", default=False,
        options={'HIDDEN'},
        description="Display the axes of the camera object"
    )

    camera_axes_size: FloatProperty(
        name="Axes Size",
        default=0.5, soft_min=0.1, soft_max=1.0, step=0.1,
        subtype='DISTANCE',
        options={'HIDDEN'},
        description="Axis display length in viewport"
    )

    # Current image preview
    use_current_image_preview: BoolProperty(
        name="Current Image", default=True,
        options={'HIDDEN'},
        description="Display an interactive gizmo with the current clone image."
        "It works approximately using simple calculations projected onto the plane of the brush."
    )

    current_image_size: IntProperty(
        name="Scale",
        default=250, min=200, soft_max=1000,
        subtype='PIXEL',
        options={'HIDDEN'},
        description="The size of the displayed image on the longest side in pixels"
    )

    current_image_alpha: FloatProperty(
        name="Alpha",
        default=0.25, soft_min=0.0, soft_max=1.0, step=1,
        subtype='FACTOR',
        options={'HIDDEN'},
        description="The transparency of the displayed gizmo."
        "If the cursor is over the gizmo, an opaque image is displayed"
    )

    current_image_position: FloatVectorProperty(
        name="Pos", size=2,
        options={'HIDDEN'},
        default=(0.0, 0.0), min=0.0, max=1.0
    )

    # Warnings
    use_warnings: BoolProperty(
        name="Use warnings", default=True,
        options={'HIDDEN'},
        description="Use warnings if drawing can potentially become lagging"
    )

    use_warning_action_draw: BoolProperty(
        name="Brush Preview", default=True,
        options={'HIDDEN'},
        description="Displays a warning in the brush preview. Doesn't depend on Use Brush Preview"
    )

    use_warning_action_popup: BoolProperty(
        name="Info popup", default=False,
        options={'HIDDEN'},
        description="Open popup warning if current context is out of recommended"
    )

    use_warning_action_lock: BoolProperty(
        name="Lock Paint", default=True,
        options={'HIDDEN'},
        description="Lock paint if current context is out of recommended"
    )

    distance_warning: FloatProperty(
        name="Safe Radius",
        default=5.0, soft_min=1.0, soft_max=15.0,
        subtype='DISTANCE',
        options={'HIDDEN'},
        description="User recommended radius projected onto the plane brush"
    )

    max_loaded_images: IntProperty(
        name="Max Loaded Images",
        default=5,
        min=2,
        soft_max=10,
        description="The number of images simultaneously loaded into memory.\n"
                    "If this limit is exceeded, the first of the loaded images is freed from memory"
    )

    # Canvas - Diffuse
    use_bind_canvas_diffuse: BoolProperty(
        name="Bind Canvas Diffuse", default=False,
        options={'HIDDEN'},
        description="Automatically set the diffuse texture to canvas when changing and in reverse"
    )
