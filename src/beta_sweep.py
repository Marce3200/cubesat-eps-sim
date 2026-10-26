"""Beta-angle sweep of the energy balance of a nadir-pointing 3U CubeSat.

Extends the two-dimensional model of the paper ("When Night Is Not the
Problem: Energy Analysis of a 3U CubeSat Relaying Emergency LoRa
Traffic") to an arbitrary beta angle, i.e., the angle between the Sun
direction and the orbital plane. For each beta it reports the eclipse
duration, the orbit-average generation, the energy margin with respect
to the baseline consumption, and the battery discharge per eclipse.

At beta = 0 the script reproduces the values reported in the paper
(35.7 min eclipse, 5.21 W average generation, 1.74x margin, 2.85 % SOC
eclipse discharge).

Usage:
    python beta_sweep.py              # prints the table
    python beta_sweep.py --csv out.csv  # also saves it as CSV
"""
import argparse
import csv

import numpy as np

# Orbit
MU = 3.986e14            # Earth's gravitational parameter [m^3/s^2]
R_EARTH = 6371e3         # mean Earth radius [m]
ALTITUDE = 500e3         # orbit altitude [m]
R_ORBIT = R_EARTH + ALTITUDE

# Photovoltaic model (Eq. 5 of the paper)
G0 = 1361.0              # solar constant [W/m^2]
F_PACKING = 0.90
ETA_CELL = 0.29
ETA_MPPT = 0.90
A_LONG = 0.030           # cell-populated area of each long face [m^2]
A_ZENITH = 0.010         # cell-populated area of the zenith face [m^2]
# The nadir face carries antennas and payload and does not generate.

# Consumption and storage (Section III-C of the paper)
P_BUS = 1.75             # continuous bus loads [W]
P_PAYLOAD = 2.0          # baseline payload, active only in sunlight [W]
E_BATTERY = 38.5         # battery capacity [Wh]
ETA_DISCHARGE = 0.95

N_SAMPLES = 200_000      # samples per orbit


def orbit_period_min():
    return 2 * np.pi * np.sqrt(R_ORBIT**3 / MU) / 60


def evaluate(beta_deg):
    """Return eclipse [min], average generation [W], margin, discharge [%]."""
    beta = np.radians(beta_deg)
    theta = np.linspace(0, 2 * np.pi, N_SAMPLES, endpoint=False)

    # Unit Sun vector in the body frame (theta measured from the
    # anti-solar point; reduces to Eq. 3 of the paper for beta = 0).
    s_x = np.sin(theta) * np.cos(beta)
    s_y = np.full_like(theta, np.sin(beta))
    s_z = -np.cos(theta) * np.cos(beta)

    # Cylindrical shadow: anti-solar side and closer to the Sun-Earth
    # axis than one Earth radius.
    along_axis = np.cos(theta) * np.cos(beta)
    dist_axis = R_ORBIT * np.sqrt(1 - along_axis**2)
    eclipse = (along_axis > 0) & (dist_axis < R_EARTH)

    k = G0 * F_PACKING * ETA_CELL * ETA_MPPT
    # ram/wake (|s_x|) and +Y/-Y (|s_y|): exactly one face of each pair
    # is lit; zenith only when the Sun is above it (s_z > 0).
    power = k * (A_LONG * np.abs(s_x)
                 + A_LONG * np.abs(s_y)
                 + A_ZENITH * np.maximum(0.0, s_z))
    power[eclipse] = 0.0

    period = orbit_period_min()
    sun_fraction = 1 - eclipse.mean()
    eclipse_min = eclipse.mean() * period
    avg_gen = power.mean()
    avg_cons = P_BUS + P_PAYLOAD * sun_fraction
    margin = avg_gen / avg_cons
    discharge = (P_BUS * eclipse_min / 60 / ETA_DISCHARGE) / E_BATTERY * 100
    return eclipse_min, avg_gen, margin, discharge


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", help="optional output CSV file")
    args = parser.parse_args()

    betas = [0, 15, 30, 45, 60, 68, 75, 90]
    rows = [(b, *evaluate(b)) for b in betas]

    print(f"{'beta [deg]':>10} {'eclipse [min]':>14} {'avg gen [W]':>12}"
          f" {'margin':>7} {'eclipse discharge [% SOC]':>26}")
    for b, ecl, gen, mar, dis in rows:
        print(f"{b:>10} {ecl:>14.1f} {gen:>12.2f} {mar:>6.2f}x {dis:>26.2f}")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["beta_deg", "eclipse_min", "avg_generation_W",
                        "margin", "eclipse_discharge_pct_soc"])
            for row in rows:
                w.writerow([f"{v:.4f}" if isinstance(v, float) else v
                            for v in row])
        print(f"\nSaved to {args.csv}")


if __name__ == "__main__":
    main()
