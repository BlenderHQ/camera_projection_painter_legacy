uniform sampler2D image;
in vec2 uvInterp;
out vec4 fragColor;

void main()
{
    fragColor = texture(image, uvInterp);
    fragColor.a = 1.0;
}