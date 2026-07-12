"""
lora.py — Módulo IoT LoRa: backhaul satélite <-> red mesh terrestre
El transceptor se activa solo durante pases sobre la zona de cobertura
(Chile): RX continuo + ráfagas TX según tráfico. Sleep fuera de pase.

Consumos según datasheet Semtech SX1276 (+ PA para enlace satelital).
"""
import numpy as np
from orbita import PERIODO

CONFIG_LORA = {
    "p_sleep": 0.0,          # [W] <1.5 uA -> despreciable
    "p_rx": 0.035,           # [W] escucha continua durante el pase
    "p_tx": 1.5,             # [W] TX con amplificador (enlace 500 km)
    "airtime_s": 2.3,        # [s] paquete ~50 bytes, SF12, BW 125 kHz
    "t_pase_s": 600.0,       # [s] duración del pase (~10 min)
    # Inicio de cada pase, en fracción de órbita [n_orbita + fase]:
    # fase 0.5 = punto subsolar (día) / fase 0.0 = anti-solar (eclipse)
    "pases": [2.5, 6.0, 10.5, 14.0],   # 2 diurnos + 2 nocturnos
}


def mascara_pases(t, cfg=CONFIG_LORA):
    """True cuando el satélite está sobre la zona de cobertura."""
    en_pase = np.zeros_like(t, dtype=bool)
    for p in cfg["pases"]:
        t0 = p * PERIODO
        en_pase |= (t >= t0) & (t < t0 + cfg["t_pase_s"])
    return en_pase


def duty_tx(paquetes_por_pase, cfg=CONFIG_LORA):
    """
    Fracción del pase transmitiendo. Saturado en 1.0: el pase tiene
    capacidad física máxima de t_pase/airtime paquetes.
    """
    demanda = paquetes_por_pase * cfg["airtime_s"] / cfg["t_pase_s"]
    return min(demanda, 1.0)


def potencia_lora(t, paquetes_por_pase, cfg=CONFIG_LORA):
    """
    Consumo del módulo LoRa [W] en el tiempo.
    Durante el pase: promedio ponderado RX/TX según duty cycle.
    Fuera del pase: sleep.
    """
    d = duty_tx(paquetes_por_pase, cfg)
    p_pase = cfg["p_rx"] + d * (cfg["p_tx"] - cfg["p_rx"])
    P = np.full_like(t, cfg["p_sleep"], dtype=float)
    P[mascara_pases(t, cfg)] = p_pase
    return P


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt
    from orbita import posicion_satelite, en_eclipse

    os.makedirs("figures", exist_ok=True)

    N_ORB = 15                       # ~1 día
    t = np.arange(0, N_ORB * PERIODO, 10.0)
    x, y, _ = posicion_satelite(t)
    eclipse = en_eclipse(x, y)

    escenarios = {"Normal (50 paq/pase)": 50,
                  "Emergencia (150 paq/pase)": 150,
                  "Desastre (400 paq/pase)": 400}

    fig, ax = plt.subplots(figsize=(10, 3.5))
    for nombre, paq in escenarios.items():
        ax.plot(t/3600, potencia_lora(t, paq), lw=1.5,
                label=f"{nombre} — duty {100*duty_tx(paq):.0f}%")
    ax.fill_between(t/3600, 0, 1.6, where=eclipse, color="gray",
                    alpha=0.2, label="Eclipse")
    ax.set_xlabel("Tiempo [h]")
    ax.set_ylabel("P LoRa [W]")
    ax.set_title("Consumo módulo LoRa — 4 pases/día sobre zona mesh")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig("figures/fig5_lora.pdf")
    plt.show()

    cap = CONFIG_LORA["t_pase_s"] / CONFIG_LORA["airtime_s"]
    print(f"Capacidad física del pase: {cap:.0f} paquetes (SF12)")
    for nombre, paq in escenarios.items():
        d = duty_tx(paq)
        e_pase = (CONFIG_LORA["p_rx"] + d*(CONFIG_LORA["p_tx"]
                  - CONFIG_LORA["p_rx"])) * CONFIG_LORA["t_pase_s"] / 3600
        print(f"{nombre:28s}: duty {100*d:5.1f} %  "
              f"-> {e_pase*1000:6.1f} mWh por pase")