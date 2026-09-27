#!/usr/bin/env python3
"""Generate the v2606 controlDict and its explicit sampling locations."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "case" / "system" / "controlDict"


def vec_list(points):
    return "\n".join(f"            ({x:.8f} 0.005 {z:.6f})" for x, z in points)


gauges = []
for x in (5.0, 5.5, 6.0, 6.5, 7.0, 8.0, 9.0, 10.2):
    sample_x = 6.99375 if x == 7.0 else (8.00625 if x == 8.0 else x + 0.000001)
    z = 0.000001
    gauges.append((sample_x, z))

profiles = []
for i in range(261):
    x = 5.0 + 0.02 * i
    sample_x = 6.99375 if abs(x - 7.0) < 1e-10 else (8.00625 if abs(x - 8.0) < 1e-10 else x + 0.000001)
    z = 0.050001 if 7.0 < x < 8.0 else 0.000001
    profiles.append((sample_x, z))

text = f"""FoamFile
{{
    format      ascii;
    class       dictionary;
    object      controlDict;
}}

application         interFoam;
startFrom           startTime;
startTime           0;
stopAt              endTime;
endTime             14.0;
deltaT              0.001;
writeControl        adjustableRunTime;
writeInterval       1.0;
purgeWrite          1;
writeFormat         binary;
writePrecision      10;
writeCompression    off;
timeFormat          general;
timePrecision       8;
runTimeModifiable   false;
adjustTimeStep      yes;
maxCo               0.45;
maxAlphaCo          0.30;
maxDeltaT           0.005;

functions
{{
    gaugeHeights
    {{
        type                interfaceHeight;
        libs                (fieldFunctionObjects);
        alpha               alpha.water;
        liquid              true;
        direction           (0 0 -1);
        interpolationScheme cellPoint;
        locations
        (
{vec_list(gauges)}
        );
        writePrecision      12;
        executeControl      adjustableRunTime;
        executeInterval     0.01;
        writeControl        adjustableRunTime;
        writeInterval       0.01;
    }}

    profileHeights
    {{
        type                interfaceHeight;
        libs                (fieldFunctionObjects);
        alpha               alpha.water;
        liquid              true;
        direction           (0 0 -1);
        interpolationScheme cellPoint;
        locations
        (
{vec_list(profiles)}
        );
        writePrecision      12;
        executeControl      adjustableRunTime;
        executeInterval     0.05;
        writeControl        adjustableRunTime;
        writeInterval       0.05;
    }}

    waterVolume
    {{
        type                volFieldValue;
        libs                (fieldFunctionObjects);
        fields              (alpha.water);
        operation           volIntegrate;
        writeFields         false;
        writePrecision      12;
        executeControl      adjustableRunTime;
        executeInterval     0.05;
        writeControl        adjustableRunTime;
        writeInterval       0.05;
    }}
}}
"""

CONTROL.write_text(text, encoding="utf-8")
print(f"Wrote {CONTROL} with {len(gauges)} gauge and {len(profiles)} profile locations")
