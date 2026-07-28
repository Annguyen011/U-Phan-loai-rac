#!/bin/bash
# =============================================================================
# CAI THU VIEN - CHAY 1 LAN DUY NHAT
# =============================================================================
cd "$(dirname "$0")/.."

echo "============================================"
echo "  CAI DAT THU VIEN PI 4"
echo "============================================"
echo ""

echo "[1/4] Don dep /tmp..."
sudo rm -rf /tmp/pip-* ~/.cache/pip 2>/dev/null || true
mkdir -p /home/pi/tmp && export TMPDIR=/home/pi/tmp

echo "[2/4] Cai Python + tools..."
sudo apt update -y -qq
sudo apt install -y -qq python3-pip python3-opencv lsof avahi-daemon arduino-cli 2>/dev/null || true

echo "[3/4] Cai Python packages..."
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages --upgrade pip 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages \
    numpy pillow ultralytics fastapi uvicorn websockets python-multipart \
    pyserial matplotlib pandas 2>/dev/null || true
rm -rf $TMPDIR/pip-* 2>/dev/null || true

echo "[4/4] Go PyQt (ko can)..."
sudo apt remove -y python3-pyqt5 2>/dev/null || true
sudo pip3 uninstall --break-system-packages -y PyQt6 PyQt5 QtPy 2>/dev/null || true

echo ""
echo "============================================"
echo "  ✅ CAI DAT XONG!"
echo "  Train AI:       scripts/train.sh"
echo "  Flash Arduino:  scripts/flash_arduino.sh"
echo "  Run server:     scripts/run.sh"
echo "============================================"