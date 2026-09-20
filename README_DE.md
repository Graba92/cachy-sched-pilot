# ⚡ Cachy-Sched-Pilot (Deutsche Dokumentation)

<div align="center">

![Cachy-Sched-Pilot Showcase](hero_showcase.jpg)

**Autonomer sched-ext (SCX) Benchmark, Tuner & Workload Governor für CachyOS / Arch Linux**

[![Arch Linux](https://img.shields.io/badge/Arch_Linux-AUR-1793D1?logo=archlinux&logoColor=white)](https://aur.archlinux.org/)
[![CachyOS](https://img.shields.io/badge/CachyOS-Optimiert-00A86B?logo=linux&logoColor=white)](https://cachyos.org)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Textual](https://img.shields.io/badge/UI-Textual_TUI-792EE5)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Englische Dokumentation: [README.md](README.md)*

</div>

---

## 🚀 Übersicht

**Cachy-Sched-Pilot** ist ein produktionsreifes System- und Telemetrie-Werkzeug zur Steuerung, Diagnose und Optimierung von Linux-CPU-Schedulern. Es wurde speziell für **CachyOS** und **Arch Linux** entwickelt und unterstützt sowohl Kernel-native Scheduler (**BORE**, **EEVDF**, **cacULE**) als auch dynamische eBPF User-Space-Scheduler via **sched-ext** (`scx_*`).

Das Tool ermöglicht unprivilegiertes Umschalten von Schedulern und CPU-Governors in Echtzeit, bietet automatische Profile für Gaming, Kompilierung und Audio-Workloads und schützt das System durch einen **Crash-Watchdog mit automatischem Fallback**.

---

### ✨ Hauptmerkmale

1. **Unprivilegierte Textual-TUI**:
   - Modernes Terminal-Dashboard, das strikt als normaler Benutzer ausgeführt wird.
   - Echtzeit-Balkenanzeige der CPU-Auslastung pro Kern, Taktraten, Governors und EPP.
   - Dynamische Prüfung der Systemfähigkeiten (nicht installierte Schedulers werden sauber deaktiviert statt abzustürzen).
   - Live-Sprachwechsel per Tastendruck (<kbd>L</kbd>) zwischen Deutsch und Englisch.

2. **Sichere Privilegientrennung via Polkit**:
   - Umschaltung von Schedulern, CPU-Governors und sysfs-Werten läuft über den Backend-Helper `cachy-sched-helper`.
   - Autorisierung über PolicyKit-Regel `org.cachyos.schedpilot.policy` (kein Root-Terminal erforderlich).

3. **Sicherheits-Fallback & Absturzschutz**:
   - Hintergrundüberwachung des Sysfs-Zustands `/sys/kernel/sched_ext/state`.
   - Sollte ein experimenteller SCX-Scheduler abstürzen, schaltet Cachy-Sched-Pilot sofort automatisch auf den nativen Kernel-Scheduler (BORE / EEVDF) zurück – ohne Desktop-Einfrieren oder System-Hangs!

4. **Präzisions-Micro-Benchmark**:
   - Nanosekunden-genaue Messung der Aufwachlatenz (Wakeup Jitter) zur Erkennung von 1% Low Drops in Spielen und Xruns in DAWs.
   - Messung des Kontextwechsel-Durchsatzes und Vergabe von Noten (S, A+, A, B, C).

5. **Headless-Automation & JSON-Telemetrie**:
   - Vollständig scriptbar über `--status --json`, `--set-profile <profil>` und `--set-sched <name>`.
   - Ideal für Tastenkürzel in **KDE Plasma**, **Hyprland**, **Waybar** oder **udev**-Regeln.

---

## 📊 Unterstützte Scheduler

| Scheduler | Typ | Optimal für | Typische Anwendungen |
| :--- | :--- | :--- | :--- |
| **`scx_lavd`** | sched-ext (eBPF) | Gaming, Audio, Emulation | CS2, Cyberpunk, RPCS3, REAPER, DAWs |
| **`scx_rusty`** | sched-ext (Rust/eBPF) | Multithread-Durchsatz | GCC, Clang, Cargo, Blender, Encoding |
| **`scx_bpfland`** | sched-ext (vruntime) | Ausgewogener Desktop | Alltägliches Browsing, Medien, Programmieren |
| **`scx_flash`** | sched-ext (eBPF) | Reaktionsschnelle UI | CPUs mit wenigen Kernen, Web-Engines |
| **`BORE`** | Nativer CachyOS Kernel | Direkte Reaktivität | Niedrige Desktop-Latenz ohne eBPF-Overhead |
| **`EEVDF`** | Nativer Linux-Kernel (6.6+) | Standard | Regulärer Linux-CFS-Nachfolger |

---

## 📦 Installation

### Über AUR / CachyOS Repositories
```bash
# Mit yay
yay -S cachy-sched-pilot

# Mit paru
paru -S cachy-sched-pilot
```

### Manuelle Installation & Entwicklung
```bash
git clone https://github.com/Graba92/cachy-sched-pilot.git
cd cachy-sched-pilot

# Abhängigkeiten installieren (CachyOS / Arch Linux)
sudo pacman -S python python-psutil python-rich python-textual polkit scx-scheds

# Polkit-Policy einrichten (erlaubt unprivilegiertes Umschalten)
sudo cp packaging/org.cachyos.schedpilot.policy /usr/share/polkit-1/actions/

# Interaktives Dashboard starten
python3 app.py tui
```

---

## ⌨️ TUI Tastenkürzel

| Taste | Aktion |
| :---: | :--- |
| <kbd>q</kbd> | Programm beenden |
| <kbd>r</kbd> | Telemetrie sofort aktualisieren |
| <kbd>l</kbd> | Sprache umschalten (**Deutsch** ⇄ **Englisch**) |
| <kbd>b</kbd> | Micro-Benchmark für aktiven Scheduler starten |
| <kbd>d</kbd> | Diagnose / Doctor erneut ausführen |

---

## 💻 CLI & Headless Nutzung

```bash
# 1. Systemstatus anzeigen (Menschlich lesbar)
cachy-sched-pilot --status

# 2. Telemetrie als JSON für Hyprland, Waybar oder Scripte
cachy-sched-pilot --status --json

# 3. Tuning-Profil aktivieren
cachy-sched-pilot --set-profile gaming
cachy-sched-pilot --set-profile compile
cachy-sched-pilot --set-profile powersave

# 4. Direkt auf einen bestimmten Scheduler schalten
cachy-sched-pilot --set-sched scx_lavd
cachy-sched-pilot --set-sched default

# 5. Systemdiagnose durchführen
cachy-sched-pilot --doctor

# 6. Autonomen Hintergrund-Governor starten
cachy-sched-pilot governor --interval 2.5
```

---

## ⚙️ Konfiguration (`config.toml`)

Konfigurationsdateien werden nach XDG-Standards an folgenden Orten gesucht:
1. `$XDG_CONFIG_HOME/sched-pilot/config.toml` (bzw. `~/.config/sched-pilot/config.toml`)
2. `/etc/sched-pilot/config.toml`

Eine detaillierte Vorlage befindet sich in [`config.example.toml`](config.example.toml).

---

## 🛡️ Sicherheitsarchitektur & Polkit

- **TUI & CLI**: Laufen strikt ohne Root-Rechte als Standardbenutzer.
- **`cachy-sched-helper`**: Ein isolierter Backend-Helper (`/usr/lib/cachy-sched-pilot/cachy-sched-helper`) führt ausschließlich validierte Aktionen aus einer Allowlist aus.
- **PolicyKit**: Ermöglicht berechtigten Benutzern über `org.cachyos.schedpilot.policy` die Ausführung ohne ständige Passworteingabe.

---

## 📄 Lizenz

Veröffentlicht unter der **MIT-Lizenz**. Siehe [LICENSE](LICENSE).
Entwickelt von Matze Graba & der CachyOS Open Source Community.
