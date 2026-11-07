from __future__ import annotations

import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGridLayout, QHBoxLayout, QLineEdit, QSpinBox,
    QVBoxLayout, QWidget,

)

from ..istemci import ModulIstemcisi

from .ortak import SonucBandi, dugme, etiket


def sonraki_id(mevcut: list[str], onek: str) -> str:
    desen = re.compile(rf"^{re.escape(onek)}(\d+)$")
    sayilar = [int(m.group(1)) for i in mevcut if (m := desen.match(i))]
    return f"{onek}{max(sayilar, default=0) + 1}"


class OnayKutulari(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.izgara = QGridLayout(self)

        self.izgara.setContentsMargins(0, 0, 0, 0)
        self.izgara.setHorizontalSpacing(12)
        self.kutular: list[QCheckBox] = []

    def doldur(self, degerler: list[str], hepsi_secili: bool = False) -> None:
        for k in self.kutular:
            k.setParent(None)
        self.kutular = []
        for i, d in enumerate(degerler):
            k = QCheckBox(d)
            k.setChecked(hepsi_secili)
            self.izgara.addWidget(k, i // 2, i % 2)
            self.kutular.append(k)
        if not degerler:
            k = QCheckBox("(tanımlı değer yok)")
            k.setEnabled(False)
            self.izgara.addWidget(k, 0, 0)
            self.kutular.append(k)

    def secilenler(self) -> list[str]:

        return [k.text() for k in self.kutular if k.isChecked() and k.isEnabled()]


class KullaniciEkleFormu(QWidget):
    eklendi = Signal(str)

    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.addWidget(etiket("Yeni kullanıcı", "baslik"))
        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        self.id = QLineEdit()
        self.ad = QLineEdit()
        self.ad.setPlaceholderText("Ad Soyad")
        self.rol = QComboBox()
        self.rol.currentTextChanged.connect(self._rol_degisti)
        self.sertifikalar = OnayKutulari()
        self.bakiye = QSpinBox()
        self.bakiye.setRange(-100000, 100000)
        self.bakiye.setSuffix(" KP")
        self.guv = QSpinBox()
        self.guv.setRange(-1000, 1000)
        self.guv.setValue(100)
        satir = QHBoxLayout()
        satir.addWidget(self.bakiye)
        satir.addWidget(etiket("Güvenilirlik", "soluk"))
        satir.addWidget(self.guv)
        form.addRow("Kimlik", self.id)
        form.addRow("Ad", self.ad)
        form.addRow("Rol", self.rol)
        form.addRow("Sertifikalar", self.sertifikalar)
        form.addRow("Bakiye", satir)
        duzen.addLayout(form)
        alt = QHBoxLayout()
        alt.addStretch(1)
        self.ekle = dugme("Kullanıcı ekle", "birincil")
        self.ekle.clicked.connect(self.gonder)
        alt.addWidget(self.ekle)
        duzen.addLayout(alt)
        self.bant = SonucBandi()
        duzen.addWidget(self.bant)

    def motor_yuklendi(self) -> None:
        p = self.istemci.motor.goruntu_parametreler()
        self.roller = p["roller"]
        self.rol.blockSignals(True)
        self.rol.clear()
        self.rol.addItems(list(self.roller))
        self.rol.blockSignals(False)
        self.sertifikalar.doldur(p["sertifikalar"])
        self._rol_degisti(self.rol.currentText())
        self.bant.temizle()
        self.id_oner()

    def id_oner(self) -> None:
        self.id.setText(sonraki_id([u["id"] for u in self.istemci.motor.goruntu_kullanicilar()], "u"))

    def _rol_degisti(self, rol: str) -> None:
        if rol in getattr(self, "roller", {}):
            self.bakiye.setValue(self.roller[rol]["haftalik_kota"])

    def gonder(self) -> None:
        kid = self.id.text().strip()
        satir = self.istemci.gonder({
            "komut": "kullanici_ekle", "id": kid, "ad": self.ad.text().strip(),
            "rol": self.rol.currentText(), "sertifikalar": self.sertifikalar.secilenler(),
            "bakiye": self.bakiye.value(), "guvenilirlik": self.guv.value()})
        self.bant.goster(satir)
        if satir["durum"] == "TAMAM":
            self.ad.clear()
            self.id_oner()
            self.eklendi.emit(kid)



#kaynak ekleme formu

class KaynakEkleFormu(QWidget):
    eklendi = Signal(str)

    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.addWidget(etiket("Yeni kaynak", "baslik"))
        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(6)
        self.id = QLineEdit()
        self.ad = QLineEdit()
        self.ad.setPlaceholderText("Görünen ad")
        self.tur = QComboBox()
        self.tur.currentTextChanged.connect(lambda _: self.id_oner())
        self.roller = OnayKutulari()
        form.addRow("Kimlik", self.id)
        form.addRow("Ad", self.ad)
        form.addRow("Tür", self.tur)
        form.addRow("İzinli roller", self.roller)
        duzen.addLayout(form)
        alt = QHBoxLayout()
        alt.addStretch(1)
        self.ekle = dugme("Kaynak ekle", "birincil")
        self.ekle.clicked.connect(self.gonder)
        alt.addWidget(self.ekle)
        duzen.addLayout(alt)
        self.bant = SonucBandi()
        duzen.addWidget(self.bant)






    def motor_yuklendi(self) -> None:
        p = self.istemci.motor.goruntu_parametreler()
        self.tur.blockSignals(True)
        self.tur.clear()
        for ad, t in p["kaynak_turleri"].items():
            self.tur.addItem(ad)
        self.tur.blockSignals(False)
        self.roller.doldur(list(p["roller"]), hepsi_secili=True)
        self.bant.temizle()
        self.id_oner()

    def id_oner(self) -> None:
        """Aynı türdeki kaynakların kimlik önekini izler (YAZ-1, YAZ-2 -> YAZ-3)."""
        if not self.istemci.hazir:
            return
        kaynaklar = self.istemci.motor.goruntu_kaynaklar()
        tur = self.tur.currentText()
        onekler = [m.group(1) for k in kaynaklar if k["tur"] == tur
                   and (m := re.match(r"^(.*?)(\d+)$", k["id"]))]
        onek = max(set(onekler), key=onekler.count) if onekler else f"{tur[:3]}-"
        self.id.setText(sonraki_id([k["id"] for k in kaynaklar], onek))

    def gonder(self) -> None:

        kid = self.id.text().strip()
        satir = self.istemci.gonder({
            "komut": "kaynak_ekle", "id": kid, "ad": self.ad.text().strip() or kid,
            "tur": self.tur.currentText(), "izinli_roller": self.roller.secilenler()})
        self.bant.goster(satir)
        if satir["durum"] == "TAMAM":
            self.ad.clear()
            self.id_oner()
            self.eklendi.emit(kid)


class EklemePaneli(QWidget):

    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(2, 12, 2, 4)
        duzen.setSpacing(18)
        self.kullanici = KullaniciEkleFormu(istemci)
        self.kaynak = KaynakEkleFormu(istemci)
        duzen.addWidget(self.kullanici)
        duzen.addWidget(self.kaynak)
        duzen.addStretch(1)

    def motor_yuklendi(self) -> None:
        self.kullanici.motor_yuklendi()
        self.kaynak.motor_yuklendi()
