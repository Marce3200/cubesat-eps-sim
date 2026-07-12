# Cuando la noche no es el problema 🛰️
### Simulación del presupuesto energético de un CubeSat 3U como backhaul LoRa para redes mesh de emergencia

Simulación modular en Python del balance de energía de un CubeSat 3U
en órbita baja (LEO, 500 km) con apuntamiento nadir, operando como
enlace de retorno (backhaul) LoRa de almacenamiento y reenvío para
redes mesh terrestres de comunicaciones de emergencia.

Este repositorio acompaña al paper *"Cuando la noche no es el
problema: análisis energético de un CubeSat 3U retransmitiendo
tráfico LoRa de emergencia"* (Universidad Andrés Bello, 2026) y
garantiza la reproducibilidad de todos sus resultados y figuras.

## Demostración

![Animación del CubeSat en órbita](figures/animacion_orbita.gif)

El satélite (dorado al sol, gris en eclipse) mantiene apuntamiento
nadir mientras orbita a 500 km. El panel derecho muestra la potencia
generada y el estado de carga de la batería en tiempo real.

## Estructura del proyecto

```
cubesat-eps-sim/
├── src/
│   ├── orbita.py           # geometría orbital y detección de eclipse
│   ├── irradiancia.py      # vector solar y ángulo de incidencia por cara
│   ├── potencia.py         # modelo fotovoltaico y potencia generada
│   ├── bateria.py          # perfil de consumo y balance de energía (caso base)
│   ├── lora.py             # módulo LoRa: pases y escenarios de tráfico
│   ├── escenarios_lora.py  # caso de estudio: SOC bajo tráfico LoRa
│   ├── panel.py            # curva I-V/P-V de la celda con MPP
│   ├── main.py             # orquestador: figuras finales estilo IEEE
│   └── animacion.py        # GIF de la órbita con balance en vivo
├── figures/                # figuras exploratorias y GIF
│   └── final/              # figuras de publicación (generadas por main.py)
├── requirements.txt
└── README.md
```

## Reproducir

```bash
pip install -r requirements.txt
python src/main.py          # regenera todas las figuras del paper
python src/animacion.py     # regenera el GIF (1-2 min)
```

Cada módulo también puede ejecutarse individualmente
(`python src/orbita.py`, etc.) para ver sus figuras exploratorias y
validaciones numéricas.

## Parámetros principales

| Parámetro | Valor | Fuente |
|---|---|---|
| Órbita | Circular, 500 km, β = 0 | — |
| Periodo / eclipse | 94.47 min / 35.71 min (37.8%) | Kepler + sombra cilíndrica |
| Satélite | 3U (10×10×34 cm), apuntamiento nadir, paneles fijos | — |
| Constante solar | 1361 W/m² | Kopp & Lean (2011) |
| Celda solar | Triple juntura, η = 29.5% @ AM0, 28 °C | AzurSpace 3G30C-Advanced |
| Batería | Li-ion 2S2P, 7.4 V, 38.5 Wh, DoD máx 30% | GomSpace BP4 |
| Consumo bus | 1.75 W (supervivencia) / 3.75 W (con payload) | Datasheets GomSpace |
| LoRa | SX1276: RX 0.035 W, TX 1.5 W (con PA), SF12, airtime 2.3 s | Datasheet Semtech |
| Pases | 4/día × 10 min (2 diurnos + 2 nocturnos), por agenda | — |

## Hallazgos principales

**H1 — La cara nadir es casi inútil para generación.**
Su irradiancia máxima alcanza solo 508 W/m² (37.3% del nominal):
su instante óptimo de iluminación cae dentro de la sombra terrestre,
por lo que solo ve el sol en los bordes del eclipse. Validado
analíticamente: cos θ = R⊕/r = 0.373. Coherente con la práctica de
reservar la cara nadir para payload y antenas.

