uniform mat4 ModelViewProjectionMatrix;
uniform mat4 modelMatrix;
uniform float display_size;
uniform vec2 scale;

in vec3 pos;
in vec2 uv;

out vec2 uvInterp;

void main()
{
    uvInterp = vec2(uv.x * scale.x, (0.25 + uv.y) * scale.y);

    vec3 P = pos * display_size;
    gl_Position = ModelViewProjectionMatrix * modelMatrix * vec4(P.x * scale.x, P.y * scale.y, P.z, 1.0);
}