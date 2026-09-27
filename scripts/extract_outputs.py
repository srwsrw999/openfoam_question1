#!/usr/bin/env python3
"""Convert OpenFOAM function-object and solver logs to required CSV files."""

import csv
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case"
OUT = ROOT / "outputs"
LOGS = ROOT / "logs"
OUT.mkdir(exist_ok=True)


def data_files(function_name, filename):
    base = CASE / "postProcessing" / function_name
    return sorted(base.glob(f"*/{filename}"), key=lambda p: float(p.parent.name))


def numeric_rows(paths):
    by_time = {}
    for path in paths:
        for line in path.read_text(errors="replace").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            vals = [float(v) for v in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", line)]
            if vals:
                by_time[round(vals[0], 10)] = vals
    return [by_time[t] for t in sorted(by_time)]


gauge_rows = numeric_rows(data_files("gaugeHeights", "height.dat"))
if not gauge_rows:
    raise RuntimeError("No gaugeHeight data found")
with (OUT / "wave_gauges.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["time_s"] + [f"eta_G{i}_m" for i in range(1, 9)])
    for vals in gauge_rows:
        if len(vals) < 17:
            raise RuntimeError(f"Malformed gauge row at t={vals[0]}")
        heights = [vals[1 + 2 * i] for i in range(8)]
        bottoms = [0, 0, 0, 0, 0, 0, 0, 0]
        w.writerow([f"{vals[0]:.8f}"] + [f"{h + b - 0.1:.12e}" for h, b in zip(heights, bottoms)])

profile_rows = numeric_rows(data_files("profileHeights", "height.dat"))
if not profile_rows:
    raise RuntimeError("No profileHeight data found")
xs = [5.0 + 0.02 * i for i in range(261)]
with (OUT / "surface_profiles.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["time_s", "x_m", "eta_m"])
    for vals in profile_rows:
        if len(vals) < 1 + 2 * len(xs):
            raise RuntimeError(f"Malformed profile row at t={vals[0]}: {len(vals)} values")
        for i, x in enumerate(xs):
            h = vals[1 + 2 * i]
            bottom = 0.05 if 7.0 < x < 8.0 else 0.0
            w.writerow([f"{vals[0]:.8f}", f"{x:.2f}", f"{h + bottom - 0.1:.12e}"])

volume_rows = numeric_rows(data_files("waterVolume", "volFieldValue.dat"))
if not volume_rows:
    raise RuntimeError("No waterVolume data found")
with (OUT / "water_area.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["time_s", "water_area_m2"])
    for vals in volume_rows:
        w.writerow([f"{vals[0]:.8f}", f"{vals[1] / 0.01:.12e}"])

solver_text = (LOGS / "log.solver").read_text(errors="replace")
time_history = []
co = phase_co = dt = math.nan
for line in solver_text.splitlines():
    m = re.search(r"^Courant Number mean:\s*\S+\s+max:\s*(\S+)", line)
    if m:
        co = float(m.group(1))
        continue
    m = re.search(r"^Interface Courant Number mean:\s*\S+\s+max:\s*(\S+)", line)
    if m:
        phase_co = float(m.group(1))
        continue
    m = re.search(r"^deltaT\s*=\s*(\S+)", line)
    if m:
        dt = float(m.group(1))
        continue
    m = re.search(r"^Time\s*=\s*(\S+)", line)
    if m:
        t = float(m.group(1))
        time_history.append((t, dt, co, phase_co))

if not time_history:
    raise RuntimeError("No solver time history found")
with (OUT / "solver_time_history.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["time_s", "delta_t_s", "max_courant", "max_phase_courant"])
    for row in time_history:
        w.writerow([f"{row[0]:.10g}"] + [f"{v:.12e}" for v in row[1:]])

mesh_text = (LOGS / "log.checkMesh").read_text(errors="replace")
block_text = (LOGS / "log.blockMesh").read_text(errors="replace")


def first(pattern, text, cast=float):
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise RuntimeError(f"Could not parse mesh statistic: {pattern}")
    return cast(m.group(1))


cell_count = first(r"^\s*nCells:\s*(\d+)", block_text, int)
point_count = first(r"^\s*nPoints:\s*(\d+)", block_text, int)
face_count = first(r"^\s*nFaces:\s*(\d+)", block_text, int)
number = r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"
min_vol = first(r"Min volume =\s*" + number, mesh_text)
max_nonorth = first(r"Mesh non-orthogonality Max:\s*" + number, mesh_text)
max_skew = first(r"Max skewness =\s*" + number, mesh_text)
passed = "true" if "Mesh OK." in mesh_text else "false"
with (OUT / "mesh_statistics.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["cell_count", "point_count", "face_count", "min_cell_volume_m3", "max_non_orthogonality", "max_skewness", "mesh_check_passed"])
    w.writerow([cell_count, point_count, face_count, f"{min_vol:.12e}", f"{max_nonorth:.12g}", f"{max_skew:.12e}", passed])

env = {}
for line in (LOGS / "log.environment").read_text(errors="replace").splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

max_co = max(row[2] for row in time_history if math.isfinite(row[2]))
end_time = max(row[0] for row in time_history)
start_utc = env.get("run_start_utc", "unknown")
end_utc = env.get("run_end_utc", "unknown")
run_id = "formal_" + re.sub(r"\D", "", start_utc)[:14]
foam_version = env.get("foam_version", "unknown")
if foam_version == "unknown":
    foam_version = env.get("WM_PROJECT_VERSION", "v2606")
with (OUT / "run_summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["case_id", "run_id", "openfoam_version", "solver_name", "parallel_processes", "cell_count", "physical_time_end_s", "max_courant_observed", "output_interval_s", "start_time_utc", "end_time_utc"])
    w.writerow(["Q1_Solitary_Wave_Submerged_Step", run_id, foam_version, "interFoam", 16, cell_count, f"{end_time:.8f}", f"{max_co:.12e}", "1.0", start_utc, end_utc])

print(f"Extracted {len(gauge_rows)} gauge records, {len(profile_rows)} profiles, {len(volume_rows)} water-area records")
