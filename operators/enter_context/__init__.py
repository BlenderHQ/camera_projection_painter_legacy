from ... import poll
from . import io_fbx
from . import ui_io_fbx
from ... import __package__ as addon_pkg

if "bpy" in locals():
    import importlib
    importlib.reload(poll)
    importlib.reload(io_fbx)

import bpy


def _check(ob):
    return ob and ob.type == 'MESH' and len(ob.data.polygons)


def get_valid_mesh_object(context):
    A_ob = None
    max_poly_count = 0
    for ob in context.visible_objects:
        if _check(ob):
            poly_count = len(ob.data.polygons)
            if poly_count > max_poly_count:
                max_poly_count = poly_count
                A_ob = ob
    return A_ob


def stage_none(self, context, event):
    wm = context.window_manager
    wm.cpp.progress_stage_complete()
    return {'RUNNING_MODAL'}


def stage_mesh_check(self, context, event):
    wm = context.window_manager

    preferences = context.preferences.addons[addon_pkg].preferences

    if not _check(context.active_object):
        A_ob = get_valid_mesh_object(context)
        if A_ob:
            context.view_layer.objects.active = A_ob
    if not _check(context.active_object):
        self.report(type={'WARNING'}, message="Missing mesh object")
        self.cancel(context)
        return {'CANCELLED'}

    ob = context.active_object
    image_paint = context.scene.tool_settings.image_paint

    if ob.active_material is None:
        self.report(type={'INFO'}, message="No active material detected, new material created")
        ob.data.materials.append(bpy.data.materials.new("Material"))

    material = ob.active_material
    if material is None:
        self.report(type={'WARNING'}, message="Missing active material")
    else:
        material.use_nodes = True

        tree = material.node_tree
        nodes = tree.nodes

        new_canvas = None
        for i, node in enumerate(nodes):
            if (node.bl_idname == "ShaderNodeTexImage") and (node.image):
                new_canvas = node.image
                break

        if new_canvas and new_canvas != image_paint.canvas:
            self.report(type={'INFO'}, message=f"""Image "{node.image.name}" set as texture (canvas)""")
            image_paint.canvas = new_canvas

        if tree.active_texnode_index == -1:
            dim = preferences.new_texture_size
            bpy.ops.paint.add_texture_paint_slot(
                width=dim[0], height=dim[1], color=(0.8, 0.8, 0.8, 1.0),
                alpha=False, generated_type='BLANK', float=True)
            self.report(type={'INFO'}, message=f"No texture found (canvas), a new one was created ({dim[0]}x{dim[1]})")

        tex_node = nodes[tree.active_texnode_index]
        if tex_node and tex_node.image:
            image_paint.canvas = tex_node.image

    wm.cpp.progress_stage_complete()
    return {'RUNNING_MODAL'}


def stage_bind_images(self, context, event):
    wm = context.window_manager

    if wm.cpp.import_dir:
        context.scene.cpp.source_dir = wm.cpp.import_dir

    bpy.ops.cpp.bind_camera_image('INVOKE_DEFAULT', mode='ALL', search_blend=True,
                                  rename=True, refresh_image_previews=True)

    bpy.ops.cpp.import_cameras_csv('EXEC_DEFAULT')

    wm.cpp.progress_stage_complete()
    return {'RUNNING_MODAL'}


def stage_tool_settings(self, context, event):
    wm = context.window_manager

    ob = context.active_object
    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    if ob.mode != 'TEXTURE_PAINT':
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

    tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    if tool.idname != "builtin_brush.Clone":
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Clone", cycle=False, space_type='VIEW_3D')

    if image_paint.mode != 'IMAGE':
        image_paint.mode = 'IMAGE'

    if not image_paint.use_clone_layer:
        image_paint.use_clone_layer = True

    if (not scene.camera) and scene.cpp.has_camera_objects:
        scene.camera = list(scene.cpp.camera_objects)[0]

    if scene.camera:
        image = scene.camera.data.cpp.image
        if image and image.size[0] and image.size[1] and (image != image_paint.clone_image):
            image_paint.clone_image = image

    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.light = 'FLAT'

    wm.cpp.progress_stage_complete()
    return {'RUNNING_MODAL'}


def stage_view_all(self, context, event):
    wm = context.window_manager
    if context.area.type == 'VIEW_3D':
        bpy.ops.view3d.view_all('INVOKE_DEFAULT')
        # duration = context.preferences.view.smooth_view / 100.0
        # wm.cpp.progress_wait_before_next_stage(duration)

    wm.cpp.progress_stage_complete()
    return {'RUNNING_MODAL'}


