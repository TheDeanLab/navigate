#version 430 core

out vec4 FragColor;

// volume texture array (5-channels)
uniform sampler3D volume[5];

// transfer texture
uniform sampler2D transfer;

uniform mat4 invProjView;
uniform vec2 viewportSize;

uniform vec3 boxMin;
uniform vec3 boxMax;

uniform float stepWorld = 0.25;       // step length in WORLD units

// contrast params
uniform float opacity = 0.15;  // global density/opacity
uniform vec2 cMinMax[5];
uniform float cGamma[5] = float[5](1.0, 1.0, 1.0, 1.0, 1.0);

// channels
uniform int nChannels = 5; // hard-coded: navigate has 5 channels max

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

// Shear Matrix: shifts X based on Z
mat4 shearMatrix(float angleDeg, float dz, float xyPixelSize)
{
    float t = radians(angleDeg/2.0);

    float dy = sin(t)*dz/xyPixelSize;

    return mat4(
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0,  dy, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    );
}

// Rotation Matrix: rotate about Y
mat4 rotationMatrix_Y(float angleDeg)
{
    float t = radians(angleDeg/2.0);

    return mat4(
        1.0,    0.0,    0.0,  0.0,
        0.0, cos(t), -sin(t), 0.0,
        0.0, sin(t),  cos(t), 0.0,
        0.0,    0.0,    0.0,  1.0
    );
}

// Translation Matrix
mat4 translationMatrix(vec3 t)
{
    return mat4(
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        t.x, t.y, t.z, 1.0
    );
}

// Combined DSR transformation (PetaKit5D)
mat4 deskewRotateMatrix(float angleDeg, float dz, float xyPixelSize, vec3 volumeCenter)
{
    // 1: Translate to origin
    mat4 T1 = translationMatrix(-volumeCenter);

    // 2: Apply shear
    mat4 S = shearMatrix(angleDeg, dz, xyPixelSize);

    // 3: Rotate by theta
    mat4 R = rotationMatrix_Y(angleDeg);

    // 4: Translate back
    mat4 T2 = translationMatrix(volumeCenter);

    // Combined DSR:
    return T2 * S * T1;
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
    // mat4 invShear  = inverseShearYZ(shear_angle);
    // vec3 ro = (invShear * vec4(roW, 1.0)).xyz;
    // vec3 rd = normalize(mat3(invShear) * rdW);   // direction uses linear part only

    // PetaKit5D style deskew-rotate (DSR)
    vec3 volumeCenter = (boxMin_um + boxMax_um) * 0.5; // use _um ...?

    mat4 DSR = deskewRotateMatrix(shear_angle, dz, px, volumeCenter);

    // apply
    vec3 ro = (DSR * vec4(roW, 1.0)).xyz;
    vec3 rd = normalize(mat3(DSR) * rdW);

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