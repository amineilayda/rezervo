# Rezervo

A rule-driven reservation engine for shared campus resources (meeting rooms, labs, 3D printers, GPU servers), with a PySide6 desktop app on top.

The engine (`rezervasyon/`) is pure Python with no dependencies and no UI code. It reads an initial state, processes commands one by one and writes one JSON result per command. The desktop app (`arayuz/`) drives the same engine through the same command handler, so the CLI and the GUI always produce identical results.

> Code identifiers, commands and UI text are in Turkish.

## Features

- **Ordered validation chain:** 12 rules (time step, working hours, duration, booking horizon, role, certificate, maintenance, overlap, preparation gap, back-to-back limit) plus balance; the first failing rule's code is returned.
- **Dynamic pricing:** 15-minute slots, occupancy-based band multiplier, peak-hour multiplier for energy-heavy resources. Exact arithmetic with `Fraction`, rounded once at the end.
- **Simulated clock:** advancing time processes every event in order (weekly reset, auto-complete, no-show, waitlist assignment), so even large jumps miss nothing.
- **Reliability score** affecting booking horizon, bundle eligibility and waitlist priority.
- **Bundles** of 2–4 items, all-or-nothing.
- **Waitlist** that auto-books the next eligible user when a slot frees up.
- **Desktop app:** resource timeline with drag-to-select, price preview, one-click actions, event log showing each command as JSON.

## Quick start

Requires Python 3.11+.

```bash
# CLI (no dependencies)
./calistir.sh ornek/baslangic.json ornek/komutlar.jsonl > sonuclar.jsonl      # Windows: .\calistir.bat ...

# Desktop app
pip install -r requirements.txt
./uygulama.sh ornek/baslangic.json                                          # Windows: .\uygulama.bat ...
```

Input: a JSON initial state (`saat`, `kaynak_turleri`, `roller`, `kaynaklar`, `bakim_pencereleri`, `kullanicilar`) and a JSON Lines command file. All rule parameters come from the initial state, nothing is hard-coded.

```json
{"komut":"rezervasyon","kullanici":"u1","kaynak":"YAZ-1","baslangic":"2027-03-08T11:00","bitis":"2027-03-08T13:00"}
→ {"no":5,"komut":"rezervasyon","durum":"TAMAM","rezervasyon_id":"r1","ucret":36,"bakiye":84}
```

Commands: `saat`, `rezervasyon`, `paket`, `fiyat`, `iptal`, `giris`, `cikis`, `bekleme`, `sorgu`, `kullanici_ekle`, `kaynak_ekle`.

## Tests

```bash
python testler/karsilastir.py ornek/beklenen.jsonl sonuclar.jsonl     # field-by-field diff

export PYTHONPATH=.                                                     # PowerShell: $env:PYTHONPATH="."
python -m unittest testler.test_ornek_senaryo                           # sample scenario
python -m testler.arayuz_senaryosu                                      # same scenario through the GUI
```

`testler/senaryolar/` holds an extra edge-case scenario with expected output.

## Structure

```
rezervasyon/   engine: motor.py (API), kurallar/ (validation, pricing, refunds), saat.py, bekleme.py
arayuz/        PySide6 app: istemci.py (single bridge to the engine), bilesenler/ (UI widgets)
ornek/         sample initial state, commands and expected results
testler/       comparator, unit test, GUI scenario, edge-case scenario
```

See [MIMARI.md](MIMARI.md) for the architecture (Turkish).
