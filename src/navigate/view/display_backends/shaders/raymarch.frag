#version 430 core

out vec4 FragColor;

// volume texture array (5-channels)
uniform sampler3D volume[5];

// transfer texture
uniform sampler2D transfer;

uniform mat4 invProjView;
uniform vec2 viewportSize;

uniform float stepWorld = 0.25;       // step length in WORLD units

uniform bool doBox = true;

// contrast params
uniform float opacity = 0.15;  // global density/opacity
uniform vec2 cMinMax[5];
uniform float cGamma[5] = float[5](1.0, 1.0, 1.0, 1.0, 1.0);

// channels
uniform int nChannels = 5; // hard-coded: navigate has 5 channels max

// OPM parameters
uniform float shear_angle = 45.0;  // degrees
uniform float dz = 0.4;             // um    
uniform float px = 0.1478;          // um

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

vec3 physicalToRawUVW(vec3 p, vec3 S, float t)
{
    // Given a point in physical deskewed world-space (um)
    // Return raw texture UVW coordinate.
    // p [um]:  physical position
    // S [um]:  physical volume dimensions
    // t [rad]: shear angle

    // convert from physical pos to tex coords, given shearing
    float u = p.x / S.x;
    float v = (p.y - p.z*tan(t)) / S.y;
    float w = p.z / (S.z * cos(t));

    return vec3(u, v, w);
}

void getPhysicalBounds(vec3 S, float t, out vec3 bmin, out vec3 bmax)
{
    // Return boxMax_um: physical bounding box in um
    // Considers extended bounds from shearing

    bmin = vec3(0.0, S.z * min(0.0, sin(t)), 0.0);
    bmax = vec3(S.x, S.y + S.z * max(0.0, sin(t)), S.z * cos(t));
}

vec3 rotX(vec3 r, float theta)
{
    float c_t = cos(theta);
    float s_t = sin(theta);

    mat4 R = mat4(
        1.,  0.,  0.,  0.,
        0.,  c_t, s_t, 0.,
        0., -s_t, c_t, 0.,
        0.,  0.,  0.,  1.
    );

    return vec3(R * vec4(r, 1.0));
}

void main()
{
    // Shear angle theta
    // Sign based on OPM scan direction
    float theta = -radians(shear_angle);

    // Physical volume dimensions
    vec3 dim = vec3(textureSize(volume[0], 0));
    vec3 S   = vec3(px*dim.x, px*dim.y, dz*dim.z);

    // Compute physical bounding box given shear angle
    vec3 boxMin_um, boxMax_um;
    getPhysicalBounds(S, theta, boxMin_um, boxMax_um);

    // -------- reconstruct world-space ray from pixel --------
    vec2 ndc = (gl_FragCoord.xy / viewportSize) * 2.0 - 1.0;
    vec4 p0w = invProjView * vec4(ndc, -1.0, 1.0);
    vec4 p1w = invProjView * vec4(ndc,  1.0, 1.0);
    
    // world-space ray position (ro) and direction (rd)
    vec3 roW = p0w.xyz / p0w.w;
    vec3 rdW = normalize(p1w.xyz / p1w.w - roW);

    // ro center-shift
    vec3 physicalCenter = (boxMin_um + boxMax_um) * 0.5;

    // rotate world back -theta after shearing
    vec3 ro = rotX(roW, -theta) + physicalCenter;
    vec3 rd = normalize(rotX(rdW, -theta));

    // -------- AABB in object space --------
    float tEnter, tExit;
    if (!intersectAABB(ro, rd, boxMin_um, boxMax_um, tEnter, tExit)) 
        discard;
    tEnter = max(tEnter, 0.0);

    // “steps per voxel” along this ray (orientation aware)
    float dVoxel = max(dot(abs(rd), vec3(px, px, dz)), 1e-6);
    float kStep  = stepWorld / dVoxel;

    // -------- march --------
    vec3 invBoxSize = 1.0 / (boxMax_um - boxMin_um); // um^-1
    
    // accumulator
    vec4 acc = vec4(0.0);

    for (float t = tEnter; t < tExit && acc.a < 0.98; t += stepWorld) {
        vec3 pos = ro + rd * t;                           // position (um)
        vec3 uvw = physicalToRawUVW(pos, S, theta);       // UVW map [0,1]^3
        
        // bounds check
        if (any(lessThan(uvw, vec3(0.0))) || any(greaterThan(uvw, vec3(1.0))))
            continue;

        if (doBox)
        {
            // -------- WIREFRAME BOX EDGES --------
            vec3 distToBox = min(pos - boxMin_um, boxMax_um - pos);
            float edgeThreshold = 0.005 * length(boxMax_um - boxMin_um) / 3.0; // adaptive threshold
            
            // Count how many dimensions are near a face
            int nearCount = 0;
            if (distToBox.x < edgeThreshold) nearCount++;
            if (distToBox.y < edgeThreshold) nearCount++;
            if (distToBox.z < edgeThreshold) nearCount++;
            
            // Only render if on an edge (2+ faces near) or corner (all 3 near)
            if (nearCount >= 2) {
                acc = mix(acc, vec4(0.6, 0.6, 0.6, 1.0), 0.4);  // soft gray edge, mixed
            }
        }

        for (int i = 0; i < nChannels; ++i)
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
            float row = (float(i) + 0.5) / float(nChannels); // normalized row position
            vec4 tf = texture(transfer, vec2(sW, row));

            // don't composite zeros
            if (tf.rgb == vec3(0.0)) continue;

            // optional gamma
            vec3 rgb = tf.rgb;
            if (cGamma[i] != 1.0) rgb = pow(rgb, vec3(cGamma[i]));

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