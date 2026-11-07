from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .modeller import (
    KaynakTuru, Rol, Kaynak, Kullanici, BakimPenceresi, Rezervasyon, BeklemeKaydi,
)
from .sabitler import RezervasyonDurumu



#Sözlükler id--nsne şeklindedir
@dataclass
class SistemDurumu:
    saat: datetime #simüle saat
    kaynak_turleri: dict[str, KaynakTuru] = field(default_factory=dict)
    roller: dict[str, Rol] = field(default_factory=dict)
    sertifikalar: set[str] = field(default_factory=set) 
    kaynaklar: dict[str, Kaynak] = field(default_factory=dict)  
    kullanicilar: dict[str, Kullanici] = field(default_factory=dict)
    bakim_pencereleri: list[BakimPenceresi] = field(default_factory=list)
    rezervasyonlar: dict[str, Rezervasyon] = field(default_factory=dict)
    bekleme_kayitlari: dict[str, BeklemeKaydi] = field(default_factory=dict)

    #Sıradaki id numaraları
    _sonraki_rezervasyon: int = 1
    _sonraki_paket: int = 1
    _sonraki_bekleme: int = 1

    #eni id verip sayacı bir artırır
    def yeni_rezervasyon_id(self) -> str:
        rid = f"r{self._sonraki_rezervasyon}"
        self._sonraki_rezervasyon += 1
        return rid

    def yeni_paket_id(self) -> str:
        pid = f"p{self._sonraki_paket}"
        self._sonraki_paket += 1
        return pid

    def yeni_bekleme_id(self) -> str:
        bid = f"b{self._sonraki_bekleme}"
        self._sonraki_bekleme += 1
        return bid



    def kaynagin_rezervasyonlari(self, kaynak_id: str,
                                 durumlar: set[RezervasyonDurumu]) -> list[Rezervasyon]:
        return [r for r in self.rezervasyonlar.values()
                if r.kaynak == kaynak_id and r.durum in durumlar]

    def kaynagin_bakimlari(self, kaynak_id: str) -> list[BakimPenceresi]:
        return [b for b in self.bakim_pencereleri if b.kaynak == kaynak_id]

 
    def turdeki_kaynaklar(self, tur: str) -> list[Kaynak]:
        return [k for k in self.kaynaklar.values() if k.tur == tur]

    # bekleyen bekleme kayıtları (sırasız)
    def kaynagin_bekleme_kayitlari(self, kaynak_id: str) -> list[BeklemeKaydi]:
        return [b for b in self.bekleme_kayitlari.values() if b.kaynak == kaynak_id]
