#!/bin/bash
# =============================================================================
# SETUP ALL-IN-ONE - RASPBERRY PI 4
# =============================================================================
# Chạy:   sudo ./setup.sh
# =============================================================================

echo "============================================"
echo "  SETUP AI PHAN LOAI RAC - Pi 4"
echo "============================================"
echo ""

# Dọn dẹp
echo "[1/5] Don dep..."
sudo rm -rf /tmp/pip-* /tmp/*.whl ~/.cache/pip 2>/dev/null || true
mkdir -p /home/pi/tmp
export TMPDIR=/home/pi/tmp

# Cài thư viện
echo "[2/5] Cai thu vien..."
sudo apt update -y -qq && sudo apt upgrade -y -qq
sudo apt install -y -qq python3 python3-pip python3-opencv libopencv-dev lsof avahi-daemon 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages --upgrade pip 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages numpy pillow ultralytics fastapi uvicorn websockets python-multipart 2>/dev/null || true
rm -rf $TMPDIR/pip-* 2>/dev/null || true

# Gỡ PyQt
echo "[3/5] Go PyQt..."
sudo apt remove -y python3-pyqt5 python3-pyqt5-sip 2>/dev/null || true
sudo pip3 uninstall --break-system-packages -y PyQt6 PyQt5 QtPy 2>/dev/null || true
sudo rm -rf /usr/lib/python3*/dist-packages/PyQt* /usr/lib/python3*/dist-packages/QtPy* 2>/dev/null || true

# Kiểm tra webcam
echo "[4/5] Kiem tra webcam..."
ls /dev/video* 2>/dev/null && echo "   ✅ Co thiet bi video" || echo "   ⚠️  Chua cam webcam"

# Train model nếu chưa có
echo "[5/5] Kiem tra model..."
if [ ! -f "models/yolo_best.pt" ]; then
    echo "   Chua co model, train..."
    python3 src/train_yolo.py
fi

echo ""
echo "============================================"
echo "  ✅ HOAN TAT!"
echo "  Chay: ./run.sh"
echo "============================================"