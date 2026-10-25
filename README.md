# Hub USB-C de 4 puertos con USB5744

Este es mi proyecto de un hub USB 3.x con una entrada USB-C y cuatro salidas USB-C. El controlador es el USB5744 de Microchip y la tarjeta se alimenta con una fuente externa de 12 V. Como referencia usé la tarjeta de evaluación EVB-USB5744 de Microchip.

Lo diseñé en OrCAD X 25.1: el esquemático en Capture y la PCB en Allegro.

Hecho por José Rodrigo Quiroa Dávila, estudiante de Ingeniería en Electrónica y Telecomunicaciones de la Universidad del Istmo.

## Estado del proyecto

El diseño está terminado. El esquemático tiene dos hojas: la principal, con el USB5744 y los conectores, y la de alimentación, donde se sacan los 5 V, 3.3 V y 1.2 V a partir de los 12 V de entrada.

La PCB es de 4 capas y mide 110 × 60 mm. Los pares diferenciales de USB van por la capa de arriba, sin vías y con una impedancia cercana a 90 Ω. La segunda capa es el plano de tierra y la tercera el de 5 V. Todo está ruteado y el DRC da cero errores.

Ya generé los archivos para fabricarla: los Gerbers de las cuatro capas de cobre, la máscara, la pasta, la serigrafía y el ensamble de los dos lados, el contorno, los archivos de taladro y el PDF del esquemático. Todo está en la carpeta `entregables`.

Así se ven la capa de cobre de arriba y la serigrafía:

![Cobre de la capa de arriba](entregables/vistas/L1_TOP.png)

![Serigrafía de arriba](entregables/vistas/SILK_TOP.png)

## Qué hay en cada carpeta

- `orcad`: el proyecto de Capture, el esquemático, la PCB y los símbolos y footprints que hice o descargué.
- `entregables`: los Gerbers, el taladro, el PDF del esquemático y una hoja que explica cada archivo.
- `docs`: la lista de materiales y las decisiones de diseño.
- `herramientas`: los scripts que usé para el ruteo y para acomodar la serigrafía.

Para abrirlo, hay que abrir `orcad/Hub.opj` en Capture y `orcad/HUB.brd` en OrCAD X PCB. La carpeta `orcad/footprints` tiene que estar en la ruta de librerías de PCB, o si no, copiar esos archivos junto al `.brd`.

## Cuidado con Specctra

No exporten a Specctra desde la carpeta del proyecto. Allegro guarda ese archivo como `HUB.dsn`, con el mismo nombre que el esquemático, y lo sobrescribe. A mí me pasó y tuve que recuperar el esquemático del respaldo automático de Capture.

## Lo que falta

Revisar los Gerbers en un visor antes de mandarlos a fabricar.
