# 📢 Release & Community Announcement: Cachy-Sched-Pilot v1.2.0

## 🚀 Title:
**Cachy-Sched-Pilot v1.2.0: Autonomous sched-ext (SCX) Scheduler Management, Telemetry & Precision Benchmark for CachyOS & Arch Linux**

---

### 🌐 English Posting (Reddit r/cachyos, r/archlinux, GitHub Discussions, Discord):

> **Hey everyone!** 👋
>
> We just released **Cachy-Sched-Pilot v1.2.0** — an unprivileged, production-ready scheduler manager, live telemetry dashboard, and precision micro-benchmarking tool tailored specifically for CachyOS and Arch Linux kernels featuring **sched-ext** (`SCX`) and optimized native schedulers (**BORE**, **EEVDF**, **cacULE**).
>
> ### 🌟 What's New in v1.2.0?
> - **Strict Privilege Separation with Polkit**: The interactive Textual TUI runs completely unprivileged as standard user! All scheduler switches, governor changes, and sysfs writes route safely through a sandboxed helper via `org.cachyos.schedpilot.policy`.
> - **Automated Safety Crash Fallback**: If an experimental eBPF scheduler (`scx_lavd`, `scx_rusty`, etc.) encounters an unexpected panic, Cachy-Sched-Pilot immediately resets scheduling to native kernel defaults (BORE/EEVDF)—zero system hangs or desktop lockups!
> - **Full Bilingual Localization (de_DE / en_US)**: Dynamic language toggling on-the-fly via CLI flag `--lang` or pressing `L` in the TUI.
> - **Live CPU Telemetry & Per-Core Load Bars**: Real-time per-core utilization, scaling governors, EPP (Energy Performance Preference), and underlying kernel scheduler detection.
> - **Headless CLI & JSON Automation**: Instant telemetry export via `cachy-sched-pilot --status --json` for Hyprland, Sway, KDE Plasma shortcuts, Waybar widgets, or udev triggers.
> - **AUR & CachyOS PKGBUILD Ready**: Clean packaging template for Arch User Repository (`yay -S cachy-sched-pilot`).
>
> 🔗 **GitHub Repository**: https://github.com/Graba92/cachy-sched-pilot
> 💬 Feedback and contributions are very welcome!

---

### 🇩🇪 Deutsches Posting (CachyOS / Arch Linux DACH Community & Foren):

> **Moin zusammen!** 🐧
>
> Für alle CachyOS- und Arch-Linux-Enthusiasten gibt es ein großes Update: **Cachy-Sched-Pilot v1.2.0** ist da!
>
> Das Tool bietet ein interaktives Terminal-Dashboard (Textual TUI), Live-Telemetrie und eine Nanosekunden-genaue Micro-Benchmark-Suite für Linux CPU-Scheduler (sowohl Kernel-native Scheduler wie **BORE**, **EEVDF** als auch eBPF User-Space-Scheduler via **sched-ext** wie `scx_lavd`, `scx_rusty` und `scx_bpfland`).
>
> ### 🛠️ Highlights von v1.2.0:
> - **Sichere Privilegientrennung via Polkit**: Das Dashboard läuft vollständig ohne Root-Rechte als Standardbenutzer. Umschaltungen laufen über den dedizierten Backend-Helper `cachy-sched-helper` und Polkit.
> - **Crash-Watchdog & Notfall-Fallback**: Stürzt ein experimenteller SCX-Scheduler ab, greift automatisch das Fail-Safe-System und stellt das System ohne Freezes auf Kernel-Standard zurück.
> - **Komplett zweisprachig (Deutsch & Englisch)**: Umschalten per Tastendruck (`L`) im Dashboard oder per Flag `--lang de`.
> - **Echtzeit-Telemetrie**: Balkenanzeige der Kerne, Governor, EPP und Workload-Erkennung (Gaming, Emulation, Audio DAW, Compile).
> - **Headless-Modus mit JSON-Export**: Ideal zur Einbindung in Hyprland, Waybar, KDE-Shortcuts oder udev-Regeln (`cachy-sched-pilot --status --json`).
> - **AUR-ready PKGBUILD**: Direkt paketierbar (`yay -S cachy-sched-pilot`).
>
> 🔗 **Repository**: https://github.com/Graba92/cachy-sched-pilot
