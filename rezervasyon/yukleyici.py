# baslangic.json dosyasını okuyup SistemDurumu nesnesini kurar
from __future__ import annotations

import json
from pathlib import Path

from .durum import SistemDurumu
from .modeller import KaynakTuru, Rol, Kaynak, Kullanici, BakimPenceresi
from .zaman import coz


# Dosyayı açıp JSON olarak okur, kurulumu sozlukten_yukle'ye bırakır
def dosyadan_yukle(yol: str | Path) -> SistemDurumu:
    with open(yol, encoding="utf-8-sig") as f:
        return sozlukten_yukle(json.load(f))


# JSON sözlüğündeki her bölümü ilgili veri sınıfına çevirip duruma ekler
def sozlukten_yukle(veri: dict) -> SistemDurumu:
    # Başlangıç simüle saati
    durum = SistemDurumu(saat=coz(veri["saat"]))

    # Kaynak türleri; türün istediği sertifika bilinen sertifikalara eklenir
    for ad, t in veri.get("kaynak_turleri", {}).items():
        durum.kaynak_turleri[ad] = KaynakTuru(
            ad=ad, hazirlik_dk=int(t["hazirlik_dk"]), temel_ucret=t["temel_ucret"],
            enerji_yogun=bool(t["enerji_yogun"]), sertifika=t.get("sertifika"))
        if t.get("sertifika"):
            durum.sertifikalar.add(t["sertifika"])

    # Roller ve sınırları
    for ad, r in veri.get("roller", {}).items():
        durum.roller[ad] = Rol(ad=ad, haftalik_kota=r["haftalik_kota"],
                               ileri_gun=r["ileri_gun"], azami_sure_dk=r["azami_sure_dk"])

    # Kaynaklar (dosyadaki sırayla)
    for k in veri.get("kaynaklar", []):
        durum.kaynaklar[k["id"]] = Kaynak(id=k["id"], ad=k["ad"], tur=k["tur"],
                                          izinli_roller=list(k["izinli_roller"]))

    # Bakım pencereleri
    for b in veri.get("bakim_pencereleri", []):
        durum.bakim_pencereleri.append(
            BakimPenceresi(kaynak=b["kaynak"], baslangic=coz(b["baslangic"]), bitis=coz(b["bitis"])))

    # Kullanıcılar; sahip oldukları sertifikalar da bilinen sertifikalara eklenir
    for u in veri.get("kullanicilar", []):
        durum.kullanicilar[u["id"]] = Kullanici(
            id=u["id"], ad=u["ad"], rol=u["rol"], sertifikalar=list(u.get("sertifikalar", [])),
            bakiye=u["bakiye"], guvenilirlik=u["guvenilirlik"])
        durum.sertifikalar.update(u.get("sertifikalar", []))

    return durum
