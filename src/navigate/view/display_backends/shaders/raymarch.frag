#version 430 core

out vec4 FragColor;

// volume texture array (4-channels)
uniform sampler3D volume[4];

// transfer texture
uniform sampler2D transfer;

uniform mat4 invProjView;
uniform vec2 viewportSize;

uniform vec3 boxMin;
uniform vec3 boxMax;

uniform float stepWorld;       // step length in WORLD units

// contrast params
uniform float opacity = 0.15;  // global density/opacity
uniform vec2 cMinMax[4];
uniform float gamma   = 1.0;

// channels
uniform int nChannels = 4;

// OPM parameters
uniform float shear_angle = 50.0;   // degrees
uniform float dz = 0.4;             // um    
uniform float px = 0.1348;          // um

// ---------- utilities ----------

// test intersection
bool intersectAABB(vec3 ro, vec3 rd, vec3 bmin, vec3 bmax, out float t0, out float t1)
{
    vec3 invD = 1.0/rd;
    vec3 tA = (bmin - ro) * invD;
    vec3 tB = (bmax - ro) * invD;
    vec3 tmin = min(tA,tB), tmax = max(tA,tB);
    
    t0 = max(max(tmin.x, tmin.y), tmin.z);
    t1 = min(min(tmax.x, tmax.y), tmax.z);
    
    return t1 > max(t0, 0.0);
}

// OPM shear transform
// Build the inverse of the shear Y -= k*Z
mat4 inverseShearYZ(float angleDeg)
{
    float k = sin(radians(angleDeg));
    mat4 m = mat4(1.0);
    m[1][2] = k;
    
    // need to properly scale somehow: interpolation?
    // m[1][2] = px * k / dz;
    // m[0][0] = dz * k;
    // m[2][2] = dz * cos(radians(angleDeg));

    return m;
}

void main()
{
    // voxel size (um): note that we assume px = py
    vec3 spacing = vec3(px, px, dz);

    // scaled box min/max
    vec3 boxMin_um = boxMin * spacing;
    vec3 boxMax_um = boxMax * spacing;

    // -------- reconstruct world-space ray from pixel --------
    vec2 ndc = (gl_FragCoord.xy / viewportSize) * 2.0 - 1.0;
    vec4 p0w = invProjView * vec4(ndc, -1.0, 1.0);
    vec4 p1w = invProjView * vec4(ndc,  1.0, 1.0);
    vec3 roW = p0w.xyz / p0w.w;
    vec3 rdW = normalize(p1w.xyz / p1w.w - roW);

    // -------- transform ray to OBJECT space via inverse shear --------
    mat4 invShear  = inverseShearYZ(shear_angle);
    vec3 ro = (invShear * vec4(roW, 1.0)).xyz;
    vec3 rd = normalize(mat3(invShear) * rdW);   // direction uses linear part only

    // -------- AABB in object space --------
    float tEnter, tExit;
    if (!intersectAABB(ro, rd, boxMin_um, boxMax_um, tEnter, tExit)) 
        discard;
    tEnter = max(tEnter, 0.0);

    // -------- step-size invariant opacity terms --------
    vec3 dim = vec3(textureSize(volume[0], 0));       // voxel counts (X,Y,Z)

    // “steps per voxel” along this ray (orientation aware)
    float dVoxel  = max(dot(abs(rd), spacing), 1e-6);
    float kStep   = stepWorld / dVoxel;

    // -------- march --------
    
    vec3 invBoxSize = 1.0 / (boxMax_um - boxMin_um); // um^-1
    
    // accumulator
    vec4 acc = vec4(0.0);

    for (float t = tEnter; t < tExit && acc.a < 0.98; t += stepWorld) {
        vec3 pos = ro + rd * t;                           // position (um)
        vec3 uvw = (pos - boxMin_um) * invBoxSize;        // [0,1]^3

        // sample scalar (all 4 channels in RGBA)
        // vec4 s = texture(volume, uvw);            

        for (int i = 0; i < 4; ++i)
        {
            if (i >= nChannels) break;

            // select current channel
            float s_i = texture(volume[i], uvw).r;

            // scale and normalize
            float cMin = cMinMax[i].x;
            float cMax = cMinMax[i].y;
            float sW = (s_i - cMin) / max(cMax - cMin, 1e-6);
            sW = clamp(sW, 0.0, 1.0);

            // 2D transfer lookup: channels arranged by row
            float row = (float(i) + 0.5) / 4.0; // normalized row position
            vec4 tf = texture(transfer, vec2(sW, row));

            // don't composite zeros
            if (tf.rgb == vec3(0.0)) continue;

            // optional gamma
            vec3 rgb = tf.rgb;
            if (gamma != 1.0) rgb = pow(rgb, vec3(gamma));

            // Beer-Lambert step-invariant opacity based on tf.alpha
            float a = 1.0 - exp(-opacity * tf.a * kStep);
            vec3  c = rgb * a;

            // front-to-back premultiplied composite
            acc.rgb += (1.0 - acc.a) * c;
            acc.a   += (1.0 - acc.a) * a;
        }
    }
    
    FragColor = acc;
}