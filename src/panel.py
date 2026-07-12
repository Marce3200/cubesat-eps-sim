"""
panel.py — Curva I-V y P-V de la celda solar con MPP
Modelo simplificado de diodo único en forma explícita:
  I(V) = Isc * (1 - C1*(exp(V/(C2*Voc)) - 1))
con C1, C2 calculados desde los puntos de datasheet (Voc, Isc, Vmp, Imp).

Celda de referencia: triple juntura GaInP/GaAs/Ge clase 30%
(tipo AzurSpace 3G30 — valores POR VERIFICAR contra datasheet).
"""
import numpy as np

CONFIG_CELDA = {
    "Voc": 2.70,     # [V] tensión circuito abierto
    "Isc": 0.520,    # [A] corriente cortocircuito
    "Vmp": 2.41,     # [V] tensión en MPP (datasheet)
    "Imp": 0.503,    # [A] corriente en MPP (datasheet)
    "area_cm2": 30.18,   # [cm^2] área activa
}


def curva_iv(cfg=CONFIG_CELDA, n=500):
    """Retorna V, I, P de la celda a irradiancia nominal (AM0, 25°C)."""
    Voc, Isc = cfg["Voc"], cfg["Isc"]
    Vmp, Imp = cfg["Vmp"], cfg["Imp"]

    C2 = (Vmp / Voc - 1.0) / np.log(1.0 - Imp / Isc)
    C1 = (1.0 - Imp / Isc) * np.exp(-Vmp / (C2 * Voc))

    V = np.linspace(0.0, Voc, n)
    I = Isc * (1.0 - C1 * (np.exp(V / (C2 * Voc)) - 1.0))
    I = np.clip(I, 0.0, None)
    return V, I, V * I


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.makedirs("figures", exist_ok=True)

    V, I, P = curva_iv()
    k = np.argmax(P)

    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(V, I, color="tab:blue", lw=1.8, label="Corriente I(V)")
    ax1.set_xlabel("Tensión [V]")
    ax1.set_ylabel("Corriente [A]", color="tab:blue")
    ax1.set_ylim(0, 0.6)

    ax2 = ax1.twinx()
    ax2.plot(V, P, color="tab:red", lw=1.8, label="Potencia P(V)")
    ax2.set_ylabel("Potencia [W]", color="tab:red")
    ax2.set_ylim(0, 1.4)

    ax1.plot(V[k], I[k], "ko", ms=6)
    ax2.annotate(f"MPP: {P[k]:.2f} W @ {V[k]:.2f} V",
                 xy=(V[k], P[k]), xytext=(0.3, 1.25),
                 arrowprops=dict(arrowstyle="->", lw=0.8))
    ax1.set_title("Curva I-V y P-V — celda triple juntura (AM0, 25 °C)")
    fig.tight_layout()
    fig.savefig("figures/fig7_curva_panel.pdf")
    plt.show()

    G0, area_m2 = 1361.0, CONFIG_CELDA["area_cm2"] * 1e-4
    eff = P[k] / (G0 * area_m2)
    print(f"MPP: {P[k]:.3f} W en V = {V[k]:.3f} V, I = {I[k]:.3f} A")
    print(f"Eficiencia en MPP: {100*eff:.1f} %")