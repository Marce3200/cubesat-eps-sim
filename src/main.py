"""
main.py — Orquestador: regenera todas las figuras finales del paper
Corre: python src/main.py   (desde la raíz del proyecto)
Salida: figures/final/*.pdf
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from orbita import (posicion_satelite, en_eclipse,
                    PERIODO, R_TIERRA, R_ORBITA)
from irradiancia import irradiancia_por_cara, G_SOLAR
from potencia import potencia_por_cara
from bateria import CONFIG_CONSUMO, simular_soc, perfil_consumo
from lora import potencia_lora, CONFIG_LORA, duty_tx
from escenarios_lora import ESCENARIOS, perfil_consumo_lora
from panel import curva_iv

# --- Estilo IEEE ---
plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "legend.fontsize": 6.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "lines.linewidth": 1.2, "figure.dpi": 150,
})
ANCHO = 3.45          # [in] ancho de columna IEEE
OUT = "figures/final"
os.makedirs(OUT, exist_ok=True)

# --- Corrección de fase: arrancar saliendo del eclipse ---
TH_SALIDA = np.arcsin(R_TIERRA / R_ORBITA)          # ~68.1°
T_OFFSET = TH_SALIDA / (2 * np.pi) * PERIODO

def tiempos(n_orbitas, paso=10.0):
    """Array de tiempo de simulación desplazado a la salida del eclipse."""
    t_plot = np.arange(0, n_orbitas * PERIODO, paso)
    return t_plot, t_plot + T_OFFSET


def fig_eclipse():
    t, ts = tiempos(3)
    x, y, _ = posicion_satelite(ts)
    ecl = en_eclipse(x, y)
    fig, ax = plt.subplots(figsize=(ANCHO, 1.4))
    ax.fill_between(t/60, 0, 1, where=~ecl, color="gold", alpha=0.6)
    ax.fill_between(t/60, 0, 1, where=ecl, color="gray", alpha=0.6)
    ax.set_xlabel("Tiempo [min]"); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(f"{OUT}/fig1_eclipse.pdf")


def fig_irradiancia():
    t, ts = tiempos(2)
    G, ecl = irradiancia_por_cara(ts)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.4))
    for nombre, g in G.items():
        ax.plot(t/60, g, label=nombre.split("(")[0].strip())
    ax.fill_between(t/60, 0, G_SOLAR, where=ecl, color="gray", alpha=0.2)
    ax.set_xlabel("Tiempo [min]"); ax.set_ylabel("Irradiancia [W/m²]")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.32))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig2_irradiancia.pdf")


def fig_potencia():
    t, ts = tiempos(2)
    P, P_tot, ecl = potencia_por_cara(ts)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.4))
    for nombre, p in P.items():
        if p.max() > 0:
            ax.plot(t/60, p, label=nombre.split("(")[0].strip())
    ax.plot(t/60, P_tot, "k", lw=1.6, label="Total")
    ax.fill_between(t/60, 0, 11, where=ecl, color="gray", alpha=0.2)
    ax.set_xlabel("Tiempo [min]"); ax.set_ylabel("Potencia [W]")
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.32))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig3_potencia.pdf")


def fig_soc_base():
    t, ts = tiempos(5)
    x, y, _ = posicion_satelite(ts)
    ecl = en_eclipse(x, y)
    _, P_gen, _ = potencia_por_cara(ts)
    P_cons = perfil_consumo(ts, ecl)
    soc = simular_soc(ts, P_gen, P_cons)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.2))
    ax.plot(t/60, soc*100, color="tab:blue")
    ax.fill_between(t/60, 0, 100, where=ecl, color="gray", alpha=0.2)
    ax.axhline(70, color="tab:orange", ls="--", lw=0.9)
    ax.set_xlabel("Tiempo [min]"); ax.set_ylabel("SOC [%]")
    ax.set_ylim(60, 102)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig4_soc_base.pdf")
    print(f"  Caso base : SOC final {100*soc[-1]:5.1f} %, "
          f"mínimo {100*soc.min():5.1f} %")


def fig_soc_escenarios():
    t, ts = tiempos(15)
    x, y, _ = posicion_satelite(ts)
    ecl = en_eclipse(x, y)
    _, P_gen, _ = potencia_por_cara(ts)
    fig, ax = plt.subplots(figsize=(ANCHO*2, 2.4))
    for nombre, paq in ESCENARIOS.items():
        P_lora = potencia_lora(ts, paq)
        soc = simular_soc(ts, P_gen, perfil_consumo_lora(ts, P_lora))
        ax.plot(t/3600, soc*100, label=nombre)
        print(f"  {nombre:28s}: SOC final {100*soc[-1]:5.1f} %, "
              f"mínimo {100*soc.min():5.1f} %")
    ax.fill_between(t/3600, 0, 100, where=ecl, color="gray", alpha=0.2)
    ax.axhline(70, color="tab:orange", ls="--", lw=0.9)
    ax.set_xlabel("Tiempo [h]"); ax.set_ylabel("SOC [%]")
    ax.set_ylim(60, 102)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.35))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig5_soc_escenarios.pdf")


def fig_panel():
    V, I, P = curva_iv()
    k = int(np.argmax(P))
    fig, ax1 = plt.subplots(figsize=(ANCHO, 2.4))
    ax1.plot(V, I, color="tab:blue")
    ax1.set_xlabel("Tensión [V]")
    ax1.set_ylabel("Corriente [A]", color="tab:blue")
    ax2 = ax1.twinx()
    ax2.plot(V, P, color="tab:red")
    ax2.set_ylabel("Potencia [W]", color="tab:red")
    ax1.plot(V[k], I[k], "ko", ms=4)
    ax2.annotate(f"MPP {P[k]:.2f} W", xy=(V[k], P[k]),
                 xytext=(0.4, P[k]*0.92),
                 arrowprops=dict(arrowstyle="->", lw=0.7))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig6_panel_iv.pdf")


if __name__ == "__main__":
    print("Generando figuras finales en", OUT)
    fig_eclipse()
    fig_irradiancia()
    fig_potencia()
    fig_soc_base()
    fig_soc_escenarios()
    fig_panel()
    print("Listo:", len(os.listdir(OUT)), "figuras.")