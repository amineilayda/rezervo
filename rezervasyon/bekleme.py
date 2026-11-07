from __future__ import annotations
from .durum import SistemDurumu
from .kurallar.dogrulama import dogrula
from .modeller import BeklemeKaydi, Olay, Rezervasyon, Talep    
from .sabitler import OlayTuru
from .zaman import bicimle


#önce yüksek güvenilirlik, eşitse erken kayıt, o da eşitse küçük id
def sirali_kayitlar(durum: SistemDurumu, kaynak_id: str) -> list[BeklemeKaydi]:
    return sorted(durum.kaynagin_bekleme_kayitlari(kaynak_id),
                  key=lambda b: (-durum.kullanicilar[b.kullanici].guvenilirlik, b.kayit_saati, b.no))
#key neye göre sıralayacağını belirler, - ile azalan sıraya

#aşlangıcı geçmi (artık işe yaramayan) bekleme kayıtlarını siler
def eskileri_sil(durum: SistemDurumu) -> None: #bişey döndürmez
    for bid in [b.id for b in durum.bekleme_kayitlari.values() if b.baslangic < durum.saat]: #süresi geçmiş
        del durum.bekleme_kayitlari[bid]


# Kaynakta yer açıldığınd (iptal, çıkış, gelmedi)sıradaki kayıtları dener
#tüm kurallardan geçen her kayıt için rezervasyon oluşturup OTOMATIK_ATAMAolay döndürür
def tara(durum: SistemDurumu, kaynak_id: str) -> list[Olay]:
    eskileri_sil(durum)
    olaylar = []
    for kayit in sirali_kayitlar(durum, kaynak_id):
        talep = Talep(kayit.kullanici, kayit.kaynak, bicimle(kayit.baslangic), bicimle(kayit.bitis))
        #Normal rezervasyondaki tüm kontroller(bakiye dahil burada da uygulanır
        sonuc = dogrula(durum, talep)
        if not sonuc.gecerli:
            continue  #bu kayıt hâlâ sığmıyor, sıradakine geç

        #Ücreti düş, rezervasyonu oluştur, bekleme kaydını sil  eğer uygunsa
        kullanici = durum.kullanicilar[kayit.kullanici]
        kullanici.bakiye -= sonuc.ucret
        rez = Rezervasyon(id=durum.yeni_rezervasyon_id(), kullanici=kayit.kullanici,
                          kaynak=kayit.kaynak, baslangic=kayit.baslangic, bitis=kayit.bitis,
                          ucret=sonuc.ucret)
        durum.rezervasyonlar[rez.id] = rez
        del durum.bekleme_kayitlari[kayit.id]
        olaylar.append(Olay(durum.saat, OlayTuru.OTOMATIK_ATAMA, {
            "bekleme": kayit.id, "rezervasyon": rez.id, "kullanici": kullanici.id,
            "ucret": rez.ucret, "bakiye": kullanici.bakiye}))
    return olaylar
