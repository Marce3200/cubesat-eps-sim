"""
potencia.py — Potencia eléctrica generada por cara y total
P_cara = G_cara * A_cara * f_empaque * eta_celda * eta_mppt
"""
import numpy as np
from orbita import posicion_satelite, en_eclipse, PERIODO
from irradiancia import irradiancia_por_cara, CARAS

# --- Parámetros del sistema fotovoltaico ---
CONFIG_PV = {
    "eta_celda": 0.29,     # eficiencia celda triple juntura (GaAs) a 25°C
    "f_empaque": 0.90,     # fracción de cara realmente cubierta por celdas
    "eta_mppt": 0.90,      # eficiencia del convertidor MPPT
    # Caras SIN celdas solares (nadir: ocupada por payload/antena)
    "caras_sin_celdas": ["nadir  (-Z, 10x10)"],
}


def potencia_por_cara(t, config=CONFIG_PV):
    """
    Potencia eléctrica [W] entregada al bus por cada cara, y la total.
    Retorna (dict {cara: array}, array P_total, array eclipse).
    """
    G, eclipse = irradiancia_por_cara(t)
    eta_total = config["eta_celda"] * config["f_empaque"] * config["eta_mppt"]

    P = {}
    for nombre, (_normal, area) in CARAS.items():
        if nombre in config["caras_sin_celdas"]:
            P[nombre] = np.zeros_like(G[nombre])
        else:
            P[nombre] = G[nombre] * area * eta_total

    P_total = np.sum(list(P.values()), axis=0)
    return P, P_total, eclipse


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.makedirs("figures", exist_ok=True)

    t = np.arange(0, 2 * PERIODO, 10.0)
    P, P_total, eclipse = potencia_por_cara(t)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)

    for nombre, p in P.items():
        ax1.plot(t/60, p, label=nombre, linewidth=1.2)
    ax1.fill_between(t/60, 0, 10, where=eclipse, color="gray", alpha=0.2)
    ax1.set_ylabel("Potencia por cara [W]")
    ax1.set_title("Potencia generada — 3U nadir, LEO 500 km (β = 0)")
    ax1.legend(fontsize=7, ncol=2, loc="upper right")
    ax1.set_ylim(0, 10)

    ax2.plot(t/60, P_total, color="black", linewidth=1.8, label="P total")
    ax2.axhline(P_total[~eclipse].mean(), color="tab:blue", linestyle="--",
                linewidth=1, label=f"Media en sol: {P_total[~eclipse].mean():.2f} W")
    ax2.fill_between(t/60, 0, P_total.max()*1.1, where=eclipse,
                     color="gray", alpha=0.2, label="Eclipse")
    ax2.set_xlabel("Tiempo [min]")
    ax2.set_ylabel("Potencia total [W]")
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig("figures/fig3_potencia.pdf")
    plt.show()

    # Validación numérica
    print(f"P máx por cara 10x30 : {max(P[c].max() for c in P):6.2f} W")
    print(f"P total máxima       : {P_total.max():6.2f} W")
    print(f"P media (solo en sol): {P_total[~eclipse].mean():6.2f} W")
    print(f"P media orbital      : {P_total.mean():6.2f} W")