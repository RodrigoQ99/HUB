# Decisiones de diseño y reglas

## Stackup (4 capas, estilo JLC04161H‑3313, 1.6 mm)
| Capa | Uso | Espesor |
|---|---|---|
| L1 TOP | señales, pares diferenciales | 35 µm |
| prepreg εr 4.1 | | 0.0994 mm |
| L2 GND | plano de tierra (referencia de TOP) | |
| núcleo εr 4.6 | | 1.265 mm |
| L3 PWR | plano de 5 V | |
| prepreg εr 4.1 | | 0.0994 mm |
| L4 BOTTOM | señales, desacople | 35 µm |

## Reglas
- Ancho/espacio por defecto: 0.127 / 0.127 mm. Agujeros no metalizados: 0.2032 mm.
- Pares diferenciales (CSet DP90): W = 0.14 mm, S = 0.14 mm → Zdiff ≈ 90 Ω. Tolerancia de fase 0.127 mm en pares SS.
- Vía estándar `via`: broca 0.33 mm, pad 0.61 mm. Vía pequeña `VIA02B`: broca 0.20 mm, pad 0.45 mm (solo junto a U1).
- Anchos de potencia planificados: 12 V 1.0 mm, PWR1‑4 (VBUS de puertos) 0.6 mm, VDD12/1V2 0.5 mm, 3V3/VDD33 0.4 mm.

## Topología USB
- TX con capacitores de acople AC en línea; RX directo a B10/B11.
- USB 2.0 solo en A6/A7 (B6/B7 NC); cruce resuelto con puente de 0 Ω en D− (R111–R115).
- Consecuencia: los receptáculos Type‑C funcionan en una sola orientación.

## Alimentación
- Entrada 12 V por jack CUI PJ‑063AH, protección de polaridad con MOSFET P AO4407A.
- 5 V: módulo RECOM RPM5.0‑6.0 (6 A). 1V2: TI TLV62569 (VDD12 ≈ 0.7 A). 3V3: MCP1725 (VDD33 sube después de VDD12).
- Reset: red RC + pulsador + PWRGD del MCP1725 hacia RESET_N (U1.42).

## Correcciones hechas el 24‑oct
- Huella del cristal Y1 (XTAL3225): el padstack SMD140X120 estaba en unidades erróneas (pads de 0.036 mm);
  se reemplazó por SMD140X120MM (1.4 × 1.2 mm).
- El autorouter Specctra no corre en esta instalación (licencia en modo demo); el ruteo de potencia se planifica con
  scripts propios (`herramientas/router`) y se aplica con SKILL.

## Decisiones de ruteo junto a U1 (pendientes de aplicar)
- C75 (desacople VDD12, BOTTOM) se corre +2.0 mm en X y +0.5 mm en Y para liberar espacio de vías a las señales PRT_CTL.
- R117 (TESTEN) se mueve ~6.5 mm hacia arriba, sobre Y1, para que TESTEN no cruce las líneas del cristal.
- VDD12 une sus pines por el anillo entre la fila de pines y el pad térmico de U1 (0.65 mm disponibles).
- Las salidas de la esquina superior izquierda de U1 (TESTEN, XTALI/XTALO, RBIAS, VDD33) van ruteadas a mano.
- Lado derecho de U1: VBUS_DET va directo a R62/C65/R110; las cuatro señales de strap hacia U11 (pines 38–41)
  pasan por encima de R110 y bajan entre las dos columnas de U11, entrando a los pines por dentro.
