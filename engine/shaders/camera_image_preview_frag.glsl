uniform sampler2D image;
uniform vec4 image_space_color;

in vec2 uvInterp;
out vec4 fragColor;

void main()
{
    fragColor = blender_srgb_to_framebuffer_space(texture(image, undistorted_uv(uvInterp)));
    if (fragColor.a < 0.95f){
        fragColor = image_space_color;
    }
}