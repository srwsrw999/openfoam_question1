#!/usr/bin/env python3
"""Verify required fields, intervals, end time and restart evidence."""

import csv
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

required = {
    "run_summary.csv": ["case_id","run_id","openfoam_version","solver_name","parallel_processes","cell_count","physical_time_end_s","max_courant_observed","output_interval_s","start_time_utc","end_time_utc"],
    "solver_time_history.csv": ["time_s","delta_t_s","max_courant","max_phase_courant"],
    "mesh_statistics.csv": ["cell_count","point_count","face_count","min_cell_volume_m3","max_non_orthogonality","max_skewness","mesh_check_passed"],
    "wave_gauges.csv": ["time_s"] + [f"eta_G{i}_m" for i in range(1,9)],
    "surface_profiles.csv": ["time_s","x_m","eta_m"],
    "water_area.csv": ["time_s","water_area_m2"],
}


def load(name):
    path = OUT / name
    if not path.is_file():
        raise AssertionError(f"missing {path}")
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != required[name]:
            raise AssertionError(f"wrong header in {name}: {reader.fieldnames}")
        return list(reader)


data = {name: load(name) for name in required}
summary = data["run_summary.csv"][0]
assert int(summary["cell_count"]) <= 120000
assert float(summary["physical_time_end_s"]) >= 14.0 - 1e-9
assert data["mesh_statistics.csv"][0]["mesh_check_passed"].lower() == "true"

for name, limit in (("wave_gauges.csv", 0.0100001), ("water_area.csv", 0.0500001)):
    times = [float(r["time_s"]) for r in data[name]]
    assert all(b > a for a, b in zip(times, times[1:])), f"non-increasing {name}"
    assert max(b-a for a,b in zip(times,times[1:])) <= limit, f"sampling gap in {name}"
    assert summary["physical_time_end_s"] and float(summary["physical_time_end_s"]) - times[-1] <= limit

profile_times = sorted({float(r["time_s"]) for r in data["surface_profiles.csv"]})
assert all(b > a for a,b in zip(profile_times,profile_times[1:]))
assert max(b-a for a,b in zip(profile_times,profile_times[1:])) <= 0.0500001
assert float(summary["physical_time_end_s"]) - profile_times[-1] <= 0.0500001
for target in (2.0,4.0,6.0,8.0):
    assert any(abs(t-target) <= 1e-6 for t in profile_times), f"missing profile t={target}"
for t in profile_times:
    xs = [float(r["x_m"]) for r in data["surface_profiles.csv"] if abs(float(r["time_s"])-t) < 1e-9]
    assert abs(min(xs)-5.0) < 1e-9 and abs(max(xs)-10.2) < 1e-9 and len(xs) == 261
    assert max(b-a for a,b in zip(sorted(xs),sorted(xs)[1:])) <= 0.0200001

for image in (OUT/"mesh.png", OUT/"result_01.png"):
    assert image.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"invalid PNG {image}"
assert (OUT/"report.md").stat().st_size > 1000
solver_log = (ROOT/"logs"/"log.solver").read_text(errors="replace")
assert "FOAM FATAL" not in solver_log and re.search(r"^End\s*$", solver_log, re.MULTILINE)

final_times = []
for p in (ROOT/"case").iterdir():
    if p.is_dir():
        try:
            final_times.append(float(p.name))
        except ValueError:
            pass
assert final_times and max(final_times) >= 14.0 - 1e-9, "missing reconstructed restart time"

entries = []
for rel in [Path("Allrun"), Path("Allclean")]:
    entries.append((str(rel), "automation script", "formal case", "n/a"))
for folder, desc in (("case/system","OpenFOAM controls"),("case/constant","mesh and physical properties"),("case/0","initialized fields"),(f"case/{max(final_times):g}","reconstructed restart fields"),("scripts","generation and QA scripts"),("logs","formal run evidence"),("outputs","derived deliverables")):
    for p in sorted((ROOT/folder).rglob("*")):
        if p.is_file() and p.name != "submission_manifest.csv":
            units = "SI" if p.suffix == ".csv" else "n/a"
            entries.append((str(p.relative_to(ROOT)), desc, "formal OpenFOAM run", units))
with (OUT/"submission_manifest.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["file_name","description","source_case","units"])
    w.writerows(entries)

print("VERIFIED: headers, monotonic times, sampling intervals, requested profiles, mesh limit, final restart, logs and PNGs")
