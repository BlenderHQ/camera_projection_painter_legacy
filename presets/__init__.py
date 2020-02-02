# <pep8 compliant>

import os
import shutil

import bpy

PRESETS_DIR_NAME = "camera_projection_painter"

WORKFLOW_PRESETS_DIR_NAME = os.path.join(PRESETS_DIR_NAME, "workflow")


def register():
    default_presets_path = os.path.dirname(bpy.path.abspath(__file__))

    def _is_preset(file_name):
        name, ext = os.path.splitext(file_name)
        if (name == "__init__") or (ext != ".py"):
            return False
        return True
    
    sucess = 0
    
    for name in os.listdir(default_presets_path):
        path = os.path.join(default_presets_path, name)
        if os.path.isdir(path) and name != "__pycache__":
            target_path = os.path.join("presets", PRESETS_DIR_NAME, name)
            
            for file_name in os.listdir(path):
                if _is_preset(file_name):
                    default_preset_file_path = os.path.join(path, file_name)
                    if os.path.isfile(default_preset_file_path):
                        target_path = (bpy.utils.user_resource('SCRIPTS', target_path, create=True))
                        target_file_path = os.path.join(target_path, file_name)

                        if os.path.isfile(target_file_path):
                            continue
                        try:
                            shutil.copy(default_preset_file_path, target_file_path)
                            sucess += 1
                        except WindowsError:
                            print("Can't copy default presets. Violation access to %s" % target_path)
                        except:
                            print("Unknown exception while copying default presets to %s" % target_path)
    if sucess:
        print("Camera Projection Painter: Successfully copied %d preset files" % sucess)







