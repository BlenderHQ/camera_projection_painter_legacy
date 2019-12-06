uniform sampler2D image;
uniform float alpha;

uniform bool colorspace_srgb;

in vec2 uvInterp;
out vec4 fragColor;

void main()
{
    vec4 imageTexture = texture(image, uvInterp);
    imageTexture.a *= alpha;

    if (colorspace_srgb == false) {
        fragColor = imageTexture;
    }
    else {
        fragColor = linearrgb_to_srgb(imageTexture);
    }
}