uniform mat4 ModelViewProjectionMatrix;
uniform mat4 model_matrix;

uniform vec2 image_aspect_scale;

uniform float focal_length;
uniform vec2 shift;
uniform int sensor_fit; // 0 - auto, 1 - Horizontal, 2 - Vertical
uniform float sensor_width;
uniform float sensor_height;

uniform float cameras_viewport_size;

in vec3 pos;

void main()
{
    vec3 p = pos;
    
    if (gl_VertexID != 0) {
        vec2 aspect = image_aspect_scale;

        float sensor_size;
        bool horizontal_fit;

        if (sensor_fit == 0) { // AUTO
            horizontal_fit = (aspect.x > aspect.y);
            sensor_size = sensor_width;
        }
        else if (sensor_fit == 1) { // HORIZONTAL
            horizontal_fit = true;
            sensor_size = sensor_width;
        }
        else { // VERTICAL
            horizontal_fit = false;
            sensor_size = sensor_height;
        }
        if (horizontal_fit == false) {
            aspect = vec2(aspect.x / aspect.y, 1.0);
        }

        p.z *= focal_length / sensor_size;
        p.xy *= aspect;
        p.xy += shift;
        p *= cameras_viewport_size;
    }
    gl_Position = ModelViewProjectionMatrix * model_matrix * vec4(p, 1.0);
}
