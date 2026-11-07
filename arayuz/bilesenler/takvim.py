from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from .. import metinler
from .. import tema

BAS_DK = 8 * 60
BIT_DK = 22 * 60
TOPLAM_DK = BIT_DK - BAS_DK
ADIM_DK = 15

ETIKET_W = 172
UST_H = 30
SERIT_H = 34

SERIT_ARA = 4
SATIR_PAD = 7
SAG_BOSLUK = 14

AKTIF = {"ONAYLI", "KULLANIMDA", "TAMAMLANDI"}


def dakika(zaman: str, gun: str) -> int:

    
    tarih = zaman[:10]
    if tarih < gun:
        return 0
    if tarih > gun:
        return 24 * 60
    return int(zaman[11:13]) * 60 + int(zaman[14:16])


def seritlere_yerlestir(rezler: list[dict], gun: str) -> list[list[dict]]:
    
    


    sirali = sorted(rezler, key=lambda r: (r["durum"] not in AKTIF,
                                           dakika(r["baslangic"], gun), int(r["id"][1:])))
    seritler: list[list[tuple[int, int]]] = []
    sonuc: list[list[dict]] = []
    for r in sirali:
        b, e = dakika(r["baslangic"], gun), dakika(r["bitis"], gun)
        for i, serit in enumerate(seritler):
            if all(e <= sb or b >= se for sb, se in serit):
                serit.append((b, e))
                sonuc[i].append(r)
                break
        else:
            seritler.append([(b, e)])
            sonuc.append([r])
    return sonuc or [[]]


