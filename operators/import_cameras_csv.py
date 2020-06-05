
import os
import time
import csv

import bpy

# Full calibration parameters list is:
#     ['#name', 'x', 'y', 'alt', 'heading', 'pitch', 'roll', 'f', 'px', 'py', 'k1', 'k2', 'k3', 'k4', 't1', 't2']
# but we are interested only in next:
CALIB_PARAMS = dict.fromkeys(["#name", "f", "px", "py", "k1", "k2", "k3", "k4", "t1", "t2"])


def get_csv_file_filepath(filepath):
    fp = bpy.path.abspath(filepath)
    if os.path.isfile(fp):
        ext = os.path.splitext(fp)[-1]
        if ext.lower() == ".csv":
            return fp


class CPP_OT_import_cameras_csv(bpy.types.Operator):
    bl_idname = "cpp.import_cameras_csv"
    bl_label = "Import CSV"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return get_csv_file_filepath(context.scene.cpp.calibration_source_file)

    @staticmethod
    def iter_name_variations(name: str):
        splext = os.path.splitext(name)
        if len(splext) > 1:
            yield splext[0] + splext[-1].lower()
        yield splext[0]

    def execute(self, context):
        scene = context.scene

        fp = get_csv_file_filepath(scene.cpp.calibration_source_file)
        filename = os.path.basename(fp)

        dt = time.time()
        success_rows = 0
        skipped_rows = 0

        with open(fp, "r") as file:
            reader = csv.reader(file)
            first_row_length = 0
            for i, row in enumerate(reader):
                if i == 0:
                    first_row_length = len(row)
                    # In Reality Capture exported *.csv first line always starts with commented line camera #name
                    is_supported_file = False

                    if first_row_length and row[0] == "#name":
                        params_found = 0
                        for i, item in enumerate(row):
                            if item in CALIB_PARAMS:
                                CALIB_PARAMS[item] = i
                                params_found += 1
                        if params_found == len(CALIB_PARAMS):
                            is_supported_file = True
                            continue

                    if is_supported_file is False:
                        self.report(type={'WARNING'}, message=f"Unsupported calibration file: {filename}")
                        return {'CANCELLED'}

                if len(row) != first_row_length:
                    skipped_rows += 1
                    continue

                item_name = str(row[CALIB_PARAMS["#name"]])
                camera_object = None
                for ob in scene.cpp.camera_objects:
                    for name in self.iter_name_variations(ob.name):
                        for iname in self.iter_name_variations(item_name):
                            if name == iname:
                                camera_object = ob

                if camera_object is None:
                    skipped_rows += 1
                    continue
                camera = camera_object.data

                camera.lens = float(row[CALIB_PARAMS["f"]])
                camera.cpp.principal_point_x = float(row[CALIB_PARAMS["px"]])
                camera.cpp.principal_point_y = float(row[CALIB_PARAMS["py"]])

                camera.cpp.k1 = float(row[CALIB_PARAMS["k1"]])

                k2 = float(row[CALIB_PARAMS["k2"]])
                camera.cpp.k2 = k2

                k3 = float(row[CALIB_PARAMS["k3"]])
                camera.cpp.k3 = k3

                k4 = float(row[CALIB_PARAMS["k4"]])
                camera.cpp.k4 = k4

                t1 = float(row[CALIB_PARAMS["t1"]])
                camera.cpp.t1 = t1

                t2 = float(row[CALIB_PARAMS["t2"]])
                camera.cpp.t2 = t2

                if (k2 or k3):
                    camera.cpp.camera_lens_model = 'brown3'
                    if k4:
                        camera.cpp.camera_lens_model = 'brown4'
                    if (t1 or t2):
                        camera.cpp.camera_lens_model = 'brown3t2'
                        if k4:
                            camera.cpp.camera_lens_model = 'brown4t2'
                success_rows += 1

        cam_txt = "cameras"
        if success_rows == 1:
            cam_txt = "camera"
        mtp = 'INFO'
        if success_rows == 0:
            mtp = 'WARNING'
        t = round(time.time() - dt, 3)
        self.report(
            type={mtp},
            message=f"Imported calibration parameters for {success_rows} {cam_txt}, skipped {skipped_rows} in {t} sec"
        )

        return {'FINISHED'}