**H2 — El mínimo de generación diurna ocurre en el punto subsolar.**
La curva de potencia total tiene forma de "M": en el instante de
máxima iluminación solo genera la cara zenit (10×10 cm, ~3.2 W)
porque ram y wake pasan por cero. La geometría 3U nadir castiga el
mediodía orbital y motiva paneles desplegables.

**H3 — El balance del caso base cierra con margen ~2.2×.**
Generación media orbital de 5.21 W vs consumo medio de ~2.4 W.
Descargas por eclipse de ~3 puntos de SOC, muy por debajo del
límite de DoD del 30%.

**H4 — El cuello de botella del backhaul LoRa es el canal, no la
energía.** Con SF12 (airtime 2.3 s/paquete), un pase de 10 min tiene
capacidad física de 261 paquetes, independiente de la energía
disponible. Duty cycles: 19.2% (normal, 50 paq), 57.5% (emergencia,
150 paq), 100% saturado (desastre, 400+ paq). Energía por pase:
52.6 / 146.2 / 250.0 mWh — incluso saturado, <1% de la batería.

**H5 — El pase nocturno es el peor caso energético, pero holgado.**
Transmitir en eclipse (emergencia nocturna) es puro consumo de
batería con generación cero; aun así el impacto es <1% de SOC por
pase. Las curvas de SOC de los tres escenarios de tráfico resultan
indistinguibles.

**H6 — La restricción operativa de la misión es la capacidad del
canal, no el presupuesto energético.** Corolario de H4+H5: el EPS
3U estándar soporta el backhaul LoRa con margen amplio incluso en
desastre. El espacio de diseño resultante: más pases/día, batería
menor, payload adicional, SF adaptativo, y arquitecturas DTN de
almacenamiento y reenvío para absorber el tráfico excedente entre
pases.

## Supuestos y limitaciones

- Caso 2D con β = 0: peor caso de eclipse; las caras laterales ±Y
  no generan. La variación anual de β modifica ambos efectos en
  sentidos opuestos.
- Sombra cilíndrica (penumbra despreciada; del orden de segundos a
  500 km).
- Pases por agenda (la simulación 2D no modela la rotación
  terrestre).
- Balance en energía (Wh); la tensión de bus de 7.4 V es documental
  y no entra al cálculo.
- MPPT ideal (extracción siempre en el MPP), justificado con la
  curva I-V de la celda.
- Sin modelo térmico ni degradación por radiación: los valores
  absolutos de generación son optimistas hacia el fin de la vida
  útil.
- El cierre del enlace LoRa a 500 km (link budget) queda fuera del
  alcance.
- La simulación inicia a la salida del eclipse para evitar
  artefactos de condición inicial.

## Validaciones cruzadas

Cada módulo se validó contra valores analíticos antes de integrar:

- Periodo orbital: 94.47 min (Kepler, error < 0.1%).
- Fracción de eclipse: 37.8% vs arcsin(R⊕/r)/π = 37.7% analítico.
- Irradiancia máx. de la cara nadir: 508 W/m² vs 1361·(R⊕/r) = 508.
- MPP de la celda: 1.21 W @ 2.41 V, reproduce los puntos de catálogo
  del datasheet (Vmp = 2411 mV, Imp = 504.4 mA).
- Eficiencia en MPP: 29.5%, consistente con el η = 0.29 usado en el
  modelo de potencia (coherencia mutua de los modelos eléctrico y
  energético).

## Contexto

Este trabajo se desarrolló como proyecto final del curso Transformación y Control de la Energía Electrica y se conecta
con la investigación doctoral Arquitectura resiliente
de comunicaciones de emergencia: mesh LoRa terrestre + DTN + backhaul
satelital) en la Universidad Andrés Bello, Chile.

## Autora

Marcela Quezada-Araya — Universidad Andrés Bello, Santiago, Chile.

Si utilizas este código, por favor cita el repositorio o el paper
asociado.