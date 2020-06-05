uniform sampler2D image;
uniform vec4 image_space_color;

in vec2 uvInterp;
out vec4 frag;

void main()
{
    vec2 undist_uv = undistorted_uv(uvInterp);

    frag = blender_srgb_to_framebuffer_space(texture(image, undist_uv));
    if (frag.a < 0.95f){
        frag = image_space_color;
    }

}