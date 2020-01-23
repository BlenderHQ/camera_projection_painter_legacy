# <pep8 compliant>

# At the moment, there is no way to fully use custom gizmo when
# splitting a window (see link), therefore, standard
# https://developer.blender.org/T71941

import importlib

import bpy

from .. import poll
from .. import __package__ as pkg

if "_rc" in locals():  # In case of module reloading
    importlib.reload(poll)

_rc = None


class CPP_GGT_camera_gizmo_group(bpy.types.GizmoGroup):
    bl_idname = "CPP_GGT_camera_gizmo_group"
    bl_label = "Camera Painter Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'DEPTH_3D', 'SCALE'}

    _camera_gizmos: dict

    __slots__ = ("_camera_gizmos",)

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def _create_gizmo(self, camera_ob):
        """The method adds one gizmo and sets its properties"""
        mpr = self.gizmos.new("GIZMO_GT_primitive_3d")
        props = mpr.target_set_operator("cpp.call_pie")
        props.camera_name = camera_ob.name

        mpr.matrix_basis = camera_ob.matrix_world

        mpr.use_select_background = True
        mpr.use_event_handle_all = False

        self._camera_gizmos[camera_ob] = mpr

        return mpr

    def setup(self, context):
        scene = context.scene

        self._camera_gizmos = {}

        # Gizmo created for every camera in the scene.
        for camera_ob in context.scene.cpp.camera_objects:
            self._create_gizmo(camera_ob)

    def refresh(self, context):
        _invalid_camera_gizmos = {}
        # Fill the dictionary with links to cameras that are deleted
        for camera_ob, mpr in self._camera_gizmos.items():
            try:
                _name = camera_ob.name
            except ReferenceError:
                _invalid_camera_gizmos[camera_ob] = mpr

        # Remove the gizmo of these cameras and from the dictionary
        for camera_ob, mpr in _invalid_camera_gizmos.items():
            self._camera_gizmos.pop(camera_ob)
            self.gizmos.remove(mpr)

        # Update the parameters of the gizmo of the existing cameras
        # and also add new ones if necessary
        for camera_ob in context.scene.cpp.camera_objects:
            if camera_ob in self._camera_gizmos.keys():
                mpr = self._camera_gizmos[camera_ob]
                mpr.matrix_basis = camera_ob.matrix_world
            else:
                mpr = self._create_gizmo(camera_ob)

    def draw_prepare(self, context):
        preferences = context.preferences.addons[pkg].preferences
        # Properties concerning only rendering are changed when possible
        for mpr in self.gizmos:
            mpr.color = preferences.gizmo_color[0:3]
            mpr.alpha = preferences.gizmo_color[3]
            mpr.alpha_highlight = preferences.gizmo_color[3]

            mpr.scale_basis = preferences.gizmo_radius
