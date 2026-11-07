
HATA_ACIKLAMALARI: dict[str, str] = {
    "BULUNAMADI": "Kullanıcı, kaynak veya rezervasyon bulunamadı.",
    "ZAMAN_ADIMI_HATASI": "Saatler 15 dakikalık adımlara oturmalı ve bitiş başlangıçtan sonra olmalı.",
    "GECMIS_ZAMAN": "Başlangıç simüle saatten önce olamaz.",
    "CALISMA_SAATI_DISI": "Rezervasyon aynı gün içinde 08:00–22:00 arasında kalmalı.",
    "SURE_SINIRI": "Süre en az 30 dakika, en fazla rolün azami süresi kadar olabilir.",
    "ILERI_TARIH_SINIRI": "Rolün ileri tarih sınırı aşıldı (güvenilirlik 50'nin altındaysa 1 gün).",
    "ROL_IZNI_YOK": "Kullanıcının rolü bu kaynağı rezerve edemez.",
    "SERTIFIKA_YOK": "Bu kaynak türü için gerekli sertifika kullanıcıda yok.",
    "BAKIM": "Talep edilen aralık bir bakım penceresiyle çakışıyor.",
    "KESISME": "Talep edilen aralık başka bir rezervasyonla çakışıyor.",
    "HAZIRLIK_IHLALI": "Kaynağın hazırlık süresi (soğuma/havalandırma) ihlal ediliyor.",
    "ARDISIK_KULLANIM": "Aynı kaynakta iki rezervasyonunuz arasında en az 60 dakika olmalı.",
    "BAKIYE_YETERSIZ": "Bakiye bu ücret için yetersiz.",
    "PAKET_BOYUTU": "Paket 2 ile 4 arasında kalem içermeli.",
    "GUVENILIRLIK_DUSUK": "Güvenilirlik 50'nin altında; paket rezervasyon yapılamaz.",
    "PAKET_RED": "Paketteki en az bir kalem doğrulamadan geçemedi.",
    "PAKET_ICI_KESISME": "Paketteki kalemler kendi aralarında çakışıyor veya kuralları ihlal ediyor.",
    "DURUM_HATASI": "Rezervasyon bu işlem için uygun durumda değil.",
    "GIRIS_PENCERESI_DISI": "Giriş yalnızca başlangıçtan 10 dk önce ile 15 dk sonra arasında yapılabilir.",
    "BEKLEME_GEREKSIZ": "Bu aralık zaten müsait; doğrudan rezervasyon yapabilirsiniz.",
    "ID_MEVCUT": "Bu kimlikle bir kayıt zaten var.",
    "TANIMSIZ_DEGER": "Rol, tür veya izinli rollerden biri tanımlı değil.",
    "GECERSIZ_DEGER": "Bakiye 0 ile haftalık kota arasında, güvenilirlik 0–100 arası tam sayı olmalı.",
    "SAAT_GERI": "Simüle saat geri alınamaz.",
    "BILINMEYEN_KOMUT": "Komut tanınmadı.",
}

KOMUT_ADLARI = {
    "saat": "Saat", "rezervasyon": "Rezervasyon", "paket": "Paket", "fiyat": "Fiyat",
    "iptal": "İptal", "giris": "Giriş", "cikis": "Çıkış", "bekleme": "Bekleme",
    "sorgu": "Sorgu", "kullanici_ekle": "Kullanıcı ekle", "kaynak_ekle": "Kaynak ekle",
}

DURUM_ADLARI = {
    "ONAYLI": "Onaylı", "KULLANIMDA": "Kullanımda", "TAMAMLANDI": "Tamamlandı",
    "IPTAL": "İptal", "GELMEDI": "Gelmedi",
}


def aciklama(kod: str) -> str:
    return HATA_ACIKLAMALARI.get(kod, kod)


def saat_kismi(zaman: str) -> str:
    return zaman[11:16] if zaman and len(zaman) >= 16 else zaman


