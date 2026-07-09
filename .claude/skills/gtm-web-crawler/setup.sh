#!/usr/bin/env bash
# Setup idempotente del gtm-web-crawler. Seguro correr en cada sesion nueva:
# lo que ya esta, lo salta. Primera vez ~1-2 min (instala crawl4ai); luego ~seg.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${CRAWLER_VENV:-$DIR/.venv}"

echo "[1/3] certutil (para el CA del proxy en el NSS de Chromium)..."
if ! command -v certutil >/dev/null 2>&1; then
  apt-get update -qq >/dev/null 2>&1 || true
  apt-get install -y -qq libnss3-tools >/dev/null 2>&1
fi

echo "[2/3] venv + crawl4ai (NO descarga browser: usamos el Chromium preinstalado)..."
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
python -c "import crawl4ai, html2text" 2>/dev/null || pip install -q crawl4ai html2text

echo "[3/3] importar CA del proxy al NSS store (idempotente)..."
python -c "import sys; sys.path.insert(0, '$DIR'); import sandbox_browser as sb; sb.bootstrap_nss()"

echo "OK. Activa con:  source $VENV/bin/activate"
echo "Corre con:      python $DIR/crawl.py DOMINIO"
