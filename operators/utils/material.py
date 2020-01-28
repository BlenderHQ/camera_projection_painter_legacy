import bpy
from mathutils import Vector


SPACE_BEETWEEN_NODES = 50
NODE_FRAME_TEXT = "Camera Painter Added"
NODE_FRAME_COLOR = (0.5, 0.6, 0.8)


def get_nodes_active_output(nodes: bpy.types.bpy_prop_collection):
    """Returns the active output from the node tree nodes"""
    for node in nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial":
            if node.is_active_output:
                return node


def nodes_recursive_search(nodes: bpy.types.bpy_prop_collection, active_output: bpy.types.Node):
    """
    Returns data about a node, its input (color or shader),
    its index from the node tree by searching from the active output
    """
    current_node = active_output
    current_node_index = 0
    current_input_socket = None
    nodes_count = len(nodes)

    while nodes_count > 1:
        if current_node.bl_idname == "ShaderNodeTexImage":
            break
        for i, current_input_socket in enumerate(current_node.inputs):
            if current_input_socket.bl_idname in ("NodeSocketColor", "NodeSocketShader"):
                if current_input_socket.is_linked:
                    current_node = current_input_socket.links[0].from_node
                else:
                    current_input_socket = current_input_socket
                    current_node_index = i
                break
        nodes_count -= 1

    return current_node, current_input_socket, current_node_index


def set_canvas_to_material_diffuse(material: bpy.types.Material, image: bpy.types.Image):
    """Sets canvas as a diffuse texture of the active material"""
    material.use_nodes = True
    material_node_tree = material.node_tree

    nodes = material_node_tree.nodes

    active_output = get_nodes_active_output(nodes)
    if not active_output:
        active_output = material_node_tree.nodes.new(type="ShaderNodeOutputMaterial")

    current_node, current_input_socket, current_node_index = nodes_recursive_search(nodes, active_output)

    if current_node.bl_idname != "ShaderNodeTexImage" and current_input_socket:
        # Frame around created nodes
        node_frame = None
        for node in nodes:
            if node.label == NODE_FRAME_TEXT:
                node_frame = node
        if not node_frame:
            node_frame = material_node_tree.nodes.new(type="NodeFrame")

        node_frame.label = NODE_FRAME_TEXT
        node_frame.use_custom_color = True
        node_frame.color = NODE_FRAME_COLOR
        node_frame.select = False

        def create_node(node_type, next_node, node_index):
            """Function to add nodes"""
            new_node = material_node_tree.nodes.new(node_type=node_type)
            new_node_location = Vector(next_node.location) - Vector([new_node.width + SPACE_BEETWEEN_NODES, 0])
            new_node.location = new_node_location
            new_node.parent = node_frame
            new_node.select = False
            material_node_tree.links.new(new_node.outputs[0], next_node.inputs[node_index])
            return new_node

        # In case there was a Shader input
        if current_input_socket.bl_idname == "NodeSocketShader":
            new_bsdf_node = create_node("ShaderNodeBsdfPrincipled", current_node, current_node_index)

            current_node = new_bsdf_node
            current_node_index = 0
            current_input_socket = [n for n in new_bsdf_node.inputs if n.bl_idname == "NodeSocketColor"][0]

        # In case there was a Color input
        if current_input_socket.bl_idname == "NodeSocketColor":
            new_tex_image_node = create_node("ShaderNodeTexImage", current_node, current_node_index)

            current_node = new_tex_image_node

    # If TexImage node is found
    if current_node.bl_idname == "ShaderNodeTexImage":
        current_node.image = image
        return -1
    return 0


def search_diffuse_node(material: bpy.types.Material):
    node_tree = material.node_tree
    nodes = node_tree.nodes

    active_output = get_nodes_active_output(nodes)
    if not active_output:
        return 1
    node = nodes_recursive_search(nodes, active_output)[0]

    if node.bl_idname == "ShaderNodeTexImage":
        return node


def set_material_diffuse_to_canvas(image_paint: bpy.types.ImagePaint, material: bpy.types.Material):
    """Sets the diffuse texture of the active material as canvas"""

    diffuse_node = search_diffuse_node(material)

    if diffuse_node:
        image = diffuse_node.image
        if image and image.cpp.valid:
            image_paint.canvas = image
            return -1
        else:
            return 2
    return 3
