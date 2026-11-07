from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel

from .. import metinler
from .. import tema
from ..istemci import ModulIstemcisi
from .ortak import AcilirKart, SonucBandi, dugme, etiket


def durum_rozeti(durum: str) -> str:
    dolgu, kenar, yazi = tema.DURUM_RENKLERI[durum]
    return (f"<span style='background-color:{dolgu}; color:{yazi}; font-weight:600;'>"
            f"&nbsp;&nbsp;{tema.DURUM_ETIKETLERI[durum]}&nbsp;&nbsp;</span>")


class RezervasyonKarti(AcilirKart):
    def __init__(self, istemci: ModulIstemcisi, rez_id: str, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        self.rez_id = rez_id
        self.setMinimumWidth(340)

        ust = QHBoxLayout()
        self.baslik = etiket("", "baslik")
        self.rozet = QLabel()
        ust.addWidget(self.baslik)
        ust.addStretch(1)
        ust.addWidget(self.rozet)
        self.duzen.addLayout(ust)

        self.form = QFormLayout()
        self.form.setHorizontalSpacing(14)
        self.form.setVerticalSpacing(4)
        self.alanlar = {}

        for ad in ("Kullanıcı", "Kaynak", "Aralık", "Ücret", "Paket"):
            lbl = etiket()
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.alanlar[ad] = lbl
            baslik = etiket(ad, "soluk")
            self.form.addRow(baslik, lbl)
        self.duzen.addLayout(self.form)

        eylem = QHBoxLayout()
        eylem.addStretch(1)
        for metin, komut, ad in (("Giriş", "giris", None), ("Çıkış", "cikis", None), ("İptal", "iptal", "tehlike")):
            b = dugme(metin, ad)
            b.clicked.connect(lambda _=False, k=komut: self.eylem(k))
            eylem.addWidget(b)
        self.duzen.addLayout(eylem)
        self.bant = SonucBandi()

        
        self.duzen.addWidget(self.bant)
        self.yenile()

    def yenile(self) -> None:
        motor = self.istemci.motor
        r = motor.goruntu_rezervasyon(self.rez_id)
        if r is None:
            return
        kullanicilar = {u["id"]: u for u in motor.goruntu_kullanicilar()}
        kaynaklar = {k["id"]: k for k in motor.goruntu_kaynaklar()}
        self.baslik.setText(f"Rezervasyon {r['id']}")
        self.rozet.setText(durum_rozeti(r["durum"]))
        u = kullanicilar.get(r["kullanici"], {})
        k = kaynaklar.get(r["kaynak"], {})
        self.alanlar["Kullanıcı"].setText(f"{r['kullanici']} · {u.get('ad', '')}")
        self.alanlar["Kaynak"].setText(f"{r['kaynak']} · {k.get('ad', '')}")
        self.alanlar["Aralık"].setText(
            f"{r['baslangic'][8:10]}.{r['baslangic'][5:7]}.{r['baslangic'][:4]}  "
            f"{metinler.saat_kismi(r['baslangic'])}–{metinler.saat_kismi(r['bitis'])}")
        self.alanlar["Ücret"].setText(f"{r['ucret']} KP")
        self.alanlar["Paket"].setText(r["paket"] or "—")

    def eylem(self, komut: str) -> None:
        satir = self.istemci.gonder({"komut": komut, "rezervasyon": self.rez_id})
        self.bant.goster(satir)
        self.yenile()
        self.adjustSize()


class KaynakSorguKarti(AcilirKart):
    """Kaynak adına tıklanınca o günün 'sorgu kaynak' sonucunu gösterir."""

    def __init__(self, istemci: ModulIstemcisi, kaynak_id: str, gun: str, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        satir = istemci.gonder({"komut": "sorgu", "tur": "kaynak", "id": kaynak_id, "gun": gun})
        self.duzen.addWidget(etiket(f"{kaynak_id} · {gun[8:10]}.{gun[5:7]}.{gun[:4]} doluluğu", "baslik"))
        bant = SonucBandi()
        bant.goster(satir)
        self.duzen.addWidget(bant)

