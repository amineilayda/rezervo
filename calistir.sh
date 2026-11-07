#!/usr/bin/env sh
# Kullanım: ./calistir.sh baslangic.json komutlar.jsonl > sonuclar.jsonl
DIZIN="$(cd "$(dirname "$0")" && pwd)"
for ADAY in python3 python py; do
  if command -v "$ADAY" >/dev/null 2>&1 &&
     "$ADAY" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    PYTHONPATH="$DIZIN" PYTHONIOENCODING=utf-8 exec "$ADAY" -m rezervasyon "$@"
  fi
done
echo "Python 3.11+ bulunamadi" >&2
exit 1
