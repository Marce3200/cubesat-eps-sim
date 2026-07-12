"""
escenarios_lora.py — Caso de estudio: CubeSat como backhaul LoRa
Integra el módulo LoRa (lora.py) con el balance de energía
(bateria.py) bajo distintos escenarios de tráfico de la red mesh.

El caso base (payload genérico) permanece en bateria.py sin cambios.
Aquí el payload ES el módulo LoRa, con su lógica de pases.
"""
import numpy as np
from orbita import posicion_satelite, en_eclipse, PERIODO
from potencia import potencia_por_cara
from bateria import CONFIG_CONSUMO, simular_soc
from lora import potencia_lora

# --- Escenarios de tráfico: agregar uno = agregar una línea ---
ESCENARIOS = {
    "Normal (50 paq/pase)": 50,
    "Emergencia (150 paq/pase)": 150,
    "Desastre (400 paq/pase)": 400,
}


def perfil_consumo_lora(t, P_lora, cfg=CONFIG_CONSUMO):
    """
    Consumo total [W]: cargas base de bus (siempre activas) + LoRa.
    A diferencia del caso base (bateria.py), no hay payload genérico:
    la carga útil de la misión es el propio módulo LoRa.
    """
    base = cfg["obc"] + cfg["adcs"] + cfg["eps"] + cfg["rx"]
    return np.full_like(t, base, dtype=float) + P_lora


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.makedirs("figures", exist_ok=True)

    N_ORB = 15                      # ~1 día, cubre los 4 pases
    t = np.arange(0, N_ORB * PERIODO, 10.0)
    x, y, _ = posicion_satelite(t)
    eclipse = en_eclipse(x, y)
    _, P_gen, _ = potencia_por_cara(t)

    fig, ax = plt.subplots(figsize=(10, 4))
    for nombre, paq in ESCENARIOS.items():
        P_lora = potencia_lora(t, paq)
        P_cons = perfil_consumo_lora(t, P_lora)
        soc = simular_soc(t, P_gen, P_cons)
        ax.plot(t/3600, soc*100, lw=1.5, label=nombre)
        print(f"{nombre:28s}: SOC final {100*soc[-1]:5.1f} %  "
              f"mínimo {100*soc.min():5.1f} %")

    ax.fill_between(t/3600, 0, 100, where=eclipse, color="gray", alpha=0.2)
    ax.axhline(70, color="tab:orange", ls="--", lw=1, label="Límite DoD 30%")
    ax.set_xlabel("Tiempo [h]")
    ax.set_ylabel("SOC [%]")
    ax.set_ylim(0, 105)
    ax.set_title("SOC bajo escenarios de tráfico LoRa — 1 día, 4 pases")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig("figures/fig6_soc_escenarios.pdf")
    plt.show()