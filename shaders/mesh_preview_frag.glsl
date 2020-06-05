uniform vec3 camera_forward;
uniform bool use_projection_preview;
uniform bool use_normal_highlight;
uniform bool use_warnings;
uniform bool use_warning_action_draw;
uniform bool full_draw;
uniform bool active_view;
uniform bool warning_status;
uniform sampler2D clone_image;
uniform sampler2D brush_img;
uniform int outline_type;
uniform vec4 outline_color;
uniform float outline_width;
uniform float outline_scale;
uniform vec4 image_space_color;
uniform vec4 normal_highlight_color;
uniform vec2 mouse_pos;
uniform float brush_radius;
uniform float brush_strength;
uniform vec4 warning_color;

in vec2 _pos_interp;
in vec3 _nrm_interp;
in vec2 wh_div;

out vec4 frag;

void main() {

    vec2 undist_uv = undistorted_uv(_pos_interp);

    bool image_frame = inside_rect(_pos_interp, vec2(0.0), vec2(1.0)); // Inside draw preview, outside draw outline
    bool image_frame_u = inside_rect(undist_uv, vec2(0.0), vec2(1.0));

    if (!image_frame) {
        vec4 frag_outline;
        float outline_pattern;

        if (use_projection_preview == true) {
            if (outline_type == 1) {
            outline_pattern = 1.0;
            }
            else if (outline_type == 2) {
                outline_pattern = checker_pattern(_pos_interp, wh_div, outline_scale);
            }
            else if (outline_type == 3) {
                outline_pattern = lines_pattern(_pos_interp, wh_div, outline_scale);
            }
            if (outline_type != 0) {
                bool outlineMask = inside_outline(_pos_interp, outline_width, wh_div);
                bool outlineMaskFrame = inside_outline(_pos_interp, outline_width * 0.1, wh_div);
                if (outlineMaskFrame == true) {
                    outline_pattern = 1.0;
                }
                frag = outline_color;
                if (outlineMask == true) {
                    frag.a = outline_pattern;
                }
                else {
                    frag = vec4(0.0);
                }
            }
        }
    }
    else if (!image_frame_u) {
        frag = image_space_color;
    }
    else {
        vec4 tex;
        vec2 brush_tex_coord;
        float brush_mask;

        if (active_view == true || full_draw == true) {
            float dist = distance((gl_FragCoord.xy - mouse_pos) / vec2(brush_radius), vec2(0.0));
            brush_tex_coord = vec2(dist, 0.1);
            if (dist < 0.96 || full_draw == true) {
                brush_mask = texture(brush_img, brush_tex_coord).r;
                tex = texture(clone_image, undist_uv);
            }
        }

        vec4 frag_nm_highlight;

        if (use_normal_highlight == true) {
            float nm_dot = 1.0 - clamp(dot(_nrm_interp, -camera_forward), 0.0, 1.0);
            frag_nm_highlight = normal_highlight_color * nm_dot;
        }

        float opacity = 1.0;
        if (full_draw == false) {
            opacity = clamp(brush_strength * brush_mask, 0.0, 1.0);
        }

        if (active_view == true || full_draw == true) {
            if (use_warnings == true && use_warning_action_draw == true
                    && warning_status == true && full_draw == false) {
                if (use_projection_preview == true && use_normal_highlight == true) {
                    frag = premultiplied_alpha_blend(vec4(warning_color * opacity), frag_nm_highlight);
                }
                else {
                    frag = vec4(warning_color * opacity);
                }
            }
            else {
                if (use_projection_preview == true) {
                    tex.a *= opacity;
                    frag = premultiplied_alpha_blend(tex, frag_nm_highlight);
                }
            }
        }
        else if (use_projection_preview == true) {
                frag = frag_nm_highlight;
        }
    }
}