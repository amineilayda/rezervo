"""bölüm 6 örnek senaryosu: 19 komut beklenen sonuçlarla birebir
 python -m unittest discover testler
"""
import json
import unittest
from pathlib import Path

from rezervasyon import RezervasyonMotoru
from rezervasyon.komut_isleyici import calistir, sonuc_satiri
from testler.karsilastir import alt_kume_mi, oku

KOK = Path(__file__).resolve().parent.parent


def senaryo_calistir(baslangic: Path, komutlar: Path) -> list[dict]:
    motor = RezervasyonMotoru.dosyadan(baslangic)
    with open(komutlar, encoding="utf-8") as f:
        komut_listesi = [json.loads(s) for s in f if s.strip()]
    return [sonuc_satiri(i, k, calistir(motor, k)) for i, k in enumerate(komut_listesi, 1)]


class OrnekSenaryo(unittest.TestCase):
    def test_ornek(self):
        ornek = KOK / "ornek"
        if not (ornek / "baslangic.json").exists():
            self.skipTest("ornek/ klasörüne e-destek dosyaları konmadı")
        uretilen = senaryo_calistir(ornek / "baslangic.json", ornek / "komutlar.jsonl")
        for b, u in zip(oku(ornek / "beklenen.jsonl"), uretilen):
            with self.subTest(no=b["no"]):
                self.assertTrue(alt_kume_mi(b, u), f"\n{b}\n{u}")

    def test_kendi_senaryolarimiz(self):
       
        klasor = KOK / "testler" / "senaryolar"
        for komutlar in sorted(klasor.glob("*.jsonl")):
            if komutlar.name.endswith(".beklenen.jsonl"):
                continue
            ad = komutlar.stem
            baslangic = klasor / f"{ad}.baslangic.json"
            if not baslangic.exists():
                baslangic = KOK / "ornek" / "baslangic.json"
            uretilen = senaryo_calistir(baslangic, komutlar)
            beklenen = oku(klasor / f"{ad}.beklenen.jsonl")
            self.assertEqual(len(beklenen), len(uretilen), ad)
            for b, u in zip(beklenen, uretilen):
                with self.subTest(senaryo=ad, no=b["no"]):
                    self.assertTrue(alt_kume_mi(b, u), f"\n{b}\n{u}")


if __name__ == "__main__":
    unittest.main()
