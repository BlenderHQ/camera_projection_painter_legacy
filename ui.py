from . import operators
from . import poll

if "bpy" in locals():
    import importlib
    importlib.reload(operators)
    importlib.reload(poll)

import bpy
from mathutils import Vector

import os
import math

COMPAT_MODES = frozenset({'OBJECT', 'PAINT_TEXTURE'})


def progress_draw(self, context):
    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False
    wm = context.window_manager

    ui_cancel_button = wm.cpp.p_ui_cancel_button
    if ui_cancel_button and ui_cancel_button != 'NONE':
        layout.label(text="Cancel", icon=f"EVENT_{ui_cancel_button}")

    layout.separator_spacer()

    row = layout.row(align=True)
    row.label(text=wm.cpp.p_text, icon=wm.cpp.p_icon)
    srow = row.row(align=True)
    srow.enabled = True
    srow.ui_units_x = 6
    srow.prop(wm.cpp, "progress", text="")

    layout.separator_spacer()
    scene = context.scene
    view_layer = context.view_layer
    layout.label(text=scene.statistics(view_layer), translate=False)


class DATA_UL_scene_camera_item(bpy.types.UIList):
    IMAGE = 1 << 0
    NONE_IMAGE = 2 << 0
    INVALID_IMAGE = 4 << 0

    order: bpy.props.EnumProperty(
        items=[
            ('ALPHA', "", "Cameras in alphabetical order", 'SORTALPHA', 0),
            ('RADIAL', "", "Cameras ordered by world direction in XY plane", 'ORIENTATION_VIEW', 1)
        ],
        name="Filter Order",
        default='RADIAL'
    )

    filter_available: bpy.props.BoolProperty(
        name="Only Available",
        default=False,
        description="Show only cameras with binded valid images"
    )

    filter_used: bpy.props.BoolProperty(
        name="Only Used",
        default=True,
        description="Show only used cameras"
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        image = item.data.cpp.image

        is_active = active_data.active_camera_index == index
        is_image = (flt_flag & self.IMAGE)
        is_none_image = (flt_flag & self.NONE_IMAGE)
        is_invalid_image = (flt_flag & self.INVALID_IMAGE)

        if self.layout_type in {'DEFAULT', 'COMPACT', 'GRID'}:
            row = layout.row(align=True)

            row.prop(item, "initial_visible", text="")
            row.label(text=item.name)

            if is_image:
                if is_active:
                    row.label(text=image.name, icon_value=image.preview.icon_id)
                else:
                    row.prop(item.data.cpp, "image", text="", icon_value=image.preview.icon_id)

            elif is_none_image:
                row.label(icon='ERROR')

            elif is_invalid_image:
                if is_active:
                    row.label(text=image.name, icon='LIBRARY_DATA_BROKEN')
                else:
                    row.prop(item.data.cpp, "image", text="", icon='LIBRARY_DATA_BROKEN')

        # elif self.layout_type in {'GRID'}:
            # TODO: https://developer.blender.org/T75784

    def filter_items(self, context, data, propname):
        objects = getattr(data, propname)

        def _get_bitflag(ob):
            if ob.type == 'CAMERA':
                image = ob.data.cpp.image
                if image is None:
                    return self.bitflag_filter_item + self.NONE_IMAGE
                elif not image.cpp.valid:
                    return self.bitflag_filter_item + self.INVALID_IMAGE
                else:
                    return self.bitflag_filter_item + self.IMAGE
            return self.bitflag_filter_item

        flt_flags = [_get_bitflag(ob) if (ob.type == 'CAMERA') else True for ob in objects]
        flt_neworder = list(range(len(objects)))

        helper_funcs = bpy.types.UI_UL_list

        if self.order == 'RADIAL':
            camera_angles = {}
            for ob in objects:
                mat = ob.matrix_world
                x, y = -Vector([mat[0][2], mat[1][2]]).normalized()
                camera_angles[ob] = math.atan2(x, y)

            cameras_radial = [i[0] for i in sorted(camera_angles.items(), key=lambda item: item[1], reverse=False)]
            for i, ob in enumerate(objects):
                if ob.type == 'CAMERA':
                    flt_flags[i] &= _get_bitflag(ob)
                    flt_neworder[i] = cameras_radial.index(ob)

        if self.filter_name:
            for i, val in enumerate(helper_funcs.filter_items_by_name(
                    self.filter_name, self.bitflag_filter_item, objects, "name", reverse=False)):
                if val == 0:
                    flt_flags[i] &= val

        if self.filter_available or self.filter_used:
            for i, ob in enumerate(objects):
                if ob.type == 'CAMERA':
                    if self.filter_available:
                        image = ob.data.cpp.image
                        if not (image and image.cpp.valid):
                            flt_flags[i] = True
                    if self.filter_used:
                        if not ob.initial_visible:
                            flt_flags[i] = True

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "filter_available")
        col.prop(self, "filter_used")
        row = col.row(align=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "order", expand=True, emboss=True)


