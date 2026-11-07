# Mimari

Rezervo — Python 3.11+, arayüz PySide6 (Qt).

## Katmanlar

```
┌─────────────────────────┐      ┌──────────────────────────────┐
│ calistir.sh / .bat      │      │ arayuz/  (PySide6)           │
│ rezervasyon/__main__.py │      │  bilesenler/* ── istemci.py  │
└───────────┬─────────────┘      └──────────────┬───────────────┘
            │  komut sözlüğü                    │  komut sözlüğü
            ▼                                   ▼
        ┌────────────────── komut_isleyici.py ─────────────────┐
        │  {"komut": ...}  →  motor.<fonksiyon>()  →  sonuç     │
        └───────────────────────────┬──────────────────────────┘
                                    ▼
        ┌──────────────────── motor.py (genel API) ────────────┐
        │ saat, rezervasyon, paket, fiyat, iptal, giris, cikis, │
        │ bekleme, sorgu_*, kullanici_ekle, kaynak_ekle,        │
        │ goruntu_* (arayüz için salt-okunur)                   │
        └──────┬───────────────┬──────────────┬────────────────┘
               ▼               ▼              ▼
        kurallar/          bekleme.py      saat.py
        dogrulama         
        ucret    
        iade     
               └───────────────┴──────────────┘
                               ▼
                  durum.py  (SistemDurumu, bellekte)
                  modeller.py, sabitler.py, zaman.py
                               ▲
                  yukleyici.py ← baslangic.json
```

**Temel ilkeler**

1. **Tek motor, iki giriş.** CLI ve arayüz aynı `komut_isleyici` → `RezervasyonMotoru`
   yolundan geçer. Arayüzden yapılan 19 işlem, komut dosyasıyla aynı sonucu verir; olay
   günlüğündeki JSON da doğal olarak Bölüm 5 biçimindedir.
2. **Arayüzde iş kuralı yok.** Arayüz talepleri engellemez; tüm doğrulamayı modül yapar.
   Takvimin ihtiyaç duyduğu veriler (hazırlık blokları dahil) `goruntu_*` ile modülden gelir.
3. **Parametreler kodda değil, dosyada.** Tür, rol, ücret, kota, hazırlık süresi, sertifika
   `baslangic.json`'dan okunur. `sabitler.py` yalnızca dokümanda sabit verilen değerleri
   (15 dk dilim, 08–22, bantlar, pik saatler, iade oranları, güvenilirlik değişimleri) içerir.
4. **Kurallar saf fonksiyon.** `kurallar/` durumu okur, değiştirmez → birim test edilebilir.
   Durum değişikliği yalnızca `motor.py`, `bekleme.py` ve `saat.py` içindedir.
5. **Kesin aritmetik.** Ücret `Fraction` ile hesaplanır, yarımda yukarı yuvarlanır.

## Dosya yapısı

