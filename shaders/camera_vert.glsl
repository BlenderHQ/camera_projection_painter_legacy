uniform mat4 ModelViewProjectionMatrix;
uniform mat4 modelMatrix;
uniform float display_size;
uniform vec2 scale;

in vec3 pos;

void main()
{
    vec3 P = pos * display_size;
    gl_Position = ModelViewProjectionMatrix * modelMatrix * vec4(P.x * scale.x, P.y * scale.y, P.z, 1.0);
}
