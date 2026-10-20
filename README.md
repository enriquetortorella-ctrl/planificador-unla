# Círculo Rojo · Planificador UNLa

Seguimiento de carrera con identidad arcade: personajes, rangos, medallas y
sonidos sintetizados. No realiza inscripciones en SIU ni reemplaza el plan oficial.

## Probar sin datos reales

Python 3.12 recomendado. Desde la carpeta del proyecto:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run demo.py
```

`demo.py` reemplaza el conector antes de cargar la app. Usa un soldado Demo y
datos ficticios en memoria; no importa el conector real ni lee secretos. Los
cambios se pierden al reiniciar la sesión. No usarlo junto a `app.py` dentro del
mismo proceso de Python: el reemplazo del conector es deliberadamente global.

Para ejecutar la app existente con su configuración de Sheets: `python -m streamlit
run app.py`. La configuración privada se conserva en `.streamlit/secrets.toml`,
que está ignorado por Git. No copiar credenciales a archivos de ejemplo o tests.

## Pantallas

- **Mi cursada:** materias activas, parciales, finales pendientes y horarios
  personales; la oferta completa sigue disponible desmarcando el filtro.
- **Planificar:** búsqueda sin tildes, filtros de estado, requisitos y materias
  siguientes. El mapa es opcional y se enfoca en una materia; ofrece acercar,
  alejar, centrar y ver todo. La lista conserva la información para teclado y móvil.
- **Mi avance:** créditos, barras por área, curva de aprobaciones fechadas,
  medallas e historial editable. El escenario de egreso es orientativo.
- **Squad:** actividad del grupo y aprobaciones, como en la versión anterior.

La cabina arcade permite activar sonidos, ajustar volumen y desactivar efectos.
La fuente se sirve desde el proyecto. Los sonidos usan Web Audio con un limitador;
el navegador puede bloquear reproducción automática: se ofrece un botón para
reproducir el efecto. Los GIF existentes se ocultan con movimiento reducido,
igual que el CRT y las animaciones. Las celebraciones son breves y locales.

## Datos y guardado

Se mantienen nombres de columnas, estados y formato de Sheets. Los identificadores
normalizados son internos: no se agregan IDs ni se migran filas existentes. La vista
de avance deduplica materias y usa nombres canónicos; Historial conserva las filas
originales y sus alertas de integridad.

Cada guardado necesita una lectura fresca, compara las filas propias con la copia
que inició la edición, conserva las filas actuales de otros usuarios y verifica la
hoja tras escribir. Si falla la lectura previa, no escribe. Si falla la escritura o
su verificación, no anuncia éxito ni celebra y pide recargar antes de reintentar.
El respaldo `backup` es opcional: su ausencia se informa tras un guardado confirmado.
La copia usada para editar se conserva durante la sesión; sólo se renueva con
Actualizar datos o después de un guardado confirmado, incluso si vence la caché.

**Límite de concurrencia:** Sheets no ofrece una transacción compare-and-swap para
este flujo. Hay exclusión mutua dentro del proceso de la app y detección de datos
propios desactualizados; otro proceso o editor externo aún puede escribir entre
lectura y actualización. Para eliminar ese riesgo hace falta un almacenamiento
transaccional. Esta entrega no cambia el backend ni realiza migraciones.

Elegir un nombre sigue siendo selección de perfil, no autenticación. Mantener la
protección del despliegue existente y revisar permisos antes de compartir públicamente.

No se cambiaron correlativas ni reglas académicas: `Final` o `Aprobada` siguen
habilitando cursar. La restricción real de optativos y la oferta vigente requieren
validación contra documentación oficial. Compartir día genera una advertencia de
horario, no un bloqueo: el catálogo actual no contiene intervalos horarios.

## Regresiones

```sh
python -m unittest discover -s tests -v
```

Los tests usan sólo dobles de conexión y `demo.py`. Cubren fallos de lectura,
escritura/verificación, edición concurrente, preservación de otros usuarios,
navegación de un clic, nota/fecha existentes, aprobación por cursada, búsqueda,
filtros, mapa y ausencia de fechas inventadas. AppTest puede necesitar permiso
para sockets locales internos, aunque no se conecta a Sheets.

Versiones de validación: Python 3.12.14, Streamlit 1.66.0, pandas 3.0.6,
Plotly 7.1.0. No se probó una conexión real a Sheets.

## QA visual pendiente

Las pruebas de Streamlit no renderizan JavaScript ni certifican el diseño.
Comprobar en `demo.py`, escritorio y móvil:

1. Navegar por cada pantalla y cambiar de materia aprobada antes de editar.
2. Abrir mapa, seleccionar nodos, usar teclado, zoom, pan y pellizco; redimensionar.
3. Revisar textos largos, contraste, foco y controles táctiles a 360 y 1280 px.
4. Probar sonido, volumen, bloqueo de autoplay y movimiento reducido del sistema.
5. Registrar una aprobación y comprobar una única celebración; desactivar efectos.

En el entorno de implementación no había un navegador accesible: no se aprobó QA visual.

## Recursos

- Press Start 2P: Copyright 2012 The Press Start 2P Project Authors
  (cody@zone38.net). Descarga del repositorio oficial
  [google/fonts](https://github.com/google/fonts/tree/main/ofl/pressstart2p).
  Fuente sin modificar, SIL Open Font License 1.1; licencia completa en
  `assets/fonts/OFL.txt`.
- El mapa SVG, las partículas y el control de audio nuevos son código local, sin
  librerías ni solicitudes remotas. No se descargaron audios ni GIF nuevos.
- Los GIF de personajes ya estaban en el repositorio. Esta entrega no acredita
  derechos adicionales sobre ellos; revisar su licencia antes de una redistribución.
