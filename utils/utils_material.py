import bpy
from mathutils import Vector

SPACE_BEETWEEN_NODES = 50
FRAME_TEXT = "Camera Painter Added"
FRAME_COLOR = (0.5, 0.6, 0.8)


def basic_setup_material(self, ob, target_image, create_new_material = False):
    if create_new_material:
        material = bpy.data.materials.new(target_image.name)
        ob.data.materials.append(material)
        ob.active_material = material

    if not ob.active_material:
        self.report(type = {'WARNING'}, message = "Object have no active material!")
        return

    material = ob.active_material

    material.use_nodes = True
    node_tree = material.node_tree

    nodes = node_tree.nodes

    # get active output
    active_output = None

    for node in nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial":
            if node.is_active_output:
                active_output = node
                break
    if not active_output:
        self.report(type = {'WARNING'}, message = "Node tree has no active output!")
        return

    _node = active_output
    _index = 0
    _socket = None
    _cou = len(nodes)
    while _cou:
        if _node.bl_idname == "ShaderNodeTexImage":
            break
        for i, socket in enumerate(_node.inputs):
            if socket.bl_idname in ("NodeSocketColor", "NodeSocketShader"):
                if socket.is_linked:
                    _node = socket.links[0].from_node
                else:
                    _socket = socket
                    _index = i
                break
        _cou += -1

    if _node.bl_idname != "ShaderNodeTexImage" and _socket:
        node_frame = None
        for n in nodes:
            if n.label == FRAME_TEXT:
                node_frame = n
        if not node_frame:
            node_frame = node_tree.nodes.new(type = "NodeFrame")

        node_frame.label = FRAME_TEXT
        node_frame.use_custom_color = True
        node_frame.color = FRAME_COLOR
        node_frame.select = False

        def _add_node(type, next_node, index):
            new_node = node_tree.nodes.new(type = type)
            new_node.location = Vector(next_node.location) - Vector([new_node.width + SPACE_BEETWEEN_NODES, 0])
            new_node.parent = node_frame
            new_node.select = False
            node_tree.links.new(new_node.outputs[0], next_node.inputs[index])
            return new_node

        if _socket.bl_idname == "NodeSocketShader":
            bsdf_node = _add_node("ShaderNodeBsdfPrincipled", _node, _index)

            _node = bsdf_node
            _index = 0
            _socket = [i for i in bsdf_node.inputs if i.bl_idname == "NodeSocketColor"][0]

        if _socket.bl_idname == "NodeSocketColor":
            tex_image_node = _add_node("ShaderNodeTexImage", _node, _index)

            _node = tex_image_node

    if _node.bl_idname == "ShaderNodeTexImage":
        _node.image = target_image
