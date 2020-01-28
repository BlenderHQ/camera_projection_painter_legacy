uniform mat4 ModelViewProjectionMatrix;
uniform mat4 model_matrix;
uniform mat4 camera_model_matrix;

uniform vec2 image_aspect_scale;

uniform vec2 shift;


uniform vec3 camera_position;
uniform vec3 camera_forward;
uniform vec3 camera_up;

in vec3 pos;
in vec3 normal;

out vec2 _pos_interp;
out vec3 _nrm_interp;


out vec2 wh_div;


void main()
{
    
    vec2 aspect = image_aspect_scale;

    vec3 interp = vec3(model_matrix * vec4(pos, 1.0));

    vec3 sub1 = camera_forward;
    vec3 cp1 = cross(sub1, camera_up);
    vec3 sub2 = interp - camera_position;

    float div1 = dot(sub1, sub2) / dot(sub1, sub1);
    float div2 = (dot(normalize(cross(cp1, sub1)), sub2) / div1) - shift.y;
    float div3 = (dot(normalize(cp1), sub2) / div1) - shift.x;

    _pos_interp = vec2((div3 * aspect.x) + 0.5, (div2 * aspect.y) + 0.5);

    
    wh_div = aspect;

    _nrm_interp = vec3(model_matrix * vec4(normal, 1.0));

    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(pos, 1.0);
}