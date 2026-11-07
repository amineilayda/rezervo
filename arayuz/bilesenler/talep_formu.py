from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDateEdit, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from .. import metinler
from .. import tema
from ..istemci import ModulIstemcisi
from .ortak import SaatKutusu, SonucBandi, dugme, dk_ekle, etiket, varsayilan_baslangic

BEKLEME_ONERILEN = {"KESISME", "HAZIRLIK_IHLALI"}



def tarih_kutusu() -> QDateEdit:
    d = QDateEdit()
    d.setCalendarPopup(True)
    
    d.setDisplayFormat("dd.MM.yyyy")
    d.setMinimumWidth(100)
    return d


def kaynak_kutusu() -> QComboBox:
    c = QComboBox()
    c.setMinimumWidth(80)
    return c


def kaynaklari_doldur(kutu: QComboBox, kaynaklar: list[dict], kisa: bool = False) -> None:
    secili = kutu.currentData()
    kutu.blockSignals(True)
    kutu.clear()
    for i, k in enumerate(kaynaklar):
        kutu.addItem(k["id"] if kisa else f"{k['id']} · {k['ad']}", k["id"])
        kutu.setItemData(i, f"{k['ad']} · {k['tur']}", Qt.ToolTipRole)
    i = kutu.findData(secili)
    kutu.setCurrentIndex(i if i >= 0 else 0)
    kutu.blockSignals(False)


def zaman(tarih: QDateEdit, saat: SaatKutusu) -> str:
    return f"{tarih.date().toString('yyyy-MM-dd')}T{saat.deger()}"


def onizleme_metni(sonuc: dict) -> str:
    if sonuc.get("durum") == "TAMAM":
        return f"<span style='color:{tema.METIN}; font-size:13pt; font-weight:600'>{sonuc['ucret']} KP</span>"
    return (f"<span style='color:{tema.HATA}; font-weight:600'>✕ {sonuc['kod']}</span><br>"
            f"<span style='color:{tema.SOLUK}'>{metinler.aciklama(sonuc['kod'])}</span>")


class KalemSatiri(QFrame):
    

    degisti = Signal()
    sil_istendi = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.secimle_dolduruldu = False
        duzen = QGridLayout(self)
        duzen.setContentsMargins(0, 4, 0, 4)
        duzen.setHorizontalSpacing(6)
        duzen.setVerticalSpacing(2)
        self.no = etiket("", "soluk")
        self.no.setFixedWidth(16)
        self.kaynak = kaynak_kutusu()
        self.tarih = tarih_kutusu()
        self.bas = SaatKutusu()
        self.bit = SaatKutusu()
        self.sil = QToolButton()
        self.sil.setText("✕")
        self.sil.setToolTip("Kalemi kaldır")
        self.sil.setCursor(Qt.PointingHandCursor)
        self.sil.clicked.connect(lambda: self.sil_istendi.emit(self))
        self.durum = etiket(kelime_kaydir=True)
        self.durum.setStyleSheet("font-size: 9pt;")
        duzen.addWidget(self.no, 0, 0)
        duzen.addWidget(self.kaynak, 0, 1)
        duzen.addWidget(self.tarih, 0, 2)
        duzen.addWidget(self.bas, 0, 3)
        duzen.addWidget(self.bit, 0, 4)
        duzen.addWidget(self.sil, 0, 5)
        duzen.addWidget(self.durum, 1, 1, 1, 5)
        duzen.setColumnStretch(1, 1)
        for w in (self.kaynak, self.bas, self.bit):
            w.currentTextChanged.connect(self.degisti)
        self.tarih.dateChanged.connect(self.degisti)

    def komut(self) -> dict:
        return {"kaynak": self.kaynak.currentData(), "baslangic": zaman(self.tarih, self.bas),
                
                "bitis": zaman(self.tarih, self.bit)}

    def sonuc_goster(self, html: str) -> None:
        self.durum.setText(html)


