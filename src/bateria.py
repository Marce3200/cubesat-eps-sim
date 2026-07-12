"""
bateria.py — Perfil de consumo y balance de energía (SOC)
Integración: E[k+1] = E[k] + (P_gen*eff_carga - P_cons/eff_descarga) * dt
"""
import numpy as np
from orbita import posicion_satelite, en_eclipse, PERIODO
from potencia import potencia_por_cara

# --- Perfil de consumo [W] ---
CONFIG_CONSUMO = {
    "obc": 0.40,        # computador de a bordo (100%)
    "adcs": 1.00,       # control de actitud (100%)
    "eps": 0.15,        # electrónica de potencia (100%)
    "rx": 0.20,         # radio en recepción (100%)
    "tx": 4.00,         # radio transmitiendo (solo en pases, aquí: 0)
    "payload": 2.00,    # carga útil (solo fuera de eclipse)
}

# --- Batería (GomSpace BP4-like, 2S2P Li-ion) ---
CONFIG_BATERIA = {
    "capacidad_wh": 38.5,
    "soc_inicial": 0.70,    # arrancamos al 70% para ver la dinámica
    "dod_max": 0.30,        # alarma si SOC < 70%... ver nota abajo
    "eff_carga": 0.95,
    "eff_descarga": 0.95,
}


def perfil_consumo(t, eclipse, cfg=CONFIG_CONSUMO):
    """
    Consumo total [W]: cargas base siempre activas;
    payload solo en sol (se apaga en eclipse); TX omitida en caso base.
    """
    base = cfg["obc"] + cfg["adcs"] + cfg["eps"] + cfg["rx"]
    P = np.full_like(t, base, dtype=float)
    P[~eclipse] += cfg["payload"]
    return P


def simular_soc(t, P_gen, P_cons, cfg=CONFIG_BATERIA):
    """
    Integra el balance de energía. La batería absorbe el excedente
    (con eff_carga) y entrega el déficit (con eff_descarga).
    SOC saturado en [0, 1]: si llega a 1, el excedente se desecha
    (los MPPT reales hacen shunt/derating).
    Retorna SOC (fracción 0-1).
    """
    dt = np.diff(t, prepend=t[0])  # [s]; primer elemento dt=0
    cap_J = cfg["capacidad_wh"] * 3600.0
    E = np.empty_like(t, dtype=float)
    E[0] = cfg["soc_inicial"] * cap_J

    for k in range(1, len(t)):
        balance = P_gen[k] - P_cons[k]      # [W]
        if balance >= 0:
            dE = balance * cfg["eff_carga"] * dt[k]
        else:
            dE = balance / cfg["eff_descarga"] * dt[k]
        E[k] = np.clip(E[k-1] + dE, 0.0, cap_J)

    return E / cap_J


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.makedirs("figures", exist_ok=True)

    N_ORB = 5
    t = np.arange(0, N_ORB * PERIODO, 10.0)
    x, y, theta = posicion_satelite(t)
    eclipse = en_eclipse(x, y)

    _, P_gen, _ = potencia_por_cara(t)
    P_cons = perfil_consumo(t, eclipse)
    soc = simular_soc(t, P_gen, P_cons)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)

    ax1.plot(t/60, P_gen, color="tab:green", label="Generada", lw=1.5)
    ax1.plot(t/60, P_cons, color="tab:red", label="Consumida", lw=1.5)
    ax1.fill_between(t/60, 0, 11, where=eclipse, color="gray", alpha=0.2)
    ax1.set_ylabel("Potencia [W]")
    ax1.set_title(f"Balance de energía y SOC — {N_ORB} órbitas")
    ax1.legend(fontsize=8)

    ax2.plot(t/60, soc*100, color="tab:blue", lw=1.8)
    ax2.fill_between(t/60, 0, 100, where=eclipse, color="gray", alpha=0.2)
    ax2.axhline(70, color="tab:orange", ls="--", lw=1,
                label="Límite DoD 30%")
    ax2.set_xlabel("Tiempo [min]")
    ax2.set_ylabel("SOC [%]")
    ax2.set_ylim(0, 105)
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig("figures/fig4_soc.pdf")
    plt.show()

    dod_por_eclipse = 100 * (soc.max() - soc[eclipse].min()) if eclipse.any() else 0
    print(f"Consumo en sol      : {P_cons[~eclipse].mean():5.2f} W")
    print(f"Consumo en eclipse  : {P_cons[eclipse].mean():5.2f} W")
    print(f"SOC final           : {100*soc[-1]:5.1f} %")
    print(f"SOC mínimo          : {100*soc.min():5.1f} %")