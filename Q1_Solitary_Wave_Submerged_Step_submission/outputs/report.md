# Solitary wave over a rectangular submerged step — technical report

## Run identification

- Case: `Q1_Solitary_Wave_Submerged_Step`; formal run: `formal_20260903092306`.
- Software/solver: OpenFOAM `v2606`, `interFoam`, laminar two-phase VOF.
- Parallel execution: 16 MPI ranks; UTC interval 2026-09-03T09:23:06Z to 2026-09-03T09:56:55Z.
- Physical end time: 14.000000 s; maximum observed Courant number: 0.738097.

## Geometry, mesh, and physics

The 2-D flume spans x=0–14.2 m and z=0–0.25 m with a 0.01 m empty-direction thickness. The still-water level is z=0.10 m. A rectangular solid step occupies x=7–8 m and z=0–0.05 m. The structured mesh uses Δx=0.0125 m and Δz=0.0025 m, giving 112,000 cells. `checkMesh` reported `true`, maximum non-orthogonality 0° and maximum skewness 5.307e-12.

Water and air properties are taken directly from `case_parameters.csv`: ρw=998.2 kg/m³, νw=1.004×10⁻⁶ m²/s, ρa=1.204 kg/m³, νa=1.5×10⁻⁵ m²/s, σ=0.072 N/m, and g=9.81 m/s². Walls are no-slip. The open end patches use OpenFOAM's `shallowWaterAbsorption` wave-velocity condition; the top is pressure-open.

## Initial wave and numerics

At t=0 the field is initialized with

`η(x)=H sech²(k(x-xc))`, where H=0.009 m, h=0.10 m, xc=2.80 m and `k=sqrt(3H/(4h³))=2.598076211 m⁻¹`.

The horizontal velocity is `u=c η/(h+η)` with `c=sqrt(g(h+H))=1.034064795 m/s`; the vertical velocity follows depth-integrated continuity, `w=-z du/dx`. The VOF fraction in each interfacial cell is initialized as the exact horizontal-cut fraction on the Δz grid rather than a binary cell-centre step.

Temporal integration is first-order Euler with adaptive stepping, a target maxCo of 0.45, maxAlphaCo=0.30 and maxDeltaT=0.005 s. The instantaneous global Courant peak was 0.738097 at t=5.183048 s (the controller acts on the following step); the maximum phase/interface Courant number was 0.155820. Interface advection uses van Leer/MULES with two alpha corrections and two subcycles. Pressure–velocity coupling uses PISO/PIMPLE with two pressure correctors.

## Data provenance and results

`wave_gauges.csv` and `surface_profiles.csv` are derived from the formal run's `interfaceHeight` function-object output. `water_area.csv` is the domain integral of `alpha.water`, divided by the 0.01 m empty-direction thickness. No curve was digitized from an image. Profiles contain x=5.0–10.2 m at 0.02 m spacing; the requested snapshots are retained within the continuous 0.05 s profile history.

To prevent an `interfaceHeight` ray from lying exactly on an MPI partition face, ordinary sampling rays are shifted 1×10⁻⁶ m in x while retaining their requested nominal coordinates in the CSV. At the two sharp vertical step edges, an exact ray is also geometrically ambiguous: the nominal x=7.0 m value is sampled at the adjacent upstream cell centre x=6.99375 m, and x=8.0 m at the adjacent downstream cell centre x=8.00625 m. This one-sided edge convention avoids duplicate ray integration and remains below the required 0.02 m profile spacing.

| Gauge | peak time (s) | peak eta (mm) |
|---|---:|---:|
| G1 | 2.1400 | 8.7496 |
| G2 | 2.6200 | 8.7119 |
| G3 | 3.1100 | 8.6727 |
| G4 | 3.6000 | 8.6887 |
| G5 | 4.0800 | 9.6971 |
| G6 | 5.2500 | 8.1757 |
| G7 | 6.3100 | 8.5598 |
| G8 | 7.5000 | 8.3169 |

| profile time (s) | min eta (mm) | max eta (mm) |
|---:|---:|---:|
| 2.0000 | -0.0000 | 7.7159 |
| 4.0000 | -0.0000 | 9.9728 |
| 6.0000 | -1.4623 | 8.6247 |
| 8.0000 | -1.1703 | 1.9413 |

Across the complete record, water area ranged from 1.369197222 to 1.376931589 m² (span 7.734e-03 m², 0.5617% of the first sampled area). Late-time area changes can include physical flux through the absorbing open boundaries and should not be interpreted solely as numerical mass error.

The profile figure shows the incident crest approaching the front face, shoaling over the 0.05 m water depth above the step, and the transmitted/deformed components downstream. Exact quantitative review should use the CSV files rather than the plotted line width.

## Reproducibility and limitations

Run `./Allclean && ./Allrun` in a sourced OpenFOAM v2606 shell. The formal solver, decomposition, reconstruction, mesh-check and environment logs are in `logs/`; the reconstructed final time is retained in `case/`. This is a single-grid 2-D laminar VOF calculation. It supports process review but does not constitute a mesh-convergence, turbulence-model, or 3-D sidewall-sensitivity study.
