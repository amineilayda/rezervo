
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPlainTextEdit, QSplitter, QWidget

from .. import metinler
from .. import tema


def jsonl(veri: dict) -> str:
    return json.dumps(veri, ensure_ascii=False, separators=(",", ":"))


class OlayGunlugu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        duzen = QHBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        bolucu = QSplitter(Qt.Horizontal)
        self.liste = QListWidget()
        self.liste.setUniformItemSizes(True)
        self.liste.currentItemChanged.connect(self._secildi)
        self.ayrinti = QPlainTextEdit()
        self.ayrinti.setReadOnly(True)
        self.ayrinti.setPlaceholderText("JSON görmek için günlükten bir satır seçin")
        bolucu.addWidget(self.liste)
        bolucu.addWidget(self.ayrinti)
        bolucu.setSizes([520, 420])
        duzen.addWidget(bolucu)



    def temizle(self) -> None:
        self.liste.clear()
        self.ayrinti.clear()

    def ekle(self, komut: dict, satir: dict) -> None:
        tamam = satir.get("durum") == "TAMAM"
        ad = metinler.KOMUT_ADLARI.get(komut.get("komut"), komut.get("komut"))
        metin = f"#{satir['no']:<3} {'✓' if tamam else '✕'}  {ad:<14} {metinler.ozet(satir)}"
        oge = QListWidgetItem(metin)
        oge.setData(Qt.UserRole, (komut, satir))
        oge.setForeground(QColor(tema.METIN if tamam else tema.HATA))
        oge.setToolTip("\n".join(metinler.ayrinti_satirlari(satir)) or metin)
        self.liste.addItem(oge)
        self.liste.setCurrentItem(oge)

    def _secildi(self, oge: QListWidgetItem | None, _=None) -> None:
        if oge is None:
            self.ayrinti.clear()
            return
        komut, satir = oge.data(Qt.UserRole)
        self.ayrinti.setPlainText(
            f"// komut\n{jsonl(komut)}\n\n// sonuç\n{jsonl(satir)}\n\n"
            f"// sonuç (okunaklı)\n{json.dumps(satir, ensure_ascii=False, indent=2)}")
