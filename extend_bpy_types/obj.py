# <pep8 compliant>

from bpy.types import PropertyGroup
from bpy.props import BoolProperty


class ObjectProperties(PropertyGroup):
    """
    Contains properties and methods related to the Object
    """
    initial_hide_viewport: BoolProperty(default=True, options={'HIDDEN'})
