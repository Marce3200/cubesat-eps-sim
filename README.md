# Simulación del sistema de energía de un CubeSat 3U en LEO

Simulación del balance de energía de un CubeSat 3U en órbita baja
(500 km, apuntamiento nadir): irradiancia por cara, potencia generada,
consumo y estado de carga de la batería, incluyendo periodos de eclipse.

## Estructura
- `src/orbita.py` — geometría orbital y detección de eclipse
- `src/irradiancia.py` — vector solar y ángulo de incidencia por cara
- `src/potencia.py` — modelo fotovoltaico y balance de energía
- `src/main.py` — ejecución completa y generación de figuras
- `figures/` — figuras de salida (PDF/PNG)

## Reproducir

    pip install -r requirements.txt
    python src/main.py
