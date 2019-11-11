# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


import gpu
import os
from ..constants import (
    SHADER_EXTENSION,
    SEPARATOR,
    SHADER_VERTEX,
    SHADER_FRAGMENT,
    SHADER_GEOMETRY,
    SHADER_DEFINES,
    SHADER_LIBRARY)

__all__ = ["generate_shaders", "shaders"]


def generate_shaders():
    directory = os.path.dirname(__file__)

    shader_endings = (
        SHADER_VERTEX,
        SHADER_FRAGMENT,
        SHADER_GEOMETRY,
        SHADER_DEFINES,
        SHADER_LIBRARY)

    _shader_dict = {}
    _shader_library = ""

    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if not os.path.isfile(file_path):
            continue
        file_name, extension = file.split(".")
        if extension != SHADER_EXTENSION:
            continue
        name_split = file_name.split(SEPARATOR)
        if len(name_split) == 1:
            raise NameError("Shader name must be name_type.glsl pattern")
        if len(name_split) == 2:
            shader_name, shader_type = name_split
        else:
            shader_type = name_split[-1]
            shader_name = SEPARATOR.join(name_split[:-1])
        if shader_type in shader_endings[0:2]:
            if shader_name not in _shader_dict:
                _shader_dict[shader_name] = [None for _ in range(5)]

            shader_index = shader_endings.index(shader_type)
            with open(file_path, 'r') as code:
                data = code.read()

                _shader_dict[shader_name][shader_index] = data

        elif shader_type == SHADER_LIBRARY:  # TODO: Usage of shader libraries
            with open(file_path, 'r') as code:
                data = code.read()
                _shader_library += "\n\n%s" % data

        elif shader_type == SHADER_DEFINES:  # TODO: Usage of defines
            pass

    _res = {}
    for shader_name in _shader_dict.keys():
        shader_code = _shader_dict[shader_name]
        vertex_code, frag_code, geo_code, lib_code, defines = shader_code
        if _shader_library:
            lib_code = _shader_library

        kwargs = {"vertexcode": vertex_code,
                  "fragcode": frag_code,
                  "geocode": geo_code,
                  "libcode": lib_code,
                  "defines": defines}

        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
        data = gpu.types.GPUShader(**kwargs)
        _res[shader_name] = data

    return _res


class ShaderStorage(object):
    def __init__(self):
        for shader_name, data in generate_shaders().items():
            object.__setattr__(self, shader_name, data)

        self.builtin_3d_smooth_color = gpu.shader.from_builtin('3D_SMOOTH_COLOR')


shaders = ShaderStorage()
