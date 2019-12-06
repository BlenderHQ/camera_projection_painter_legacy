uniform vec3 projectorForward;

uniform sampler2D sourceImage;
uniform sampler2D brushImage;

uniform vec2 sourceScale;

uniform int outlineType;
uniform vec4 outlineColor;
uniform float outlineWidth;
uniform float outlineScale;


uniform int useNormalInspection;
uniform vec4 normalHighlightColor;

uniform vec2 mousePos;
uniform int useBrush;
uniform float brushRadius;
uniform float brushStrength;

uniform int fullDraw;

uniform int warning;
uniform vec4 warningColor;

uniform bool colorspace_srgb;

in vec2 posInterp;
in vec3 nrmInterp;

out vec4 fragColor;


void main() {
    float imageFrameMask = inside_rect(posInterp, vec2(0.0), vec2(1.0)); // Inside draw preview, outside draw outline

    if (imageFrameMask != 0.0) {
        vec4 textureSource;
        vec2 brushCoord;
        float brushMask;

        if (useBrush != 0 || fullDraw == 1) {
            float dist = distance((gl_FragCoord.xy - mousePos) / vec2(brushRadius), vec2(0.0));
            brushCoord = vec2(dist, 0.1);
            if (dist < 0.96 || fullDraw == 1) {
                brushMask = texture(brushImage, brushCoord).r;

                if (colorspace_srgb == false) {
                    textureSource = texture(sourceImage, posInterp);
                }
                else {
                    textureSource = linearrgb_to_srgb(texture(sourceImage, posInterp));
                }
            }
        }

        vec4 fragNormalInspection;
        float normalInspectionFactor = 35.0;

        if (useNormalInspection != 0) {
            float nrmDot = 1.0 - clamp(dot(nrmInterp, projectorForward) / normalInspectionFactor, 0.0, 1.0);
            fragNormalInspection = linearrgb_to_srgb(normalHighlightColor) * nrmDot;
        }

        float opacity = 1.0;
        if (fullDraw == 0) {
            opacity = clamp(brushStrength * brushMask, 0.0, 1.0);
        }
        if (useBrush != 0 || fullDraw == 1) {
            if (warning != 0 && fullDraw == 0) {
                fragColor = linearrgb_to_srgb(warningColor * opacity);
            }
            else {
                textureSource.a *= opacity;
                fragColor = premultiplied_alpha_blend(textureSource, fragNormalInspection);
            }
        }
        else {
            fragColor = fragNormalInspection;
        }
    }
    else {
        vec4 fragOutline;
        float outlinePattern;

        if (outlineType == 1) {
            outlinePattern = 1.0;
        }
        else if (outlineType == 2) {
            outlinePattern = checker_pattern(posInterp, sourceScale, outlineScale);
        }
        else if (outlineType == 3) {
            outlinePattern = lines_pattern(posInterp, sourceScale, outlineScale);
        }
        if (outlineType != 0) {
            float outlineMask = inside_outline(posInterp, outlineWidth, sourceScale);
            fragColor = linearrgb_to_srgb(outlineColor);
            fragColor.a *= outlineMask * outlinePattern;
        }
    }
}