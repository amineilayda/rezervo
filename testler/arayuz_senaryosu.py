"""Örnek senaryonun 19 adımı
: python -m testler.arayuz_senaryosu 
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, QDateTime, QLocale  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from arayuz import tema  # noqa: E402
from arayuz.ana_pencere import AnaPencere  # noqa: E402
from arayuz.bilesenler.rezervasyon_karti import RezervasyonKarti  # noqa: E402
from arayuz.istemci import ModulIstemcisi  # noqa: E402
from testler.karsilastir import alt_kume_mi, oku  # noqa: E402

KOK = Path(__file__).resolve().parent.parent


def tarih(metin: str) -> QDate:
    return QDate.fromString(metin, "yyyy-MM-dd")


def kullanici_ekle(p: AnaPencere, kid, ad, rol, bakiye, guv):
    f = p.ekleme.kullanici
    f.id.setText(kid)
    f.ad.setText(ad)
    f.rol.setCurrentText(rol)
    f.bakiye.setValue(bakiye)
    f.guv.setValue(guv)
    f.ekle.click()


def kaynak_ekle(p: AnaPencere, kid, ad, tur, roller):
    f = p.ekleme.kaynak
    f.tur.setCurrentText(tur)
    f.id.setText(kid)
    f.ad.setText(ad)
    for k in f.roller.kutular:
        k.setChecked(k.text() in roller)
    f.ekle.click()



def tek_talep(p: AnaPencere, kullanici, kaynak, gun, bas, bit, dugme="gonder_btn"):
    p.ozet.sec(kullanici)
    f = p.form
    if f.yigin.currentIndex() != 0:
        f.tek_btn.click()
    f.kaynak.setCurrentIndex(f.kaynak.findData(kaynak))
    f.tarih.setDate(tarih(gun))
    f.bas.ayarla(bas)
    f.bit.ayarla(bit)
    getattr(f, dugme).click()


def paket(p: AnaPencere, kullanici, kalemler):
    p.ozet.sec(kullanici)
    f = p.form
    f.paket_btn.click()
    while len(f.kalemler) < len(kalemler):
        f.kalem_ekle()
    for satir, (kaynak, gun, bas, bit) in zip(f.kalemler, kalemler):
        satir.kaynak.setCurrentIndex(satir.kaynak.findData(kaynak))
        satir.tarih.setDate(tarih(gun))
        satir.bas.ayarla(bas)
        satir.bit.ayarla(bit)
    f.paket_gonder.click()
    f.tek_btn.click()


def panel_eylem(p: AnaPencere, kullanici, rez_id, eylem):
    p.ozet.sec(kullanici)
    t = p.panel.tablo
    for i in range(t.rowCount()):
        if t.item(i, 0).text() == rez_id:
            t.selectRow(i)
    getattr(p.panel, eylem).click()


def calistir(goruntu: str | None = None) -> int:
    QLocale.setDefault(QLocale(QLocale.Turkish, QLocale.Turkey))
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(tema.acik_palet())
    app.setStyleSheet(tema.STIL)
    istemci = ModulIstemcisi()
    p = AnaPencere(istemci)
    p.resize(1440, 880)
    p.show()
    p.dosya_yukle(str(KOK / "ornek" / "baslangic.json"))


    G = "2027-03-08"
    kullanici_ekle(p, "u1", "Ayşe Kaya", "OGRENCI", 120, 80)                       # 1
    kullanici_ekle(p, "u2", "Mehmet Demir", "OGRENCI", 120, 80)                    # 2
    kaynak_ekle(p, "YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])                  # 3
    kaynak_ekle(p, "LAB-1", "Laboratuvar 1", "LAB", ["OGRENCI", "ARASTIRMACI", "TEKNISYEN"])  # 4
    tek_talep(p, "u1", "YAZ-1", G, "11:00", "13:00")                               # 5
    tek_talep(p, "u2", "YAZ-2", G, "10:00", "12:00")                               # 6
    tek_talep(p, "u2", "YAZ-2", G, "12:30", "13:30")                               # 7
    tek_talep(p, "u2", "LAB-1", G, "14:00", "15:00")                               # 8
    tek_talep(p, "u1", "YAZ-1", G, "13:10", "14:00")                               # 9 
    
    tek_talep(p, "u1", "YAZ-1", G, "13:15", "14:00")                               # 10
    tek_talep(p, "u3", "CIH-1", G, "14:00", "16:00", "fiyat_btn")                  # 11
    paket(p, "u3", [("CIH-1", G, "14:00", "16:00"), ("ODA-1", G, "14:00", "16:00")])  # 12
    tek_talep(p, "u1", "CIH-1", G, "16:30", "17:30")                               # 13
    tek_talep(p, "u1", "ODA-2", "2027-03-16", "09:00", "10:00")                    # 14
    tek_talep(p, "u2", "YAZ-1", G, "12:00", "13:00", "bekleme_btn")                # 15
    p.saat_paneli.hedef.setDateTime(QDateTime.fromString("2027-03-08T11:20", "yyyy-MM-ddTHH:mm"))
    p.saat_paneli.ilerlet.click()                                                  # 16
    panel_eylem(p, "u1", "r1", "giris")                                            # 17
    kart = RezervasyonKarti(istemci, "r4", p)                                      # 18 
    
    next(b for b in kart.findChildren(type(p.panel.iptal)) if b.text() == "İptal").click()
    p.ozet.sec("u2")
    p.panel.sorgula.click()                                                        # 19

    beklenen = oku(KOK / "ornek" / "beklenen.jsonl")
    uretilen = [satir for _, satir in istemci.gunluk]
    hata = 0
    for b, u in zip(beklenen, uretilen):
        if not alt_kume_mi(b, u):
            hata += 1
            print(f"FARK #{b['no']}\n  beklenen {b}\n  uretilen {u}")
    if len(beklenen) != len(uretilen):
        hata += 1
        print(f"Satır sayısı farklı: {len(beklenen)} != {len(uretilen)}")
    print(f"Arayüz senaryosu: {len(beklenen) - hata}/{len(beklenen)} eşleşti")

    if goruntu:
        p.ozet.sec("u2")
        p.sekmeler.setCurrentIndex(0)
        app.processEvents()
        p.grab().save(goruntu)
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(calistir(sys.argv[1] if len(sys.argv) > 1 else None))
