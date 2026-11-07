from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
## kullanici bilgiler bakiye gğvenilirlik rol


from .. import metinler
from .. import tema
from ..istemci import ModulIstemcisi
from .ortak import SonucBandi, dugme, etiket


class KullaniciOzeti(QFrame):
    kullanici_degisti = Signal(object)  # str | None

    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        duzen = QGridLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.setHorizontalSpacing(14)
        duzen.setVerticalSpacing(4)

        duzen.addWidget(etiket("Kullanıcı", "altBaslik"), 0, 0, 1, 2)
        self.secici = QComboBox()
        self.secici.setMinimumWidth(200)
        self.secici.currentIndexChanged.connect(self._secim_degisti)
        duzen.addWidget(self.secici, 1, 0, 1, 2)

        self.bakiye = etiket("—", "buyukDeger")
        self.bakiye_bar = QProgressBar()
        self.bakiye_bar.setTextVisible(False)
        self.guv = etiket("—", "buyukDeger")
        self.guv_bar = QProgressBar()
        self.guv_bar.setTextVisible(False)
        self.guv_bar.setRange(0, 100)
        self.rol = etiket("", "soluk")
        self.rol.setWordWrap(True)

        duzen.addWidget(etiket("Bakiye", "altBaslik"), 2, 0)
        duzen.addWidget(etiket("Güvenilirlik", "altBaslik"), 2, 1)
        duzen.addWidget(self.bakiye, 3, 0)
        duzen.addWidget(self.guv, 3, 1)
        duzen.addWidget(self.bakiye_bar, 4, 0)
        duzen.addWidget(self.guv_bar, 4, 1)
        duzen.addWidget(self.rol, 5, 0, 1, 2)
        duzen.setColumnStretch(0, 1)
        duzen.setColumnStretch(1, 1)

    def secili(self) -> str | None:
        return self.secici.currentData()

    def _secim_degisti(self, _=None) -> None:
        self._degerleri_yaz(self._kullanici_bul(self.secili()))
        self.kullanici_degisti.emit(self.secili())

    def _kullanici_bul(self, kid: str | None) -> dict | None:
        if not self.istemci.hazir:
            return None
        return next((u for u in self.istemci.motor.goruntu_kullanicilar() if u["id"] == kid), None)

    def sec(self, kullanici_id: str) -> None:
        i = self.secici.findData(kullanici_id)
        if i >= 0:
            self.secici.setCurrentIndex(i)

    def yenile(self) -> None:
        motor = self.istemci.motor
        kullanicilar = motor.goruntu_kullanicilar()
        secili = self.secili()
        self.secici.blockSignals(True)
        self.secici.clear()
        for u in kullanicilar:
            self.secici.addItem(f"{u['id']} · {u['ad']}  ({u['rol']})", u["id"])
        i = self.secici.findData(secili)
        self.secici.setCurrentIndex(i if i >= 0 else 0)
        self.secici.blockSignals(False)
        if self.secili() != secili:
            self.kullanici_degisti.emit(self.secili())
        self._degerleri_yaz(next((u for u in kullanicilar if u["id"] == self.secili()), None))

    def _degerleri_yaz(self, u: dict | None) -> None:
        if u is None:
            self.bakiye.setText("—")
            self.guv.setText("—")
            self.rol.setText("Kullanıcı yok")
            return
        rol = self.istemci.motor.goruntu_parametreler()["roller"][u["rol"]]
        kota = rol["haftalik_kota"]
        self.bakiye.setText(f"{u['bakiye']} <span style='color:{tema.SOLUK}; font-size:9pt; "
                            f"font-weight:400'>/ {kota} KP</span>")
        self.bakiye_bar.setRange(0, max(1, kota))
        self.bakiye_bar.setValue(u["bakiye"])
        dusuk = u["guvenilirlik"] < 50
        renk = tema.HATA if dusuk else tema.BASARI
        self.guv.setText(f"<span style='color:{renk}'>{u['guvenilirlik']}</span>"
                         f"<span style='color:{tema.SOLUK}; font-size:9pt; font-weight:400'> / 100</span>")
        self.guv_bar.setValue(u["guvenilirlik"])
        self.guv_bar.setStyleSheet(f"QProgressBar::chunk {{ background: {renk}; }}")
        sertifika = ", ".join(u["sertifikalar"]) or "sertifika yok"
        uyari = " · <b style='color:%s'>paket yapılamaz</b>" % tema.HATA if dusuk else ""
        self.rol.setText(f"{u['rol']} · en fazla {rol['azami_sure_dk']} dk · {u['ileri_gun']} gün ileri · "
                         f"{sertifika}{uyari}")


