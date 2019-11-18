uniform mat4 ModelViewProjectionMatrix;
uniform mat4 ModelMatrix;


in vec3 pos;
in vec2 unique_uv;
in vec3 normal;

out vec2 posInterp;
out vec3 nrmInterp;

void main()
{
    posInterp = unique_uv;
    nrmInterp = vec3(ModelMatrix * vec4(normal, 1.0));

    gl_Position = ModelViewProjectionMatrix * ModelMatrix * vec4(pos, 1.0);
}