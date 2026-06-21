# Revisión beta humana: La Campana Negra de Bruma

Fecha de análisis: 2026-05-19.
Sesión Codex: `019e36f2-8264-7e23-9791-ebc45fedcb31`.

## Métricas

- 70 turnos de Codex registrados; 69 completados.
- 72 mensajes de usuario y 70 respuestas finales de Codex.
- 56 eventos de generación de imagen.
- Duración media por turno: 277 s; mediana: 269 s.
- Turnos con imagen: media 336 s; mediana 314 s.
- Turnos sin imagen: media 65 s; mediana 60 s.
- Pico de fricción: cadena de tres tiradas bajas alrededor de la trampilla del
  molino, seguida por petición explícita del usuario para avanzar.

## Lo que funcionó

- El opening funcionó porque empezó con presión clara: Luro atrapado, Nela, caja
  peligrosa, guardias acercándose y una decisión inmediata.
- Las consecuencias grises fueron el punto más fuerte: apagar faroles ayudó pero
  borró promesas; destruir la lengua muda impidió nuevos olvidos, pero no bastó
  como prueba pública.
- La sesión permitió jugar con cautela, coartadas, sigilo y contravigilancia sin
  obligar al combate.
- El misterio del Cabildo, la Cofradía y la Campana Negra dejó un hilo claro para
  continuar: recuperar la orden sellada de Luro.
- Las interrupciones fuera de personaje fueron sanas: inventario, habilidades,
  aclaración de relojes, pistas y “no sé cómo continuar” mantuvieron la partida
  usable.

## Problemas detectados

- Las imágenes se usaron casi una por beat. Fue inmersivo, pero elevó latencia,
  coste de revisión y riesgo de drift visual.
- Algunas imágenes colapsaron varios momentos en una sola escena física. El caso
  `desayuno-discreto-posada.png` ya está marcado como `rejected`; la versión
  corregida usa viñetas.
- Estados visibles persistentes, como mano vendada, caja con escala estable,
  capa gris o marca de tiza roja, no tenían un ledger dedicado y dependían de que
  cada prompt los recordase.
- El inventario y XP aparecieron demasiado tarde o solo bajo demanda. La partida
  necesita recompensar progreso con XP, loot útil, contactos, pruebas o ventaja
  narrativa, no solo avanzar la escena.
- Las opciones no siempre mostraban modificadores del personaje. Cuando el
  jugador duda, conviene presentar 2-4 opciones con `Sigilo +5`, `Carisma +0`,
  `Fuerza -1`, dificultad y riesgo visible.
- La trampilla del molino demostró que los fallos repetidos pueden atascar una
  escena. Tras dos fallos contra el mismo obstáculo, el siguiente resultado debe
  mover la ficción con coste.

## Cambios aplicados al plugin

- Añadido `scripts/action_options.py` para formatear opciones con modificadores,
  dificultad y riesgo.
- Añadido `scripts/check_resolution.py` para clasificar checks y forzar
  `failure_forward` con coste y nueva opción.
- Añadido `scripts/comic_panels.py` y `templates/comic-page-prompt.md` para
  decidir entre escena única, cómic, mapa o referencia antes de generar.
- Añadido `templates/visual-ledger.md` para estados visibles persistentes.
- Ampliado `visual-index.md` con columnas de anchors, tags y notas de revisión,
  manteniendo compatibilidad con índices antiguos.
- Ampliadas plantillas de campaña y personaje con XP, loot, moneda, estados
  persistentes y ledger de recompensas.

## Reglas de producto resultantes

- Una escena física coherente puede ser una imagen única.
- Varios lugares, tiempos o acciones consecutivas deben ser viñetas o imágenes
  separadas.
- La generación visual debe leer anchors y ledger antes de pedir una imagen.
- El usuario siempre puede salir de personaje para pedir inventario, habilidades,
  pista, resumen de opciones o aclaración.
- Un fallo debe cambiar la situación; no debe pedir la misma tirada hasta que el
  usuario se aburra.
- Los misterios deben tener hilos concretos: prueba, testigo, lugar, documento,
  deuda o enemigo localizable.
