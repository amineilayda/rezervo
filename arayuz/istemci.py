""" arayüz ile rezervasyon modülü arasındaki tek köprü

"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from rezervasyon import RezervasyonMotoru
from rezervasyon.komut_isleyici import calistir, sonuc_satiri

DURUM_DEGISTIRMEYEN = {"fiyat", "sorgu"}


class ModulIstemcisi(QObject):
    durum_degisti = Signal()
    gunluge_eklendi = Signal(dict, dict)  # (komut, sonuc_satiri)
    motor_yuklendi = Signal()

    def __init__(self):
        super().__init__()
        self.motor: RezervasyonMotoru | None = None
        self.dosya: Path | None = None
        self.gunluk: list[tuple[dict, dict]] = []

    @property
    def hazir(self) -> bool:
        return self.motor is not None
    

    def yukle(self, yol: str) -> None:
        motor = RezervasyonMotoru.dosyadan(yol)  # hata olursa eski durum korunur
        self.motor = motor
        self.dosya = Path(yol)
        self.gunluk.clear()
        self.motor_yuklendi.emit()
        self.durum_degisti.emit()

    def gonder(self, komut: dict) -> dict:
    
        govde = calistir(self.motor, komut)
        satir = sonuc_satiri(len(self.gunluk) + 1, komut, govde)
        self.gunluk.append((komut, satir))
        self.gunluge_eklendi.emit(komut, satir)
        if komut["komut"] not in DURUM_DEGISTIRMEYEN and govde.get("durum") == "TAMAM":
            self.durum_degisti.emit()
        return satir

    def onizle(self, komut: dict) -> dict:
        
        assert komut["komut"] in DURUM_DEGISTIRMEYEN
        return calistir(self.motor, komut)
