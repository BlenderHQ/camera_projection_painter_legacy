uniform sampler2D image;
uniform float alpha;

in vec2 uvInterp;
out vec4 frag;

void main()
{
    frag = texture(image, uvInterp);
    frag.a *= alpha;
}