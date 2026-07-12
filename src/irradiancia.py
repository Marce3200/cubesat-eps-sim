"""
irradiancia.py — Vector solar en el marco del cuerpo e irradiancia por cara
CubeSat 3U con apuntamiento nadir. Caso 2D (beta = 0).

Marco del cuerpo (convención):
  +Z_b : zenit (opuesto a la Tierra)     — cara 10x10 cm
  -Z_b : nadir (apunta a la Tierra)      — cara 10x10 cm... 

OJO: en un 3U el eje largo suele alinearse con nadir-zenit, de modo que
las tapas 10x10 son nadir/zenit y las caras 10x30 son las laterales.
  +X_b : dirección de vuelo (ram)        — cara 10x30 cm
  -X_b : anti-vuelo (wake)               — cara 10x30 cm
  +Y_b / -Y_b : normal al plano orbital  — caras 10x30 cm
"""
import numpy as np
from orbita import posicion_satelite, en_eclipse, PERIODO

# --- Constantes ---
G_SOLAR = 1361.0   # constante solar [W/m^2]

# --- Geometría del 3U: nombre, vector normal (marco cuerpo), área [m^2] ---
CARAS = {
    "zenit  (+Z, 10x10)": (np.array([0, 0, 1]),  0.01),
    "nadir  (-Z, 10x10)": (np.array([0, 0, -1]), 0.01),
    "ram    (+X, 10x30)": (np.array([1, 0, 0]),  0.03),
    "wake   (-X, 10x30)": (np.array([-1, 0, 0]), 0.03),
    "lado   (+Y, 10x30)": (np.array([0, 1, 0]),  0.03),
    "lado   (-Y, 10x30)": (np.array([0, -1, 0]), 0.03),
}


def vector_sol_cuerpo(theta):
    """
    Dirección DESDE el satélite HACIA el sol, en el marco del cuerpo.

    En el marco inercial el sol está en -X (los rayos viajan hacia +X).
    Con apuntamiento nadir, el marco del cuerpo rota con el ángulo
    orbital theta: 
      -Z_b apunta a la Tierra (dirección -r̂),
      +X_b apunta en la dirección de vuelo (tangente a la órbita).

    Resultado (derivación en el paper):
      s_body = [ sin(theta), 0, -cos(theta) ]
    """
    s = np.zeros((len(theta), 3))
    s[:, 0] = np.sin(theta)
    s[:, 1] = 0.0
    s[:, 2] = -np.cos(theta)
    return s


def irradiancia_por_cara(t):
    """
    Irradiancia [W/m^2] sobre cada cara a lo largo del tiempo.
    G_cara = G_SOLAR * max(0, n̂ · ŝ), y 0 durante eclipse.
    Retorna dict {nombre_cara: array} y el array de eclipse.
    """
    x, y, theta = posicion_satelite(t)
    eclipse = en_eclipse(x, y)
    s_body = vector_sol_cuerpo(theta)

    G = {}
    for nombre, (normal, _area) in CARAS.items():
        cos_theta_i = s_body @ normal
        g = G_SOLAR * np.clip(cos_theta_i, 0.0, None)
        g[eclipse] = 0.0
        G[nombre] = g
    return G, eclipse


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.makedirs("figures", exist_ok=True)

    t = np.arange(0, 2 * PERIODO, 10.0)   # 2 órbitas para claridad
    G, eclipse = irradiancia_por_cara(t)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for nombre, g in G.items():
        ax.plot(t/60, g, label=nombre, linewidth=1.5)
    ax.fill_between(t/60, 0, G_SOLAR, where=eclipse,
                    color="gray", alpha=0.2, label="Eclipse")
    ax.set_xlabel("Tiempo [min]")
    ax.set_ylabel("Irradiancia [W/m²]")
    ax.set_title("Irradiancia por cara — 3U nadir, LEO 500 km (β = 0)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig("figures/fig2_irradiancia_caras.pdf")
    plt.show()

    # Validación numérica rápida
    for nombre, g in G.items():
        print(f"{nombre}: máx = {g.max():7.1f} W/m²")