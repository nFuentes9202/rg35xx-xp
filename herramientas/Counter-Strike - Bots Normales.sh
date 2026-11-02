#!/bin/bash
# Lanzador creado por Claude: fija la dificultad de los bots YaPB (Normales = 2) y abre Counter-Strike
sed -i "s/^yb_difficulty \"[0-9]\"/yb_difficulty \"2\"/" /userdata/roms/ports/counter-strike/cstrike/addons/yapb/conf/yapb.cfg
exec "/userdata/roms/ports/Counter-Strike.sh" "$@"
