# HUB USB 3.x – 1 entrada USB‑C y 4 salidas USB‑C (USB5744)

Proyecto de diseño de un hub USB 3.x de alta velocidad (SuperSpeed 5 Gb/s + USB 2.0) basado en el
controlador **Microchip USB5744** (QFN‑56), con un puerto de subida USB‑C (J12) y cuatro puertos de bajada
USB‑C (J1–J4), alimentado desde una fuente externa de 12 V.

Herramientas: **OrCAD X Capture 25.1** (esquemático) y **OrCAD X PCB 25.1 / Allegro** (PCB).
Referencia de diseño: tarjeta de evaluación EVB‑USB5744 de Microchip (hojas 1–3).

Autor: José Rodrigo Quiroa Dávila – Ingeniería en Electrónica y Telecomunicaciones, Universidad del Istmo.

## Estado al 25‑oct‑2026

| Etapa | Estado |
|---|---|
| Esquemático – hoja principal (USB5744, conectores J1–J4/J12, straps, desacople) | ✅ Completo, ordenado como el EVB |
| Esquemático – hoja POWER (12 V → 5 V RPM5.0‑6.0, 1V2 TLV62569, 3V3 MCP1725, reset) | ✅ Completo y verificado |
| Netlist Capture → Allegro | ✅ Importado sin errores |
| Tarjeta: 4 capas (TOP / GND / PWR / BOTTOM), 110 × 60 mm | ✅ Contorno, keep‑in y stackup |
| Colocación de componentes (incluida la etapa de potencia) | ✅ Completa |
| Ruteo de pares diferenciales (20 pares, 45 redes, TOP, sin vías, impedancia ≈ 90 Ω) | ✅ Completo |
| Planos: GND en L2 y 5 V en L3 | ✅ Creados |
| Ruteo de potencia y control (740 pistas, 258 vías) | ✅ Aplicado en HUB.brd, **DRC 0, sin conexiones abiertas** |
| Serigrafía y dibujos de ensamble | ✅ Referencias reubicadas (texto 1.0 mm / trazo 0.15 mm), nada sobre pads |
| Gerbers L1–L4, máscara, pasta, serigrafía y ensamble (TOP y BOTTOM), contorno | ✅ Generados (`entregables/gerber`) |
| Taladro NC (PTH, NPTH y ranuras) | ✅ Generado (`entregables/drill`) |
| PDF del esquemático (hoja principal y POWER) | ✅ `entregables/HUB_esquematico.pdf` |

### Vista de los Gerbers

Cobre TOP (L1) y serigrafía TOP, generados a partir de los Gerbers finales:

![L1 TOP](entregables/vistas/L1_TOP.png)

![Serigrafía TOP](entregables/vistas/SILK_TOP.png)

## Estructura del repositorio

```
orcad/
  Hub.opj            proyecto de Capture
  HUB.DSN            esquemático (2 hojas)
  HUB.brd            PCB de Allegro / OrCAD X PCB
  lib/               símbolos (.OLB) y su exportación XML
  footprints/        footprints (.dra/.psm/.ssm) y padstacks (.pad) propios
docs/
  BOM.csv            lista de materiales exportada de Capture
  decisiones.md      decisiones de diseño y reglas
  img/               imágenes de avance
entregables/         paquete de fabricación: gerber/, drill/, vistas/ y LEEME_fabricacion.md
herramientas/router/ scripts de Python usados para planificar el ruteo
herramientas/allegro/ scripts SKILL aplicados en Allegro (ruteo, films, serigrafía)
herramientas/serigrafia/ scripts de Python para colocar referencias y revisar los Gerbers
```

Para abrir el proyecto: abrir `orcad/Hub.opj` en Capture y `orcad/HUB.brd` en OrCAD X PCB. Los footprints y
padstacks de `orcad/footprints/` deben estar en la ruta de librerías de PCB (o en la misma carpeta que el .brd).

## Próximos pasos

1. Revisión final del paquete con un visor de Gerber antes de enviarlo a fabricar.

> Nota: `orcad/HUB.DSN` es el esquemático de Capture. No exportar a Specctra desde esta carpeta:
> Allegro escribe `HUB.dsn` (mismo nombre) y sobrescribe el esquemático (pasó el 24‑oct; se restauró
> desde el respaldo automático de Capture del 24‑oct 17:26, que coincide con el netlist final).