class CPP_OT_enter_context(bpy.types.Operator):
    bl_idname = "cpp.enter_context"
    bl_label = "Setup Context"
    bl_options = {'INTERNAL'}

    __slots__ = ("timer", "is_import", "func_stages")

    @classmethod
    def poll(cls, context):
        return not poll.full_poll(context)

    @classmethod
    def description(cls, context, properties):
        result = ""

        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        workspace_tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)

        is_file_import_required = False

        # Object check
        ob = context.active_object
        if not _check(ob):
            old_ob = ob
            ob = get_valid_mesh_object(context)
            if ob and old_ob:
                result += \
                    f"""\u2022 "{old_ob.name}" is not valid for texture paint, "{ob.name}" will be set active.\n"""
            elif ob:
                result += f"""\u2022 "{ob.name}" will be set active.\n"""
        if not _check(ob):
            is_file_import_required = True
            result += "\u2022 FBX file will be imported.\n"

        # Bind images path
        info_path = scene.cpp.source_dir
        if (not info_path):
            if is_file_import_required:
                info_path = "file import directory"
            elif len(bpy.data.images):
                info_path = "already opened images"
        else:
            info_path = f""""{info_path}" """

        if info_path:
            result += f"\u2022 Camera images will be binded from {info_path}.\n"
        else:
            result += "\u203c No way to bind images, select source directory or open images manually first!\n"

        # Material check
        if (not is_file_import_required):
            if _check(ob):
                material = ob.active_material
                if material is None:
                    result += f"""\u2022 "{ob.name}" object missing material, a new one will be created.\n"""
                else:
                    tree = material.node_tree
                    nodes = tree.nodes
                    new_canvas = None
                    for i, node in enumerate(nodes):
                        if (node.bl_idname == "ShaderNodeTexImage") and (node.image):
                            new_canvas = node.image
                            break
                    if new_canvas and new_canvas != image_paint.canvas:
                        result += f"""\u2022 Image "{new_canvas.name}" will be set as texture (canvas).\n"""
                    elif new_canvas is None and image_paint.canvas is None:
                        result += f"""\u2022 A new image will be set as texture (canvas).\n"""

            # Camera check
            camera_object = scene.camera
            if (not camera_object) and scene.cpp.has_camera_objects:
                camera_object = list(scene.cpp.camera_objects)[0]
                result += f"""\u2022 Scene camera will be set to "{camera_object.name}".\n"""

            if camera_object:
                image = camera_object.data.cpp.image
                if image and image.cpp.valid and (image != image_paint.clone_image):
                    result += f"""\u2022 Image Paint "Clone Image" will be set to "{image.name}".\n"""
            elif not scene.cpp.has_camera_objects:
                result += "\u203c Scene missing camera objects.\n"

        # Scene/Tool settings check
        if (workspace_tool.idname != "builtin_brush.Clone") or\
                (image_paint.mode != 'IMAGE') or\
                (not image_paint.use_clone_layer):
            result += "\u2022 Scene/tool settings will be changed.\n"

        #
        if not result:
            result = "Context is ready"
        if result.endswith(".\n"):
            result = result[0:-2]
        return result

    def invoke(self, context, event):
        wm = context.window_manager

        self.func_stages = [
            stage_bind_images,
            stage_mesh_check,
            stage_tool_settings,
            stage_view_all
        ]

        # Object check
        if not _check(context.active_object):
            A_ob = get_valid_mesh_object(context)
            if A_ob:
                context.view_layer.objects.active = A_ob

        # Invoke import if not found any valid object
        self.is_import = not _check(context.active_object)

        if self.is_import:
            bpy.ops.cpp.io_fbx('INVOKE_DEFAULT')
            self.func_stages.insert(0, stage_none)
        else:
            wm.cpp.progress_invoke(
                progress_stages_count=len(self.func_stages),
                text=self.__class__.bl_label,
                icon='TIME'
            )

        self.timer = wm.event_timer_add(time_step=1 / 60, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.cpp.progress_complete()
        context.window.cursor_modal_restore()
        wm.event_timer_remove(self.timer)

    def modal(self, context, event):
        wm = context.window_manager

        pstage = wm.cpp.progress_modal(self.timer)

        if self.is_import:
            if wm.cpp.import_state == 'FILESELECT':
                return {'PASS_THROUGH'}

            elif wm.cpp.import_state == 'FINISHED':
                wm.cpp.progress_invoke(
                    progress_stages_count=len(self.func_stages),
                    text="Setup Context",
                    icon='TIME',
                    ui_cancel_button='ESC'
                )
                self.is_import = False
                return {'RUNNING_MODAL'}

            elif wm.cpp.import_state == 'CANCELLED':
                self.cancel(context)
                return {'CANCELLED'}

        elif event.type != 'TIMER':
            return {'RUNNING_MODAL'}

        if pstage == -2:
            if poll.full_poll(context):
                self.report(type={'INFO'}, message="Context is ready")
            else:
                self.report(type={'INFO'}, message="Context is not completely ready")
            self.cancel(context)
            return {'FINISHED'}

        elif pstage == -1:
            return {'RUNNING_MODAL'}

        else:
            return self.func_stages[pstage](self, context, event)

        self.cancel(context)
        return {'CANCELLED'}
