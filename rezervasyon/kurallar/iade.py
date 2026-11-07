#İptal iadesi, bakiye ve güvenilirlik güncellemeleri
from __future__ import annotations
from datetime import datetime, timedelta
from ..durum import SistemDurumu
from ..modeller import Kullanici, Rezervasyon
from ..sabitler import (
    IADE_TAM_SAAT, IADE_YARIM_SAAT, GUVENILIRLIK_GEC_IPTAL, GUVENILIRLIK_MIN, GUVENILIRLIK_MAX,
)


#İptalde(iade miktarı, güvenilirlik farkı):başlangıca 24+ saat varsa tam iade
# 2–24 saat varsa yarım iade, 2 saatten az kaldıysa iade yok ve -5 puan
def iptal_iadesi(rez: Rezervasyon, simdi: datetime) -> tuple[int, int]:
    kalan = rez.baslangic - simdi
    if kalan >= timedelta(hours=IADE_TAM_SAAT):
        return rez.ucret, 0
    if kalan >= timedelta(hours=IADE_YARIM_SAAT):
        return rez.ucret // 2, 0
    return 0, GUVENILIRLIK_GEC_IPTAL



def bakiyeye_ekle(durum: SistemDurumu, kullanici: Kullanici, miktar: int) -> int:
    kota = durum.roller[kullanici.rol].haftalik_kota
    eklenen = max(0, min(miktar, kota - kullanici.bakiye))
    kullanici.bakiye += eklenen
    return eklenen


def guvenilirlik_degistir(kullanici: Kullanici, fark: int) -> None:
    kullanici.guvenilirlik = max(GUVENILIRLIK_MIN, min(GUVENILIRLIK_MAX, kullanici.guvenilirlik + fark))


def haftalik_sifirla(durum: SistemDurumu) -> None:
    for kullanici in durum.kullanicilar.values():
        kullanici.bakiye = durum.roller[kullanici.rol].haftalik_kota
