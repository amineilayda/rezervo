""" python -m testler.karsilastir .jsonl uretilen.jsonl
"""
import json
import sys


def alt_kume_mi(beklenen, uretilen) -> bool:
    if isinstance(beklenen, dict):
        return isinstance(uretilen, dict) and all(
            k in uretilen and alt_kume_mi(v, uretilen[k]) for k, v in beklenen.items())
    if isinstance(beklenen, list):
        return (isinstance(uretilen, list) and len(beklenen) == len(uretilen)
                and all(alt_kume_mi(b, u) for b, u in zip(beklenen, uretilen)))
    return beklenen == uretilen


def oku(yol: str) -> list[dict]:
    # Windows PowerShell 5.1 '>' yönlendirmesi UTF-16 yazar
    with open(yol, "rb") as f:
        ham = f.read()
    kodlama = "utf-16" if ham[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    return [json.loads(s) for s in ham.decode(kodlama).splitlines() if s.strip()]


def main(beklenen_yol: str, uretilen_yol: str) -> int:
    beklenen, uretilen = oku(beklenen_yol), oku(uretilen_yol)
    hata = 0
    for i, b in enumerate(beklenen):
        u = uretilen[i] if i < len(uretilen) else None
        if u is None or not alt_kume_mi(b, u):
            hata += 1
            print(f"#{i + 1}\n  beklenen: {json.dumps(b, ensure_ascii=False)}\n"
                  f"  uretilen: {json.dumps(u, ensure_ascii=False)}")
    print(f"{len(beklenen) - hata}/{len(beklenen)} satır eşleşti")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
