uniform mat4 ModelViewProjectionMatrix;

uniform mat4 model_matrix;
uniform vec3 projector_position;
uniform vec3 projector_forward;
uniform vec3 projector_up_axis;
uniform vec2 aspect;

in vec3 pos;
in vec3 normal;

out vec2 _pos_interp;
out vec3 _nrm_interp;

vec2 project(in vec3 coo, in mat4 mat, in vec3 ppos, in vec3 pdir, in vec3 pup, in vec2 sscale)
{
    vec3 interpolation = vec3(mat * vec4(coo, 1.0));

    vec3 sub1 = ppos - pdir;
    vec3 cp1 = cross(sub1, pup);
    vec3 sub2 = interpolation - ppos;

    float div1 = dot(sub1, sub2) / dot(sub1, sub1);
    float div2 = dot(normalize(cross(cp1, sub1)), sub2) / div1;
    float div3 = dot(normalize(cp1), sub2) / div1;

    vec2 projected = (vec2(div3 * sscale.x, div2 * - sscale.y)) + vec2(0.5, 0.5);
    return projected;
}

void main()
{
    _pos_interp = project(pos, model_matrix, projector_position, projector_forward, projector_up_axis, aspect);
    _nrm_interp = vec3(model_matrix * vec4(normal, 1.0));

    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(pos, 1.0);
}