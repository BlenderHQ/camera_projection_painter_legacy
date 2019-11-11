uniform mat4 ModelViewProjectionMatrix;
uniform mat4 modelMatrix;

in vec3 pos;
in vec2 texCoord;

out vec2 uvInterp;

void main()
{
    uvInterp = texCoord;
    gl_Position = ModelViewProjectionMatrix * modelMatrix * vec4(pos, 1.0);
}