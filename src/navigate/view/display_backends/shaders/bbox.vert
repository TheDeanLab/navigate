#version 430 core

uniform mat4 proj_view;

uniform float shear_angle = 45.0;
uniform vec3  phys_size = vec3(1.0);

const int LINE_INDICES[24] = int[24](
    0,1, 2,3, 4,5, 6,7,
    0,2, 1,3, 4,6, 5,7,
    0,4, 1,5, 2,6, 3,7
);

vec3 shearedBoxBounds(vec3 S, float t)
{
    // Compute a bounding box which encapsulates the sheared volume
    // S [um]:  physical volume dimensions
    // t [rad]: shear angle
    
    float dx = S.x / 2.0;
    float dy = S.y * cos(t) / 2.0;
    float dz = S.z / 2.0  + dy*abs(tan(t));

    return vec3(dx, dy, dz);
}

void main() {
    vec3 bounds = shearedBoxBounds(phys_size, -radians(shear_angle));

    int ci = LINE_INDICES[gl_VertexID];
    vec3 corner = vec3(
        bool(ci & 1) ? bounds.x : -bounds.x,
        bool(ci & 2) ? bounds.y : -bounds.y,
        bool(ci & 4) ? bounds.z : -bounds.z
    );
    gl_Position = proj_view * vec4(corner, 1.0);
}
