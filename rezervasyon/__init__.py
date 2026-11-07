"""Kampüs Kaynak Rezervasyon Sistemi – arayüzden bağımsız rezervasyon modülü."""
# Dışarıdan kullanılacak tek sınıf motor; arayüz ve CLI yalnızca onu import eder
from .motor import RezervasyonMotoru

# "from rezervasyon import *" yazıldığında dışarı açılan adlar
__all__ = ["RezervasyonMotoru"]
