#version 430 core

uniform mat4 proj_view;
uniform mat4 model;
uniform vec3 bmin;
uniform vec3 bmax;

const int LINE_INDICES[24] = int[24](
    0,1, 2,3, 4,5, 6,7,
    0,2, 1,3, 4,6, 5,7,
    0,4, 1,5, 2,6, 3,7
);

void main() {
    int ci = LINE_INDICES[gl_VertexID];
    vec3 corner = vec3(
        bool(ci & 1) ? bmax.x : bmin.x,
        bool(ci & 2) ? bmax.y : bmin.y,
        bool(ci & 4) ? bmax.z : bmin.z
    );
    gl_Position = proj_view * model * vec4(corner, 1.0);
}
