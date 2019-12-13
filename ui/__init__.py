# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(templates)
    importlib.reload(camera)
    importlib.reload(scene)
    importlib.reload(image_paint)
    importlib.reload(context_menu)

    del importlib
else:
    from . import templates
    from . import camera
    from . import scene
    from . import image_paint
    from . import context_menu

import bpy
