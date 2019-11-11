uniform vec3 projectorForward;

uniform sampler2D sourceImage;
uniform sampler2D brushImage;

uniform vec2 sourceScale;

uniform int outlineType;
uniform vec4 outlineColor;
uniform float outlineWidth;
uniform float outlineScale;

uniform int useOutlineText;
uniform float outlineTextAspect;
uniform float outlineTextScale;

uniform int useNormalInspection;
uniform vec4 normalHighlightColor;

uniform vec2 mousePos;
uniform int useBrush;
uniform float brushRadius;
uniform float brushStrength;

uniform int warning;
uniform vec4 warningColor;

in vec2 posInterp;
in vec3 nrmInterp;

out vec4 fragColor;// Output


float inside_rect(vec2 _coo, vec2 _bottom_left, vec2 _top_right)
{
    vec2 st = step(_bottom_left, _coo) - step(_top_right, _coo);
    return st.x * st.y;
}

float inside_outline(in vec2 _coo, in float _width, in vec2 _scale)
{
    float inside_image = inside_rect(_coo, vec2(0.0), vec2(1.0));
    vec2 sw = _scale * vec2(_width);
    float inside = inside_rect(_coo, -sw, vec2(1.0) + sw);
    return (1.0 - inside_image) * inside;
}

float checker_pattern(in vec2 _coo, in vec2 _scale, in float _check_size)
{
    float fmod_result = (mod(floor(_check_size * _scale.y * _coo.x) +
    floor(_check_size * _scale.x * _coo.y), 2.0));
    float checker = clamp(fmod_result, 0.0, 1.0);
    return checker;
}


void main()
{
    vec4 textureSource;
    float brushMask;
    vec2 brushCoord;

    float imageFrameMask = inside_rect(posInterp, vec2(0.0), vec2(1.0));

    if (useBrush != 0)
    {
        float dist = distance((gl_FragCoord.xy - mousePos) / vec2(brushRadius), vec2(0.0));
        brushCoord = vec2(dist, 0.0);
        if (dist <= 1.0)
        {
            brushMask = texture(brushImage, brushCoord).r;
            textureSource = texture(sourceImage, posInterp);
        }
    }


    // Normal inspection
    vec4 fragNormalInspection;
    float normalInspectionFactor = 35.0;

    if (useNormalInspection != 0)
    {
        float nrmDot = 1.0 - clamp(dot(nrmInterp, projectorForward) / normalInspectionFactor, 0.0, 1.0);
        float fac = imageFrameMask * nrmDot;
        fragNormalInspection = normalHighlightColor * fac;
    }

    // Outline
    vec4 fragOutline;
    float outlinePattern;

    if (outlineType == 1)// Fill color
    {
        outlinePattern = 1.0;
    }
    else if (outlineType == 2)// Checher pattern
    {
        outlinePattern = checker_pattern(posInterp, sourceScale, outlineScale);
    }

    if (outlineType != 0)
    {
        float outlineMask = inside_outline(posInterp, outlineWidth, sourceScale);
        fragOutline = outlineColor;
        fragOutline *= outlineMask * outlinePattern;
    }

    vec4 overlay = fragNormalInspection + fragOutline;
    fragColor = overlay;
    if (useBrush != 0)
    {
        if (brushMask != 0.0)
        {
            if (warning != 0)
            {
                fragColor = warningColor;
            }
            else
            {
                float opacity = clamp(brushStrength * brushMask, 0.0, 1.0);
                vec4 texture = textureSource;
                texture.a = opacity;
                overlay *= 1.0 - opacity;
                fragColor = texture + overlay;
            }
        }
    }
}