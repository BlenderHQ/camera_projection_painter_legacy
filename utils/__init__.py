# <flake8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(common)
    importlib.reload(poll)

    del importlib
else:
    from . import common
    from . import poll

import bpy
