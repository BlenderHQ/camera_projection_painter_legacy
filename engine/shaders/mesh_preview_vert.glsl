uniform mat4 ModelViewProjectionMatrix;
uniform mat4 proj_MVP;
uniform mat4 model_matrix;

in vec3 pos;
in vec3 normal;

out vec2 _pos_interp;
out vec3 _nrm_interp;


void main()
{
    vec4 HP = proj_MVP * model_matrix * vec4(pos, 1.0f);
    _pos_interp = vec2(HP.x / HP.w + 0.5f, HP.y / HP.w + 0.5f);
    _nrm_interp = vec3(model_matrix * vec4(normal, 1.0f));
    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(pos, 1.0f);
}