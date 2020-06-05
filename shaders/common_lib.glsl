#define PI 3.14159265358979323846

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

bool inside_rect(vec2 _coo, vec2 _bottom_left, vec2 _top_right) {
    vec2 st = step(_bottom_left, _coo) - step(_top_right, _coo);
    float inside = st.x * st.y;
    if (inside == 0.0) {
        return false;
    }
    else {
        return true;
    }
}

bool inside_outline(in vec2 _coo, in float _width, in vec2 _scale) {
    vec2 sw = _scale * vec2(_width);
    return inside_rect(_coo, -sw, vec2(1.0) + sw);
}