class Takvim(QWidget):
    rezervasyon_tiklandi = Signal(str, QPoint)          # rezervasyon id, ekran k
    
    aralik_secildi = Signal(str, str, str, str)        
    
    kaynak_tiklandi = Signal(str, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(ETIKET_W + 56 * 9 + SAG_BOSLUK)
        self.gun = ""
        self.simdi = ""
        self.kaynaklar: list[dict] = []
        self.veri: dict = {}
        self.kullanici_adlari: dict[str, str] = {}
        self.satirlar: list[dict] = []
        self.kutular: list[tuple[QRectF, dict]] = []
        self.secim: tuple[str, int, int] | None = None
        self.surukleme: tuple[str, int] | None = None
        self.vurgulu: str | None = None
        self.aktif_kullanici: str | None = None

    # ------------
    
    def yukle(self, gun: str, simdi: str, kaynaklar: list[dict], veri: dict,
              kullanici_adlari: dict[str, str]) -> None:
        self.gun, self.simdi = gun, simdi
        self.kaynaklar, self.veri = kaynaklar, veri
        self.kullanici_adlari = kullanici_adlari
        self.secim = None
        self._yerlesim()
        self.update()

    def _yerlesim(self) -> None:
        self.satirlar = []
        y = UST_H
        for k in self.kaynaklar:
            gunluk = self.veri.get(k["id"], {"rezervasyonlar": [], "bakimlar": [], "hazirliklar": []})
            seritler = seritlere_yerlestir(gunluk["rezervasyonlar"], self.gun)
            h = SATIR_PAD * 2 + len(seritler) * SERIT_H + (len(seritler) - 1) * SERIT_ARA
            self.satirlar.append({"kaynak": k, "y": y, "h": h, "seritler": seritler,
                                  "bakimlar": gunluk["bakimlar"], "hazirliklar": gunluk["hazirliklar"]})
            y += h
        self.setFixedHeight(max(y + 1, UST_H + 60))

    # --- koordinatl
    
    def _cizim_w(self) -> float:
        return self.width() - ETIKET_W - SAG_BOSLUK

    def _x(self, dk: int) -> float:
        dk = max(BAS_DK, min(BIT_DK, dk))
        return ETIKET_W + (dk - BAS_DK) / TOPLAM_DK * self._cizim_w()

    def _dk(self, x: float) -> float:
        return BAS_DK + (x - ETIKET_W) / self._cizim_w() * TOPLAM_DK

    def _satir_bul(self, y: float) -> dict | None:
        for s in self.satirlar:
            if s["y"] <= y < s["y"] + s["h"]:
                return s
        return None

    # -
    
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(tema.YUZEY))
        self.kutular = []
        if not self.kaynaklar:
            p.setPen(QColor(tema.SOLUK))
            p.drawText(self.rect(), Qt.AlignCenter, "Gösterilecek kaynak yok")
            return

        self._izgara(p)
        for s in self.satirlar:
            self._satir(p, s)
        self._secim_ciz(p)
        self._simdi_ciz(p)
        p.end()

    def _izgara(self, p: QPainter) -> None:
        alt = self.satirlar[-1]["y"] + self.satirlar[-1]["h"]
        kucuk = QFont(self.font())
        kucuk.setPointSizeF(8.5)
        p.setFont(kucuk)
        for i, s in enumerate(self.satirlar):
            if i % 2:
                p.fillRect(QRectF(0, s["y"], self.width(), s["h"]), QColor("#FAFBFC"))
        simdi_x = None
        if self.simdi and self.simdi[:10] == self.gun and BAS_DK <= dakika(self.simdi, self.gun) <= BIT_DK:
            simdi_x = self._x(dakika(self.simdi, self.gun))
        for dk in range(BAS_DK, BIT_DK + 1, ADIM_DK):
            x = self._x(dk)
            if dk % 60 == 0:
                p.setPen(QPen(QColor("#DDE2E8"), 1))
                p.drawLine(QPointF(x, UST_H - 6), QPointF(x, alt))
                if simdi_x is None or abs(x - simdi_x) > 44:  # simüle saat etiketiyle çakışmasın
                    p.setPen(QColor(tema.SOLUK))
                    p.drawText(QRectF(x - 24, 4, 48, UST_H - 10), Qt.AlignCenter, f"{dk // 60:02d}:00")
            elif dk % 30 == 0:
                p.setPen(QPen(QColor("#ECEFF3"), 1))
                p.drawLine(QPointF(x, UST_H), QPointF(x, alt))
            else:
                p.setPen(QPen(QColor("#F3F5F8"), 1, Qt.DotLine))
                p.drawLine(QPointF(x, UST_H), QPointF(x, alt))
        p.setPen(QPen(QColor(tema.KENAR), 1))
        p.drawLine(QPointF(0, UST_H - 0.5), QPointF(self.width(), UST_H - 0.5))
        p.drawLine(QPointF(ETIKET_W - 0.5, 0), QPointF(ETIKET_W - 0.5, alt))



    def _satir(self, p: QPainter, s: dict) -> None:
        k = s["kaynak"]
        y, h = s["y"], s["h"]
        p.setPen(QPen(QColor("#EEF0F3"), 1))
        p.drawLine(QPointF(0, y + h - 0.5), QPointF(self.width(), y + h - 0.5))

        # Etiket: id, ad, tür
        kalin = QFont(self.font())
        kalin.setBold(True)
        p.setFont(kalin)
        p.setPen(QColor(tema.METIN))
        p.drawText(QRectF(12, y + SATIR_PAD, ETIKET_W - 20, 18), Qt.AlignLeft | Qt.AlignVCenter, k["id"])
        kucuk = QFont(self.font())
        kucuk.setPointSizeF(8.5)
        p.setFont(kucuk)
        p.setPen(QColor(tema.SOLUK))
        fm = QFontMetrics(kucuk)
        p.drawText(QRectF(12, y + SATIR_PAD + 18, ETIKET_W - 20, 16), Qt.AlignLeft | Qt.AlignVCenter,
                   fm.elidedText(f"{k['ad']} · {k['tur']}", Qt.ElideRight, ETIKET_W - 22))

        ust = y + SATIR_PAD
        tum_h = h - 2 * SATIR_PAD


        
        for b in s["bakimlar"]:
            r = self._aralik_rect(b["baslangic"], b["bitis"], ust, tum_h)
            if r.width() <= 0:
                continue
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(tema.BAKIM_DOLGU))
            p.drawRoundedRect(r, 4, 4)
            p.setBrush(QBrush(QColor(tema.BAKIM_CIZGI), Qt.BDiagPattern))
            p.drawRoundedRect(r, 4, 4)
            p.setPen(QColor("#92400E"))
            p.setFont(kucuk)
            if r.width() > 40:
                p.drawText(r.adjusted(6, 0, -4, 0), Qt.AlignLeft | Qt.AlignVCenter, "Bakım")
            self.kutular.append((r, {"_bakim": b}))

        # Hazırlık blokları: ilgili rezervasyonun şeridinde
        serit_no = {r["id"]: i for i, serit in enumerate(s["seritler"]) for r in serit}
        for hz in s["hazirliklar"]:
            i = serit_no.get(hz["rezervasyon"], 0)
            r = self._aralik_rect(hz["baslangic"], hz["bitis"], ust + i * (SERIT_H + SERIT_ARA), SERIT_H)
            if r.width() <= 0:
                continue
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(tema.HAZIRLIK_DOLGU))
            p.drawRoundedRect(r.adjusted(0, 3, 0, -3), 3, 3)
            p.setBrush(QBrush(QColor(tema.HAZIRLIK_CIZGI), Qt.FDiagPattern))
            p.drawRoundedRect(r.adjusted(0, 3, 0, -3), 3, 3)
            self.kutular.append((r, {"_hazirlik": hz}))

        # Rezervasyon
        
        for i, serit in enumerate(s["seritler"]):
            sy = ust + i * (SERIT_H + SERIT_ARA)
            for rez in serit:
                r = self._aralik_rect(rez["baslangic"], rez["bitis"], sy, SERIT_H)
                if r.width() <= 0:
                    continue
                self._kutu(p, r, rez)
                self.kutular.append((r, rez))

    def _aralik_rect(self, bas: str, bit: str, y: float, h: float) -> QRectF:
        x1, x2 = self._x(dakika(bas, self.gun)), self._x(dakika(bit, self.gun))
        return QRectF(x1, y, max(0.0, x2 - x1), h)

    def _kutu(self, p: QPainter, r: QRectF, rez: dict) -> None:
        dolgu, kenar, yazi = tema.DURUM_RENKLERI.get(rez["durum"], tema.DURUM_RENKLERI["ONAYLI"])
        ic = r.adjusted(1, 1, -1, -1)
        secili = rez["id"] == self.vurgulu
        kalem = QPen(QColor(kenar), 2 if secili else 1)
        if rez["durum"] == "IPTAL":
            kalem.setStyle(Qt.DashLine)
        p.setPen(kalem)
        p.setBrush(QColor(dolgu))
        p.drawRoundedRect(ic, 5, 5)

        
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(kenar))
        p.drawRoundedRect(QRectF(ic.left(), ic.top(), 3.5, ic.height()), 2, 2)
        if secili:
            p.setPen(QPen(QColor(tema.METIN), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(-1, -1, 1, 1), 6, 6)

        metin_r = ic.adjusted(8, 2, -5, -2)
        if metin_r.width() < 14:
            return
        f1 = QFont(self.font())
        f1.setPointSizeF(8.5)
        f1.setBold(True)
        f1.setStrikeOut(rez["durum"] == "IPTAL")
        f2 = QFont(self.font())
        f2.setPointSizeF(8)
        fm1, fm2 = QFontMetrics(f1), QFontMetrics(f2)
        ust = f"{rez['id']} · {rez['kullanici']}"
        if rez.get("paket"):
            ust += f" · {rez['paket']}"
        alt = f"{metinler.saat_kismi(rez['baslangic'])}–{metinler.saat_kismi(rez['bitis'])}"
        if rez["durum"] in ("IPTAL", "GELMEDI", "KULLANIMDA", "TAMAMLANDI"):
            alt += f" · {tema.DURUM_ETIKETLERI[rez['durum']]}"
        p.setPen(QColor(yazi))
        p.setFont(f1)
        p.drawText(QRectF(metin_r.left(), metin_r.top(), metin_r.width(), 15),
                   Qt.AlignLeft | Qt.AlignVCenter, fm1.elidedText(ust, Qt.ElideRight, int(metin_r.width())))
        p.setFont(f2)
        p.drawText(QRectF(metin_r.left(), metin_r.top() + 14, metin_r.width(), 14),
                   Qt.AlignLeft | Qt.AlignVCenter, fm2.elidedText(alt, Qt.ElideRight, int(metin_r.width())))

    def _secim_ciz(self, p: QPainter) -> None:
        if not self.secim:
            return
        kaynak_id, d1, d2 = self.secim
        s = next((s for s in self.satirlar if s["kaynak"]["id"] == kaynak_id), None)
        if not s:
            return
        x1, x2 = self._x(min(d1, d2)), self._x(max(d1, d2))
        r = QRectF(x1, s["y"] + 2, x2 - x1, s["h"] - 4)
        renk = QColor(tema.SECIM_DOLGU)
        renk.setAlpha(36)
        p.setBrush(renk)
        p.setPen(QPen(QColor(tema.SECIM_DOLGU), 1.5, Qt.DashLine))
        p.drawRoundedRect(r, 5, 5)
        p.setPen(QColor(tema.VURGU_KOYU))
        f = QFont(self.font())
        f.setPointSizeF(8)
        f.setBold(True)
        p.setFont(f)
        a, b = min(d1, d2), max(d1, d2)
        p.drawText(r.adjusted(4, 0, -4, 0), Qt.AlignCenter,
                   f"{a // 60:02d}:{a % 60:02d}–{b // 60:02d}:{b % 60:02d}")

    def _simdi_ciz(self, p: QPainter) -> None:
        if not self.simdi or self.simdi[:10] != self.gun:
            return
        dk = dakika(self.simdi, self.gun)
        if not BAS_DK <= dk <= BIT_DK:
            return
        x = self._x(dk)
        alt = self.satirlar[-1]["y"] + self.satirlar[-1]["h"]
        renk = QColor(tema.SIMULE_SAAT_RENGI)
        p.setPen(QPen(renk, 2))
        p.drawLine(QPointF(x, UST_H - 2), QPointF(x, alt))
        etiket = QRectF(x - 22, 6, 44, 17)
        p.setPen(Qt.NoPen)
        p.setBrush(renk)
        p.drawRoundedRect(etiket, 8, 8)
        p.setPen(QColor("white"))
        f = QFont(self.font())
        f.setPointSizeF(8)
        f.setBold(True)
        p.setFont(f)
        p.drawText(etiket, Qt.AlignCenter, metinler.saat_kismi(self.simdi))


    
    def _kutu_bul(self, nokta: QPointF) -> dict | None:

       
        for r, veri in reversed(self.kutular):
            if r.contains(nokta):
                return veri
        return None

    def _yakala(self, x: float, yukari: bool) -> int:
        dk = self._dk(x)
        adim = (int(dk) // ADIM_DK + (1 if yukari and dk % ADIM_DK else 0)) * ADIM_DK
        return max(BAS_DK, min(BIT_DK, adim))

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton or not self.satirlar:
            return
        nokta = e.position()
        s = self._satir_bul(nokta.y())
        if s is None:
            return
        if nokta.x() < ETIKET_W:
            self.kaynak_tiklandi.emit(s["kaynak"]["id"], e.globalPosition().toPoint())
            return
        veri = self._kutu_bul(nokta)
        if veri and "id" in veri:
            self.vurgulu = veri["id"]
            self.update()
            self.rezervasyon_tiklandi.emit(veri["id"], e.globalPosition().toPoint())
            return
        d = self._yakala(nokta.x(), False)
        self.surukleme = (s["kaynak"]["id"], d)
        self.secim = (s["kaynak"]["id"], d, d + ADIM_DK)
        self.update()

    def mouseMoveEvent(self, e):
        nokta = e.position()
        if self.surukleme:
            kaynak_id, d0 = self.surukleme
            d = self._yakala(nokta.x(), nokta.x() > self._x(d0))
            self.secim = (kaynak_id, d0, d if d != d0 else d0 + ADIM_DK)
            self.update()
            return
        veri = self._kutu_bul(nokta) if nokta.x() >= ETIKET_W else None
        if veri:
            self.setCursor(Qt.PointingHandCursor if "id" in veri else Qt.ArrowCursor)
            QToolTip.showText(e.globalPosition().toPoint(), self._ipucu(veri), self)
        else:
            self.setCursor(Qt.PointingHandCursor if nokta.x() < ETIKET_W and self._satir_bul(nokta.y())
                           else Qt.CrossCursor if nokta.x() >= ETIKET_W else Qt.ArrowCursor)
            QToolTip.hideText()

    def mouseReleaseEvent(self, e):
        if not self.surukleme or e.button() != Qt.LeftButton:
            return
        kaynak_id, d0 = self.surukleme
        self.surukleme = None
        _, a, b = self.secim
        a, b = min(a, b), max(a, b)
        if b - a <= ADIM_DK:  # tek tıkl
            
            b = min(BIT_DK, a + 60)
        self.secim = (kaynak_id, a, b)
        self.update()
        self.aralik_secildi.emit(kaynak_id, self.gun, f"{a // 60:02d}:{a % 60:02d}",
                                 f"{b // 60:02d}:{b % 60:02d}")

    def leaveEvent(self, _):
        QToolTip.hideText()

    def _ipucu(self, veri: dict) -> str:
        if "_bakim" in veri:
            b = veri["_bakim"]
            return f"Bakım · {metinler.tarih_saat(b['baslangic'])} – {metinler.tarih_saat(b['bitis'])}"
        if "_hazirlik" in veri:
            h = veri["_hazirlik"]
            return (f"Hazırlık süresi ({h['rezervasyon']} sonrası) · "
                    f"{metinler.saat_kismi(h['baslangic'])}–{metinler.saat_kismi(h['bitis'])}")
        ad = self.kullanici_adlari.get(veri["kullanici"], "")
        satirlar = [
            f"<b>{veri['id']}</b> · {tema.DURUM_ETIKETLERI.get(veri['durum'], veri['durum'])}",
            f"{veri['kullanici']} {('· ' + ad) if ad else ''}",
            f"{metinler.saat_kismi(veri['baslangic'])}–{metinler.saat_kismi(veri['bitis'])} · {veri['ucret']} KP",
        ]
        if veri.get("paket"):
            satirlar.append(f"Paket {veri['paket']}")
        satirlar.append("<i>Ayrıntı ve işlemler için tıklayın</i>")
        return "<br>".join(satirlar)
