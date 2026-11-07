from __future__ import annotations
import math
from datetime import datetime, timedelta
from fractions import Fraction
from ..durum import SistemDurumu
from ..sabitler import (
    RezervasyonDurumu as D, DILIM_DK, BANT_DK, CALISMA_BASLANGIC_SAAT,
    PIK_BASLANGIC_SAAT, PIK_BITIS_SAAT,
)
from ..zaman import dilimler, ortak_dk

DOLULUGA_SAYILAN = {D.ONAYLI, D.KULLANIMDA}  #dolulukta sayılan rezervasyonlar
PIK_CARPANI = Fraction(3, 2)              
DILIM_ORANI = Fraction(DILIM_DK, 60)         

#ilimin içinde bulunduğu 2 saatlik bandın başlangıcı
def bant_baslangici(an: datetime) -> datetime:
    saat = an.hour - (an.hour - CALISMA_BASLANGIC_SAAT) % (BANT_DK // 60)
    return an.replace(hour=saat, minute=0, second=0, microsecond=0)


#Bantta aynı türdeki kaynakların ne kadarının dolu olduğu
def doluluk(durum: SistemDurumu, tur: str, bant_bas: datetime) -> Fraction: #bu fonksiyon draction döndürür
    kaynak_idleri = {k.id for k in durum.turdeki_kaynaklar(tur)}
    if not kaynak_idleri:
        return Fraction(0) #küme boşsa 0 döner
    bant_bit = bant_bas + timedelta(minutes=BANT_DK) #bant dk 120
    # Banda düşen dolu dakikaların toplamı
    dolu = sum(ortak_dk(r.baslangic, r.bitis, bant_bas, bant_bit)
               for r in durum.rezervasyonlar.values()
               if r.kaynak in kaynak_idleri and r.durum in DOLULUGA_SAYILAN) #(iptal edilenler ve gelinmeyenler sayılmıyor)
    # Toplam kapasite = kaynak sayısı × bant süresi
    return Fraction(dolu, len(kaynak_idleri) * BANT_DK)


#Doluluğa göre çarpan: her %25 doluluk ücreti 0.25 artırır (1, 1.25, 1.5, 1.75, 2)
def bant_carpani(doluluk_orani: Fraction) -> Fraction:
    return 1 + Fraction(1, 4) * math.floor(4 * doluluk_orani)


#Enerji yoğun kaynak pik saatteyse 3/2, değilse 1
def pik_carpani(durum: SistemDurumu, tur: str, dilim: datetime) -> Fraction:
    if durum.kaynak_turleri[tur].enerji_yogun and PIK_BASLANGIC_SAAT <= dilim.hour < PIK_BITIS_SAAT:
        return PIK_CARPANI
    return Fraction(1)


# Yarımı yukarı yuvarlama (2.5 -> 3); Python'un round()'u 2.5'i 2 yaptığı için kullanılmaz
def yuvarla(deger: Fraction) -> int:
    return math.floor(deger + Fraction(1, 2))


# Ücret = her 15 dk dilim için temel × 1/4 × bant çarpanı × pik çarpanı, toplanıp yuvarlanır
def ucret_hesapla(durum: SistemDurumu, kaynak_id: str,
                  baslangic: datetime, bitis: datetime) -> int:  #int yuvarlanmış ücret döndürür
    tur = durum.kaynaklar[kaynak_id].tur
    temel = Fraction(durum.kaynak_turleri[tur].temel_ucret)
    bant_onbellek: dict[datetime, Fraction] = {}  #aynı bant için doluluk tekrar hesaplanmasın
    toplam = Fraction(0)
    for dilim in dilimler(baslangic, bitis):
        bant = bant_baslangici(dilim)#Dilimin içinde olduğu 2 saatlik bandı
        if bant not in bant_onbellek:
            bant_onbellek[bant] = bant_carpani(doluluk(durum, tur, bant)) #ornı çarpana çevir 
        toplam += temel * DILIM_ORANI * bant_onbellek[bant] * pik_carpani(durum, tur, dilim)
    return yuvarla(toplam)
#Hesap boyunca toplam tam bir kesir olarak kalıyo