#!/bin/bash
# Scanner de Acciones — arranque para macOS (doble clic)
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python no está instalado en esta Mac."
  echo "Descárgalo de https://www.python.org/downloads/ , instálalo y vuelve a abrir este archivo."
  read -p "Presiona Enter para salir..."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Preparando la app por primera vez (puede tardar 1-2 minutos)..."
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

if [ ! -f tv_sessionid.txt ]; then
  echo ""
  echo "OPCIONAL — datos en TIEMPO REAL con tu cuenta Premium de TradingView:"
  echo "pega aquí tu cookie sessionid y presiona Enter."
  echo "(o deja vacío y presiona Enter para usar datos con ~15 min de retraso)"
  read -p "sessionid: " SID
  if [ -n "$SID" ]; then
    echo "$SID" > tv_sessionid.txt
  fi
fi

if [ -f tv_sessionid.txt ]; then
  export TV_SESSIONID="$(cat tv_sessionid.txt)"
  echo "Tiempo real activado con tu sesión Premium."
fi

echo "Iniciando Scanner de Acciones en http://localhost:8877 ..."
( sleep 2; open "http://localhost:8877" ) &
./.venv/bin/python app.py
