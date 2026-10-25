# Planificador de ruteo (Python)

Ruteador de rejilla (0.05 mm, A* en 2 capas con vías) usado para planificar el ruteo de potencia y control,
porque el autorouter de Allegro no está licenciado en esta instalación.

- `router.py`: modelo de cobre, campos de distancia, reglas (0.127 mm) y A* (numba).
- `drive.py`, `core.py`: bajadas a planos GND/5V, escapes de U1, ruteo por red y rip‑up & reroute.
- `manual.py`: rutas planificadas a mano en la esquina superior izquierda de U1.
- `xcheck.py`: verificación geométrica exacta (shapely) de separaciones.
- `gen_il.py`: genera el script SKILL que crea pistas y vías en Allegro.
- `plan_ruteo_24oct.json`: resultado actual (722 segmentos, 259 vías) y conexiones pendientes.

Requiere los volcados de Allegro (`claude_pads48.txt`, `claude_etch48.txt`) que generan los scripts SKILL del proyecto.
