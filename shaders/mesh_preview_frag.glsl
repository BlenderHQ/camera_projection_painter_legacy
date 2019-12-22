uniform vec3 projector_forward;
uniform vec2 aspect;

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

uniform vec4 normal_highlight_color;

uniform vec2 mouse_pos;
uniform float brush_radius;
uniform float brush_strength;


uniform vec4 warning_color;

uniform bool colorspace_srgb;

in vec2 _pos_interp;
in vec3 _nrm_interp;

out vec4 frag;


void main() {
    bool image_frame = inside_rect(_pos_interp, vec2(0.0), vec2(1.0)); // Inside draw preview, outside draw outline

    if (image_frame == true) {
        vec4 tex;
        vec2 brush_tex_coord;
        float brush_mask;

        if (active_view == true || full_draw == true) {
            float dist = distance((gl_FragCoord.xy - mouse_pos) / vec2(brush_radius), vec2(0.0));
            brush_tex_coord = vec2(dist, 0.1);
            if (dist < 0.96 || full_draw == true) {
                brush_mask = texture(brush_img, brush_tex_coord).r;

                if (colorspace_srgb == true) {
                    tex = linearrgb_to_srgb(texture(clone_image, _pos_interp));
                }
                else {
                    tex = texture(clone_image, _pos_interp);
                }
            }
        }

        vec4 frag_nm_highlight;
        float nm_highlight_fac = 35.0;

        if (use_normal_highlight == true) {
            float nm_dot = 1.0 - clamp(dot(_nrm_interp, projector_forward) / nm_highlight_fac, 0.0, 1.0);
            frag_nm_highlight = linearrgb_to_srgb(normal_highlight_color) * nm_dot;
        }

        float opacity = 1.0;
        if (full_draw == false) {
            opacity = clamp(brush_strength * brush_mask, 0.0, 1.0);
        }

        if (active_view == true || full_draw == true) {
            if (use_warnings == true && use_warning_action_draw == true
                    && warning_status == true && full_draw == false) {
                if (use_projection_preview == true && use_normal_highlight == true) {
                    frag = premultiplied_alpha_blend(linearrgb_to_srgb(warning_color * opacity), frag_nm_highlight);
                }
                else {
                    frag = linearrgb_to_srgb(warning_color * opacity);
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
    else {
        vec4 frag_outline;
        float outline_pattern;

        if (use_projection_preview == true) {
            if (outline_type == 1) {
            outline_pattern = 1.0;
            }
            else if (outline_type == 2) {
                outline_pattern = checker_pattern(_pos_interp, aspect, outline_scale);
            }
            else if (outline_type == 3) {
                outline_pattern = lines_pattern(_pos_interp, aspect, outline_scale);
            }
            if (outline_type != 0) {
                bool outlineMask = inside_outline(_pos_interp, outline_width, aspect);
                frag = linearrgb_to_srgb(outline_color);
                if (outlineMask == true) {
                    frag.a = outline_pattern;
                }
                else {
                    frag = vec4(0.0);
                }
            }
        }
    }
}