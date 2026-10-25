# Paquete de fabricación – HUB USB‑C 1×4 (USB5744)

Estado al 25‑oct‑2026 00:45: ruteo completo, **DRC 0**, sin conexiones abiertas.

Tarjeta de 4 capas, 110 × 60 mm, espesor 1.6 mm (stackup tipo JLC04161H‑3313), cobre exterior 1 oz.
Coordenadas absolutas en mm, origen del diseño en la esquina inferior izquierda (50, 50) del contorno.

## Gerber (RS‑274X, mm, formato 3.5, ceros iniciales suprimidos)

| Archivo | Contenido |
|---|---|
| gerber/L1_TOP.art | Cobre capa 1 (TOP: señales y pares diferenciales USB) |
| gerber/L2_GND.art | Cobre capa 2 (plano GND, positivo) |
| gerber/L3_PWR.art | Cobre capa 3 (plano 5 V, positivo) |
| gerber/L4_BOTTOM.art | Cobre capa 4 (BOTTOM) |
| gerber/MASK_TOP.art, MASK_BOTTOM.art | Máscara antisoldante. **Vías tapadas (tented)**: solo abren pines |
| gerber/PASTE_TOP.art, PASTE_BOTTOM.art | Pasta / esténcil (14 capacitores 0402 en BOTTOM bajo U1) |
| gerber/SILK_TOP.art, SILK_BOTTOM.art | Serigrafía; texto de 1.0 mm con trazo de 0.15 mm; sin serigrafía sobre pads (verificado) |
| gerber/ASSY_TOP.art, ASSY_BOTTOM.art | Dibujos de ensamble (referencias dentro de cada componente) |
| gerber/OUTLINE.art | Contorno de la tarjeta (110 × 60 mm) |

Las capas de cobre, máscara y serigrafía no llevan el contorno; el contorno va en OUTLINE.art.

## Taladro (Excellon mejorado, mm, formato 3.5, absoluto)

| Archivo | Contenido |
|---|---|
| drill/HUB-1-4.drl | Agujeros metalizados: 0.20 (12 vías chicas), 0.33 (246 vías), 0.40 (60 pines TH USB‑C), 0.79, 1.20, 2.40 mm |
| drill/HUB-1-4-np.drl | No metalizados: 0.65 (10, postes USB‑C) y 1.60 (1, guía del jack J5) |
| drill/HUB_1-4_plated.rou | Ranuras metalizadas (NC route, fresa 0.5 mm): 20 ovaladas 0.5×1.1 (lengüetas del blindaje USB‑C) y 4 rectangulares (J5) |

## Reglas usadas

Pista/espacio mínimo 0.127/0.127 mm; vía 0.33/0.61 mm y vía chica 0.20/0.45 mm (solo junto a U1);
pares diferenciales USB 0.14/0.14 mm (≈ 90 Ω diferencial referidos al plano GND de L2).

## Otros

- brd/HUB.brd: tarjeta de Allegro con los films de artwork ya definidos.
- vistas/*.png: vista previa de cada Gerber, generada a partir de los archivos para revisarlos.
- gerber/photoplot.log, drill/ncdrill.log, drill/ncroute.log: bitácoras de Allegro. Las únicas advertencias
  son "Null REGULAR‑PAD" en los agujeros de montaje USB‑C, que son NPTH sin cobre (es lo esperado).
