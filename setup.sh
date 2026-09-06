#!/usr/bin/env bash
# Ubuntu 24.04 amd64: extract runtime tools locally, without root.
set -euo pipefail
root=$(dirname "$(readlink -f -- "${BASH_SOURCE[0]}")")
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Requires x86_64 Linux.' >&2; exit 1; }
for command in python3 apt-get dpkg-deb; do
  command -v "$command" >/dev/null || { echo "Missing dependency: $command" >&2; exit 1; }
done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11 or later is required.")'
mkdir -p "$root/tools"
scratch=$(mktemp -d "$root/tools/.qemu-download-XXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
cd "$scratch"
apt-get download qemu-user
apt-get download ripgrep
dpkg-deb -x qemu-user_*.deb extracted
dpkg-deb -x ripgrep_*.deb extracted-ripgrep
extracted/usr/bin/qemu-x86_64 --version
extracted-ripgrep/usr/bin/rg --version
mkdir -p "$root/tools/qemu"
mkdir -p "$root/tools/ripgrep"
cp -a extracted/. "$root/tools/qemu/"
cp -a extracted-ripgrep/. "$root/tools/ripgrep/"
cp qemu-user_*.deb "$root/tools/"
cp ripgrep_*.deb "$root/tools/"
echo 'Local QEMU and ripgrep ready.'