```
rezervo/
├── calistir.sh, calistir.bat     # ./calistir.sh baslangic.json komutlar.jsonl
├── uygulama.sh, uygulama.bat     # masaüstü uygulaması
├── requirements.txt              # PySide6
├── MIMARI.md
├── rezervasyon/                  # Arayüzden bağımsız modül (yalnızca standart kütüphane)
│   ├── __main__.py               # CLI girişi
│   ├── komut_isleyici.py         # komut sözlüğü → motor fonksiyonu
│   ├── motor.py                  # RezervasyonMotoru (genel API)
│   ├── durum.py                  # SistemDurumu + id üretimi (r, p, b)
│   ├── modeller.py               # dataclass'lar
│   ├── sabitler.py               # durumlar, hata kodları, sabit kural değerleri
│   ├── zaman.py                  # çözümleme, aralık, dilim, Pazartesi geçişi
│   ├── yukleyici.py              # baslangic.json → SistemDurumu
│   ├── bekleme.py                # bekleme listesi
│   ├── saat.py                   # simüle saat, olay döngüsü
│   └── kurallar/
│       ├── dogrulama.py          # doğrulama zinciri
│       ├── ucret.py              # ücret
│       └── iade.py               # iade, güvenilirlik
├── arayuz/                       # Masaüstü uygulaması: python -m arayuz
│   ├── __main__.py
│   ├── istemci.py                # motor köprüsü, günlük, durum_degisti sinyali
│   ├── ana_pencere.py            # tek ekran yerleşimi
│   ├── tema.py, metinler.py      # renkler / Türkçe hata açıklamaları
│   └── bilesenler/
│       ├── takvim.py             # kaynak takvimi (alt şeritli, sürükleyerek seçim)
│       ├── talep_formu.py        # tek/paket, fiyat önizleme, bekleme önerisi
│       ├── rezervasyon_karti.py  # takvimden açılan ayrıntı kartı (giriş/çıkış/iptal)
│       ├── kullanici_paneli.py   # kullanıcı seçici + rezervasyonlar + bekleme kayıtları
│       ├── saat_paneli.py        # simüle saat göstergesi ve ilerletme
│       ├── olay_gunlugu.py       # tüm sonuçlar + seçilen satırın JSON'u
│       ├── ekleme_diyaloglari.py # yeni kullanıcı / kaynak formları
│       └── ortak.py              # sonuç bandı, açılır kart, saat kutusu
├── ornek/                        # e-destek örnek dosyaları
├── testler/
│   ├── karsilastir.py            # alan alan karşılaştırıcı (fazla alan serbest)
│   ├── test_ornek_senaryo.py
│   ├── arayuz_senaryosu.py       # 19 adımı arayüz bileşenleriyle yapar
│   └── senaryolar/               # kendi komut + beklenen dosyalarımız
└── rapor/                        # IEEE rapor
```

## Kritik akışlar

**Rezervasyon:** `dogrula()` 13 adımı sırayla çalıştırır, ilk hatada döner →
geçerliyse `ucret_hesapla()` (talep anındaki doluluk) → bakiye düş → `r<n>` oluştur.

**Fiyat:** aynı zincir, `bakiye_kontrolu=False`, durum değişmez.

**Paket:** BULUNAMADI → PAKET_BOYUTU → GUVENILIRLIK_DUSUK → her kalem bağımsız
doğrulama (paket öncesi duruma göre; bakiye hariç) → PAKET_RED (kalem listesi) →
kalemler arası hazırlık/ardışık → BAKIYE_YETERSIZ (toplam) → hepsini oluştur, `p<n>`.

**Bekleme:** doğrulama yalnızca KESISME/HAZIRLIK_IHLALI ile düşüyorsa kayıt açılır;
geçerliyse BEKLEME_GEREKSIZ; diğer hatalar aynen döner. Bakiye bakılmaz.

**Saat:** `(eski, yeni]` içindeki en yakın olay anı bulunur → o anda sırayla
haftalık sıfırlama, TAMAMLANDI'lar, GELMEDI'ler, boşalan kaynakların bekleme taraması
→ saat o ana alınır → tekrar. Otomatik atamalar yeni olay doğurabileceği için kuyruk
her adımda yeniden hesaplanır. Eski bekleme kayıtları temizlenir.

**İptal / çıkış:** durum değişir, iade/güvenilirlik uygulanır, ardından o kaynağın
bekleme listesi taranır → `olaylar` alanında OTOMATIK_ATAMA'lar döner.

## Dikkat edilecek ayrıntılar

- TAMAMLANDI hazırlık ve ardışık kullanımda sayılır, kesişmede ve dolulukta sayılmaz.
- Erken çıkışta `bitis` çıkış saatine güncellenir (hazırlık oradan başlar), güvenilirlik değişmez;
  zamanında tamamlanan için +2.
- Doluluk, kaynak sayısını **talep anında** alır (kaynak_ekle sonrası artar).
- `iade` alanı = bakiyeye **gerçekte eklenen** miktar (kota tavanı).
- Güvenilirlik < 50 → ileri_gun = 1 ve paket yasak.
- Sorgu kullanıcı: başlangıca, eşitlikte rezervasyon numarasına göre (sayısal: r2 < r10).
