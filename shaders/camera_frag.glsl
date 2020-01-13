uniform vec4 wire_color;
out vec4 fragColor;

void main()
{
    fragColor = linearrgb_to_srgb(wire_color);
}