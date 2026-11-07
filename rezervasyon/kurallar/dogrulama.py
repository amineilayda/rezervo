from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from ..durum import SistemDurumu
from ..modeller import Talep

from ..sabitler import (
    HataKodu as H, RezervasyonDurumu as D,
    CALISMA_BASLANGIC_SAAT, CALISMA_BITIS_SAAT, ASGARI_SURE_DK, ARDISIK_BOSLUK_DK,
    GUVENILIRLIK_ESIK, DUSUK_GUVENILIRLIK_ILERI_GUN,
)
from ..zaman import coz, adima_oturuyor, kesisir, dk, gun_basi
from .ucret import ucret_hesapla


#iptal edilen ve gelinmeyen rezervasyonlar hiçbirinde sayılmaz
KESISMEDE_SAYILAN = {D.ONAYLI, D.KULLANIMDA}
HAZIRLIKTA_SAYILAN = {D.ONAYLI, D.KULLANIMDA, D.TAMAMLANDI}
ARDISIKTA_SAYILAN = {D.ONAYLI, D.KULLANIMDA, D.TAMAMLANDI}

@dataclass
class DogrulamaSonucu:
    kod: H | None  #None geçerli boşsa kurallardan geçmiştir
    baslangic: datetime | None = None
    bitis: datetime | None = None
    ucret: int | None = None

    @property
    def gecerli(self) -> bool: #hata varsa false
        return self.kod is None



#epsi geçerse ücreti hesaplar ve (bakiye_kontrolu açıksa) bakiyeye bakar.
def dogrula(durum: SistemDurumu, talep: Talep, *, bakiye_kontrolu: bool = True) -> DogrulamaSonucu:
    #Kullanıc /kaynak yoksa diğer kontroller yapılamaz
    if bulunamadi(durum, talep):
        return DogrulamaSonucu(H.BULUNAMADI)

    try:
        b, e = coz(talep.baslangic), coz(talep.bitis)
    except ValueError:
        return DogrulamaSonucu(H.ZAMAN_ADIMI_HATASI)

    u, k = talep.kullanici, talep.kaynak
   
    #lambda sayesinde her kontrol ancak sırası gelince çalışır
    adimlar = [
        (H.ZAMAN_ADIMI_HATASI, lambda: zaman_adimi_hatasi(b, e)),
        (H.GECMIS_ZAMAN, lambda: gecmis_zaman(durum, b)),
        (H.CALISMA_SAATI_DISI, lambda: calisma_saati_disi(b, e)),
        (H.SURE_SINIRI, lambda: sure_siniri(durum, u, b, e)),
        (H.ILERI_TARIH_SINIRI, lambda: ileri_tarih_siniri(durum, u, b)),
        (H.ROL_IZNI_YOK, lambda: rol_izni_yok(durum, u, k)),
        (H.SERTIFIKA_YOK, lambda: sertifika_yok(durum, u, k)),
        (H.BAKIM, lambda: bakim(durum, k, b, e)),
        (H.KESISME, lambda: kesisme(durum, k, b, e)),
        (H.HAZIRLIK_IHLALI, lambda: hazirlik_ihlali(durum, k, b, e)),
        (H.ARDISIK_KULLANIM, lambda: ardisik_kullanim(durum, u, k, b, e)),
    ]
    #İlk ihlalde dur
    for kod, ihlal in adimlar:
        if ihlal():
            return DogrulamaSonucu(kod, b, e)

    #ücreti hesapla, gerekirse bakiyeyle karşılaştır
    #hata bulunursa ücret hesaplanmaz
    ucret = ucret_hesapla(durum, k, b, e)
    if bakiye_kontrolu and ucret > durum.kullanicilar[u].bakiye:
        return DogrulamaSonucu(H.BAKIYE_YETERSIZ, b, e, ucret)
    return DogrulamaSonucu(None, b, e, ucret)





def bulunamadi(durum: SistemDurumu, talep: Talep) -> bool:
    return talep.kullanici not in durum.kullanicilar or talep.kaynak not in durum.kaynaklar


#Saatler 15 dakikalık adıma oturmuyorsa veya bitiş başlangıçtan sonra değilse
def zaman_adimi_hatasi(b: datetime, e: datetime) -> bool:
    return not (adima_oturuyor(b) and adima_oturuyor(e)) or e <= b


#Başlangıç simüle saatten önceyse
def gecmis_zaman(durum: SistemDurumu, b: datetime) -> bool:
    return b < durum.saat


#08:00'den önce başlıyor veya 22:00'den sonra bitiyorsa
#True ise ihlal var, False ise sorun yok
#açılıştan önce mi başlıyor?
#kapanıştan sonra mı bitiyor
def calisma_saati_disi(b: datetime, e: datetime) -> bool:
    gun = gun_basi(b)
    return (b < gun + timedelta(hours=CALISMA_BASLANGIC_SAAT)
            or e > gun + timedelta(hours=CALISMA_BITIS_SAAT))


