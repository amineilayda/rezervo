# Modül genelinde kullanılan sabit değerler ve sabit kod listeleri.
# StrEnum: değerleri doğrudan metin gibi davranır, JSON çıktısına aynen yazılır.
from enum import StrEnum


# Bir rezervasyonun yaşam döngüsündeki durumlar
class RezervasyonDurumu(StrEnum):
    ONAYLI = "ONAYLI"           
    KULLANIMDA = "KULLANIMDA"    
    TAMAMLANDI = "TAMAMLANDI"    
    IPTAL = "IPTAL"              
    GELMEDI = "GELMEDI"          


#komutun durumu
class Sonuc(StrEnum):
    TAMAM = "TAMAM"
    RED = "RED"

#saat ilerlerken olan seyler
class OlayTuru(StrEnum):
    HAFTALIK_SIFIRLAMA = "HAFTALIK_SIFIRLAMA"  
    TAMAMLANDI = "TAMAMLANDI"                  
    GELMEDI = "GELMEDI"                        
    OTOMATIK_ATAMA = "OTOMATIK_ATAMA"          


class HataKodu(StrEnum):
    #doğrulama.py
    BULUNAMADI = "BULUNAMADI"
    ZAMAN_ADIMI_HATASI = "ZAMAN_ADIMI_HATASI"
    GECMIS_ZAMAN = "GECMIS_ZAMAN"
    CALISMA_SAATI_DISI = "CALISMA_SAATI_DISI"
    SURE_SINIRI = "SURE_SINIRI"
    ILERI_TARIH_SINIRI = "ILERI_TARIH_SINIRI"
    ROL_IZNI_YOK = "ROL_IZNI_YOK"
    SERTIFIKA_YOK = "SERTIFIKA_YOK"
    BAKIM = "BAKIM"
    KESISME = "KESISME"
    HAZIRLIK_IHLALI = "HAZIRLIK_IHLALI"
    ARDISIK_KULLANIM = "ARDISIK_KULLANIM"
    BAKIYE_YETERSIZ = "BAKIYE_YETERSIZ"

    
    PAKET_BOYUTU = "PAKET_BOYUTU"
    GUVENILIRLIK_DUSUK = "GUVENILIRLIK_DUSUK"
    PAKET_RED = "PAKET_RED"
    PAKET_ICI_KESISME = "PAKET_ICI_KESISME"

    DURUM_HATASI = "DURUM_HATASI"
    GIRIS_PENCERESI_DISI = "GIRIS_PENCERESI_DISI"

    BEKLEME_GEREKSIZ = "BEKLEME_GEREKSIZ"

    ID_MEVCUT = "ID_MEVCUT"
    TANIMSIZ_DEGER = "TANIMSIZ_DEGER"
    GECERSIZ_DEGER = "GECERSIZ_DEGER"

    SAAT_GERI = "SAAT_GERI"


ZAMAN_BICIMI = "%Y-%m-%dT%H:%M"   
GUN_BICIMI = "%Y-%m-%d"           
DILIM_DK = 15                     
CALISMA_BASLANGIC_SAAT = 8        
CALISMA_BITIS_SAAT = 22           
ASGARI_SURE_DK = 30               
BANT_DK = 120                     
PIK_BASLANGIC_SAAT = 10          
PIK_BITIS_SAAT = 16

PIK_CARPANI_ENERJI_YOGUN = 1.5  

#aynı kişi ard arda kullanma zaman aralık
ARDISIK_BOSLUK_DK = 60


GIRIS_ONCE_DK = 10      
GIRIS_SONRA_DK = 15     
IADE_TAM_SAAT = 24     
IADE_YARIM_SAAT = 2     


GUVENILIRLIK_GELMEDI = -15
GUVENILIRLIK_GEC_IPTAL = -5
GUVENILIRLIK_ZAMANINDA_TAMAMLANDI = +2
GUVENILIRLIK_ESIK = 50             
DUSUK_GUVENILIRLIK_ILERI_GUN = 1    
GUVENILIRLIK_MIN = 0
GUVENILIRLIK_MAX = 100

PAKET_MIN_KALEM = 2
PAKET_MAX_KALEM = 4
