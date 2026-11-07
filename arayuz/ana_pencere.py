from __future__ import annotations

from PySide6.QtCore import Qt, QDate, QPoint
from PySide6.QtWidgets import (
    QDateEdit, QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QScrollArea, QSplitter, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)

from . import tema
from .bilesenler.ekleme_diyaloglari import EklemePaneli
from .bilesenler.kullanici_paneli import KullaniciOzeti, KullaniciPaneli
from .bilesenler.olay_gunlugu import OlayGunlugu
from .bilesenler.ortak import dugme, etiket
from .bilesenler.rezervasyon_karti import KaynakSorguKarti, RezervasyonKarti
from .bilesenler.saat_paneli import SaatPaneli
from .bilesenler.takvim import Takvim
from .bilesenler.talep_formu import TalepFormu
from .istemci import ModulIstemcisi



def kart(*ic: QWidget, kenar: int = 12) -> QFrame:
    f = QFrame()
    f.setObjectName("kart")
    d = QVBoxLayout(f)
    d.setContentsMargins(kenar, kenar, kenar, kenar)
    d.setSpacing(8)
    for w in ic:
        d.addWidget(w)
    return f


def renk_aciklamasi() -> QWidget:
    w = QWidget()
    d = QHBoxLayout(w)
    d.setContentsMargins(0, 0, 0, 0)
    d.setSpacing(10)
    ogeler = [(ad, *tema.DURUM_RENKLERI[k][:2]) for k, ad in tema.DURUM_ETIKETLERI.items()]
    ogeler += [("Bakım", tema.BAKIM_DOLGU, tema.BAKIM_CIZGI), ("Hazırlık", tema.HAZIRLIK_DOLGU, tema.HAZIRLIK_CIZGI)]
    for ad, dolgu, kenar in ogeler:
        kutu = QLabel()
        kutu.setFixedSize(12, 12)
        stil = "dashed" if ad == "İptal" else "solid"
        kutu.setStyleSheet(f"background:{dolgu}; border:1px {stil} {kenar}; border-radius:3px;")
        d.addWidget(kutu)
        lbl = etiket(ad, "soluk")
        lbl.setStyleSheet("font-size: 8.5pt;")
        d.addWidget(lbl)
    return w


