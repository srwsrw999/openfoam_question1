#!/usr/bin/env python3
"""Build a concise technical report populated with formal-run metrics."""

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def rows(name):
    with (OUT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


run = rows("run_summary.csv")[0]
mesh = rows("mesh_statistics.csv")[0]
gauges = rows("wave_gauges.csv")
areas = rows("water_area.csv")
profiles = rows("surface_profiles.csv")
solver_history = rows("solver_time_history.csv")

peak_lines = []
for i in range(1, 9):
    best = max(gauges, key=lambda r: float(r[f"eta_G{i}_m"]))
    peak_lines.append(f"| G{i} | {float(best['time_s']):.4f} | {1000*float(best[f'eta_G{i}_m']):.4f} |")

snap = defaultdict(list)
for r in profiles:
    snap[round(float(r["time_s"]), 6)].append(float(r["eta_m"]))
snap_lines = []
for target in (2.0, 4.0, 6.0, 8.0):
    key = min(snap, key=lambda t: abs(t - target))
    vals = snap[key]
    snap_lines.append(f"| {key:.4f} | {1000*min(vals):.4f} | {1000*max(vals):.4f} |")

area_values = [float(r["water_area_m2"]) for r in areas]
area0 = area_values[0]
area_span = max(area_values) - min(area_values)
area_rel = area_span / area0 * 100
phase_peak = max(float(r["max_phase_courant"]) for r in solver_history)
co_peak_row = max(solver_history, key=lambda r: float(r["max_courant"]))

report = f"""# Solitary wave over a rectangular submerged step — technical report

## Run identification

- Case: `{run['case_id']}`; formal run: `{run['run_id']}`.
- Software/solver: OpenFOAM `{run['openfoam_version']}`, `interFoam`, laminar two-phase VOF.
- Parallel execution: {run['parallel_processes']} MPI ranks; UTC interval {run['start_time_utc']} to {run['end_time_utc']}.
- Physical end time: {float(run['physical_time_end_s']):.6f} s; maximum observed Courant number: {float(run['max_courant_observed']):.6f}.

## Geometry, mesh, and physics

The 2-D flume spans x=0–14.2 m and z=0–0.25 m with a 0.01 m empty-direction thickness. The still-water level is z=0.10 m. A rectangular solid step occupies x=7–8 m and z=0–0.05 m. The structured mesh uses Δx=0.0125 m and Δz=0.0025 m, giving {int(mesh['cell_count']):,} cells. `checkMesh` reported `{mesh['mesh_check_passed']}`, maximum non-orthogonality {float(mesh['max_non_orthogonality']):g}° and maximum skewness {float(mesh['max_skewness']):.3e}.

Water and air properties are taken directly from `case_parameters.csv`: ρw=998.2 kg/m³, νw=1.004×10⁻⁶ m²/s, ρa=1.204 kg/m³, νa=1.5×10⁻⁵ m²/s, σ=0.072 N/m, and g=9.81 m/s². Walls are no-slip. The open end patches use OpenFOAM's `shallowWaterAbsorption` wave-velocity condition; the top is pressure-open.

## Initial wave and numerics

At t=0 the field is initialized with

`η(x)=H sech²(k(x-xc))`, where H=0.009 m, h=0.10 m, xc=2.80 m and `k=sqrt(3H/(4h³))=2.598076211 m⁻¹`.

The horizontal velocity is `u=c η/(h+η)` with `c=sqrt(g(h+H))=1.034064795 m/s`; the vertical velocity follows depth-integrated continuity, `w=-z du/dx`. The VOF fraction in each interfacial cell is initialized as the exact horizontal-cut fraction on the Δz grid rather than a binary cell-centre step.

Temporal integration is first-order Euler with adaptive stepping, a target maxCo of 0.45, maxAlphaCo=0.30 and maxDeltaT=0.005 s. The instantaneous global Courant peak was {float(co_peak_row['max_courant']):.6f} at t={float(co_peak_row['time_s']):.6f} s (the controller acts on the following step); the maximum phase/interface Courant number was {phase_peak:.6f}. Interface advection uses van Leer/MULES with two alpha corrections and two subcycles. Pressure–velocity coupling uses PISO/PIMPLE with two pressure correctors.

## Data provenance and results

`wave_gauges.csv` and `surface_profiles.csv` are derived from the formal run's `interfaceHeight` function-object output. `water_area.csv` is the domain integral of `alpha.water`, divided by the 0.01 m empty-direction thickness. No curve was digitized from an image. Profiles contain x=5.0–10.2 m at 0.02 m spacing; the requested snapshots are retained within the continuous 0.05 s profile history.

To prevent an `interfaceHeight` ray from lying exactly on an MPI partition face, ordinary sampling rays are shifted 1×10⁻⁶ m in x while retaining their requested nominal coordinates in the CSV. At the two sharp vertical step edges, an exact ray is also geometrically ambiguous: the nominal x=7.0 m value is sampled at the adjacent upstream cell centre x=6.99375 m, and x=8.0 m at the adjacent downstream cell centre x=8.00625 m. This one-sided edge convention avoids duplicate ray integration and remains below the required 0.02 m profile spacing.

| Gauge | peak time (s) | peak eta (mm) |
|---|---:|---:|
{chr(10).join(peak_lines)}

| profile time (s) | min eta (mm) | max eta (mm) |
|---:|---:|---:|
{chr(10).join(snap_lines)}

Across the complete record, water area ranged from {min(area_values):.9f} to {max(area_values):.9f} m² (span {area_span:.3e} m², {area_rel:.4f}% of the first sampled area). Late-time area changes can include physical flux through the absorbing open boundaries and should not be interpreted solely as numerical mass error.

The profile figure shows the incident crest approaching the front face, shoaling over the 0.05 m water depth above the step, and the transmitted/deformed components downstream. Exact quantitative review should use the CSV files rather than the plotted line width.

## Reproducibility and limitations

Run `./Allclean && ./Allrun` in a sourced OpenFOAM v2606 shell. The formal solver, decomposition, reconstruction, mesh-check and environment logs are in `logs/`; the reconstructed final time is retained in `case/`. This is a single-grid 2-D laminar VOF calculation. It supports process review but does not constitute a mesh-convergence, turbulence-model, or 3-D sidewall-sensitivity study.
"""
(OUT / "report.md").write_text(report, encoding="utf-8")
print("Wrote outputs/report.md")
