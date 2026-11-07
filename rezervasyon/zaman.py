from __future__ import annotations
from datetime import datetime, timedelta
from .sabitler import ZAMAN_BICIMI, GUN_BICIMI, DILIM_DK


# "2026-10-20T10:00" metnini datetime'a çevirir; bozuksa ValueError
def coz(metin: str) -> datetime:
    if not isinstance(metin, str):
        raise ValueError(metin)
    return datetime.strptime(metin, ZAMAN_BICIMI)


# datetime -> "2026-10-20T10:00"
def bicimle(an: datetime) -> str:
    return an.strftime(ZAMAN_BICIMI)


# "2026-10-20" gün metnini o günün 00:00'ına çevirir
def gun_coz(metin: str) -> datetime:
    if not isinstance(metin, str):
        raise ValueError(metin)
    return datetime.strptime(metin, GUN_BICIMI)


# Dakika 15'in katı mı (00, 15, 30, 45)
def adima_oturuyor(an: datetime) -> bool:
    return an.minute % DILIM_DK == 0 and an.second == 0


# [b1, e1) ile [b2, e2) aralıkları çakışıyor mu; uç uca değmek çakışma sayılmaz
def kesisir(b1: datetime, e1: datetime, b2: datetime, e2: datetime) -> bool:
    return b1 < e2 and e1 > b2


# İki aralığın ortak kısmı kaç dakika (çakışmıyorsa 0)
def ortak_dk(b1: datetime, e1: datetime, b2: datetime, e2: datetime) -> int:
    bas, bit = max(b1, b2), min(e1, e2)
    return dk(bit - bas) if bit > bas else 0


# Süreyi tam dakikaya çevirir
def dk(sure: timedelta) -> int:
    return int(sure.total_seconds() // 60)


# Aralığı 15 dakikalık dilimlerin başlangıçlarına böler (ücret dilim dilim hesaplanır)
def dilimler(baslangic: datetime, bitis: datetime):
    an = baslangic
    while an < bitis:
        yield an
        an += timedelta(minutes=DILIM_DK)


# Aynı günün 00:00'ı
def gun_basi(an: datetime) -> datetime:
    return an.replace(hour=0, minute=0, second=0, microsecond=0)


# Verilen andan kesinlikle sonraki ilk pazartesi 00:00 (haftalık sıfırlama anı)
def sonraki_pazartesi(an: datetime) -> datetime:
    aday = gun_basi(an) + timedelta(days=(7 - an.weekday()) % 7)
    if aday <= an:
        aday += timedelta(days=7)
    return aday
