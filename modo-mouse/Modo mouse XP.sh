#!/bin/bash
# Prende / apaga el modo mouse XP (palanca derecha = mover, R3 = clic). Hecho por Claude.
D=/userdata/system/cursor_xp; P=/tmp/cursor_xp.pid
avisar(){ curl -s -X POST http://127.0.0.1:1234/notify -d "$1" >/dev/null 2>&1; }
if [ -f $P ] && kill -0 "$(cat $P)" 2>/dev/null; then
  kill "$(cat $P)"; rm -f $P; avisar "Modo mouse XP desactivado"
else
  nohup python3 $D/cursor_xp.py >/dev/null 2>&1 &
  echo $! > $P; sleep 2
  if kill -0 "$(cat $P)" 2>/dev/null; then avisar "Modo mouse XP activado: palanca derecha + R3"; else rm -f $P; avisar "No se pudo activar el modo mouse (ver /tmp/cursor_xp.log)"; fi
fi
exit 0
