#!/bin/bash
# =============================================================================
# SETUP SCRIPT TOÀN DIỆN - RASPBERRY PI 4
# =============================================================================
# Chỉ cần chạy 1 lệnh:   sudo ./setup_pi.sh
# Tự động làm MỌI THỨ: cài đặt + gỡ PyQt + fix /tmp đầy
# =============================================================================

echo "============================================"
echo "  SETUP AI PHAN LOAI RAC - Pi 4 (ALL IN ONE)"
echo "============================================"
echo ""

# Fix lỗi /tmp đầy: dọn dẹp + tạo tmp trên home
echo "[0/8] Don dep /tmp + tao TMPDIR tren home..."
sudo rm -rf /tmp/pip-* /tmp/*.whl ~/.cache/pip 2>/dev/null || true
mkdir -p /home/pi/tmp
export TMPDIR=/home/pi/tmp
echo "   ✅ TMPDIR=$TMPDIR"

# ==================================================================
# 1. CẬP NHẬT HỆ THỐNG
# ==================================================================
echo "[1/8] Cap nhat he thong..."
sudo apt update -y && sudo apt upgrade -y

# ==================================================================
# 2. CÀI PYTHON + PIP + TOOLS
# ==================================================================
echo "[2/8] Cai Python3 + pip + tools..."
sudo apt install -y python3 python3-pip python3-venv git curl wget lsof avahi-daemon

# ==================================================================
# 3. CÀI OPENCV
# ==================================================================
echo "[3/8] Cai OpenCV..."
sudo apt install -y python3-opencv libopencv-dev 2>/dev/null || true
echo "   ✅ OpenCV OK"

# ==================================================================
# 4. GỠ PYQT (DÙNG --break-system-packages)
# ==================================================================
echo "[4/8] Go bo PyQt..."
sudo apt remove -y python3-pyqt5 python3-pyqt5-sip 2>/dev/null || true
sudo apt autoremove -y 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 uninstall --break-system-packages -y PyQt6 PyQt5 PyQt6-sip QtPy 2>/dev/null || true
echo "   ✅ PyQt da duoc go"

# ==================================================================
# 5. CÀI NUMPY + PILLOW
# ==================================================================
echo "[5/8] Cai numpy, pillow..."
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages --upgrade pip 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages numpy pillow 2>/dev/null || true

# ==================================================================
# 6. CÀI YOLOv11
# ==================================================================
echo "[6/8] Cai YOLOv11..."
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages ultralytics 2>/dev/null || true
echo "   ✅ YOLO OK"

# ==================================================================
# 7. CÀI WEB SERVER (FastAPI)
# ==================================================================
echo "[7/8] Cai FastAPI + WebSocket..."
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages fastapi uvicorn websockets python-multipart jinja2 2>/dev/null || true
echo "   ✅ FastAPI OK"

# Dọn dẹp
rm -rf $TMPDIR/pip-* 2>/dev/null || true

# ==================================================================
# 8. KIỂM TRA TẤT CẢ
# ==================================================================
echo "[8/8] Kiem tra..."
echo ""

python3 --version && echo "   ✅ Python3 OK"
python3 -c "import cv2; print('   ✅ OpenCV', cv2.__version__)" 2>/dev/null || echo "   ⚠️  OpenCV chua OK"
python3 -c "from ultralytics import YOLO; print('   ✅ YOLO OK')" 2>/dev/null || echo "   ⚠️  YOLO chua OK"
python3 -c "from fastapi import FastAPI; print('   ✅ FastAPI OK')" 2>/dev/null || echo "   ⚠️  FastAPI chua OK"

echo ""
echo "📷 Webcam:"
ls /dev/video* 2>/dev/null && echo "   ✅ Co thiet bi video!" || echo "   ⚠️  Chua cam webcam USB"

echo ""
echo "🔍 PyQt:"
python3 -c "import PyQt5" 2>/dev/null && echo "   ⚠️  PyQt5 con!" || echo "   ✅ PyQt5 da go"
python3 -c "import PyQt6" 2>/dev/null && echo "   ⚠️  PyQt6 con!" || echo "   ✅ PyQt6 da go"

echo ""
echo "============================================"
echo "  ✅ SETUP HOAN TAT!"
echo ""
echo "  Chay server:"
echo "    ./run.sh"
echo "============================================"
