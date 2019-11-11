uniform sampler2D image;
in vec2 uvInterp;
out vec4 frag;

void main()
{
    frag = texture(image, uvInterp);
}