class KullaniciPaneli(QWidget):
    rezervasyona_git = Signal(str)  # rezervasyon id 

    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        self.kullanici: str | None = None

        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(2, 12, 2, 4)
        duzen.setSpacing(8)

        ust = QHBoxLayout()
        ust.addWidget(etiket("Rezervasyonlar", "altBaslik"))
        ust.addStretch(1)
        self.sorgula = dugme("Sorgula", "kucuk", "sorgu komutu (tur: kullanici)")
        self.sorgula.clicked.connect(self.sorgula_tiklandi)
        ust.addWidget(self.sorgula)
        duzen.addLayout(ust)

        self.tablo = self._tablo(["No", "Kaynak", "Zaman", "KP", "Durum"])
        self.tablo.itemSelectionChanged.connect(self._secim_degisti)
        self.tablo.itemDoubleClicked.connect(
            lambda _: self.secili_rez() and self.rezervasyona_git.emit(self.secili_rez()))
        duzen.addWidget(self.tablo, 3)



        eylem = QHBoxLayout()
        self.secili_etiket = etiket("Bir rezervasyon seçin", "soluk")
        eylem.addWidget(self.secili_etiket, 1)
        self.giris = dugme("Giriş", "kucuk")
        self.cikis = dugme("Çıkış", "kucuk")
        self.iptal = dugme("İptal", "kucuk")
        self.iptal.setObjectName("tehlike")
        for b, ad in ((self.giris, "giris"), (self.cikis, "cikis"), (self.iptal, "iptal")):
            b.clicked.connect(lambda _=False, k=ad: self.eylem(k))
            eylem.addWidget(b)
        duzen.addLayout(eylem)
        self.bant = SonucBandi()
        duzen.addWidget(self.bant)

        duzen.addWidget(etiket("Bekleme kayıtları", "altBaslik"))
        self.bekleme = self._tablo(["No", "Kaynak", "Zaman", "Sıra"])
        duzen.addWidget(self.bekleme, 1)
        self._secim_degisti()

    def _tablo(self, basliklar: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(basliklar))
        t.setHorizontalHeaderLabels(basliklar)
        t.verticalHeader().hide()
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.SingleSelection)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setDefaultSectionSize(26)
        h = t.horizontalHeader()
        h.setHighlightSections(False)
        for i in range(len(basliklar)):
            h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        return t

    # --
    def kullanici_ayarla(self, kullanici_id: str | None) -> None:
        if kullanici_id != self.kullanici:
            self.bant.temizle()
        self.kullanici = kullanici_id
        self.yenile()

    def yenile(self) -> None:
        if not self.istemci.hazir:
            return
        secili = self.secili_rez()
        sorgu = self.istemci.motor.sorgu_kullanici(self.kullanici) if self.kullanici else {}
        rezler = sorgu.get("rezervasyonlar", [])
        self.tablo.setRowCount(len(rezler))
        for i, r in enumerate(rezler):
            zaman = f"{metinler.tarih_saat(r['baslangic'])}–{metinler.saat_kismi(r['bitis'])}"
            dolgu, kenar, yazi = tema.DURUM_RENKLERI[r["durum"]]
            hucreler = [r["id"], r["kaynak"], zaman, str(r["ucret"]),
                        tema.DURUM_ETIKETLERI[r["durum"]]]
            for j, metin in enumerate(hucreler):
                oge = QTableWidgetItem(metin)
                oge.setData(Qt.UserRole, r["id"])
                if j == 3:
                    oge.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if j == 4:
                    oge.setForeground(QColor(yazi))
                    oge.setBackground(QColor(dolgu))
                self.tablo.setItem(i, j, oge)
            if r["id"] == secili:
                self.tablo.selectRow(i)

        kayitlar = self.istemci.motor.goruntu_bekleme_kayitlari(self.kullanici) if self.kullanici else []
        self.bekleme.setRowCount(len(kayitlar))
        for i, b in enumerate(kayitlar):
            zaman = f"{metinler.tarih_saat(b['baslangic'])}–{metinler.saat_kismi(b['bitis'])}"
            for j, metin in enumerate([b["id"], b["kaynak"], zaman, str(b["sira"])]):
                self.bekleme.setItem(i, j, QTableWidgetItem(metin))
        self._secim_degisti()

    def secili_rez(self) -> str | None:
        satirlar = self.tablo.selectionModel().selectedRows()
        if not satirlar:
            return None
        oge = self.tablo.item(satirlar[0].row(), 0)
        return oge.data(Qt.UserRole) if oge else None

    def _secim_degisti(self) -> None:
        rid = self.secili_rez()
        for b in (self.giris, self.cikis, self.iptal):
            b.setEnabled(rid is not None)  
        self.secili_etiket.setText(f"<b>{rid}</b> seçili" if rid else "Bir rezervasyon seçin")

    def eylem(self, komut: str) -> None:
        rid = self.secili_rez()
        if rid:
            self.bant.goster(self.istemci.gonder({"komut": komut, "rezervasyon": rid}))

    def sorgula_tiklandi(self) -> None:
        self.bant.goster(self.istemci.gonder({"komut": "sorgu", "tur": "kullanici", "id": self.kullanici}))
