# Modülün ana sınıfı RezervasyonMotoru. Her komut bir metottur; metotlar
# {"durum": "TAMAM", ...} veya {"durum": "RED", "kod": ...} sözlüğü döndürür.
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from . import bekleme as bekleme_k
from . import saat as saat_k
from .durum import SistemDurumu
from .kurallar.dogrulama import dogrula, kalemler_catisiyor, hazirlik_dk, ileri_gun
from .kurallar.iade import iptal_iadesi, bakiyeye_ekle, guvenilirlik_degistir
from .modeller import Kaynak, Kullanici, Rezervasyon, BeklemeKaydi, Talep
from .sabitler import (
    HataKodu as H, RezervasyonDurumu as D, Sonuc,
    PAKET_MIN_KALEM, PAKET_MAX_KALEM, GUVENILIRLIK_ESIK, GIRIS_ONCE_DK, GIRIS_SONRA_DK,
    GUVENILIRLIK_MIN, GUVENILIRLIK_MAX,
)
from .yukleyici import dosyadan_yukle, sozlukten_yukle
from .zaman import coz, bicimle, gun_coz, kesisir


# Başarılı sonuç sözlüğü
def tamam(**alanlar) -> dict:
    return {"durum": Sonuc.TAMAM.value, **alanlar}


# Red sonuç sözlüğü
def red(kod: H, **alanlar) -> dict:
    return {"durum": Sonuc.RED.value, "kod": kod.value, **alanlar}


# Gerçek tam sayı mı (Python'da True/False da int sayıldığı için bool ayrıca dışlanır)
def tam_sayi_mi(deger) -> bool:
    return isinstance(deger, int) and not isinstance(deger, bool)


