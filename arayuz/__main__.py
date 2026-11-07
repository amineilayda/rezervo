import sys

from PySide6.QtCore import QLocale, QTimer
from PySide6.QtWidgets import QApplication

from . import tema
from .ana_pencere import AnaPencere
from .istemci import ModulIstemcisi


def main() -> int:
    QLocale.setDefault(QLocale(QLocale.Turkish, QLocale.Turkey))
    app = QApplication(sys.argv)
    app.setApplicationName("Kampüs Kaynak Rezervasyon")
    app.setStyle("Fusion")
    app.setPalette(tema.acik_palet())
    app.setStyleSheet(tema.STIL)

    istemci = ModulIstemcisi()
    pencere = AnaPencere(istemci)
    pencere.show()
    if len(sys.argv) > 1:
        pencere.dosya_yukle(sys.argv[1])
    else:
        QTimer.singleShot(0, pencere.dosya_sec)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
