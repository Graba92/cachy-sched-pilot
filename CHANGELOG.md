# Changelog

All notable changes to **Cachy-Sched-Pilot** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-09-20

### Added
- **Privilege Separation & Polkit Architecture**:
  - Unprivileged execution for TUI and CLI as standard user.
  - Dedicated backend helper `cachy-sched-helper` with strict input sanitization.
  - Polkit policy file `org.cachyos.schedpilot.policy` authorizing safe sysfs/governor manipulation without sudo password prompts.
- **Full Internationalization (i18n)**:
  - Complete English (`en_US`) and German (`de_DE`) translations across CLI, TUI, Doctor diagnostics, and benchmarks.
  - Dynamic runtime language switching via CLI flag (`--lang de|en`), configuration (`config.toml`), and interactive TUI keybinding (`L`).
- **Telemetry & Low-Level Hardware Inspection**:
  - Live per-core CPU utilization bars with color-coded load thresholds.
  - CPU Scaling Governor and Energy Performance Preference (EPP) detection.
  - Underlying kernel scheduler identification: EEVDF, BORE, cacULE, and sched-ext state.
- **Safety Fallback & Watchdog**:
  - Automatic detection of crashed or aborted dynamic `scx_*` schedulers.
  - Instant automated fail-safe reversion to default kernel scheduling without machine lockup.
- **XDG Base Directory Compliance**:
  - Full support for `$XDG_CONFIG_HOME/sched-pilot/config.toml` and `/etc/sched-pilot/config.toml`.
  - Comprehensive `config.example.toml` reference file.
- **Headless CLI Automation**:
  - `--status` with optional `--json` export for scripts, window managers (Hyprland, KDE, Sway), and udev rules.
  - `--set-profile <profile>` and `--set-sched <scheduler>` headless commands.
- **Arch Linux & CachyOS Packaging**:
  - Production-ready `PKGBUILD` for AUR and CachyOS repositories.
  - Desktop entry file `cachy-sched-pilot.desktop`.
- **Online Presence & Community Postings**:
  - Synchronized social media and community release announcements in `posting.md`.

### Changed
- Refactored `core.manager` to execute operations strictly via `cachy-sched-helper` or `scxctl`.
- Enhanced Textual TUI dashboard with tabbed layout, dynamic button state checking, and real-time refresh.
- Upgraded micro-benchmark suite to measure scheduling jitter and wake-up latencies concurrently.

### Fixed
- Fixed potential traceback if `/sys/kernel/sched_ext` is unavailable or sched-ext binaries are absent in `$PATH`.
- Resolved privilege escalation vulnerabilities by replacing open shell calls with whitelisted helper commands.

---

## [1.1.0] - 2026-09-15
### Added
- Integration with `scxctl` D-Bus client.
- System Doctor health diagnostics check.
- Audio and emulation profiles.

---

## [1.0.0] - 2026-09-15
### Added
- Initial release of Cachy-Sched-Pilot.
- Textual TUI dashboard and micro-benchmark suite.
- Autonomous process governor.
