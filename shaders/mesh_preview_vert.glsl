uniform mat4 ModelViewProjectionMatrix;

uniform mat4 model_matrix;
uniform vec3 projector_position;
uniform vec3 projector_forward;
uniform vec3 projector_up_axis;
uniform float wh_div;

in vec3 pos;
in vec3 normal;

out vec2 _pos_interp;
out vec3 _nrm_interp;

vec2 project(in vec3 _coord, in mat4 _mat, in vec3 _p_position, in vec3 _p_forward, in vec3 _p_up, in float _aspect) {
    vec3 interp = vec3(_mat * vec4(_coord, 1.0));

    vec3 sub1 = _p_position - _p_forward;
    vec3 cp1 = cross(sub1, _p_up);
    vec3 sub2 = interp - _p_position;

    float div1 = dot(sub1, sub2) / dot(sub1, sub1);
    float div2 = dot(normalize(cross(cp1, sub1)), sub2) / div1;
    float div3 = dot(normalize(cp1), sub2) / div1;

    vec2 projected = (vec2(div3, div2 * - _aspect)) + vec2(0.5, 0.5);
    return projected;
}

void main()
{
    _pos_interp = project(pos, model_matrix, projector_position, projector_forward, projector_up_axis, wh_div);
    _nrm_interp = vec3(model_matrix * vec4(normal, 1.0));

    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(pos, 1.0);
}