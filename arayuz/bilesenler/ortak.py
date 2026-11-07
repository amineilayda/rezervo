from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QPoint, QTime, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QApplication,
)

from .. import metinler
from .. import tema
  ##bileşen paylaşma

def etiket(metin: str = "", ad: str | None = None, kelime_kaydir: bool = False) -> QLabel:
    lbl = QLabel(metin)
    if ad:
        lbl.setObjectName(ad)
    lbl.setWordWrap(kelime_kaydir)
    return lbl



def dugme(metin: str, ad: str | None = None, ipucu: str | None = None) -> QPushButton:
    btn = QPushButton(metin)
    if ad:
        btn.setObjectName(ad)
    if ipucu:
        btn.setToolTip(ipucu)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def yeniden_cilala(w: QWidget) -> None:
    w.style().unpolish(w)
    w.style().polish(w)


class SonucBandi(QFrame):

  
    eylem_tiklandi = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("bant")
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(10, 8, 10, 8)
        duzen.setSpacing(3)
        ust = QHBoxLayout()
        ust.setSpacing(8)
        self.baslik = etiket()
        self.baslik.setWordWrap(True)
        self.baslik.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ust.addWidget(self.baslik, 1)
        self.eylem = dugme("", "kucuk")
        self.eylem.clicked.connect(self.eylem_tiklandi)
        self.eylem.hide()
        ust.addWidget(self.eylem, 0, Qt.AlignTop)
        duzen.addLayout(ust)
        self.ayrinti = etiket(kelime_kaydir=True)
        self.ayrinti.setStyleSheet(f"color: {tema.METIN}; font-size: 9pt;")
        duzen.addWidget(self.ayrinti)
        self.hide()

    def goster(self, satir: dict, eylem_metni: str | None = None) -> None:
        tamam = satir.get("durum") == "TAMAM"
        self.setProperty("tur", "tamam" if tamam else "red")
        yeniden_cilala(self)
        renk = tema.BASARI if tamam else tema.HATA
        isaret = "✓" if tamam else "✕"
        komut = metinler.KOMUT_ADLARI.get(satir.get("komut"), satir.get("komut"))
        self.baslik.setText(
            f"<span style='color:{renk}; font-weight:600'>{isaret} {komut} · #{satir.get('no')}</span>"
            f"&nbsp;&nbsp;{metinler.ozet(satir)}")
        self._ayrinti_yaz(metinler.ayrinti_satirlari(satir))
        self._eylem_ayarla(eylem_metni)
        self.show()

    def bilgi(self, metin: str, ayrinti: list[str] | None = None) -> None:
        self.setProperty("tur", "bilgi")
        yeniden_cilala(self)
        self.baslik.setText(metin)
        self._ayrinti_yaz(ayrinti or [])
        self._eylem_ayarla(None)
        self.show()

    def _ayrinti_yaz(self, satirlar: list[str]) -> None:
        self.ayrinti.setText("<br>".join(f"• {s}" for s in satirlar))
        self.ayrinti.setVisible(bool(satirlar))

    def _eylem_ayarla(self, metin: str | None) -> None:
        self.eylem.setVisible(bool(metin))
        if metin:
            self.eylem.setText(metin)

    def temizle(self) -> None:
        self.hide()




class AcilirKart(QFrame):

  
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("acilirKart")
        self.duzen = QVBoxLayout(self)
        self.duzen.setContentsMargins(14, 12, 14, 12)
        self.duzen.setSpacing(8)

    def ac(self, konum: QPoint) -> None:
        self.adjustSize()
        ekran = QApplication.screenAt(konum) or QApplication.primaryScreen()
        alan = ekran.availableGeometry()
        x = min(konum.x() + 8, alan.right() - self.width() - 8)
        y = min(konum.y() + 8, alan.bottom() - self.height() - 8)
        self.move(max(alan.left(), x), max(alan.top(), y))
        self.show()


def saat_listesi() -> list[str]:
    
    return [f"{dk // 60:02d}:{dk % 60:02d}" for dk in range(7 * 60, 23 * 60 + 1, 15)]


class SaatKutusu(QComboBox):

 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.addItems(saat_listesi())
        self.setMaxVisibleItems(16)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMinimumWidth(70)

    def deger(self) -> str:
        return self.currentText().strip()

    def ayarla(self, metin: str) -> None:
        i = self.findText(metin)
        if i >= 0:
            self.setCurrentIndex(i)
        else:
            self.setEditText(metin)


def varsayilan_baslangic(an: datetime) -> datetime:

    
    return an.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def dk_ekle(saat: str, dk: int) -> str:

    
    t = QTime.fromString(saat, "HH:mm")
    if not t.isValid():
        return saat
    toplam = max(0, min(t.hour() * 60 + t.minute() + dk, 23 * 60 + 45))
    return f"{toplam // 60:02d}:{toplam % 60:02d}"
