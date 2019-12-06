uniform vec4 color;
out vec4 fragColor;

void main()
{
    fragColor = linearrgb_to_srgb(color);
}