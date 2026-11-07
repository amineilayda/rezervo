from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .sabitler import RezervasyonDurumu

@dataclass(frozen=True)  #sonradan değişmeyenler frozen
class KaynakTuru:
    ad: str
    hazirlik_dk: int          
    temel_ucret: int          
    enerji_yogun: bool      #1.5 katına çıkar
    sertifika: str | None     

@dataclass(frozen=True)
class Rol:
    ad: str
    haftalik_kota: int        #her pazartesi bakiyenin döndüğü değer,akiyenin üst sınırı
    ileri_gun: int            
    azami_sure_dk: int        


#rezervasyonu olan asıl kaynak
@dataclass
class Kaynak:
    id: str
    ad: str
    tur: str                  #KaynakTuru adı
    izinli_roller: list[str]  #bu kaynağı kullanabilen roller


@dataclass
class Kullanici:
    id: str
    ad: str
    rol: str
    sertifikalar: list[str]
    bakiye: int
    guvenilirlik: int      


@dataclass
class BakimPenceresi:
    kaynak: str
    baslangic: datetime
    bitis: datetime


@dataclass
class Rezervasyon:
    id: str  #r1,r2
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    ucret: int
    durum: RezervasyonDurumu = RezervasyonDurumu.ONAYLI
    paket: str | None = None  # p1

    #sıralama sayısını alma
    @property
    def no(self) -> int:
        return int(self.id[1:])


#dolu bir an için bekleme listesine yazılan kayıt
@dataclass
class BeklemeKaydi:
    id: str  # b1
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    kayit_saati: datetime     #sırada eşitlik olursa önce yazıla

    @property
    def no(self) -> int:
        return int(self.id[1:])


# Doğrulamaya giren rezervasyon isteği
@dataclass
class Talep:
    kullanici: str
    kaynak: str
    baslangic: str    #tarih formatı değilll
    bitis: str


# Saat ilerlerken oluşan olay (gelmedi, tamamlandı, otomatik atama...)
@dataclass
class Olay:
    zaman: datetime
    tur: str #AFTALIK_SIFIRLAMA, TAMAMLANDI, GELMEDI, OTOMATIK_ATAMA
    alanlar: dict = field(default_factory=dict)  # olaya özel ek alanlar er yeni nesneye ayrı, boş bir sözlük veriyor

    # Çıktıya yazılacak sözlük biçimi
    def sozluk(self) -> dict:
        from .zaman import bicimle
        return {"zaman": bicimle(self.zaman), "tur": str(self.tur), **self.alanlar}
