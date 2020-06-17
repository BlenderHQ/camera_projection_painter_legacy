// uniform vec3 camera_forward;
// uniform bool use_projection_preview;
// uniform bool use_normal_highlight;
// uniform bool use_warnings;
// uniform bool use_warning_action_draw;
// uniform bool full_draw;
// uniform bool active_view;
// uniform bool warning_status;
// uniform sampler2D clone_image;
// uniform sampler2D brush_img;
// uniform int outline_type;
// uniform vec4 outline_color;
// uniform float outline_width;
// uniform float outline_scale;
// uniform vec4 image_space_color;
// uniform vec4 normal_highlight_color;
// uniform vec2 mouse_pos;
// uniform float brush_radius;
// uniform float brush_strength;
// uniform vec4 warning_color;
// ---------------------
// Images
uniform sampler2D image;
uniform sampler2D image_brush;

// Switches
uniform bool is_warning;
uniform bool is_active_view;
uniform bool is_full_draw;
uniform bool is_brush;
uniform bool is_normal_highlight;
uniform int outline_type;

// Colors
uniform vec4 image_space_color;
uniform vec4 warning_color;
uniform vec4 outline_color;
uniform vec4 normal_highlight_color;

// Brush
uniform vec2 mouse_pos;
uniform float brush_radius;
uniform float brush_strength;

// Outline and Highlight
uniform float outline_scale;
uniform float outline_width;
uniform vec3 camera_forward;

//
in vec2 _pos_interp;
in vec3 _nrm_interp;

out vec4 fragColor;

void main()
{
    vec2 wh_div = vec2(1.0f, 1.0f);
    if (UND_image_width > UND_image_height) {
        wh_div.y = UND_image_width / UND_image_height;
    }
    else if (UND_image_height > UND_image_width) {
        wh_div.x = UND_image_height / UND_image_width;
    }

    vec2 undist_uv = undistorted_uv(_pos_interp - vec2(0.5f));

    bool image_frame = inside_rect(_pos_interp, vec2(0.0f), vec2(1.0f)); // Inside draw preview, outside draw outline
    bool image_frame_u = inside_rect(undist_uv, vec2(0.0f), vec2(1.0f));

    vec4 frag_nm_highlight = vec4(0.0f, 0.0f, 0.0f, 1.0f);
    if (is_normal_highlight) {
        float nm_dot = clamp(dot(_nrm_interp, -camera_forward / 18.0f), 0.0f, 1.0f);
        frag_nm_highlight = normal_highlight_color;
        frag_nm_highlight.a *= nm_dot;
    }
    else {
        frag_nm_highlight.a = 0.0f;
    }
    
    if (!image_frame) {
        float outline_pattern;
            if (outline_type == 1) {
                outline_pattern = 1.0f;
            }
            else if (outline_type == 2) {
                outline_pattern = checker_pattern(_pos_interp, wh_div, outline_scale);
            }
            else if (outline_type == 3) {
                outline_pattern = lines_pattern(_pos_interp, wh_div, outline_scale);
            }
            if (outline_type != 0) {
                bool outlineMask = inside_outline(_pos_interp, outline_width, wh_div);
                bool outlineMaskFrame = inside_outline(_pos_interp, outline_width * 0.1f, wh_div);
                if (outlineMaskFrame == true) {
                    outline_pattern = 1.0;
                }
                fragColor = outline_color;
                if (outlineMask == true) {
                    fragColor.a = outline_pattern;
                }
                else {
                    fragColor = vec4(0.0f);
                }
            }
        }
    else if (!image_frame_u) {
        fragColor = image_space_color;
    }
    else if (is_active_view || is_full_draw) {
        vec4 tex = texture(image, undist_uv);
        float brush_mask;

        if (!is_full_draw) {
            float dist = distance((gl_FragCoord.xy - mouse_pos) / vec2(brush_radius), vec2(0.0f));
            vec2 brush_tex_coord = vec2(dist, 0.1);
            if (dist < 0.985f) {
                brush_mask = texture(image_brush, brush_tex_coord).r;
            }
        }

        float opacity;
        if (is_full_draw) {
            opacity = 1.0f;
        }
        else {
            opacity = clamp(brush_strength * brush_mask, 0.0f, 1.0f);
        }
        if (is_warning && !is_full_draw) {
            if (is_brush && is_normal_highlight) {
                fragColor = premultiplied_alpha_blend(vec4(warning_color * opacity), frag_nm_highlight);
            }
            else {
                fragColor = vec4(warning_color * opacity);
            }
        }
        else if (is_brush) {
                tex *= opacity;
                fragColor = premultiplied_alpha_blend(tex, (frag_nm_highlight * (1.0 - opacity)));
            }
    }
    else if (is_normal_highlight) {
        fragColor = frag_nm_highlight;
    }
}