class TalepFormu(QWidget):
    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        self.kullanici: str | None = None
        self.kaynaklar: list[dict] = []
        self.son_tek_talep: dict | None = None
        self.paket_sonucu_sabit = False  # gönderim sonucu, kullanıcı alan değiştirene değin kalır

        self.onizleme_zamanlayici = QTimer(self, singleShot=True, interval=120)
        self.onizleme_zamanlayici.timeout.connect(self.onizle)

        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(2, 12, 2, 4)
        duzen.setSpacing(10)

        
        segment = QHBoxLayout()
        segment.setSpacing(0)
        self.tek_btn = dugme("Tek rezervasyon", "segment")
        self.paket_btn = dugme("Paket (2–4 kalem)", "segment")
        grup = QButtonGroup(self)
        for i, b in enumerate((self.tek_btn, self.paket_btn)):
            b.setCheckable(True)
            grup.addButton(b, i)
            segment.addWidget(b)
        self.tek_btn.setChecked(True)
        segment.addStretch(1)
        duzen.addLayout(segment)

        self.yigin = QStackedWidget()
        self.yigin.addWidget(self._tek_sayfa())
        self.yigin.addWidget(self._paket_sayfa())
        duzen.addWidget(self.yigin)
        grup.idClicked.connect(self._mod_degisti)

        self.bant = SonucBandi()
        self.bant.eylem_tiklandi.connect(self.bekleme_ac)
        duzen.addWidget(self.bant)
        duzen.addStretch(1)

    # --- sayfalar -------
    def _tek_sayfa(self) -> QWidget:
        w = QWidget()
        sayfa = QVBoxLayout(w)
        sayfa.setContentsMargins(0, 0, 0, 0)
        sayfa.setSpacing(8)
        izgara = QGridLayout()
        sayfa.addLayout(izgara)
        izgara.setHorizontalSpacing(8)
        izgara.setVerticalSpacing(6)

        self.kaynak = kaynak_kutusu()
        self.tarih = tarih_kutusu()
        self.bas = SaatKutusu()
        self.bit = SaatKutusu()

        izgara.addWidget(etiket("Kaynak", "altBaslik"), 0, 0, 1, 3)
        izgara.addWidget(self.kaynak, 1, 0, 1, 3)
        izgara.addWidget(etiket("Tarih", "altBaslik"), 2, 0)
        izgara.addWidget(etiket("Başlangıç", "altBaslik"), 2, 1)
        izgara.addWidget(etiket("Bitiş", "altBaslik"), 2, 2)
        izgara.addWidget(self.tarih, 3, 0)
        izgara.addWidget(self.bas, 3, 1)
        izgara.addWidget(self.bit, 3, 2)
        izgara.setColumnStretch(0, 1)

        # Hızlı süre seçimi

        sureler = QHBoxLayout()
        sureler.setSpacing(4)
        sureler.addWidget(etiket("Süre:", "soluk"))
        for metin, dk in (("30 dk", 30), ("1 sa", 60), ("2 sa", 120), ("3 sa", 180)):
            b = dugme(metin, "kucuk")
            b.clicked.connect(lambda _=False, d=dk: self.bit.ayarla(dk_ekle(self.bas.deger(), d)))
            sureler.addWidget(b)
        sureler.addStretch(1)
        izgara.addLayout(sureler, 4, 0, 1, 3)

        # Ücret önizlemesi
        ucret_kutu = QFrame()
        ucret_kutu.setObjectName("kart")
        ud = QVBoxLayout(ucret_kutu)
        ud.setContentsMargins(10, 6, 10, 8)
        ud.setSpacing(2)
        ud.addWidget(etiket("Ücret (fiyat önizlemesi)", "altBaslik"))
        self.ucret = etiket(kelime_kaydir=True)
        self.ucret.setTextFormat(Qt.RichText)
        ud.addWidget(self.ucret)
        sayfa.addWidget(ucret_kutu)

        dugmeler = QHBoxLayout()
        self.fiyat_btn = dugme("Fiyat sor", ipucu="fiyat komutu: ücreti günlüğe yazar, durum değişmez")
        self.bekleme_btn = dugme("Bekleme kaydı", ipucu="Dolu aralık için bekleme listesine gir")
        self.gonder_btn = dugme("Rezervasyon yap", "birincil")
        self.fiyat_btn.clicked.connect(lambda: self._tek_gonder("fiyat"))
        self.bekleme_btn.clicked.connect(lambda: self._tek_gonder("bekleme"))
        self.gonder_btn.clicked.connect(lambda: self._tek_gonder("rezervasyon"))
        dugmeler.addWidget(self.fiyat_btn)

        dugmeler.addWidget(self.bekleme_btn)
        dugmeler.addStretch(1)
        dugmeler.addWidget(self.gonder_btn)
        sayfa.addLayout(dugmeler)

        for c in (self.kaynak, self.bas, self.bit):
            c.currentTextChanged.connect(self._degisti)
        self.tarih.dateChanged.connect(self._degisti)
        return w

    def _paket_sayfa(self) -> QWidget:
        w = QWidget()
        d = QVBoxLayout(w)
        d.setContentsMargins(0, 0, 0, 0)
        d.setSpacing(4)
        baslik = QHBoxLayout()
        for metin, genislik in (("", 16), ("Kaynak", 0), ("Tarih", 100), ("Başlangıç", 70), ("Bitiş", 70)):
            e = etiket(metin, "altBaslik")
            if genislik:
                e.setFixedWidth(genislik)
            baslik.addWidget(e, 1 if not genislik else 0)
        baslik.addSpacing(26)
        d.addLayout(baslik)
        self.kalem_alani = QVBoxLayout()
        self.kalem_alani.setSpacing(0)
        d.addLayout(self.kalem_alani)
        self.kalemler: list[KalemSatiri] = []

        ekle = dugme("+ Kalem ekle", "kucuk")
        ekle.clicked.connect(lambda: self.kalem_ekle())
        satir = QHBoxLayout()
        satir.addWidget(ekle)
        satir.addStretch(1)
        satir.addWidget(etiket("Toplam", "altBaslik"))
        self.toplam = etiket()
        self.toplam.setObjectName("buyukDeger")
        satir.addWidget(self.toplam)
        d.addLayout(satir)

        dugmeler = QHBoxLayout()
        dugmeler.addStretch(1)
        self.paket_gonder = dugme("Paketi talep et", "birincil")
        self.paket_gonder.clicked.connect(self.paket_gonder_tiklandi)
        dugmeler.addWidget(self.paket_gonder)
        d.addLayout(dugmeler)
        return w

    # --- dış arayüz ----
    
    # -
    def motor_yuklendi(self) -> None:
        for k in list(self.kalemler):
            self._kalem_sil(k)
        self.bant.temizle()
        self.durum_yenile()
        simdi = self.istemci.motor.durum.saat
        bas = varsayilan_baslangic(simdi)
        self.tarih.setDate(QDate(bas.year, bas.month, bas.day))
        self.bas.ayarla(bas.strftime("%H:%M"))
        self.bit.ayarla(dk_ekle(bas.strftime("%H:%M"), 60))
        self.kalem_ekle()
        self.kalem_ekle()
        self._degisti()

    def durum_yenile(self) -> None:
        self.kaynaklar = self.istemci.motor.goruntu_kaynaklar()
        kaynaklari_doldur(self.kaynak, self.kaynaklar)
        for k in self.kalemler:
            kaynaklari_doldur(k.kaynak, self.kaynaklar, kisa=True)
        self.onizleme_zamanlayici.start()

    def kullanici_ayarla(self, kullanici_id: str | None) -> None:
        self.kullanici = kullanici_id
        self._degisti()

    def secimle_doldur(self, kaynak: str, gun: str, bas: str, bit: str) -> None:

        
        tarih = QDate.fromString(gun, "yyyy-MM-dd")
        if self.yigin.currentIndex() == 0:
            self.kaynak.setCurrentIndex(max(0, self.kaynak.findData(kaynak)))
            self.tarih.setDate(tarih)
            self.bas.ayarla(bas)
            self.bit.ayarla(bit)
            self.gonder_btn.setFocus()
        else:
            hedef = next((k for k in self.kalemler if not k.secimle_dolduruldu), None) or self.kalem_ekle()
            hedef.secimle_dolduruldu = True
            hedef.kaynak.setCurrentIndex(max(0, hedef.kaynak.findData(kaynak)))
            hedef.tarih.setDate(tarih)
            hedef.bas.ayarla(bas)
            hedef.bit.ayarla(bit)
        self.bant.temizle()

    # --- paket kalemleri 
    
    def kalem_ekle(self) -> KalemSatiri:
        k = KalemSatiri()
        kaynaklari_doldur(k.kaynak, self.kaynaklar, kisa=True)
        if self.kalemler:
            onceki = self.kalemler[-1]
            k.tarih.setDate(onceki.tarih.date())
            k.bas.ayarla(onceki.bas.deger())
            k.bit.ayarla(onceki.bit.deger())
        else:
            k.tarih.setDate(self.tarih.date())
            k.bas.ayarla(self.bas.deger())
            k.bit.ayarla(self.bit.deger())
        k.degisti.connect(self._degisti)
        k.sil_istendi.connect(self._kalem_sil)
        self.kalemler.append(k)
        self.kalem_alani.addWidget(k)
        self._numarala()
        self._degisti()
        return k

    def _kalem_sil(self, k: KalemSatiri) -> None:
        self.kalemler.remove(k)
        k.setParent(None)
        k.deleteLater()
        self._numarala()
        self._degisti()

    def _numarala(self) -> None:
        for i, k in enumerate(self.kalemler, 1):
            k.no.setText(str(i))

    # --- önizleme 
    
    def _mod_degisti(self, i: int) -> None:
        self.yigin.setCurrentIndex(i)
        self.bant.temizle()
        self._degisti()

    def _degisti(self, *_):
        self.paket_sonucu_sabit = False
        self.onizleme_zamanlayici.start()

    def onizle(self) -> None:
        if not self.istemci.hazir:
            return
        if self.yigin.currentIndex() == 0:
            sonuc = self.istemci.onizle({"komut": "fiyat", **self._tek_alanlar()})
            self.ucret.setText(onizleme_metni(sonuc))
            return
        if self.paket_sonucu_sabit:
            return
        toplam, eksik = 0, False
        for k in self.kalemler:
            sonuc = self.istemci.onizle({"komut": "fiyat", "kullanici": self.kullanici, **k.komut()})
            k.sonuc_goster(onizleme_metni(sonuc))
            if sonuc["durum"] == "TAMAM":
                toplam += sonuc["ucret"]
            else:
                eksik = True
        self.toplam.setText(f"{toplam} KP" + (" *" if eksik else ""))
        self.toplam.setToolTip("Geçersiz kalemler toplama katılmadı" if eksik else "")

    # --

    # - gönderim ---------------------------
    
    def _tek_alanlar(self) -> dict:
        return {"kullanici": self.kullanici, "kaynak": self.kaynak.currentData(),
                "baslangic": zaman(self.tarih, self.bas), "bitis": zaman(self.tarih, self.bit)}

    def _tek_gonder(self, komut_adi: str) -> None:
        alanlar = self._tek_alanlar()
        satir = self.istemci.gonder({"komut": komut_adi, **alanlar})
        oneri = None
        if komut_adi == "rezervasyon" and satir.get("kod") in BEKLEME_ONERILEN:
            self.son_tek_talep = alanlar
            oneri = "Bekleme listesine gir"
        self.bant.goster(satir, oneri)
        self.onizle()

    def bekleme_ac(self) -> None:

        
        if self.son_tek_talep:
            satir = self.istemci.gonder({"komut": "bekleme", **self.son_tek_talep})
            self.son_tek_talep = None
            self.bant.goster(satir)






    def paket_gonder_tiklandi(self) -> None:
        komut = {"komut": "paket", "kullanici": self.kullanici,
                 "kalemler": [k.komut() for k in self.kalemler]}
        satir = self.istemci.gonder(komut)
        self.paket_sonucu_sabit = True
        self.bant.goster(satir)
        self.toplam.setText(f"{satir['toplam']} KP" if satir["durum"] == "TAMAM" else "—")
        sonuclar = {s["sira"]: s for s in satir.get("kalemler", [])}
        for i, k in enumerate(self.kalemler):
            s = sonuclar.get(i)
            if satir["durum"] == "TAMAM":
                rid, ucret = satir["rezervasyonlar"][i], satir["ucretler"][i]
                k.sonuc_goster(f"<span style='color:{tema.BASARI}; font-weight:600'>✓ {rid}</span> "
                               f"<span style='color:{tema.SOLUK}'>· {ucret} KP</span>")
            elif s is None:
                k.sonuc_goster(f"<span style='color:{tema.SOLUK}'>— değerlendirilmedi</span>")
            elif s["durum"] == "TAMAM":
                k.sonuc_goster(f"<span style='color:{tema.BASARI}; font-weight:600'>✓ Geçti</span>")
            else:
                k.sonuc_goster(f"<span style='color:{tema.HATA}; font-weight:600'>✕ {s['kod']}</span> "
                               f"<span style='color:{tema.SOLUK}'>{metinler.aciklama(s['kod'])}</span>")
        if satir["durum"] == "TAMAM":
            for k in self.kalemler:
                k.secimle_dolduruldu = False
