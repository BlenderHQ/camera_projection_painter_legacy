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

import bpy

# Tuple of tuples ((msgctxt, msgid), (sources, gen_comments), (lang, translation, (is_fuzzy, comments)), ...)

translations_tuple = (
    # bpy.types.Camera.cpp
    (("*", "used"),
     (("bpy.types.CPP_PT_cpp_camera_options",),
      ()),
     ("ru", "Использовать",
      (False, ())),
     ),

    (("*", "Use camera as a projector"),
     (("bpy.types.Camera.cpp",),
      ()),
     ("ru", "Использовать камеру в качестве прожектора",
      (False, ())),
     ),

    # bpy.types.Scene.cpp
    (("CPP", "Source Images Directory"),
     (("bpy.types.Scene.cpp",),
      ()),
     ("ru", "Директория",
      (False, ())),
     ),

    (("*", "Path to source images used. "
           "If image named same as object not found in packed images, "
           "operator search images there and open them automatically"),
     (("bpy.types.Scene.cpp",),
      ()),
     ("ru", "Директория с используемыми изображениями. "
            "Используется для автоматической привязки изображения к камерам. "
            "Если не найдены совпадения (имя камеры - имя изображения), "
            "оператор продолжит поиск в данной директории. В случае совпадения - "
            "откроет изображение",
      (False, ())),
     ),

    # Operators
    (("Operator", "Bind Image By Name"),
     (("bpy.types.CPP_OT_bind_camera_image",),
      ()),
     ("ru", "Привязка Изображения По Имени",
      (False, ())),
     ),

    (("CPP", "Find image with equal name to camera name.\n" \
             "If no image packed into .blend, search in Source Images path. (See Scene tab)"),
     (("bpy.types.CPP_OT_bind_camera_image",),
      ()),
     ("ru", "Поиск изображений, соответствующих по имени имени обьекта камеры."
            "Если изображения не найдены в файле, поиск производится "
            "в указанной директории (см. настройки сцены)",
      (False, ())),
     ),

    (("CPP", "Bind Selected Camera Images"),
     (("bpy.types.CPP_PT_scene_cameras",),
      ()),
     ("ru", "Привязать К Выделенным Камерам",
      (False, ())),
     ),

    (("CPP", "Bind All Camera Images"),
     (("bpy.types.CPP_PT_scene_cameras",),
      ()),
     ("ru", "Привязать Ко Всем Камерам",
      (False, ())),
     ),

)

translations_dict = {}
for msg in translations_tuple:
    key = msg[0]
    for lang, trans, (is_fuzzy, comments) in msg[2:]:
        if trans and not is_fuzzy:
            translations_dict.setdefault(lang, {})[key] = trans


def register():
    bpy.app.translations.register(__name__, translations_dict)


def unregister():
    bpy.app.translations.unregister(__name__)
