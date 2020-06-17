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
    uvInterp = uv * uv_aspect_scale;

    vec3 hp = pos;
    
    hp.z *= sensor_size;
    hp.xy *= aspect_scale;
    hp.xy += shift;
    hp *= cameras_viewport_size;

    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(hp, 1.0);
}