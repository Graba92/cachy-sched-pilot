#!/usr/bin/env bash
# ==============================================================================
# Setup & Dependency Installer for Cachy-Sched-Pilot
# ==============================================================================
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}⚡ [1/3] Prüfe Linux-Distribution & sched-ext Unterstützung...${RESET}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "    Erkanntes System: ${GREEN}${NAME}${RESET}"
else
    echo -e "${YELLOW}    /etc/os-release nicht gefunden, fahre fort...${RESET}"
fi

# Paketinstallation für CachyOS / Arch
if command -v pacman &>/dev/null; then
    echo -e "${CYAN}⚡ [2/3] Installiere Abhängigkeiten via pacman / yay...${RESET}"
    sudo pacman -S --needed --noconfirm python python-rich python-psutil || true
    # sched-ext Pakete prüfen
    if ! command -v scx_lavd &>/dev/null; then
        echo -e "${YELLOW}    scx Schedulers nicht gefunden. Installiere scx-scheds...${RESET}"
        sudo pacman -S --needed --noconfirm scx-scheds scx-tools || true
    fi
fi

# Python Abhängigkeiten (textual)
echo -e "${CYAN}⚡ [3/3] Prüfe Textual TUI Framework...${RESET}"
python3 -c "import textual" 2>/dev/null || {
    echo "    Installiere Textual via pip / pacman..."
    sudo pacman -S --needed --noconfirm python-textual 2>/dev/null || pip install --user textual
}

# Symlink erstellen falls gewünscht
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$SCRIPT_DIR/run.sh" "$BIN_DIR/cachy-sched-pilot"

echo -e "${GREEN}✔ Installation erfolgreich!${RESET}"
echo -e "Starten mit: ${CYAN}cachy-sched-pilot${RESET} oder ${CYAN}./run.sh tui${RESET}"