def tarih_saat(zaman: str) -> str:

    
    if not zaman or len(zaman) < 16:
        return zaman
    return f"{zaman[8:10]}.{zaman[5:7]} {zaman[11:16]}"



def olay_metni(olay: dict) -> str:
    z = tarih_saat(olay.get("zaman", ""))
    tur = olay.get("tur")
    if tur == "HAFTALIK_SIFIRLAMA":
        return f"{z} · Haftalık kota yenilendi"
    if tur == "TAMAMLANDI":
        return (f"{z} · {olay['rezervasyon']} tamamlandı · {olay['kullanici']} "
                f"güvenilirlik {olay['guvenilirlik']}")
    if tur == "GELMEDI":
        return (f"{z} · {olay['rezervasyon']} gelinmedi · {olay['kullanici']} "
                f"güvenilirlik {olay['guvenilirlik']}")
    if tur == "OTOMATIK_ATAMA":
        return (f"{z} · {olay['bekleme']} → {olay['rezervasyon']} otomatik atandı · "
                f"{olay['kullanici']} · {olay['ucret']} KP · bakiye {olay['bakiye']}")
    return f"{z} · {tur}"



def ozet(satir: dict) -> str:

    
    if satir.get("durum") == "RED":
        return f"{satir.get('kod')} — {aciklama(satir.get('kod', ''))}"
    k = satir.get("komut")
    if k == "rezervasyon":
        return f"{satir['rezervasyon_id']} oluşturuldu · {satir['ucret']} KP · bakiye {satir['bakiye']}"
    if k == "fiyat":
        return f"Ücret {satir['ucret']} KP"
    if k == "paket":
        ucretler = " + ".join(str(u) for u in satir["ucretler"])
        return (f"{satir['paket_id']}: {', '.join(satir['rezervasyonlar'])} · "
                f"{ucretler} = {satir['toplam']} KP · bakiye {satir['bakiye']}")
    if k == "iptal":
        return (f"İptal edildi · iade {satir['iade']} KP · bakiye {satir['bakiye']} · "
                f"güvenilirlik {satir['guvenilirlik']}")
    if k == "giris":
        return f"Giriş yapıldı → {DURUM_ADLARI.get(satir['yeni_durum'], satir['yeni_durum'])}"
    if k == "cikis":
        return f"Çıkış yapıldı → Tamamlandı · güvenilirlik {satir['guvenilirlik']}"
    if k == "bekleme":
        return f"{satir['bekleme_id']} bekleme kaydı açıldı · sıra {satir['sira']}"
    if k == "saat":
        n = len(satir.get("olaylar", []))
        return f"{n} olay" if n else "Olay yok"
    if k == "sorgu":
        if "doluluk" in satir:
            return f"{len(satir['doluluk'])} dolu aralık"
        return (f"bakiye {satir['bakiye']} · güvenilirlik {satir['guvenilirlik']} · "
                f"{len(satir['rezervasyonlar'])} rezervasyon")
    if k == "kullanici_ekle":
        return "Kullanıcı eklendi"
    if k == "kaynak_ekle":
        return "Kaynak eklendi"
    return "Tamam"


def ayrinti_satirlari(satir: dict) -> list[str]:

    
    satirlar = [olay_metni(o) for o in satir.get("olaylar", [])]
    if satir.get("komut") == "sorgu" and satir.get("durum") == "TAMAM":
        for r in satir.get("rezervasyonlar", []):
            satirlar.append(f"{r['id']} · {r['kaynak']} · {tarih_saat(r['baslangic'])}–"
                            f"{saat_kismi(r['bitis'])} · {DURUM_ADLARI.get(r['durum'], r['durum'])} · "
                            f"{r['ucret']} KP")
        for d in satir.get("doluluk", []):
            ad = d.get("rezervasyon", "Bakım")
            satirlar.append(f"{saat_kismi(d['baslangic'])}–{saat_kismi(d['bitis'])} · {ad}")
    return satirlar
