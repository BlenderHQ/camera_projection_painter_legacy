# <pep8 compliant>

import os

import bpy

# https://docs.blender.org/manual/en/latest/files/media/image_formats.html#image-formats
SUPPORTED_IMAGE_EXTENSIONS = (
    ".bmp",  # BMP
    ".sgi",
    ".rgb",
    ".bw",  # Iris
    ".png",  # PNG
    ".jpg",
    ".jpeg",  # JPEG
    ".jp2",
    ".jp2",
    ".j2c",  # JPEG 2000
    ".tga",  # Targa
    ".cin",
    ".dpx",  # Cineon & DPX
    ".exr",  # OpenEXR
    ".hdr",  # Radiance HDR
    ".tif",
    ".tiff"  # TIFF
)

operator_mode = bpy.props.EnumProperty(
    items=[
        ('ACTIVE', "Active", ""),
        ('CONTEXT', "Context", ""),
        ('SELECTED', "Selected", ""),
        ('ALL', "All", ""),
        ('TMP', "Tmp", "")
    ],
    name="Mode",
    default='ACTIVE'
)


def get_source_directory_image_file_list(source_directory_path: str):
    """The method returns a list of image files with the extension from the list"""
    source_directory_file_list = []
    if os.path.isdir(source_directory_path):
        for item_name in os.listdir(source_directory_path):
            item_path = bpy.path.native_pathsep(
                os.path.join(source_directory_path, item_name))
            if os.path.isfile(item_path):
                file_ext = os.path.splitext(item_name)[1]
                if file_ext in SUPPORTED_IMAGE_EXTENSIONS:
                    source_directory_file_list.append(item_path)
    return source_directory_file_list


def get_processed_camera_objects_list(context: bpy.types.Context, mode: str):
    scene = context.scene

    processed_camera_objects_list = []

    if mode == 'ACTIVE':
        camera_object = context.active_object
        processed_camera_objects_list = (
            [camera_object]) if camera_object.type == 'CAMERA' else []

    elif mode == 'CONTEXT':
        processed_camera_objects_list = [scene.camera]

    elif mode == 'SELECTED':
        processed_camera_objects_list = list(scene.cpp.selected_camera_objects)

    elif mode == 'ALL':
        processed_camera_objects_list = list(scene.cpp.camera_objects)

    elif mode == 'TMP':
        wm = context.window_manager
        camera_object = wm.cpp_current_selected_camera_ob
        if camera_object:
            processed_camera_objects_list = [
                camera_object] if camera_object.type == 'CAMERA' else []

    else:
        raise KeyError(
            "A call with an invalid mode key value. Valid are:\n'ACTIVE', 'CONTEXT', 'SELECTED', 'ALL', 'TMP'")

    return processed_camera_objects_list


def bind_camera_image_by_name(camera_object: bpy.types.Object, source_directory_file_list: list):
    """Attaches the image to the camera in case it is found"""
    if camera_object.type != 'CAMERA':
        return

    found_image = None
    is_renamed_blend_image = False

    # First search in already opened images
    for image in bpy.data.images:
        if image.cpp.valid:
            blend_image_name = image.name
            root_image_name = os.path.splitext(blend_image_name)[0]

            if camera_object.name in (blend_image_name, root_image_name):
                found_image = image
                break
            elif image.source == 'FILE':
                file_path = image.filepath
                if os.path.isfile(file_path):
                    file_image_name = os.path.basename(file_path)
                    root_image_name = os.path.splitext(file_image_name)[0]

                    if camera_object.name in (file_image_name, root_image_name):
                        image.name = file_image_name
                        found_image = image
                        is_renamed_blend_image = True
                        break

    # And then search from files in source images directory
    if not found_image:
        for file_path in source_directory_file_list:
            file_name = bpy.path.basename(file_path)
            blend_image_name = os.path.splitext(file_name)[0]
            root_image_name = os.path.splitext(blend_image_name)[0]

            if camera_object.name in (file_name, blend_image_name, root_image_name):
                if file_name in bpy.data.images:
                    bpy.data.images[file_name].filepath = file_path
                    found_image = bpy.data.images[file_name]
                else:
                    found_image = bpy.data.images.load(
                        filepath=file_path, check_existing=True)
                break

    if found_image and found_image.cpp.valid:
        camera_object.data.cpp.image = found_image
        return found_image, is_renamed_blend_image
    camera_object.data.cpp.image = None


def operator_execute(self, context):
    """Operator Execution Method"""

    print(context.area.type)

    scene = context.scene
    source_directory_path = bpy.path.native_pathsep(
        path=bpy.path.abspath(path=scene.cpp.source_images_path))

    successful_count = 0
    renamed_images_count = 0

    source_directory_image_file_list = get_source_directory_image_file_list(
        source_directory_path)

    processed_camera_objects = get_processed_camera_objects_list(
        context, self.mode)

    for camera_object in processed_camera_objects:
        result = bind_camera_image_by_name(
            camera_object, source_directory_image_file_list)
        if result:
            found_image, is_renamed_blend_image = result
            successful_count += 1
            # Printing the names of successfully processed
            # cameras and the names of their corresponding images in the console
            if is_renamed_blend_image:
                print("Renamed image (name from file on disk):")
                renamed_images_count += 1
            print("Camera: %s - Image: %s" %
                  (camera_object.name, found_image.name))

    if successful_count:
        if renamed_images_count:
            message = "Binded %d camera images, renamed %d" % (
                successful_count, renamed_images_count)
        else:
            message = "Binded %d camera images" % successful_count
        if successful_count == 1:
            if renamed_images_count:
                message = "Binded %s camera image, renamed" % found_image.name
            else:
                message = "Binded %s camera image" % found_image.name
        self.report(type={'INFO'}, message=message)
    else:
        self.report(type={'WARNING'}, message="Images not found!")

    return {'FINISHED'}


def operator_draw(self, context):
    """Method for drawing operator options"""
    layout = self.layout
    layout.label(text="No available redo options!", icon='INFO')


class CPP_OT_bind_camera_image(bpy.types.Operator):
    bl_idname = "cpp.bind_camera_image"
    bl_label = "Bind Image By Name"
    bl_options = {'REGISTER', 'UNDO'}

    mode: operator_mode

    @classmethod
    def description(cls, context, properties):
        mode = properties.mode

        if mode == 'ACTIVE':
            return "Binding image to camera data by name matching"
        elif mode == 'CONTEXT':
            return "Binding an image to the current camera in the scene by name matching"
        elif mode == 'SELECTED':
            return "Binding images to selected cameras by name matching"
        elif mode == 'ALL':
            return "Binding images to all cameras in the scene by name matching"
        elif mode == 'TMP':
            return "Binding image to context camera data by name matching"

    execute = operator_execute

    #draw = operator_draw
