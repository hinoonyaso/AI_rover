#!/usr/bin/env bash
# Install the out-of-tree ch341 USB-serial driver (the Jetson kernel is built without it).
# Run with sudo from this directory:  sudo ./install.sh
# Re-run it (after `make`) whenever the kernel package is updated: the module only fits one kernel.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "run with sudo: sudo ./install.sh" >&2
  exit 1
fi

KVER="$(uname -r)"
HERE="$(cd "$(dirname "$0")" && pwd)"
KO="$HERE/ch341.ko"

[ -f "$KO" ] || { echo "ch341.ko not found: run 'make' first" >&2; exit 1; }
VERMAGIC="$(modinfo -F vermagic "$KO")"
case "$VERMAGIC" in
  "$KVER "*) ;;
  *) echo "ch341.ko was built for '$VERMAGIC', running kernel is $KVER: run 'make clean && make'" >&2; exit 1 ;;
esac

install -D -m 644 "$KO" "/lib/modules/$KVER/extra/ch341.ko"
depmod -a "$KVER"
modprobe ch341                       # loads usbserial first (dependency)
echo ch341 > /etc/modules-load.d/ch341.conf   # load at every boot

echo "ch341 loaded:"
lsmod | grep -E '^(ch341|usbserial)'
echo "serial devices:"
ls -l /dev/ttyUSB* 2>/dev/null || echo "  (no /dev/ttyUSB* yet: replug the USB device or check dmesg)"
