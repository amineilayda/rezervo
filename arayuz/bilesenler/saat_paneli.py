from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QDate, QDateTime, QPoint, QTime
from PySide6.QtWidgets import QDateTimeEdit, QHBoxLayout, QVBoxLayout, QWidget

from ..istemci import ModulIstemcisi
from .ortak import AcilirKart, SonucBandi, dugme, etiket

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]


def uzun_tarih(an: datetime) -> str:
    return f"{an.day} {AYLAR[an.month - 1]} {an.year}, {GUNLER[an.weekday()]}"


class SaatPaneli(QWidget):
    def __init__(self, istemci: ModulIstemcisi, parent=None):
        super().__init__(parent)
        self.istemci = istemci
        duzen = QHBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.setSpacing(8)

        gosterge = QVBoxLayout()
        gosterge.setSpacing(0)
        gosterge.addWidget(etiket("SİMÜLE SAAT", "altBaslik"))
        self.saat = etiket("--:--", "simuleSaat")
        self.gun = etiket("", "simuleGun")
        gosterge.addWidget(self.saat)
        gosterge.addWidget(self.gun)
        duzen.addLayout(gosterge)
        duzen.addSpacing(10)

        self.hedef = QDateTimeEdit()
        self.hedef.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.hedef.setCalendarPopup(True)
        self.hedef.setMinimumWidth(165)
        duzen.addWidget(self.hedef)
        for metin, dk in (("+15 dk", 15), ("+1 sa", 60), ("+1 gün", 24 * 60)):
            b = dugme(metin, "kucuk")
            b.clicked.connect(lambda _=False, d=dk: self.hedef.setDateTime(self.hedef.dateTime().addSecs(d * 60)))
            duzen.addWidget(b)
        self.ilerlet = dugme("İlerlet", "birincil")
        self.ilerlet.clicked.connect(self.ilerlet_tiklandi)
        duzen.addWidget(self.ilerlet)

    def yenile(self) -> None:
        an = self.istemci.motor.durum.saat
        self.saat.setText(an.strftime("%H:%M"))
        self.gun.setText(uzun_tarih(an))
        self.hedef.setDateTime(QDateTime(QDate(an.year, an.month, an.day), QTime(an.hour, an.minute)))

    def ilerlet_tiklandi(self) -> None:
        zaman = self.hedef.dateTime().toString("yyyy-MM-ddTHH:mm")
        satir = self.istemci.gonder({"komut": "saat", "zaman": zaman})
        kart = AcilirKart(self)
        bant = SonucBandi()
        bant.setMinimumWidth(380)
        bant.goster(satir)
        kart.duzen.addWidget(bant)
        kart.ac(self.ilerlet.mapToGlobal(QPoint(-260, self.ilerlet.height())))