class DATA_UL_bind_history_item(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon_id, active_data, active_propname, index):
        row = layout.row(align=True)

        image = item.image
        if image:
            if image.cpp.valid:
                row.template_icon(icon_value=image.preview.icon_id)
            else:
                row.label(icon="LIBRARY_DATA_BROKEN")
        else:
            row.label(icon="ERROR")

        row.prop(image, "name", text="", emboss=False)

        row.emboss = 'NONE'
        row.operator(
            operator=operators.CPP_OT_bind_history_remove.bl_idname,
            text="", icon="REMOVE"
        ).index = index


class DATA_UL_node_image_item(bpy.types.UIList):
    INVALID_NODE = 1 << 0
    DISCONN_NODE = 2 << 0
    TEX_NODE = 4 << 0

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        image = item.image
        if flt_flag & self.TEX_NODE:
            icon_value = image.preview.icon_id
            row.prop(item.image, "name", icon_value=icon_value, text="", emboss=False)
        elif flt_flag & self.DISCONN_NODE:
            row.prop(item.image, "name", icon='TEXTURE', text="", emboss=False)
        elif (flt_flag & self.INVALID_NODE):
            row.prop(item, "name", icon='ERROR', text="", emboss=False)

    def filter_items(self, context, data, propname):
        nodes = getattr(data, propname)
        flt_flags = [self.bitflag_filter_item] * len(nodes)
        flt_neworder = []

        for i, node in enumerate(nodes):
            if node.bl_idname == "ShaderNodeTexImage":
                image = node.image

                flt_flags[i] = self.bitflag_filter_item

                if image and image.cpp.valid:
                    for out in node.outputs:
                        if out.is_linked and len(out.links):
                            flt_flags[i] |= self.TEX_NODE
                            break
                        else:
                            flt_flags[i] |= self.DISCONN_NODE
                else:
                    flt_flags[i] = True
            else:
                flt_flags[i] = True

        return flt_flags, flt_neworder


class CPP_MT_camera_pie(bpy.types.Menu):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        col = pie.column(align=True)
        scene = context.scene
        wm = context.window_manager

        camob = wm.cpp.current_selected_camera_ob

        if not camob:
            return

        col.label(text="Camera:")
        col.emboss = 'RADIAL_MENU'
        col.label(text=camob.name)
        col.emboss = 'NORMAL'
        col = col.column(align=True)

        scene = context.scene

        col.ui_units_x = 11

        cam = camob.data
        image = cam.cpp.image

        if image:
            if image.cpp.valid:
                col.template_ID_preview(cam.cpp, "image", open="image.open", rows=4, cols=5)
            else:
                col.label(text="Invalid image", icon='LIBRARY_DATA_BROKEN')
                col.template_ID(cam.cpp, "image", open="image.open")
        else:
            col.template_ID(cam.cpp, "image", open="image.open")

        col.emboss = 'RADIAL_MENU'
        pie.operator(operator=operators.CPP_OT_bind_camera_image.bl_idname).mode = 'GS'

        if camob.initial_visible:
            text = "Disable"
            icon = 'HIDE_ON'
        else:
            text = "Enable"
            icon = 'HIDE_OFF'

        pie.operator(
            operator=operators.CPP_OT_toggle_camera_usage.bl_idname,
            text=text, icon=icon
        )

        text = None
        if scene.camera == camob:
            text = "Already active"

        pie.operator(operator=operators.CPP_OT_set_tmp_camera_active.bl_idname, text=text)


class CameraPainterPanelBase:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Painter"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode in COMPAT_MODES

    def get_col(self):
        layout = self.layout
        layout.use_property_split = False
        return layout.column(align=True)


