#define PI 3.14159265358979323846

float linearrgb_to_srgb(float c) {
    if (c < 0.0031308) {
        return (c < 0.0) ? 0.0 : c * 12.92;
    }
    else {
        return 1.055 * pow(c, 1.0 / 2.4) - 0.055;
    }
}

vec4 linearrgb_to_srgb(vec4 col_from) {
    // Convert color from linear to sRGB
    return vec4(
    linearrgb_to_srgb(col_from.r),
    linearrgb_to_srgb(col_from.g),
    linearrgb_to_srgb(col_from.b),
    col_from.a);
}

vec2 rotate2D(vec2 _st, float _angle) {
    // Rotate 2d vec2
    _st -= 0.5;
    _st =  mat2(cos(_angle), -sin(_angle),
    sin(_angle), cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

vec4 premultiplied_alpha_blend(vec4 src, vec4 dst) {
    // https://en.wikipedia.org/wiki/Alpha_compositing
    float final_alpha = src.a + dst.a * (1.0 - src.a);
    return vec4(
    (src.rgb * src.a + dst.rgb * dst.a * (1.0 - src.a)) / final_alpha,
    final_alpha
    );
}

float inside_rect(vec2 _coo, vec2 _bottom_left, vec2 _top_right) {
    vec2 st = step(_bottom_left, _coo) - step(_top_right, _coo);
    return st.x * st.y;
}

float inside_outline(in vec2 _coo, in float _width, in vec2 _scale) {
    float inside_image = inside_rect(_coo, vec2(0.0), vec2(1.0));
    vec2 sw = _scale * vec2(_width);
    float inside = inside_rect(_coo, -sw, vec2(1.0) + sw);
    return (1.0 - inside_image) * inside;
}