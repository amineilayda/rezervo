from PySide6.QtGui import QColor, QPalette


ZEMIN = "#F4F6F9"
YUZEY = "#FFFFFF"
KENAR = "#E2E6EC"
KENAR_KOYU = "#CBD2DB"
METIN = "#1F2937"
SOLUK = "#6B7280"
VURGU = "#2563EB"
VURGU_KOYU = "#1D4ED8"
BASARI = "#059669"
HATA = "#DC2626"


DURUM_RENKLERI = {
    "ONAYLI": ("#DBEAFE", "#2563EB", "#1E3A8A"),
    "KULLANIMDA": ("#D1FAE5", "#059669", "#065F46"),
    "TAMAMLANDI": ("#E5E7EB", "#6B7280", "#374151"),
    "IPTAL": ("#FFFFFF", "#9CA3AF", "#6B7280"),
    "GELMEDI": ("#FEE2E2", "#DC2626", "#991B1B"),
}
DURUM_ETIKETLERI = {
    "ONAYLI": "Onaylı",
    "KULLANIMDA": "Kullanımda",
    "TAMAMLANDI": "Tamamlandı",
    "IPTAL": "İptal",
    "GELMEDI": "Gelmedi",
}
BAKIM_DOLGU = "#FEF3C7"
BAKIM_CIZGI = "#F59E0B"
HAZIRLIK_DOLGU = "#EEF1F5"
HAZIRLIK_CIZGI = "#B6C0CC"
SECIM_DOLGU = "#2563EB"
SIMULE_SAAT_RENGI = "#DC2626"


def renk(kod: str) -> QColor:
    return QColor(kod)


def acik_palet() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(ZEMIN))
    p.setColor(QPalette.WindowText, QColor(METIN))
    p.setColor(QPalette.Base, QColor(YUZEY))
    p.setColor(QPalette.AlternateBase, QColor("#F9FAFB"))
    p.setColor(QPalette.Text, QColor(METIN))
    p.setColor(QPalette.Button, QColor(YUZEY))
    p.setColor(QPalette.ButtonText, QColor(METIN))
    p.setColor(QPalette.Highlight, QColor(VURGU))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.ToolTipBase, QColor(METIN))
    p.setColor(QPalette.ToolTipText, QColor("#FFFFFF"))
    p.setColor(QPalette.PlaceholderText, QColor("#9CA3AF"))
    return p


STIL = f"""
QWidget {{ font-family: "Segoe UI", "Inter", sans-serif; font-size: 10pt; color: {METIN}; }}
QMainWindow, #anaZemin {{ background: {ZEMIN}; }}

#kart {{ background: {YUZEY}; border: 1px solid {KENAR}; border-radius: 8px; }}
#ustCubuk {{ background: {YUZEY}; border-bottom: 1px solid {KENAR}; }}
#baslik {{ font-size: 11pt; font-weight: 600; }}
#altBaslik {{ color: {SOLUK}; font-size: 9pt; font-weight: 600; text-transform: uppercase; }}
#soluk {{ color: {SOLUK}; }}
#simuleSaat {{ font-size: 15pt; font-weight: 600; color: {METIN}; }}
#simuleGun {{ color: {SOLUK}; font-size: 9pt; }}
#buyukDeger {{ font-size: 14pt; font-weight: 600; }}

QPushButton {{
    background: {YUZEY}; border: 1px solid {KENAR_KOYU}; border-radius: 6px;
    padding: 5px 12px; min-height: 18px;
}}
QPushButton:hover {{ background: #F3F4F6; border-color: #9CA3AF; }}
QPushButton:pressed {{ background: #E5E7EB; }}
QPushButton:disabled {{ color: #9CA3AF; background: #F9FAFB; }}
QPushButton#birincil {{ background: {VURGU}; border-color: {VURGU}; color: white; font-weight: 600; }}
QPushButton#birincil:hover {{ background: {VURGU_KOYU}; }}
QPushButton#kucuk {{ padding: 2px 8px; font-size: 9pt; min-height: 14px; }}
QPushButton#tehlike {{ color: {HATA}; }}
QPushButton#tehlike:hover {{ background: #FEF2F2; border-color: {HATA}; }}
QPushButton#segment {{ border-radius: 0; padding: 5px 16px; }}
QPushButton#segment:checked {{ background: #EFF6FF; border-color: {VURGU}; color: {VURGU}; }}
QToolButton {{ border: none; border-radius: 6px; padding: 4px 8px; }}
QToolButton:hover {{ background: #F3F4F6; }}

QLineEdit, QComboBox, QSpinBox, QDateEdit, QDateTimeEdit {{
    background: {YUZEY}; border: 1px solid {KENAR_KOYU}; border-radius: 6px;
    padding: 4px 8px; min-height: 18px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QDateTimeEdit:focus {{
    border-color: {VURGU};
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{ border: 1px solid {KENAR_KOYU}; selection-background-color: #EFF6FF;
    selection-color: {METIN}; }}

QTabWidget::pane {{ border: none; border-top: 1px solid {KENAR}; }}
QTabBar::tab {{ background: transparent; padding: 7px 14px; border: none; color: {SOLUK}; font-weight: 600; }}
QTabBar::tab:selected {{ color: {VURGU}; border-bottom: 2px solid {VURGU}; }}
QTabBar::tab:hover {{ color: {METIN}; }}

QTableWidget, QListWidget, QPlainTextEdit {{
    background: {YUZEY}; border: 1px solid {KENAR}; border-radius: 6px;
    gridline-color: #F0F2F5; selection-background-color: #EFF6FF; selection-color: {METIN};
}}
QHeaderView::section {{ background: #F9FAFB; border: none; border-bottom: 1px solid {KENAR};
    padding: 4px 6px; color: {SOLUK}; font-weight: 600; font-size: 9pt; }}
QListWidget::item {{ padding: 3px 6px; }}
QPlainTextEdit {{ font-family: "Cascadia Mono", "Consolas", monospace; font-size: 9pt; }}

QScrollArea {{ border: none; background: transparent; }}
QSplitter::handle {{ background: {ZEMIN}; }}
QProgressBar {{ border: none; background: #EEF0F3; border-radius: 3px; max-height: 6px; }}
QProgressBar::chunk {{ border-radius: 3px; background: {VURGU}; }}
QCheckBox {{ spacing: 6px; }}
QToolTip {{ background: {METIN}; color: white; border: none; padding: 6px; border-radius: 4px; }}

#bant {{ border-radius: 6px; padding: 8px 10px; }}
#bant[tur="tamam"] {{ background: #ECFDF5; border: 1px solid #A7F3D0; }}
#bant[tur="red"] {{ background: #FEF2F2; border: 1px solid #FECACA; }}
#bant[tur="bilgi"] {{ background: #EFF6FF; border: 1px solid #BFDBFE; }}
#acilirKart {{ background: {YUZEY}; border: 1px solid {KENAR_KOYU}; border-radius: 8px; }}
"""
