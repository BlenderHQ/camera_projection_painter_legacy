from ... import engine
from ... import poll
from .. import utils
from . import ui
from . import fbx

if "bpy" in locals():
    import importlib
    importlib.reload(poll)
    importlib.reload(utils)
    importlib.reload(ui)
    importlib.reload(fbx)

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


def step_import(self, context, event):
    wm = context.window_manager
    ob = context.active_object

    if wm.cpp.import_state == 'FILESELECT':
        return {'PASS_THROUGH'}

    elif wm.cpp.import_state == 'FINISHED':
        context.window.cursor_modal_set('WAIT')

        if context.area.type == 'VIEW_3D':
            bpy.ops.view3d.view_all('INVOKE_DEFAULT')

        if not _check(ob):
            A_ob = get_valid_mesh_object(context)
            if A_ob:
                context.view_layer.objects.active = A_ob

        ob = context.active_object
        if not _check(ob):
            self.report(type={'WARNING'}, message="Missing mesh object")
            self.cancel(context)
            return {'CANCELLED'}

        self.progress.skip_tics = 30
        self.progress.step += 1
        return {'PASS_THROUGH'}

    elif wm.cpp.import_state == 'CANCELLED':
        self.cancel(context)
        return {'CANCELLED'}
    return {'RUNNING_MODAL'}


def step_mesh_check(self, context, event):
    self.progress.text = "Mesh Check"
    self.progress.icon = 'MESH_DATA'

    ob = context.active_object
    image_paint = context.scene.tool_settings.image_paint

    if ob.active_material is None:
        new_material = bpy.data.materials.new("Material")
        ob.data.materials.append(new_material)

    material = ob.active_material
    if material is None:
        self.report(type={'WARNING'}, message="Missing active material")
    else:
        material.use_nodes = True

        tree = material.node_tree
        nodes = tree.nodes

        new_canvas = None
        for i, node in enumerate(nodes):
            if (node.bl_idname == "ShaderNodeTexImage") and (node.image) and (node.image.cpp.valid):
                new_canvas = node.image
                break
        if new_canvas and new_canvas != image_paint.canvas:
            image_paint.canvas = new_canvas

        if tree.active_texnode_index == -1:
            bpy.ops.paint.add_texture_paint_slot(
                width=2048, height=2048, color=(0.8, 0.8, 0.8, 1.0),
                alpha=False, generated_type='BLANK', float=True)
        tex_node = nodes[tree.active_texnode_index]
        if tex_node and tex_node.image and tex_node.image.cpp.valid:
            image_paint.canvas = tex_node.image

    self.progress.step += 1
    return {'RUNNING_MODAL'}


def step_tool_settings(self, context, event):
    self.progress.text = "Scene Settings Check"
    self.progress.icon = 'TIME'

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

    self.progress.step += 1
    return {'RUNNING_MODAL'}


def step_bind_images(self, context, event):
    self.progress.text = "Bind Images"
    self.progress.icon = 'IMAGE'

    wm = context.window_manager
    if wm.cpp.import_dir:
        context.scene.cpp.source_dir = wm.cpp.import_dir
    bpy.ops.cpp.bind_camera_image('INVOKE_DEFAULT', mode='ALL', search_blend=True,
                                  rename=True, refresh_image_previews=True)

    self.progress.step += 1
    return {'RUNNING_MODAL'}

func_steps = (
    step_import,
    step_mesh_check,
    step_bind_images,
    step_tool_settings,
)


class CPP_OT_enter_context(bpy.types.Operator):
    bl_idname = "cpp.enter_context"
    bl_label = "Setup Context"
    bl_options = {'INTERNAL'}

    __slots__ = ("timer", "progress")

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

        wm.cpp.invoke_progress(context, 0, 5)

        self.progress = utils.progress.invoke_progress(context, steps_count=len(func_steps))

        # Object check
        if not _check(context.active_object):
            A_ob = get_valid_mesh_object(context)
            if A_ob:
                context.view_layer.objects.active = A_ob

        if not _check(context.active_object):
            self.progress.text = 'Import FBX'
            self.progress.icon = 'IMPORT'
            bpy.ops.cpp.io_fbx('INVOKE_DEFAULT')
        else:
            self.progress.step = 1

        self.progress.ui_cancel_button = 'ESC'

        wm.modal_handler_add(self)
        self.timer = wm.event_timer_add(time_step=1 / 60, window=context.window)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self.timer)
        utils.progress.end_progress(context, self.progress)
        context.window.cursor_modal_restore()

    def modal(self, context, event):
        wm = context.window_manager

        if wm.cpp.import_state == 'FILESELECT':
            return {'PASS_THROUGH'}
        elif event.type != 'TIMER':
            return {'RUNNING_MODAL'}
        elif event.type == 'ESC' and event.value == 'PRESS':
            self.cancel(context)
            return {'CANCELLED'}

        pstep = utils.progress.modal_progress(context, self.progress)
        if pstep == -1:
            return {'RUNNING_MODAL'}
        elif pstep == -2:
            wm.event_timer_remove(self.timer)
            utils.progress.end_progress(context, self.progress)
            context.window.cursor_modal_restore()
            return {'FINISHED'}

        elif pstep < len(func_steps):
            return func_steps[pstep](self, context, event)

        # It would newer be happen
        self.cancel(context)
        return {'CANCELLED'}
