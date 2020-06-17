uniform mat4 ModelViewProjectionMatrix;
uniform mat4 model_matrix;

uniform float sensor_size;
uniform vec2 aspect_scale;
uniform float cameras_viewport_size;

in vec3 pos;

void main()
{
    vec3 p = pos;
    
    if (gl_VertexID != 0) {
        p.z *= sensor_size;
        p.xy *= aspect_scale;
        p *= cameras_viewport_size;
    }
    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(p, 1.0);
}