class CPP_PT_camera_painter(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Camera Painter"
    bl_options = set()

    def draw(self, context):
        pass


class CPP_PT_dataset(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Dataset"
    bl_parent_id = "CPP_PT_camera_painter"
    bl_options = set()

    def draw(self, context):
        col = self.get_col()
        scene = context.scene

        if not poll.full_poll(context):
            scol = col.column()
            scol.scale_y = 1.5
            scol.operator(operator=operators.CPP_OT_enter_context.bl_idname)

        col.label(text="Source Images Directory:")
        row = col.row(align=True)
        row.prop(scene.cpp, "source_dir", text="", icon='IMAGE_REFERENCE')
        srow = row.row(align=True)
        srow.enabled = False
        if os.path.isdir(bpy.path.abspath(scene.cpp.source_dir)):
            srow.enabled = True
        props = srow.operator(operator="wm.path_open", text="", icon='EXTERNAL_DRIVE')
        props.filepath = scene.cpp.source_dir

        if context.mode == 'OBJECT' and scene.cpp.has_camera_objects_selected:
            col.operator(
                operator=operators.CPP_OT_bind_camera_image.bl_idname,
                text="Bind Selected Camera Images"
            ).mode = 'SELECTED'

        if scene.cpp.has_camera_objects:
            col.operator(
                operator=operators.CPP_OT_bind_camera_image.bl_idname,
                text="Bind All Camera Images"
            ).mode = 'ALL'

        col.label(text="Calibration File:")
        row = col.row(align=True)
        row.prop(scene.cpp, "calibration_source_file", text="", icon='FILE_BLANK')
        row.operator(
            operator=operators.CPP_OT_import_cameras_csv.bl_idname,
            text="",
            icon='IMPORT'
        )


class CPP_PT_canvas_texture(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Texture"
    bl_parent_id = "CPP_PT_camera_painter"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if super().poll(context) and (ob and ob.type == 'MESH'):
            return True
        return False

    def draw(self, context):
        col = self.get_col()

        ob = context.active_object
        col.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=1)
        col.template_ID(ob, "active_material", new="material.new")
        col.separator()

        mat = ob.active_material
        valid_mat = False
        if mat and mat.use_nodes:
            valid_mat = True

        if not valid_mat:
            col.label(text="Missing valid material", icon='ERROR')
            image_paint = context.scene.tool_settings.image_paint
            col.prop(image_paint, "canvas", text="Texture")
        else:
            tree = mat.node_tree
            if tree and len(list(n for n in tree.nodes if n.bl_idname == "ShaderNodeTexImage")):
                col.label(text="Textures", icon='NODE_TEXTURE')
                row = col.row(align=True)
                row.template_list(
                    "DATA_UL_node_image_item", "", tree, "nodes", tree, "active_texnode_index", rows=2
                )
            else:
                row = col.row(align=True)
                row.label(text="Missing Textures", icon='ERROR')

            row.operator_menu_enum("paint.add_texture_paint_slot", "type", icon='ADD', text="")


def _get_camera_object(context):
    ob = context.active_object
    if ob and context.mode == 'OBJECT' and ob.type == 'CAMERA':
        return context.active_object
    camob = context.scene.camera
    if camob and camob.type == 'CAMERA':
        return camob


class CPP_PT_workflow(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Workflow"
    bl_options = set()
    bl_parent_id = "CPP_PT_camera_painter"

    @classmethod
    def poll(cls, context):
        return super().poll(context) and len(context.scene.objects)

    def draw(self, context):
        col = self.get_col()
        scene = context.scene

        ui_pixel_width = [n for n in context.area.regions if n.type == 'UI'][-1].width
        num_columns = 1
        preview_size = bpy.app.render_preview_size
        ui_bias = 40

        row = col.row(align=True)
        row.separator()
        row.prop(scene.cpp, "used_all_cameras", text="")

        if ui_pixel_width > (preview_size * 4 + ui_bias):
            row.label(text="Cameras")
            num_columns = max(int((ui_pixel_width - ui_bias) / preview_size / 2), 1)

            col.template_list(
                "DATA_UL_scene_camera_item", "grid", scene, "objects", scene.cpp, "active_camera_index",
                type='GRID', columns=num_columns
            )
        else:
            row.label(text="Cameras")
            row.label(text="Images")
            col.template_list(
                "DATA_UL_scene_camera_item", "", scene, "objects", scene.cpp, "active_camera_index",
                type='DEFAULT', rows=3
            )

        camera_object = _get_camera_object(context)
        if camera_object:
            camera = camera_object.data
            image = camera.cpp.image

            if image:
                if image.cpp.valid:
                    col.template_ID_preview(camera.cpp, "image", open="image.open", rows=4, cols=5, hide_buttons=True)
                else:
                    col.label(text="Invalid image", icon='LIBRARY_DATA_BROKEN')
                    col.template_ID(camera.cpp, "image", open="image.open")
            else:
                col.template_ID(camera.cpp, "image", open="image.open")

            col.use_property_decorate = False
            col.template_list(
                "DATA_UL_bind_history_item", "",
                camera, "cpp_bind_history", camera.cpp,
                "active_bind_index",
                rows=1
            )
            props = col.operator(
                operator=operators.CPP_OT_bind_camera_image.bl_idname,
                text="Bind Image"
            )
            if context.mode == 'OBJECT':
                props.mode = 'ACTIVEOB'
            else:
                props.mode = 'SCENECAM'


class CPP_PT_camera_calibration(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Calibration"
    bl_parent_id = "CPP_PT_workflow"

    @classmethod
    def poll(cls, context):
        return (context.mode in COMPAT_MODES) and _get_camera_object(context)

    def draw(self, context):
        col = self.get_col()

        camera_object = _get_camera_object(context)
        camera = camera_object.data

        col.prop(camera, "lens")
        col.separator()
        col.prop(camera.cpp, "principal_point_x")
        col.prop(camera.cpp, "principal_point_y")
        col.separator()
        col.prop(camera.cpp, "skew")
        col.prop(camera.cpp, "aspect_ratio")


class CPP_PT_camera_lens_distortion(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Lens Distortion"
    bl_parent_id = "CPP_PT_workflow"

    @classmethod
    def poll(cls, context):
        return (context.mode in COMPAT_MODES) and _get_camera_object(context)

    def draw(self, context):
        col = self.get_col()

        camera_object = _get_camera_object(context)
        camera = camera_object.data

        col.use_property_split = True
        col.prop(camera.cpp, "camera_lens_model")
        col.use_property_split = False
        col.separator()

        clm = camera.cpp.camera_lens_model
        if clm != 'perspective':
            col.prop(camera.cpp, "k1")
            if clm != "division":
                col.prop(camera.cpp, "k2")
                col.prop(camera.cpp, "k3")
                if clm in ("brown4", "brown4t2"):
                    col.prop(camera.cpp, "k4")
                if clm in ("brown3t2", "brown4t2"):
                    col.separator()
                    col.prop(camera.cpp, "t1")
                    col.prop(camera.cpp, "t2")


class CPP_PT_view(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "View"
    bl_parent_id = "CPP_PT_camera_painter"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def draw(self, context):
        pass


class CPP_PT_texture_preview(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Texture"
    bl_parent_id = "CPP_PT_view"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def draw(self, context):
        col = self.get_col()
        col.prop(context.scene.cpp, "current_image_alpha")
        col.prop(context.scene.cpp, "current_image_size")


class CPP_PT_cameras_viewport(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Cameras"
    bl_parent_id = "CPP_PT_view"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def draw(self, context):
        col = self.get_col()
        col.prop(context.scene.cpp, "cameras_viewport_size")
        col.prop(context.scene.cpp, "camera_axes_size")


class CPP_PT_brush_preview(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Brush Preview"
    bl_parent_id = "CPP_PT_view"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def draw_header(self, context):
        self.layout.prop(context.scene.cpp, "use_projection_preview", text="")

    def draw(self, context):
        col = self.get_col()
        col.enabled = context.scene.cpp.use_projection_preview

        col.use_property_split = True
        col.prop(context.scene.cpp, "use_projection_outline")
        col.prop(context.scene.cpp, "use_normal_highlight")


class CPP_PT_warnings(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Warnings"
    bl_parent_id = "CPP_PT_view"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def draw_header(self, context):
        self.layout.prop(context.scene.cpp, "use_warnings", text="")

    def draw(self, context):
        col = self.get_col()
        col.enabled = context.scene.cpp.use_warnings

        col.prop(context.scene.cpp, "distance_warning")
        col.use_property_split = True
        col.prop(context.scene.cpp, "use_warning_action_draw")
        col.prop(context.scene.cpp, "use_warning_action_popup")
        col.prop(context.scene.cpp, "use_warning_action_lock")


class CPP_PT_brush(bpy.types.Panel, CameraPainterPanelBase):
    bl_label = "Brush"
    bl_parent_id = "CPP_PT_camera_painter"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    def draw(self, context):
        col = self.get_col()

        brush = context.tool_settings.image_paint.brush
        col.prop(brush, "size")
        col.prop(brush, "strength")
        col.separator()

        col.prop(brush, "curve_preset", text="")

        if brush.curve_preset == 'CUSTOM':
            col.template_curve_mapping(brush, "curve", brush=True)

            row = col.row(align=True)
            row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
            row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
            row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
            row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
            row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
            row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'


_classes = [
    CPP_PT_camera_painter,
    DATA_UL_scene_camera_item,
    DATA_UL_bind_history_item,
    DATA_UL_node_image_item,
    CPP_MT_camera_pie,
    CPP_PT_dataset,  # Dataset
    CPP_PT_canvas_texture,  # Texture
    CPP_PT_brush,  # Brush
    CPP_PT_workflow,  # Workflow
    CPP_PT_camera_calibration,
    CPP_PT_camera_lens_distortion,
    CPP_PT_view,  # View
    CPP_PT_texture_preview,
    CPP_PT_cameras_viewport,
    CPP_PT_brush_preview,
    CPP_PT_warnings
]

register, unregister = bpy.utils.register_classes_factory(_classes)
