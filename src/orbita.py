"""
orbita.py — Geometría orbital y detección de eclipse
CubeSat 3U en órbita circular LEO a 500 km, apuntamiento nadir.
Caso 2D: sol en el plano orbital (beta = 0), llegando desde -X.
"""
import numpy as np

# --- Constantes físicas ---
MU_TIERRA = 3.986004418e14   # parámetro gravitacional [m^3/s^2]
R_TIERRA  = 6371e3           # radio medio de la Tierra [m]
ALTURA    = 500e3            # altura de la órbita [m]

# --- Parámetros derivados ---
R_ORBITA = R_TIERRA + ALTURA                              # radio orbital [m]
PERIODO  = 2 * np.pi * np.sqrt(R_ORBITA**3 / MU_TIERRA)   # [s]


def posicion_satelite(t):
    """
    Posición del satélite en el plano orbital (2D).
    t : array de tiempos [s]
    Retorna x, y [m] y el ángulo orbital theta [rad].
    """
    n = 2 * np.pi / PERIODO      # velocidad angular media [rad/s]
    theta = n * t
    x = R_ORBITA * np.cos(theta)
    y = R_ORBITA * np.sin(theta)
    return x, y, theta


def en_eclipse(x, y):
    """
    Modelo de sombra cilíndrica: eclipse si el satélite está en el
    lado anti-sol (x > 0) y dentro del cilindro de sombra (|y| < R_TIERRA).
    Retorna array booleano.
    """
    return (x > 0) & (np.abs(y) < R_TIERRA)


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.makedirs("figures", exist_ok=True)

    # Simular 3 órbitas con paso de 10 s
    t = np.arange(0, 3 * PERIODO, 10.0)
    x, y, theta = posicion_satelite(t)
    eclipse = en_eclipse(x, y)

    frac = eclipse.mean()
    print(f"Periodo orbital : {PERIODO/60:.2f} min")
    print(f"Fracción eclipse: {frac*100:.1f} %")
    print(f"Duración eclipse: {frac*PERIODO/60:.2f} min por órbita")

    # Figura 1: línea de tiempo sol / eclipse
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.fill_between(t/60, 0, 1, where=~eclipse, color="gold",
                    alpha=0.6, label="Sol")
    ax.fill_between(t/60, 0, 1, where=eclipse, color="gray",
                    alpha=0.6, label="Eclipse")
    ax.set_xlabel("Tiempo [min]")
    ax.set_yticks([])
    ax.set_title("Intervalos de sol y eclipse — LEO 500 km, 3 órbitas")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig("figures/fig1_eclipse.pdf")
    plt.show()