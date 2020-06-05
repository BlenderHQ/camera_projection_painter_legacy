uniform sampler2D image;
uniform float alpha;
uniform vec4 image_space_color;

in vec2 uvInterp;
out vec4 fragColor;

void main()
{
    vec2 undist_uv = undistorted_uv(uvInterp);
    
    vec4 imageTexture = texture(image, undist_uv);
    imageTexture.a *= alpha;

    if (undist_uv[0] >= 0.0f && undist_uv[0] <= 1.0f && undist_uv[1] >= 0.0f && undist_uv[1] <= 1.0f)
    {
        fragColor = imageTexture;
    }
    else
    {
        fragColor = image_space_color;
    }
}