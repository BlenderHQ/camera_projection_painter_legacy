uniform mat4 ModelViewProjectionMatrix;

in vec2 pos;
in vec2 uv;

out vec2 uvInterp;


void main()
{
    uvInterp = uv;
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
}
