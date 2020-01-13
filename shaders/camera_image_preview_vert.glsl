uniform mat4 ModelViewProjectionMatrix;
uniform mat4 model_matrix;
uniform float cameras_viewport_size;
uniform float camera_lens_size;
uniform vec2 image_aspect_scale;

in vec3 pos;
in vec2 uv;

out vec2 uvInterp;

void main()
{
    uvInterp = uv;
    if (image_aspect_scale.x != 1.0) {
        uvInterp.x += 0.25;
        uvInterp.x *= image_aspect_scale.x;
    }
    else if (image_aspect_scale.y != 1.0) {
        uvInterp.y += 0.25;
        uvInterp.y *= image_aspect_scale.y;
    }

    vec3 P = pos * cameras_viewport_size;
    P.z *= camera_lens_size;
    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(P.x * image_aspect_scale.x, P.y * image_aspect_scale.y, P.z, 1.0);
}