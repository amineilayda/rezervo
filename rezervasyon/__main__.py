import json
import sys

from .komut_isleyici import calistir, sonuc_satiri
from .motor import RezervasyonMotoru


def main(argv: list[str]) -> int:
    # Tam olarak iki dosya yolu bekleniyor; yoksa kullanım bilgisi verip çık
    if len(argv) != 2:
        print("Kullanım: calistir baslangic.json komutlar.jsonl", file=sys.stderr)
        return 2
    # Başlangıç durumunu dosyadan kurarak motoru oluştur
    motor = RezervasyonMotoru.dosyadan(argv[0])
    # Türkçe karakterler Windows konsolunda bozulmasın diye çıktı UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    # utf-8-sig: dosyanın başında BOM varsa atlanır
    with open(argv[1], encoding="utf-8-sig") as f:
        no = 0  # sonuç satırlarındaki "no" alanı (boş satırlar sayılmaz)
        for satir in f:
            if not satir.strip():
                continue
            no += 1
            # Bozuk JSON satırı boş komut sayılır; motor bunu BILINMEYEN_KOMUT ile reddeder
            try:
                komut = json.loads(satir)
            except json.JSONDecodeError:
                komut = {}
            try:
                govde = calistir(motor, komut)
            except Exception as hata:  # tek bozuk satır tüm çıktı
                # Beklenmeyen bir hata tüm çalışmayı durdurmasın; o satır reddedilir
                print(f"#{no}: {hata!r}", file=sys.stderr)
                govde = {"durum": "RED", "kod": "GECERSIZ_KOMUT"}
            # no + komut adı + sonuç alanları tek satır JSON olarak yazılır
            sonuc = sonuc_satiri(no, komut, govde)
            print(json.dumps(sonuc, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
