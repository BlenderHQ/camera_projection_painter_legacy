# <pep8 compliant>

TEMP_DATA_NAME = "cpp_temp_data"

LISTEN_TIME_STEP = 1 / 4
TIME_STEP = 1 / 60

AUTOCAM_MIN = 0.852
AUTOCAM_MAX = 0.999

SPACE_BEETWEEN_NODES = 50
NODE_FRAME_TEXT = "Camera Painter Added"
NODE_FRAME_COLOR = (0.5, 0.6, 0.8)

WEB_LINKS = [
    ("Youtube tutorial", "https://youtu.be/6ffpaG8KPJk"),
    ("GitHub", "https://github.com/ivan-perevala")
]

message_startup_help = """
Main operator can be started only after
reloading Blender or opening any *.blend file
https://docs.blender.org/api/current/bpy.app.handlers.html#bpy.app.handlers.load_post
"""

message_overwrite_ui = """
This part of UI overwriten by
Camera Projection Painter
"""
