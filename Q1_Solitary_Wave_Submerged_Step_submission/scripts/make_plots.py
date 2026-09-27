#!/usr/bin/env python3
"""Generate required PNG figures from the actual mesh metadata and CSV results."""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def read_csv(name):
    with (OUT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


mesh = read_csv("mesh_statistics.csv")[0]
fig, axes = plt.subplots(2, 1, figsize=(14, 6.5), constrained_layout=True,
                         gridspec_kw={"height_ratios": [1, 2.2]})

ax = axes[0]
ax.add_patch(Rectangle((0, 0), 14.2, 0.25, facecolor="#d9eef7", edgecolor="black", linewidth=1.2))
ax.add_patch(Rectangle((7, 0), 1, 0.05, facecolor="#777777", edgecolor="black"))
ax.axhline(0.1, color="#1674b8", linewidth=1.5, label="still water level")
ax.set(xlim=(0, 14.2), ylim=(-0.005, 0.255), ylabel="z (m)", title="Actual blockMesh domain")
ax.set_aspect("equal", adjustable="box")
ax.legend(loc="upper right")

ax = axes[1]
dx, dz = 0.0125, 0.0025
for i in range(round((8.3 - 6.7) / dx) + 1):
    x = 6.7 + i * dx
    z0 = 0.05 if 7.0 - 1e-12 <= x <= 8.0 + 1e-12 else 0.0
    ax.plot([x, x], [z0, 0.15], color="#8ca5b5", linewidth=0.28)
for i in range(round(0.15 / dz) + 1):
    z = i * dz
    if z < 0.05 - 1e-12:
        ax.plot([6.7, 7.0], [z, z], color="#8ca5b5", linewidth=0.28)
        ax.plot([8.0, 8.3], [z, z], color="#8ca5b5", linewidth=0.28)
    else:
        ax.plot([6.7, 8.3], [z, z], color="#8ca5b5", linewidth=0.28)
ax.add_patch(Rectangle((7, 0), 1, 0.05, facecolor="#666666", edgecolor="black", zorder=5))
ax.axhline(0.1, color="#1674b8", linewidth=1.2, zorder=6)
ax.set(xlim=(6.7, 8.3), ylim=(0, 0.15), xlabel="x (m)", ylabel="z (m)",
       title=(f"Step-region mesh: dx={dx:g} m, dz={dz:g} m; "
              f"cells={int(mesh['cell_count']):,}; max non-orthogonality={float(mesh['max_non_orthogonality']):g} deg"))
ax.set_aspect("equal", adjustable="box")
ax.grid(False)
fig.savefig(OUT / "mesh.png", dpi=180)
plt.close(fig)

profiles = defaultdict(list)
for row in read_csv("surface_profiles.csv"):
    profiles[round(float(row["time_s"]), 6)].append((float(row["x_m"]), 1000 * float(row["eta_m"])))

gauges = read_csv("wave_gauges.csv")
fig, axes = plt.subplots(2, 1, figsize=(12, 9), constrained_layout=True)
colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
for target, color in zip((2.0, 4.0, 6.0, 8.0), colors):
    key = min(profiles, key=lambda t: abs(t - target))
    pts = sorted(profiles[key])
    axes[0].plot([p[0] for p in pts], [p[1] for p in pts], linewidth=1.8,
                 color=color, label=f"t={key:g} s")
axes[0].axhline(0, color="black", linewidth=0.7)
axes[0].axvspan(7, 8, color="#777777", alpha=0.16, label="submerged step")
axes[0].set(xlim=(5, 10.2), xlabel="x (m)", ylabel="eta (mm)",
            title="Free-surface profiles from interfaceHeight")
axes[0].grid(alpha=0.25)
axes[0].legend(ncol=3)

times = [float(r["time_s"]) for r in gauges]
palette = plt.cm.viridis([i / 7 for i in range(8)])
for i in range(1, 9):
    axes[1].plot(times, [1000 * float(r[f"eta_G{i}_m"]) for r in gauges],
                 linewidth=1.1, color=palette[i - 1], label=f"G{i}")
axes[1].axhline(0, color="black", linewidth=0.7)
axes[1].set(xlabel="time (s)", ylabel="eta (mm)", title="Wave-gauge time histories")
axes[1].grid(alpha=0.25)
axes[1].legend(ncol=4)
fig.savefig(OUT / "result_01.png", dpi=180)
plt.close(fig)

print("Wrote mesh.png and result_01.png from formal-run data")