class AnaPencere(QMainWindow):
    def __init__(self, istemci: ModulIstemcisi):
        super().__init__()
        self.istemci = istemci
        self._son_simule_gun = ""
        self.setWindowTitle("Kampüs Kaynak Rezervasyon Sistemi")
        self.resize(1440, 880)

        merkez = QWidget()
        merkez.setObjectName("anaZemin")
        self.setCentralWidget(merkez)
        ana = QVBoxLayout(merkez)

        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)
        ana.addWidget(self._ust_cubuk())

        govde = QSplitter(Qt.Horizontal)
        govde.setHandleWidth(10)
        govde.setChildrenCollapsible(False)
        govde_kap = QWidget()
        gk = QVBoxLayout(govde_kap)
        gk.setContentsMargins(12, 12, 12, 12)
        gk.addWidget(govde)
        ana.addWidget(govde_kap, 1)

        sol = QSplitter(Qt.Vertical)
        sol.setHandleWidth(10)
        sol.setChildrenCollapsible(False)
        sol.addWidget(self._takvim_karti())
        self.gunluk = OlayGunlugu()
        sol.addWidget(kart(etiket("Olay günlüğü", "altBaslik"), self.gunluk))
        sol.setStretchFactor(0, 3)
        sol.setStretchFactor(1, 1)
        sol.setSizes([560, 220])
        govde.addWidget(sol)
        govde.addWidget(self._sag_panel())
        govde.setStretchFactor(0, 1)
        govde.setSizes([975, 445])

        istemci.motor_yuklendi.connect(self.motor_yuklendi)
        istemci.durum_degisti.connect(self.yenile)
        istemci.gunluge_eklendi.connect(self.gunluk.ekle)
        self._etkin(False)

    # --- yapı ------
    
    def _ust_cubuk(self) -> QWidget:
        cubuk = QFrame()
        cubuk.setObjectName("ustCubuk")
        d = QHBoxLayout(cubuk)
        d.setContentsMargins(16, 10, 16, 10)
        d.setSpacing(12)
        baslik = QVBoxLayout()
        baslik.setSpacing(0)
        baslik.addWidget(etiket("Kampüs Kaynak Rezervasyon", "baslik"))
        self.dosya_etiketi = etiket("Başlangıç dosyası seçilmedi", "soluk")
        baslik.addWidget(self.dosya_etiketi)
        d.addLayout(baslik)
        ac = dugme("Başlangıç dosyası…", ipucu="Yeni dosya seçilince tüm durum yeniden kurulur")
        ac.clicked.connect(self.dosya_sec)
        d.addWidget(ac)
        d.addStretch(1)
        self.saat_paneli = SaatPaneli(self.istemci)
        d.addWidget(self.saat_paneli)
        return cubuk

    def _takvim_karti(self) -> QWidget:
        ust = QHBoxLayout()
        ust.setSpacing(6)
        onceki, sonraki = QToolButton(), QToolButton()
        onceki.setText("◀")
        sonraki.setText("▶")
        onceki.setToolTip("Önceki gün")
        sonraki.setToolTip("Sonraki gün")
        self.gun = QDateEdit()
        self.gun.setCalendarPopup(True)
        self.gun.setDisplayFormat("dd MMMM yyyy, dddd")
        self.gun.setMinimumWidth(210)
        self.gun.dateChanged.connect(lambda _: self.takvimi_yenile())
        onceki.clicked.connect(lambda: self.gun.setDate(self.gun.date().addDays(-1)))
        sonraki.clicked.connect(lambda: self.gun.setDate(self.gun.date().addDays(1)))
        bugun = dugme("Simüle gün", "kucuk", "Simüle saatin gününe dön")
        bugun.clicked.connect(self.simule_gune_don)
        ust.addWidget(onceki)
        ust.addWidget(self.gun)
        ust.addWidget(sonraki)
        ust.addWidget(bugun)
        ust.addStretch(1)
        ust.addWidget(renk_aciklamasi())
        ust_w = QWidget()
        ust_w.setLayout(ust)
        ust.setContentsMargins(0, 0, 0, 0)

        self.takvim = Takvim()

        self.takvim.rezervasyon_tiklandi.connect(self.rezervasyon_karti_ac)
        self.takvim.kaynak_tiklandi.connect(self.kaynak_karti_ac)
        kaydirma = QScrollArea()
        kaydirma.setWidgetResizable(True)
        kaydirma.setWidget(self.takvim)
        kaydirma.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ipucu = etiket("Boş alanda sürükleyerek aralık seçin → talep formu dolar · "
                       "kutuya tıklayın → ayrıntı ve işlemler · kaynak adına tıklayın → günlük doluluk",
                       "soluk")
        ipucu.setStyleSheet("font-size: 8.5pt;")
        return kart(ust_w, kaydirma, ipucu)

    def _sag_panel(self) -> QWidget:
        self.ozet = KullaniciOzeti(self.istemci)
        self.sekmeler = QTabWidget()
        self.form = TalepFormu(self.istemci)
        self.panel = KullaniciPaneli(self.istemci)
        self.ekleme = EklemePaneli(self.istemci)
        for w, ad in ((self.form, "Talep"), (self.panel, "Rezervasyonlar"), (self.ekleme, "Ekle")):
            self.sekmeler.addTab(w, ad)

        self.ozet.kullanici_degisti.connect(self.kullanici_degisti)
        self.takvim.aralik_secildi.connect(self.aralik_secildi)
        self.panel.rezervasyona_git.connect(self.rezervasyona_git)
        self.ekleme.kullanici.eklendi.connect(lambda kid: self.ozet.sec(kid))

        sag = kart(self.ozet, self.sekmeler, kenar=14)
        sag.setMinimumWidth(445)
        sag.setMaximumWidth(520)
        return sag

    def _etkin(self, etkin: bool) -> None:
        for w in (self.saat_paneli, self.takvim, self.ozet, self.sekmeler, self.gun):
            w.setEnabled(etkin)

    # --- olaylar ------
    
    def dosya_sec(self) -> None:
        yol, _ = QFileDialog.getOpenFileName(self, "Başlangıç dosyası seç",
                                             str(self.istemci.dosya.parent) if self.istemci.dosya else "",
                                             "JSON (*.json);;Tüm dosyalar (*)")
        if yol:
            self.dosya_yukle(yol)

    def dosya_yukle(self, yol: str) -> bool:
        try:
            self.istemci.yukle(yol)
            return True
        except Exception as hata:  # bozuk / eksik dosya
            QMessageBox.warning(self, "Dosya yüklenemedi", f"{yol}\n\n{hata!r}")
            return False

    def motor_yuklendi(self) -> None:
        self._etkin(True)
        self.dosya_etiketi.setText(str(self.istemci.dosya))
        self.gunluk.temizle()
        self.form.motor_yuklendi()
        self.ekleme.motor_yuklendi()
        self.panel.bant.temizle()
        self.ozet.yenile()
        self.kullanici_degisti(self.ozet.secili())
        self._son_simule_gun = self._simule_gun()
        self.simule_gune_don()

    def yenile(self) -> None:

    
        self.saat_paneli.yenile()
        yeni_simule = self._simule_gun()
        if self._gosterilen_gun() == self._son_simule_gun and yeni_simule != self._son_simule_gun:
            self.simule_gune_don() 
            
        self._son_simule_gun = yeni_simule
        self.takvimi_yenile()
        self.ozet.yenile()
        self.panel.yenile()
        self.form.durum_yenile()

    def kullanici_degisti(self, kullanici_id) -> None:
        self.form.kullanici_ayarla(kullanici_id)
        self.panel.kullanici_ayarla(kullanici_id)
        self.takvim.aktif_kullanici = kullanici_id

    def _gosterilen_gun(self) -> str:
        return self.gun.date().toString("yyyy-MM-dd")


    def _simule_gun(self) -> str:

        return self.istemci.motor.durum.saat.strftime("%Y-%m-%d") if self.istemci.hazir else ""

    def simule_gune_don(self) -> None:
        if self.istemci.hazir:
            an = self.istemci.motor.durum.saat
            self.gun.setDate(QDate(an.year, an.month, an.day))
            self.takvimi_yenile()

    def takvimi_yenile(self) -> None:
        if not self.istemci.hazir:
            return
        motor = self.istemci.motor
        gun = self._gosterilen_gun()
        adlar = {u["id"]: u["ad"] for u in motor.goruntu_kullanicilar()}
        self.takvim.yukle(gun, motor.goruntu_saat(), motor.goruntu_kaynaklar(), motor.goruntu_gun(gun), adlar)

    def aralik_secildi(self, kaynak: str, gun: str, bas: str, bit: str) -> None:
        self.sekmeler.setCurrentIndex(0)
        self.form.secimle_doldur(kaynak, gun, bas, bit)

    def rezervasyon_karti_ac(self, rez_id: str, konum: QPoint) -> None:
        kart_ = RezervasyonKarti(self.istemci, rez_id, self)
        self.istemci.durum_degisti.connect(kart_.yenile)
        kart_.ac(konum)

    def kaynak_karti_ac(self, kaynak_id: str, konum: QPoint) -> None:
        KaynakSorguKarti(self.istemci, kaynak_id, self._gosterilen_gun(), self).ac(konum)

    def rezervasyona_git(self, rez_id: str) -> None:
        r = self.istemci.motor.goruntu_rezervasyon(rez_id)
        if r:
            self.gun.setDate(QDate.fromString(r["baslangic"][:10], "yyyy-MM-dd"))
            self.takvim.vurgulu = rez_id
            self.takvimi_yenile()