class RezervasyonMotoru:
    def __init__(self, durum: SistemDurumu):
        self.durum = durum

    # baslangic.json dosyasından motor oluşturur
    @classmethod
    def dosyadan(cls, yol: str | Path) -> "RezervasyonMotoru":
        return cls(dosyadan_yukle(yol))

    # Hazır sözlükten motor oluşturur (testlerde kullanılır)
    @classmethod
    def sozlukten(cls, veri: dict) -> "RezervasyonMotoru":
        return cls(sozlukten_yukle(veri))

    # --- komutlar

    # Simüle saati ileri alır; aradaki olayları (gelmedi, tamamlandı, atama...) döndürür
    def saat(self, zaman: str) -> dict:
        """-> olaylar | RED SAAT_GERI"""
        try:
            yeni = coz(zaman)
        except ValueError:
            return red(H.ZAMAN_ADIMI_HATASI)
        if yeni < self.durum.saat:
            return red(H.SAAT_GERI)  # saat geri alınamaz
        olaylar = saat_k.ilerlet(self.durum, yeni)
        return tamam(olaylar=[o.sozluk() for o in olaylar])

    # Tek rezervasyon: doğrulamadan geçerse oluşturur ve ücreti bakiyeden düşer
    def rezervasyon(self, kullanici: str, kaynak: str, baslangic: str, bitis: str) -> dict:
        """-> rezervasyon_id, ucret, bakiye"""
        sonuc = dogrula(self.durum, Talep(kullanici, kaynak, baslangic, bitis))
        if not sonuc.gecerli:
            return red(sonuc.kod)
        rez = self._olustur(kullanici, kaynak, sonuc.baslangic, sonuc.bitis, sonuc.ucret)
        return tamam(rezervasyon_id=rez.id, ucret=rez.ucret,
                     bakiye=self.durum.kullanicilar[kullanici].bakiye)

    # Paket: 2–4 kalem birlikte; biri bile olmazsa hiçbiri oluşturulmaz (ya hep ya hiç)
    def paket(self, kullanici: str, kalemler: list[dict]) -> dict:
        """-> paket_id, rezervasyonlar, ucretler, toplam, bakiye
        PAKET_RED -> kalemler: [{sira, durum, kod?}]"""
        u = self.durum.kullanicilar.get(kullanici)  #kullanıcı var mı
        if u is None:
            return red(H.BULUNAMADI, kalemler=[])
        # Bozuk girdiye karşı: liste değilse boş liste, sözlük olmayan kalem boş sözlük
        kalemler = kalemler if isinstance(kalemler, list) else []
        kalemler = [k if isinstance(k, dict) else {} for k in kalemler] #eğer dict değilse dict kabul et
        if not PAKET_MIN_KALEM <= len(kalemler) <= PAKET_MAX_KALEM:
            return red(H.PAKET_BOYUTU, kalemler=[])
        if u.guvenilirlik < GUVENILIRLIK_ESIK:
            return red(H.GUVENILIRLIK_DUSUK, kalemler=[])

        # Her kalem ayrı ayrı doğrulanır; bakiye en sonda toplamla kontrol edilir
        sonuclar = [dogrula(self.durum, Talep(kullanici, k.get("kaynak"), k.get("baslangic"),
                                              k.get("bitis")), bakiye_kontrolu=False)
                    for k in kalemler]
        # Reddedilen kalem varsa her kalemin durumunu ve kodunu raporla
        if any(not s.gecerli for s in sonuclar):
            return red(H.PAKET_RED, kalemler=[
                {"sira": i, "durum": Sonuc.TAMAM.value} if s.gecerli
                else {"sira": i, "durum": Sonuc.RED.value, "kod": s.kod.value}
                for i, s in enumerate(sonuclar)])

        # Aynı kaynağı kullanan kalem çiftleri birbirine fazla yakın mı
        hepsi_tamam = [{"sira": i, "durum": Sonuc.TAMAM.value} for i in range(len(kalemler))]
        for i in range(len(kalemler)):
            for j in range(i + 1, len(kalemler)):
                ki, kj = kalemler[i]["kaynak"], kalemler[j]["kaynak"]  #ikisini karşılaştıralım sırayla
                if ki == kj and kalemler_catisiyor(hazirlik_dk(self.durum, ki),  #aynı kaynağı kullanan kalemler çakışıyor mu
                                                   sonuclar[i].baslangic, sonuclar[i].bitis,
                                                   sonuclar[j].baslangic, sonuclar[j].bitis):
                    return red(H.PAKET_ICI_KESISME, kalemler=hepsi_tamam)

        # Toplam ücrete bakiye yetiyor mu
        toplam = sum(s.ucret for s in sonuclar)
        if toplam > u.bakiye:
            return red(H.BAKIYE_YETERSIZ, kalemler=hepsi_tamam)

        # Hepsi geçti: kalemleri aynı paket id'siyle oluştur
        paket_id = self.durum.yeni_paket_id()
        rezler = [self._olustur(kullanici, k["kaynak"], s.baslangic, s.bitis, s.ucret, paket_id)
                  for k, s in zip(kalemler, sonuclar)]
        return tamam(paket_id=paket_id, rezervasyonlar=[r.id for r in rezler],
                     ucretler=[r.ucret for r in rezler], toplam=toplam, bakiye=u.bakiye)

    # Ücret önizleme: rezervasyon oluşturmadan ücreti hesaplar
    def fiyat(self, kullanici: str, kaynak: str, baslangic: str, bitis: str) -> dict:
        """-> ucret. Bakiye hariç tüm kontroller; durum değişmez."""
        sonuc = dogrula(self.durum, Talep(kullanici, kaynak, baslangic, bitis), bakiye_kontrolu=False)
        return tamam(ucret=sonuc.ucret) if sonuc.gecerli else red(sonuc.kod)

    # İptal: sadece onaylı rezervasyon iptal edilir; iade yapılır, boşalan yer için bekleme taranır
    def iptal(self, rezervasyon: str) -> dict:
        """-> iade, bakiye, guvenilirlik, olaylar"""
        rez = self.durum.rezervasyonlar.get(rezervasyon)
        if rez is None:
            return red(H.BULUNAMADI)
        if rez.durum != D.ONAYLI:
            return red(H.DURUM_HATASI)
        u = self.durum.kullanicilar[rez.kullanici]
        ham_iade, guv_fark = iptal_iadesi(rez, self.durum.saat)
        rez.durum = D.IPTAL
        iade = bakiyeye_ekle(self.durum, u, ham_iade)  # kota üst sınırı uygulanır
        guvenilirlik_degistir(u, guv_fark)
        olaylar = bekleme_k.tara(self.durum, rez.kaynak)
        return tamam(iade=iade, bakiye=u.bakiye, guvenilirlik=u.guvenilirlik,
                     olaylar=[o.sozluk() for o in olaylar])

    # Giriş: başlangıçtan 10 dk önce ile 15 dk sonra arasında yapılabilir
    def giris(self, rezervasyon: str) -> dict:
        """-> yeni_durum"""
        rez = self.durum.rezervasyonlar.get(rezervasyon)
        if rez is None:
            return red(H.BULUNAMADI)
        if rez.durum != D.ONAYLI:
            return red(H.DURUM_HATASI)
        simdi = self.durum.saat
        if not (rez.baslangic - timedelta(minutes=GIRIS_ONCE_DK) <= simdi
                <= rez.baslangic + timedelta(minutes=GIRIS_SONRA_DK)):
            return red(H.GIRIS_PENCERESI_DISI)
        rez.durum = D.KULLANIMDA
        return tamam(yeni_durum=rez.durum.value)

    # Çıkış: kullanımdaki rezervasyonu bitirir; erken çıkılırsa kalan süre bekleme listesine açılır
    def cikis(self, rezervasyon: str) -> dict:
        rez = self.durum.rezervasyonlar.get(rezervasyon)
        if rez is None:
            return red(H.BULUNAMADI)
        if rez.durum != D.KULLANIMDA:
            return red(H.DURUM_HATASI)
        # Bitiş, çıkış anına çekilir (başlangıçtan önce olamaz)
        rez.bitis = max(self.durum.saat, rez.baslangic)
        rez.durum = D.TAMAMLANDI
        u = self.durum.kullanicilar[rez.kullanici]
        olaylar = bekleme_k.tara(self.durum, rez.kaynak)
        return tamam(yeni_durum=rez.durum.value, guvenilirlik=u.guvenilirlik,
                     olaylar=[o.sozluk() for o in olaylar])

    # Bekleme kaydı: sadece KESISME / HAZIRLIK_IHLALI ile reddedilecek talepler için açılır
    def bekleme(self, kullanici: str, kaynak: str, baslangic: str, bitis: str) -> dict:
        sonuc = dogrula(self.durum, Talep(kullanici, kaynak, baslangic, bitis), bakiye_kontrolu=False)
        if sonuc.gecerli:
            return red(H.BEKLEME_GEREKSIZ)  # yer zaten boş, doğrudan rezervasyon yapılabilir
        if sonuc.kod not in (H.KESISME, H.HAZIRLIK_IHLALI):
            return red(sonuc.kod)  # başka bir kural ihlali; beklemek işe yaramaz
        kayit = BeklemeKaydi(id=self.durum.yeni_bekleme_id(), kullanici=kullanici, kaynak=kaynak,
                             baslangic=sonuc.baslangic, bitis=sonuc.bitis,
                             kayit_saati=self.durum.saat)
        self.durum.bekleme_kayitlari[kayit.id] = kayit
        # Kaydın sıradaki yeri (1'den başlar)
        sira = [b.id for b in bekleme_k.sirali_kayitlar(self.durum, kaynak)].index(kayit.id) + 1
        return tamam(bekleme_id=kayit.id, sira=sira)

    # Kullanıcı sorgusu: bakiye, güvenilirlik ve başlangıca göre sıralı rezervasyonlar
    def sorgu_kullanici(self, id: str) -> dict:
        u = self.durum.kullanicilar.get(id)
        if u is None:
            return red(H.BULUNAMADI)
        rezler = sorted((r for r in self.durum.rezervasyonlar.values() if r.kullanici == id),
                        key=lambda r: (r.baslangic, r.no))
        return tamam(bakiye=u.bakiye, guvenilirlik=u.guvenilirlik, rezervasyonlar=[
            {"id": r.id, "kaynak": r.kaynak, "baslangic": bicimle(r.baslangic),
             "bitis": bicimle(r.bitis), "durum": r.durum.value, "ucret": r.ucret}
            for r in rezler])

    # Kaynak sorgusu: verilen gündeki aktif rezervasyonlar ve bakımlar, zamana göre sıralı
    def sorgu_kaynak(self, id: str, gun: str) -> dict:
        if id not in self.durum.kaynaklar:
            return red(H.BULUNAMADI)
        try:
            gun_bas = gun_coz(gun)
        except ValueError:
            return red(H.ZAMAN_ADIMI_HATASI)
        gun_bit = gun_bas + timedelta(days=1)
        # Her öğe (sıralama anahtarı, çıktı sözlüğü); aynı saatte bakım (0) rezervasyondan (1) önce
        ogeler = []
        for r in self.durum.kaynagin_rezervasyonlari(id, {D.ONAYLI, D.KULLANIMDA}):
            if kesisir(r.baslangic, r.bitis, gun_bas, gun_bit):
                ogeler.append(((r.baslangic, 1, r.no), {
                    "baslangic": bicimle(r.baslangic), "bitis": bicimle(r.bitis),
                    "tur": "REZERVASYON", "rezervasyon": r.id}))
        for p in self.durum.kaynagin_bakimlari(id):
            if kesisir(p.baslangic, p.bitis, gun_bas, gun_bit):
                ogeler.append(((p.baslangic, 0, 0), {
                    "baslangic": bicimle(p.baslangic), "bitis": bicimle(p.bitis), "tur": "BAKIM"}))
        ogeler.sort(key=lambda o: o[0])
        return tamam(doluluk=[o[1] for o in ogeler])

    # Yeni kullanıcı: id benzersiz, rol tanımlı, bakiye 0–kota, güvenilirlik 0–100 olmalı
    def kullanici_ekle(self, id: str, ad: str, rol: str, sertifikalar: list[str],
                       bakiye: int, guvenilirlik: int) -> dict:
        if id in self.durum.kullanicilar:
            return red(H.ID_MEVCUT)
        if rol not in self.durum.roller:
            return red(H.TANIMSIZ_DEGER)
        kota = self.durum.roller[rol].haftalik_kota
        if (not tam_sayi_mi(bakiye) or not 0 <= bakiye <= kota
                or not tam_sayi_mi(guvenilirlik)
                or not GUVENILIRLIK_MIN <= guvenilirlik <= GUVENILIRLIK_MAX):
            return red(H.GECERSIZ_DEGER)
        self.durum.kullanicilar[id] = Kullanici(id=id, ad=ad, rol=rol,
                                                sertifikalar=list(sertifikalar or []),
                                                bakiye=bakiye, guvenilirlik=guvenilirlik)
        return tamam()

    # Yeni kaynak: id benzersiz, tür ve izinli roller tanımlı olmalı
    def kaynak_ekle(self, id: str, ad: str, tur: str, izinli_roller: list[str]) -> dict:
        if id in self.durum.kaynaklar:
            return red(H.ID_MEVCUT)
        if tur not in self.durum.kaynak_turleri or any(r not in self.durum.roller
                                                        for r in izinli_roller or []):
            return red(H.TANIMSIZ_DEGER)
        self.durum.kaynaklar[id] = Kaynak(id=id, ad=ad, tur=tur, izinli_roller=list(izinli_roller or []))
        return tamam()

    # Rezervasyonu duruma ekler ve ücreti bakiyeden düşer (doğrulama önceden yapılmış olmalı)
    def _olustur(self, kullanici: str, kaynak: str, b, e, ucret: int,
                 paket: str | None = None) -> Rezervasyon:
        rez = Rezervasyon(id=self.durum.yeni_rezervasyon_id(), kullanici=kullanici, kaynak=kaynak,
                          baslangic=b, bitis=e, ucret=ucret, paket=paket)
        self.durum.rezervasyonlar[rez.id] = rez
        self.durum.kullanicilar[kullanici].bakiye -= ucret
        return rez

    # --- görüntü metotları: arayüzün durumu okuması için; hiçbir şeyi değiştirmez

    # Simüle saat metin olarak
    def goruntu_saat(self) -> str:
        return bicimle(self.durum.saat)

    # Kaynak türleri, roller ve sertifikalar (arayüzdeki seçim listeleri için)
    def goruntu_parametreler(self) -> dict:
        d = self.durum
        return {
            "kaynak_turleri": {t.ad: {"hazirlik_dk": t.hazirlik_dk, "temel_ucret": t.temel_ucret,
                                      "enerji_yogun": t.enerji_yogun, "sertifika": t.sertifika}
                               for t in d.kaynak_turleri.values()},
            "roller": {r.ad: {"haftalik_kota": r.haftalik_kota, "ileri_gun": r.ileri_gun,
                              "azami_sure_dk": r.azami_sure_dk} for r in d.roller.values()},
            "sertifikalar": sorted(d.sertifikalar),
        }

    # Tüm kaynakların listesi
    def goruntu_kaynaklar(self) -> list[dict]:
        return [{"id": k.id, "ad": k.ad, "tur": k.tur, "izinli_roller": list(k.izinli_roller)}
                for k in self.durum.kaynaklar.values()]

    # Tüm kullanıcıların listesi (ileri gün sınırı dahil)
    def goruntu_kullanicilar(self) -> list[dict]:
        d = self.durum
        return [{"id": u.id, "ad": u.ad, "rol": u.rol, "sertifikalar": list(u.sertifikalar),
                 "bakiye": u.bakiye, "guvenilirlik": u.guvenilirlik,
                 "ileri_gun": ileri_gun(d, u.id)}
                for u in d.kullanicilar.values()]

    # Tek rezervasyonun ayrıntısı (yoksa None)
    def goruntu_rezervasyon(self, id: str) -> dict | None:
        r = self.durum.rezervasyonlar.get(id)
        return None if r is None else self._rez_sozluk(r)

    # Takvim için: verilen gün, her kaynağın rezervasyonları, bakımları ve hazırlık aralıkları
    def goruntu_gun(self, gun: str) -> dict:
        d = self.durum
        gun_bas = gun_coz(gun)
        gun_bit = gun_bas + timedelta(days=1)
        sonuc = {}
        for k in d.kaynaklar.values():
            h = timedelta(minutes=hazirlik_dk(d, k.id))
            rezler = sorted((r for r in d.rezervasyonlar.values()
                             if r.kaynak == k.id and kesisir(r.baslangic, r.bitis, gun_bas, gun_bit)),
                            key=lambda r: (r.baslangic, r.no))
            # Her rezervasyonun bitişinden sonraki hazırlık süresi takvimde ayrı gösterilir
            hazirliklar = [{"baslangic": bicimle(r.bitis), "bitis": bicimle(r.bitis + h),
                            "rezervasyon": r.id}
                           for r in rezler
                           if h and r.durum in (D.ONAYLI, D.KULLANIMDA, D.TAMAMLANDI)]
            bakimlar = [{"baslangic": bicimle(p.baslangic), "bitis": bicimle(p.bitis)}
                        for p in d.kaynagin_bakimlari(k.id)
                        if kesisir(p.baslangic, p.bitis, gun_bas, gun_bit)]
            sonuc[k.id] = {"rezervasyonlar": [self._rez_sozluk(r) for r in rezler],
                           "bakimlar": bakimlar, "hazirliklar": hazirliklar}
        return sonuc

    # Kullanıcının bekleme kayıtları ve her birinin kendi kaynağındaki sırası
    def goruntu_bekleme_kayitlari(self, kullanici: str) -> list[dict]:
        sonuc = []
        for kaynak_id in {b.kaynak for b in self.durum.bekleme_kayitlari.values()}:
            for sira, b in enumerate(bekleme_k.sirali_kayitlar(self.durum, kaynak_id), 1):
                if b.kullanici == kullanici:
                    sonuc.append({"id": b.id, "kaynak": b.kaynak, "baslangic": bicimle(b.baslangic),
                                  "bitis": bicimle(b.bitis), "sira": sira,
                                  "kayit_saati": bicimle(b.kayit_saati)})
        return sorted(sonuc, key=lambda b: int(b["id"][1:]))

    # Rezervasyon nesnesini çıktı sözlüğüne çevirir
    def _rez_sozluk(self, r: Rezervasyon) -> dict:
        return {"id": r.id, "kullanici": r.kullanici, "kaynak": r.kaynak,
                "baslangic": bicimle(r.baslangic), "bitis": bicimle(r.bitis),
                "ucret": r.ucret, "durum": r.durum.value, "paket": r.paket}