# Süre 30 dakikadan kısa veya rolün azami süresinden uzunsa
def sure_siniri(durum: SistemDurumu, kullanici_id: str, b: datetime, e: datetime) -> bool:
    rol = durum.roller[durum.kullanicilar[kullanici_id].rol]
    sure = dk(e - b)
    return sure < ASGARI_SURE_DK or sure > rol.azami_sure_dk


# Kullanıcının kaç gün ileriye rezervasyon yapabileceği; güvenilirliği eşiğin altındaysa 1 gün
def ileri_gun(durum: SistemDurumu, kullanici_id: str) -> int:
    kullanici = durum.kullanicilar[kullanici_id]
    if kullanici.guvenilirlik < GUVENILIRLIK_ESIK:
        return DUSUK_GUVENILIRLIK_ILERI_GUN
    return durum.roller[kullanici.rol].ileri_gun


# Başlangıç, izin verilen ileri gün sınırının ötesindeyse
def ileri_tarih_siniri(durum: SistemDurumu, kullanici_id: str, b: datetime) -> bool:
    return b > durum.saat + timedelta(days=ileri_gun(durum, kullanici_id))


# Kullanıcının rolü kaynağın izinli rolleri arasında değilse
def rol_izni_yok(durum: SistemDurumu, kullanici_id: str, kaynak_id: str) -> bool:
    return durum.kullanicilar[kullanici_id].rol not in durum.kaynaklar[kaynak_id].izinli_roller


# Kaynak türü sertifika istiyor ve kullanıcıda o sertifika yoksa
def sertifika_yok(durum: SistemDurumu, kullanici_id: str, kaynak_id: str) -> bool:
    gereken = durum.kaynak_turleri[durum.kaynaklar[kaynak_id].tur].sertifika
    return bool(gereken) and gereken not in durum.kullanicilar[kullanici_id].sertifikalar
#kaynak sertifika istiyor mu  evetse değil yoksa 

# İstenen aralık kaynağın bir bakım penceresiyle çakışıyorsa
def bakim(durum: SistemDurumu, kaynak_id: str, b: datetime, e: datetime) -> bool:
    return any(kesisir(b, e, p.baslangic, p.bitis) for p in durum.kaynagin_bakimlari(kaynak_id))


# İstenen aralık kaynaktaki onaylı / kullanımdaki bir rezervasyonla çakışıyorsa
def kesisme(durum: SistemDurumu, kaynak_id: str, b: datetime, e: datetime) -> bool:
    return any(kesisir(b, e, r.baslangic, r.bitis)
               for r in durum.kaynagin_rezervasyonlari(kaynak_id, KESISMEDE_SAYILAN))


# Kaynak türünün iki kullanım arasında gereken hazırlık süresi (dakika)
def hazirlik_dk(durum: SistemDurumu, kaynak_id: str) -> int:
    return durum.kaynak_turleri[durum.kaynaklar[kaynak_id].tur].hazirlik_dk


# Çakışma yok ama başka bir rezervasyonla arada hazırlık süresi kadar boşluk kalmıyorsa.
# Aralıkların iki ucu hazırlık süresi kadar genişletilip kesişme kontrolü yapılır.
def hazirlik_ihlali(durum: SistemDurumu, kaynak_id: str, b: datetime, e: datetime) -> bool:
    h = timedelta(minutes=hazirlik_dk(durum, kaynak_id))
    return any(b < r.bitis + h and e + h > r.baslangic
               for r in durum.kaynagin_rezervasyonlari(kaynak_id, HAZIRLIKTA_SAYILAN))


def ardisik_kullanim(durum: SistemDurumu, kullanici_id: str, kaynak_id: str,
                     b: datetime, e: datetime) -> bool:
    bosluk = timedelta(minutes=ARDISIK_BOSLUK_DK)
    return any(r.kullanici == kullanici_id and b < r.bitis + bosluk and e + bosluk > r.baslangic
               for r in durum.kaynagin_rezervasyonlari(kaynak_id, ARDISIKTA_SAYILAN))

#any en az biri doğruysa true
# Paket içinde aynı kaynaktaki iki kalem birbirine fazla yakınsa
# (hazırlık süresi ile ardışık boşluktan büyük olanı kadar ara gerekir)
def kalemler_catisiyor(h_dk: int, b1: datetime, e1: datetime, b2: datetime, e2: datetime) -> bool:
    bosluk = timedelta(minutes=max(h_dk, ARDISIK_BOSLUK_DK))
    return b1 < e2 + bosluk and e1 + bosluk > b2
