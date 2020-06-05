uniform float image_width;
uniform float image_height;

uniform int lens_distortion_model;

uniform float lens;
uniform float shiftx;
uniform float shifty;
uniform float skew;
uniform float aspect_ratio;

uniform float k1;
uniform float k2;
uniform float k3;
uniform float k4;
uniform float t1;
uniform float t2;

vec2 undistorted_uv(vec2 uv_)
{
    vec2 uv = uv_;
    uv -= vec2(0.5f);

    float scaleToPixel = max(image_width, image_height);
    float focalLength = lens * scaleToPixel / 36.0f;
    float principalPointU = shiftx * scaleToPixel + image_width / 2;
    float principalPointV = shifty * scaleToPixel + image_height / 2;
    float camera_skew = skew * scaleToPixel;

    float cx, cy, x2, y2, xy2, r2, l, dcx = 0.0f, dcy = 0.0f, dcz = 0.0f, tx, ty, kr2;
    
    cx = uv[0] * image_width / focalLength;
    cy = -uv[1] * image_height / focalLength;

    if (lens_distortion_model == 2)
    {
        // Browm-Conrady distortion
        x2 = cx * cx;
        y2 = cy * cy;
        xy2 = 2 * cx * cy;

        r2 = x2 + y2;
        l = 1.0f + (((k4 * r2 + k3) * r2 + k2) * r2 + k1) * r2;

        tx = (t1 * (r2 + 2.0f * x2) + t2 * xy2);
        ty = (t2 * (r2 + 2.0f * y2) + t1 * xy2);

        dcx = (cx * l + tx);
        dcy = (cy * l + ty);
    }
    else if (lens_distortion_model == 1)
    {
        // Division model
        kr2 = 1.0f + k1 * (cx * cx + cy * cy);
        dcx = cx / kr2;
        dcy = cy / kr2;
    }
    else
    {
        // No distortion
        dcx = cx;
        dcy = cy;

    }

    uv[0] = (focalLength * dcx + camera_skew * dcy + principalPointU) / image_width;
    uv[1] = 1.0f - ((focalLength * aspect_ratio * dcy + principalPointV) / image_height);
    return uv;
}