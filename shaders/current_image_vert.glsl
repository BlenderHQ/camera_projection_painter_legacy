uniform mat4 ModelViewProjectionMatrix;
uniform vec2 pixel_pos;
uniform vec2 pixel_size;

in vec2 pos;
in vec2 uv;

out vec2 uvInterp;

void main()
{
    uvInterp = uv;
    vec2 p = pos;

    p *= pixel_size;
    p += pixel_pos;

    gl_Position = ModelViewProjectionMatrix * vec4(p, 0.0, 1.0);
}
