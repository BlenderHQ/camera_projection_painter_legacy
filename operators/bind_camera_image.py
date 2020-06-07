import bpy

from .. import engine


class CPP_OT_bind_camera_image(bpy.types.Operator):
    bl_idname = "cpp.bind_camera_image"
    bl_label = "Bind Image By Name"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[
            ('ACTIVEOB', "Active Object", ""),
            ('SCENECAM', "Scene Camera", ""),
            ('SELECTED', "Selected Cameras", ""),
            ('ALL', "All Cameras", ""),
            ('GS', "Current Camera", "")  # Gizmo-selected
        ],
        name="Mode",
        default='ALL'
    )

    search_blend: bpy.props.BoolProperty(
        name="Search In Current File",
        default=True,
        description="Search images in current *.blend file, include image filepath (may be slow)"
    )

    rename: bpy.props.BoolProperty(
        name="Rename",
        default=False,
        description="Set camera and image name to filename on disk"
    )

    refresh_image_previews: bpy.props.BoolProperty(
        name="Refresh Image Preview",
        default=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "search_blend")
        layout.prop(self, "rename")
        layout.prop(self, "refresh_image_previews")

    @classmethod
    def description(cls, context, properties):
        mode = properties.mode

        if mode == 'ACTIVEOB':
            return "Binding image to camera data by name matching"
        elif mode == 'SCENECAM':
            return "Binding an image to the current scene camera by name matching"
        elif mode == 'SELECTED':
            return "Binding images to selected cameras by name matching"
        elif mode == 'ALL':
            return "Binding images to all cameras in the scene by name matching"
        elif mode == 'GS':
            return "Binding image to context camera data by name matching"

    def iter_processed_cameras(self, context):
        scene = context.scene
        if self.mode == 'ACTIVEOB':
            ob = context.active_object
            if ob and ob.type == 'CAMERA':
                yield ob

        elif self.mode == 'SCENECAM':
            ob = scene.camera
            if ob and ob.type == 'CAMERA':
                yield ob

        elif self.mode == 'SELECTED':
            for ob in scene.cpp.selected_camera_objects:
                yield ob
            return

        elif self.mode == 'ALL':
            for ob in scene.cpp.camera_objects:
                yield ob
            return

        elif self.mode == 'GS':
            ob = context.window_manager.cpp.current_selected_camera_ob
            if ob and ob.type == 'CAMERA':
                yield ob

    def execute(self, context):
        scene = context.scene
        camera_seq = list([_ for _ in self.iter_processed_cameras(context)])

        binded = engine.bindCameraImages(camera_seq, scene.cpp.source_dir, self.search_blend, self.rename)

        cam_txt = "cameras"
        mtp = 'INFO'
        if binded == 0:
            mtp = 'WARNING'
        elif binded == 1:
            cam_txt = "camera"

        self.report(type={mtp}, message=f"Binded {binded} {cam_txt}")

        engine.updateImageSeqStaticSize(bpy.data.images, skip_already_set=True)
        if self.refresh_image_previews:
            bpy.ops.cpp.refresh_image_preview('EXEC_DEFAULT', skip_already_set=True)

        return {'FINISHED'}
