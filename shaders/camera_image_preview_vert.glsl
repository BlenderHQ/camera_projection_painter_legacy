uniform mat4 ModelViewProjectionMatrix;
uniform mat4 model_matrix;

uniform float sensor_size;
uniform vec2 aspect_scale;
uniform vec2 uv_aspect_scale;
uniform vec2 shift;
uniform float cameras_viewport_size;

in vec3 pos;
in vec2 uv;

out vec2 uvInterp;

void main()
{
    uvInterp = uv;
    if (uv_aspect_scale.x != 1.0) {
        uvInterp.x += 0.25;
    }
    else if (uv_aspect_scale.y != 1.0) {
        uvInterp.y += 0.25;
    }
    uvInterp *= uv_aspect_scale;

    vec3 p = pos;
    
    p.z *= sensor_size;
    p.xy *= aspect_scale;
    p.xy += shift;
    p *= cameras_viewport_size;

    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(p, 1.0);
}