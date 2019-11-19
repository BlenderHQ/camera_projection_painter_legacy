uniform mat4 ModelViewProjectionMatrix;
uniform mat4 ModelMatrix;

uniform vec3 projectorPosition;
uniform vec3 projectorForward;
uniform vec3 projectorUpAxis;
uniform vec2 sourceScale;

in vec3 pos;
in vec3 normal;

out vec2 posInterp;
out vec3 nrmInterp;

vec2 project(in vec3 coo, in mat4 mat, in vec3 ppos, in vec3 pdir, in vec3 pup, in vec2 sscale)
{
    vec3 interpolation = vec3(mat * vec4(coo, 1.0));

    vec3 sub1 = ppos - pdir;
    vec3 cp1 = cross(sub1, pup);
    vec3 sub2 = interpolation - ppos;

    float div1 = dot(sub1, sub2) / dot(sub1, sub1);
    float div2 = dot(normalize(cross(cp1, sub1)), sub2) / div1;
    float div3 = dot(normalize(cp1), sub2) / div1;

    vec2 projected = (vec2(div3 * sscale.x, div2 * - sscale.y)) + vec2(0.5, 0.5);
    return projected;
}

void main()
{
    posInterp = project(pos, ModelMatrix, projectorPosition, projectorForward, projectorUpAxis, sourceScale);
    nrmInterp = vec3(ModelMatrix * vec4(normal, 1.0));

    gl_Position = ModelViewProjectionMatrix * ModelMatrix * vec4(pos, 1.0);
}