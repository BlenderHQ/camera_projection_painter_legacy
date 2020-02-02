import bpy
scene = bpy.context.scene
cpp = scene.cpp

cpp.mapping = 'UV'
cpp.use_auto_set_image = True
cpp.auto_set_camera_method = 'DIRECTION'
cpp.use_projection_preview = True
cpp.use_projection_outline = True
cpp.use_normal_highlight = False
cpp.use_camera_image_previews = False
cpp.use_camera_axes = False
cpp.use_current_image_preview = True
cpp.use_warnings = True
cpp.use_warning_action_draw = True
cpp.use_warning_action_popup = False
cpp.use_warning_action_lock = True
cpp.use_bind_canvas_diffuse = False
