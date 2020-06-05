import os

import bpy


def _get_xmp_file_filepath(filepath):
    fp = bpy.path.abspath(filepath)
    if os.path.isfile(fp):
        ext = os.path.splitext(fp)[-1]
        if ext in {".xmp", ".XMP"}:
            return fp


class CPP_OT_import_cameras_xml(bpy.types.Operator):
    bl_idname = "cpp.import_cameras_xml"
    bl_label = "Import XML"
    bl_options = {'INTERNAL'}

    mode: bpy.props.EnumProperty(
        items=[
            ('ACTIVEOB', "Active Object", ""),
            ('SCENECAM', "Scene Camera", ""),
            ('SELECTED', "Selected Cameras", ""),
            ('ALL', "All Cameras", ""),
            ('GS', "Current Camera", "")
        ],
        name="Mode",
        default='ALL'
    )

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

        elif self.mode == 'ALL':
            for ob in scene.cpp.camera_objects:
                yield ob

        elif self.mode == 'GS':
            yield context.window_manager.cpp.current_selected_camera_ob

        yield None

    def execute(self, context):
        success = 0
        skipped = 0

        for ob in self.iter_processed_cameras(context):
            if ob is None:
                continue

            camera = ob.data
            image = camera.cpp.image

            xmp_filepath = camera.cpp.xmp_filepath
            if not xmp_filepath:
                if image.source == 'FILE':
                    imfp = image.filepath
                    splext = os.path.splitext(imfp)
                    if len(splext) > 1:
                        xmp_filepath = splext[0] + ".xmp"

            fp = _get_xmp_file_filepath(xmp_filepath)
            if not fp:
                skipped += 1
                continue

            # TODO: Actually, importing...

        self.report(type={'INFO'},
                    message=f"Imported calibration parameters for {success} cameras, skipped {skipped}")

        return {'FINISHED'}
