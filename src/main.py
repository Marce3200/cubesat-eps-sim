"""
main.py — Orquestador bilingüe: regenera las figuras finales del paper
Uso: ajustar IDIOMA ("en"/"es") y correr  python src/main.py
Salida: figures/final_en/*.pdf  o  figures/final_es/*.pdf
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

# ================== CONFIGURACIÓN DE IDIOMA ==================
IDIOMA = "en"        # "en" -> paper en inglés | "es" -> español

T = {
    "es": {
        "tiempo_min": "Tiempo [min]", "tiempo_h": "Tiempo [h]",
        "irradiancia": "Irradiancia [W/m²]",
        "potencia": "Potencia [W]", "soc": "SOC [%]",
        "tension": "Tensión [V]", "corriente": "Corriente [A]",
        "pot_panel": "Potencia [W]",
        "total": "Total", "eclipse": "Eclipse",
        "dod": "Límite DoD 30%", "mpp": "MPP {:.2f} W",
        "esc": {"Normal (50 paq/pase)": "Normal (50 paq/pase)",
                "Emergencia (150 paq/pase)": "Emergencia (150 paq/pase)",
                "Desastre (400 paq/pase)": "Desastre (400 paq/pase)"},
        "caras": {"zenit": "zenit", "nadir": "nadir", "ram": "ram",
                  "wake": "wake", "lado": "lateral"},
    },
    "en": {
        "tiempo_min": "Time [min]", "tiempo_h": "Time [h]",
        "irradiancia": "Irradiance [W/m²]",
        "potencia": "Power [W]", "soc": "SOC [%]",
        "tension": "Voltage [V]", "corriente": "Current [A]",
        "pot_panel": "Power [W]",
        "total": "Total", "eclipse": "Eclipse",
        "dod": "30% DoD limit", "mpp": "MPP {:.2f} W",
        "esc": {"Normal (50 paq/pase)": "Normal (50 pkt/pass)",
                "Emergencia (150 paq/pase)": "Emergency (150 pkt/pass)",
                "Desastre (400 paq/pase)": "Disaster (400 pkt/pass)"},
        "caras": {"zenit": "zenith", "nadir": "nadir", "ram": "ram",
                  "wake": "wake", "lado": "side"},
    },
}[IDIOMA]

# --- Estilo IEEE ---
plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "legend.fontsize": 6.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "lines.linewidth": 1.2, "figure.dpi": 150,
})
ANCHO = 3.45
OUT = f"figures/final_{IDIOMA}"
os.makedirs(OUT, exist_ok=True)

# --- Corrección de fase: arrancar saliendo del eclipse ---
TH_SALIDA = np.arcsin(R_TIERRA / R_ORBITA)
T_OFFSET = TH_SALIDA / (2 * np.pi) * PERIODO


def tiempos(n_orbitas, paso=10.0):
    t_plot = np.arange(0, n_orbitas * PERIODO, paso)
    return t_plot, t_plot + T_OFFSET


def etiqueta_cara(nombre):
    """'zenit  (+Z, 10x10)' -> 'zenith (+Z)' según idioma."""
    base = nombre.split("(")[0].strip()
    eje = nombre.split("(")[1].split(",")[0].strip()
    return f"{T['caras'][base]} ({eje})"


def fig_irradiancia():
    t, ts = tiempos(2)
    G, ecl = irradiancia_por_cara(ts)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.4))
    for nombre, g in G.items():
        ax.plot(t/60, g, label=etiqueta_cara(nombre))
    ax.fill_between(t/60, 0, G_SOLAR, where=ecl, color="gray", alpha=0.2)
    ax.set_xlabel(T["tiempo_min"]); ax.set_ylabel(T["irradiancia"])
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.32))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig2_irradiancia.pdf")


def fig_potencia():
    t, ts = tiempos(2)
    P, P_tot, ecl = potencia_por_cara(ts)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.4))
    for nombre, p in P.items():
        if p.max() > 0:
            ax.plot(t/60, p, label=etiqueta_cara(nombre))
    ax.plot(t/60, P_tot, "k", lw=1.6, label=T["total"])
    ax.fill_between(t/60, 0, 11, where=ecl, color="gray", alpha=0.2)
    ax.set_xlabel(T["tiempo_min"]); ax.set_ylabel(T["potencia"])
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
    ax.set_xlabel(T["tiempo_min"]); ax.set_ylabel(T["soc"])
    ax.set_ylim(60, 102)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig4_soc_base.pdf")
    print(f"  Base: SOC final {100*soc[-1]:5.1f} %, "
          f"min {100*soc.min():5.1f} %")


def fig_soc_escenarios():
    t, ts = tiempos(15)
    x, y, _ = posicion_satelite(ts)
    ecl = en_eclipse(x, y)
    _, P_gen, _ = potencia_por_cara(ts)
    fig, ax = plt.subplots(figsize=(ANCHO*2, 2.4))
    for nombre, paq in ESCENARIOS.items():
        P_lora = potencia_lora(ts, paq)
        soc = simular_soc(ts, P_gen, perfil_consumo_lora(ts, P_lora))
        ax.plot(t/3600, soc*100, label=T["esc"][nombre])
        print(f"  {T['esc'][nombre]:28s}: final {100*soc[-1]:5.1f} %, "
              f"min {100*soc.min():5.1f} %")
    ax.fill_between(t/3600, 0, 100, where=ecl, color="gray", alpha=0.2)
    ax.axhline(70, color="tab:orange", ls="--", lw=0.9, label=T["dod"])
    ax.set_xlabel(T["tiempo_h"]); ax.set_ylabel(T["soc"])
    ax.set_ylim(60, 102)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.35))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig5_soc_escenarios.pdf")

def fig_geometria():
    from matplotlib.patches import Rectangle, Circle
    fig, ax = plt.subplots(figsize=(ANCHO, 2.7))
    Re = 1.0
    r_orb = 1.6                      # exagerado para legibilidad
    lim = r_orb * 1.30
    # Sombra cilíndrica (lado anti-solar)
    ax.add_patch(Rectangle((0, -Re), lim, 2*Re, color="gray",
                           alpha=0.25, zorder=0))
    ax.text(lim*0.98, Re*1.10, "cylindrical\nshadow",
            fontsize=7, color="gray", ha="right")
    # Tierra
    ax.add_patch(Circle((0, 0), Re, color="tab:blue", zorder=2))
    ax.text(0, 0, "Earth", ha="center", va="center",
            color="white", fontsize=8, zorder=3)
    # Órbita
    ax.add_patch(Circle((0, 0), r_orb, fill=False, ls="--",
                        color="gray", lw=0.9, zorder=1))
    ax.text(0, -r_orb*1.12, "500 km orbit (not to scale)",
            fontsize=7, color="gray", ha="center")
    # Flechas de sol
    for yy in np.linspace(-lim*0.55, lim*0.55, 3):
        ax.annotate("", xy=(-lim*0.80, yy), xytext=(-lim*1.02, yy),
                    arrowprops=dict(arrowstyle="->", color="orange"))
    ax.text(-lim*1.00, lim*0.78, "Sun", color="orange", fontsize=8)
    # Satélite en cuadrante superior derecho, con vector nadir
    th = 0.9
    sx, sy = r_orb*np.cos(th), r_orb*np.sin(th)
    ax.plot([sx], [sy], marker="s", ms=7, color="goldenrod", zorder=4)
    ax.annotate("", xy=(sx*0.62, sy*0.62), xytext=(sx*0.94, sy*0.94),
                arrowprops=dict(arrowstyle="->", lw=0.9))
    ax.text(sx*1.10, sy*1.14, "3U CubeSat\n(nadir pointing)",
            fontsize=7, ha="left")
    # Ángulo theta: arco desde el punto anti-solar (+X) al satélite
    from matplotlib.patches import Arc
    ax.add_patch(Arc((0, 0), r_orb*0.9, r_orb*0.9, angle=0,
                     theta1=0, theta2=np.degrees(th),
                     color="black", lw=0.8))
    ax.annotate("", xy=(r_orb*0.45*np.cos(th*0.95),
                        r_orb*0.45*np.sin(th*0.95)),
                xytext=(r_orb*0.45*np.cos(th*0.75),
                        r_orb*0.45*np.sin(th*0.75)),
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.plot([0, r_orb], [0, 0], color="black", lw=0.6, ls=":")
    ax.text(r_orb*0.55*np.cos(th/2), r_orb*0.50*np.sin(th/2),
            r"$\theta$", fontsize=10)
    ax.set_xlim(-lim*1.15, lim*1.15); ax.set_ylim(-lim, lim)
    ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig0_geometry.pdf")
    
def fig_panel():
    V, I, P = curva_iv()
    k = int(np.argmax(P))
    fig, ax1 = plt.subplots(figsize=(ANCHO, 2.4))
    ax1.plot(V, I, color="tab:blue")
    ax1.set_xlabel(T["tension"])
    ax1.set_ylabel(T["corriente"], color="tab:blue")
    ax2 = ax1.twinx()
    ax2.plot(V, P, color="tab:red")
    ax2.set_ylabel(T["pot_panel"], color="tab:red")
    ax1.plot(V[k], I[k], "ko", ms=4)
    ax2.annotate(T["mpp"].format(P[k]), xy=(V[k], P[k]),
                 xytext=(0.4, P[k]*0.92),
                 arrowprops=dict(arrowstyle="->", lw=0.7))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig6_panel_iv.pdf")


if __name__ == "__main__":
    print(f"Generando figuras [{IDIOMA}] en {OUT}")
    fig_irradiancia()
    fig_potencia()
    fig_soc_base()
    fig_soc_escenarios()
    fig_panel()
    fig_geometria()
    print("Listo:", len(os.listdir(OUT)), "figuras.")