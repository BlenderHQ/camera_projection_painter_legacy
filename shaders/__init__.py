# <pep8 compliant>

import gpu
import os

SEPARATOR = "_"

SHADER_EXTENSION = "glsl"
SHADER_VERTEX = "vert"
SHADER_FRAGMENT = "frag"
SHADER_GEOMETRY = "geom"
SHADER_DEFINES = "def"
SHADER_LIBRARY = "lib"


def _generate_shaders():
    directory = os.path.dirname(__file__)

    shader_endings = (
        SHADER_VERTEX,
        SHADER_FRAGMENT,
        SHADER_GEOMETRY,
        SHADER_DEFINES,
        SHADER_LIBRARY)

    _shader_dict = {}
    _shader_library = ""
    _defines_library = ""

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

        elif shader_type == SHADER_LIBRARY:
            with open(file_path, 'r') as code:
                data = code.read()
                _shader_library += "\n\n%s" % data

        elif shader_type == SHADER_DEFINES:  # TODO: Usage of defines
            with open(file_path, 'r') as code:
                data = code.read()
                _defines_library += "\n\n%s" % data

    _res = {}
    for shader_name in _shader_dict.keys():
        shader_code = _shader_dict[shader_name]
        vertex_code, frag_code, geo_code, lib_code, defines = shader_code
        if _shader_library:
            lib_code = _shader_library
        if _defines_library:
            defines = _defines_library
        kwargs = {"vertexcode": vertex_code,
                  "fragcode": frag_code,
                  "geocode": geo_code,
                  "libcode": lib_code,
                  "defines": defines}

        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
        try:
            data = gpu.types.GPUShader(**kwargs)
            _res[shader_name] = data
        except:
            print(shader_name)

    return _res


class ShaderStorage(object):
    def __init__(self):
        for shader_name, data in _generate_shaders().items():
            object.__setattr__(self, shader_name, data)

        self.builtin_3d_uniform_color = gpu.shader.from_builtin('3D_UNIFORM_COLOR')


shaders = ShaderStorage()
