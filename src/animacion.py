"""
animacion.py — Animación del CubeSat en órbita
Genera un GIF: satélite orbitando la Tierra (con zona de eclipse),
potencia instantánea y SOC acumulándose en tiempo real.
Salida: figures/animacion_orbita.gif
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle, Circle

from orbita import (posicion_satelite, en_eclipse,
                    PERIODO, R_TIERRA, R_ORBITA)
from potencia import potencia_por_cara
from bateria import simular_soc, perfil_consumo

os.makedirs("figures", exist_ok=True)

# --- Simulación base: 2 órbitas, paso grueso para un GIF liviano ---
DT = 30.0                              # [s] paso de la animación
t = np.arange(0, 2 * PERIODO, DT)
x, y, theta = posicion_satelite(t)
eclipse = en_eclipse(x, y)
_, P_gen, _ = potencia_por_cara(t)
P_cons = perfil_consumo(t, eclipse)
soc = simular_soc(t, P_gen, P_cons)

# --- Figura con dos paneles: órbita (izq) y series de tiempo (der) ---
fig = plt.figure(figsize=(10, 4.5))
ax_orb = fig.add_subplot(1, 2, 1)
ax_ts = fig.add_subplot(1, 2, 2)

# Panel orbital (unidades en radios terrestres para escala cómoda)
Re = 1.0
r_orb = R_ORBITA / R_TIERRA
lim = r_orb * 1.25

# Sombra cilíndrica (lado anti-sol: x > 0)
ax_orb.add_patch(Rectangle((0, -Re), lim, 2 * Re,
                           color="gray", alpha=0.25, zorder=0))
ax_orb.add_patch(Circle((0, 0), Re, color="tab:blue", zorder=2))
ax_orb.text(0, 0, "Tierra", ha="center", va="center",
            color="white", fontsize=9, zorder=3)
orb_circle = Circle((0, 0), r_orb, fill=False, ls="--",
                    color="gray", lw=0.8, zorder=1)
ax_orb.add_patch(orb_circle)
# Flechas de sol (llegan desde -X)
for yy in np.linspace(-lim*0.8, lim*0.8, 5):
    ax_orb.annotate("", xy=(-lim*0.75, yy), xytext=(-lim*0.98, yy),
                    arrowprops=dict(arrowstyle="->", color="orange"))
ax_orb.text(-lim*0.97, lim*0.9, "Sol", color="orange", fontsize=9)

sat_dot, = ax_orb.plot([], [], "s", ms=9, color="black", zorder=4)
estado_txt = ax_orb.text(0.03, 0.03, "", transform=ax_orb.transAxes,
                         fontsize=9)
ax_orb.set_xlim(-lim, lim); ax_orb.set_ylim(-lim, lim)
ax_orb.set_aspect("equal"); ax_orb.axis("off")
ax_orb.set_title("CubeSat 3U — LEO 500 km", fontsize=10)

# Panel de series de tiempo
ax_ts.fill_between(t/60, 0, 100, where=eclipse,
                   color="gray", alpha=0.2, label="Eclipse")
ln_soc, = ax_ts.plot([], [], color="tab:blue", lw=1.8, label="SOC [%]")
ln_pgen, = ax_ts.plot([], [], color="tab:green", lw=1.2,
                      label="P gen [W] ×5")
ax_ts.set_xlim(0, t[-1]/60); ax_ts.set_ylim(0, 105)
ax_ts.set_xlabel("Tiempo [min]")
ax_ts.legend(fontsize=8, loc="lower right")
ax_ts.set_title("Balance de energía", fontsize=10)

fig.tight_layout()


def update(k):
    sat_dot.set_data([x[k]/R_TIERRA], [y[k]/R_TIERRA])
    sat_dot.set_color("gray" if eclipse[k] else "goldenrod")
    estado_txt.set_text(
        f"t = {t[k]/60:5.1f} min   "
        f"{'ECLIPSE' if eclipse[k] else 'SOL'}   "
        f"P = {P_gen[k]:4.1f} W   SOC = {100*soc[k]:5.1f} %")
    ln_soc.set_data(t[:k+1]/60, 100*soc[:k+1])
    ln_pgen.set_data(t[:k+1]/60, 5*P_gen[:k+1])   # ×5 para escala visual
    return sat_dot, estado_txt, ln_soc, ln_pgen


anim = FuncAnimation(fig, update, frames=len(t),
                     interval=40, blit=True)

print(f"Generando GIF ({len(t)} cuadros)... esto toma 1-2 minutos")
anim.save("figures/animacion_orbita.gif",
          writer=PillowWriter(fps=25), dpi=90)
print("Listo: figures/animacion_orbita.gif")