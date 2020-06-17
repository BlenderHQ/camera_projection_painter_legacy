uniform mat4 ModelViewProjectionMatrix;
uniform mat4 modelMatrix;
uniform float camera_axes_size;

in vec3 pos;
in vec4 color;

out vec4 col_interp;

void main()
{
    col_interp = color;
    gl_Position = ModelViewProjectionMatrix * modelMatrix * vec4(pos * camera_axes_size, 1.0);
}
