#!/usr/bin/env sh
# Masaüstü uygulaması: ./uygulama.sh [baslangic.json]
DIZIN="$(cd "$(dirname "$0")" && pwd)"
for ADAY in python3 python py; do
  if command -v "$ADAY" >/dev/null 2>&1 &&
     "$ADAY" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    PYTHONPATH="$DIZIN" exec "$ADAY" -m arayuz "$@"
  fi
done
echo "Python 3.11+ bulunamadi" >&2
exit 1
