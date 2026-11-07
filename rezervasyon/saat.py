# Simüle saat ve olay döngüsü. Saat ileri alınınca aradaki her olay anı
# sırayla işlenir; böylece büyük bir atlamada da hiçbir olay atlanmaz.
from __future__ import annotations

from datetime import datetime, timedelta

from . import bekleme
from .durum import SistemDurumu
from .kurallar.iade import guvenilirlik_degistir, haftalik_sifirla
from .modeller import Olay, Rezervasyon
from .sabitler import (
    RezervasyonDurumu as D, OlayTuru, GIRIS_SONRA_DK,
    GUVENILIRLIK_GELMEDI, GUVENILIRLIK_ZAMANINDA_TAMAMLANDI,
)
from .zaman import sonraki_pazartesi

GELMEDI_ESIGI = timedelta(minutes=GIRIS_SONRA_DK)


# Giriş yapılmamışsa rezervasyonun GELMEDI sayılacağı an (başlangıç + 15 dk)
def gelmedi_ani(rez: Rezervasyon) -> datetime:
    return rez.baslangic + GELMEDI_ESIGI


# Şimdiki saat ile hedef saat arasındaki en erken olay anı; yoksa None.
# Adaylar: sonraki pazartesi, kullanımdakilerin bitişi, onaylıların gelmedi anı
def sonraki_olay_ani(durum: SistemDurumu, yeni: datetime) -> datetime | None:
    eski = durum.saat
    adaylar = [sonraki_pazartesi(eski)]
    for r in durum.rezervasyonlar.values():
        if r.durum == D.KULLANIMDA:
            adaylar.append(r.bitis)
        elif r.durum == D.ONAYLI:
            adaylar.append(gelmedi_ani(r))
    adaylar = [a for a in adaylar if eski < a <= yeni]
    return min(adaylar, default=None)


# Saati verilen ana getirir ve o anda olması gerekenleri sırayla yapar
def ani_isle(durum: SistemDurumu, an: datetime) -> list[Olay]:
    durum.saat = an
    olaylar: list[Olay] = []

    # 1) Pazartesi 00:00 ise bakiyeleri sıfırla
    if sonraki_pazartesi(an - timedelta(microseconds=1)) == an:  #an’dan 1 mikrosaniye geri gidilip o andan sonraki pazartesi soruluyor
        haftalik_sifirla(durum)
        olaylar.append(Olay(an, OlayTuru.HAFTALIK_SIFIRLAMA))

    # 2) Süresi dolan kullanımdaki rezervasyonları tamamla (+2 güvenilirlik)
    sirali = sorted(durum.rezervasyonlar.values(), key=lambda r: r.no)
    for r in sirali:
        if r.durum == D.KULLANIMDA and r.bitis == an: #Koşul: Rezervasyon kullanımda olmalı (giriş yapılmış) ve bitiş saati tam bu an olmalı
            r.durum = D.TAMAMLANDI
            u = durum.kullanicilar[r.kullanici]
            guvenilirlik_degistir(u, GUVENILIRLIK_ZAMANINDA_TAMAMLANDI)
            olaylar.append(Olay(an, OlayTuru.TAMAMLANDI, {
                "rezervasyon": r.id, "kullanici": u.id, "guvenilirlik": u.guvenilirlik}))

    # 3) Giriş yapılmayanları GELMEDI yap (-15 güvenilirlik), boşalan kaynakları not et
    bosalan: list[str] = []
    for r in sirali:
        if r.durum == D.ONAYLI and gelmedi_ani(r) == an:
            r.durum = D.GELMEDI
            u = durum.kullanicilar[r.kullanici]
            guvenilirlik_degistir(u, GUVENILIRLIK_GELMEDI)
            olaylar.append(Olay(an, OlayTuru.GELMEDI, {
                "rezervasyon": r.id, "kullanici": u.id, "guvenilirlik": u.guvenilirlik}))
            if r.kaynak not in bosalan:
                bosalan.append(r.kaynak)

    # 4) Geçmiş bekleme kayıtlarını sil, boşalan kaynaklar için bekleme listesini tara
    bekleme.eskileri_sil(durum)
    for kaynak_id in bosalan:
        olaylar.extend(bekleme.tara(durum, kaynak_id))
    return olaylar

#sonraki_olay_ani(durum, yeni): şimdiki saat ile hedef arasındaki en erken olay anını buluyor.
#n := ...: bulunan değeri an değişkenine atıyor. Walrus operatörü atamayı ve kontrolü aynı satırda yapmayı sağlıyor.
#s not None: bir olay anı bulunduysa döngüye giriliyor, bulunmadıysa çıkılıyor.

#Saati hedefe kadar olay olay ilerletir, oluşan tüm olayları sırayla döndürür ana döngü
def ilerlet(durum: SistemDurumu, yeni: datetime) -> list[Olay]:
    olaylar: list[Olay] = []
    while (an := sonraki_olay_ani(durum, yeni)) is not None:
        olaylar.extend(ani_isle(durum, an))
    durum.saat = yeni
    bekleme.eskileri_sil(durum)
    return olaylar
