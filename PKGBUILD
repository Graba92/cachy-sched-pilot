# Maintainer: Matze Graba <graba@cachyos.org>
pkgname=cachy-sched-pilot
pkgver=1.2.0
pkgrel=1
pkgdesc="Autonomous sched-ext (SCX) CPU scheduler management, telemetry & benchmark suite for CachyOS / Arch Linux"
arch=('any')
url="https://github.com/Graba92/cachy-sched-pilot"
license=('MIT')
depends=(
    'python'
    'python-psutil'
    'python-rich'
    'python-textual'
    'polkit'
)
optdepends=(
    'scx-scheds: Core collection of sched-ext schedulers (scx_lavd, scx_rusty, scx_bpfland)'
    'scxctl: D-Bus client for scheduler switching and introspection'
    'cpupower: Linux kernel CPU frequency and governor tuning tool'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname-$pkgver" 2>/dev/null || cd "$srcdir/$pkgname" 2>/dev/null || cd "$startdir"

    # 1. Install internal application tree
    install -dm755 "$pkgdir/usr/lib/$pkgname"
    cp -r core ui "$pkgdir/usr/lib/$pkgname/"
    install -Dm755 app.py "$pkgdir/usr/lib/$pkgname/app.py"

    # 2. Install privileged backend helper
    install -Dm755 bin/cachy-sched-helper "$pkgdir/usr/lib/$pkgname/cachy-sched-helper"
    install -dm755 "$pkgdir/usr/bin"
    ln -s "/usr/lib/$pkgname/cachy-sched-helper" "$pkgdir/usr/bin/cachy-sched-helper"

    # 3. Install user CLI wrapper
    cat << 'EOF' > "$pkgdir/usr/bin/cachy-sched-pilot"
#!/usr/bin/env sh
exec /usr/bin/python3 /usr/lib/cachy-sched-pilot/app.py "$@"
EOF
    chmod 755 "$pkgdir/usr/bin/cachy-sched-pilot"

    # 4. Install Polkit Policy
    install -Dm644 packaging/org.cachyos.schedpilot.policy "$pkgdir/usr/share/polkit-1/actions/org.cachyos.schedpilot.policy"

    # 5. Install Desktop entry
    install -Dm644 packaging/cachy-sched-pilot.desktop "$pkgdir/usr/share/applications/cachy-sched-pilot.desktop"

    # 6. Install configuration example
    install -Dm644 config.example.toml "$pkgdir/etc/sched-pilot/config.toml.example"

    # 7. Documentation & License
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
    install -Dm644 README_DE.md "$pkgdir/usr/share/doc/$pkgname/README_DE.md"
    install -Dm644 CHANGELOG.md "$pkgdir/usr/share/doc/$pkgname/CHANGELOG.md"
}
