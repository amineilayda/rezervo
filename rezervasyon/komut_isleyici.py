"""Komut sözlüğü -> motor fonksiyonu -> sonuç satırı.

CLI ve arayüzün olay günlüğü aynı eşlemeyi kullanır; böylece arayüzden yapılan
19 işlem ile komut dosyası birebir aynı sonucu verir.
Eksik alanlar None olarak iletilir; motor bunları ilgili hata koduyla reddeder.
"""
from __future__ import annotations

from .motor import RezervasyonMotoru

# rezervasyon / fiyat / bekleme komutlarının ortak alanları (bu sırayla iletilir)
TALEP_ALANLARI = ("kullanici", "kaynak", "baslangic", "bitis")


#getattr: Bir nesnenin özelliğini veya metodunu adıyla (metin olarak) bulmayı sağlıyor.

def calistir(motor: RezervasyonMotoru, komut: dict) -> dict:
    """{"komut": ..., alanlar...} -> sonuç gövdesi (durum, kod / ek alanlar)."""
    ad = komut.get("komut")
    al = komut.get  # kısaltma: alan yoksa None döner
    if ad == "saat":
        return motor.saat(al("zaman"))
    # Aynı parametreleri alan komutlar: getattr ile motordaki aynı adlı metot çağrılır
    if ad in ("rezervasyon", "fiyat", "bekleme"):
        return getattr(motor, ad)(*(al(a) for a in TALEP_ALANLARI))
    if ad == "paket":
        return motor.paket(al("kullanici"), al("kalemler"))
    if ad in ("iptal", "giris", "cikis"):
        return getattr(motor, ad)(al("rezervasyon"))
    # Sorgu: tur alanına göre kaynak veya kullanıcı sorgusu
    if ad == "sorgu":
        if al("tur") == "kaynak":
            return motor.sorgu_kaynak(al("id"), al("gun"))
        return motor.sorgu_kullanici(al("id"))
    if ad == "kullanici_ekle":
        return motor.kullanici_ekle(al("id"), al("ad"), al("rol"), al("sertifikalar"),
                                    al("bakiye"), al("guvenilirlik"))
    if ad == "kaynak_ekle":
        return motor.kaynak_ekle(al("id"), al("ad"), al("tur"), al("izinli_roller"))
    return {"durum": "RED", "kod": "BILINMEYEN_KOMUT"}


# Çıktı satırı: sıra numarası ve komut adı başa, motorun döndürdüğü alanlar arkaya
def sonuc_satiri(no: int, komut: dict, govde: dict) -> dict:
    return {"no": no, "komut": komut.get("komut"), **govde}
