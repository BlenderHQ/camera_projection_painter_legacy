# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils
    from .. import __package__ as pkg

import bpy


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
        return utils.poll.tool_setup_poll(context)

    def _create_gizmo(self, camera_ob):
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

        for camera_ob in context.scene.cpp.camera_objects:
            self._create_gizmo(camera_ob)

    def refresh(self, context):
        _invalid_camera_gizmos = {}
        for camera_ob, mpr in self._camera_gizmos.items():
            try:
                _name = camera_ob.name
            except ReferenceError:
                _invalid_camera_gizmos[camera_ob] = mpr

        for camera_ob, mpr in _invalid_camera_gizmos.items():
            self._camera_gizmos.pop(camera_ob)
            self.gizmos.remove(mpr)

        for camera_ob in context.scene.cpp.camera_objects:
            if camera_ob in self._camera_gizmos.keys():
                mpr = self._camera_gizmos[camera_ob]
                mpr.matrix_basis = camera_ob.matrix_world
            else:
                mpr = self._create_gizmo(camera_ob)

    def draw_prepare(self, context):
        preferences = context.preferences.addons[pkg].preferences
        for mpr in self.gizmos:
            mpr.color = preferences.gizmo_color[0:3]
            mpr.alpha = preferences.gizmo_color[3]
            mpr.alpha_highlight = preferences.gizmo_color[3]

            mpr.scale_basis = preferences.gizmo_radius
