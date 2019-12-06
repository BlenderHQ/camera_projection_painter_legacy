// PI defined in common_lib

float checker_pattern(in vec2 _coo, in vec2 _scale, in float _check_size) {
    float fmod_result = (mod(floor(_check_size * _scale.y * _coo.x) +
    floor(_check_size * _scale.x * _coo.y), 2.0));
    float checker = clamp(fmod_result, 0.0, 1.0);
    return checker;
}

float lines_pattern(in vec2 _coo, in vec2 _scale, in float _check_size) {
    vec2 _rcoo = rotate2D(_coo, PI * 0.25);
    float fmod_result = (mod(floor(_check_size * _scale.y * _rcoo.x * 4.0), 2.0));
    float pattern = clamp(fmod_result, 0.0, 1.0);
    return pattern;
}