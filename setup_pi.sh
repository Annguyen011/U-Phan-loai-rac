#!/bin/bash
# =============================================================================
# SETUP SCRIPT TOÀN DIỆN CHO RASPBERRY PI 4
# =============================================================================
# Chạy: chmod +x setup_pi.sh && sudo ./setup_pi.sh
# =============================================================================

set -e  # Dừng ngay nếu có lỗi

echo "============================================"
echo "  SETUP AI PHAN LOAI RAC - Pi 4 (FULL)"
echo "============================================"
echo ""

# ==================================================================
# 1. CẬP NHẬT HỆ THỐNG
# ==================================================================
echo "[1/7] Cap nhat he thong..."
sudo apt update -y && sudo apt upgrade -y

# ==================================================================
# 2. CÀI PYTHON + PIP + TOOLS CƠ BẢN
# ==================================================================
echo "[2/7] Cai Python3 + pip + tools..."
sudo apt install -y python3 python3-pip python3-venv git curl wget lsof avahi-daemon

# ==================================================================
# 3. CÀI OPENCV (TỪ APT - NHANH NHẤT)
# ==================================================================
echo "[3/7] Cai OpenCV (apt)..."
sudo apt install -y python3-opencv libopencv-dev libatlas-base-dev libhdf5-dev libharfbuzz-dev

# ==================================================================
# 4. GỠ PYQT (NẾU CÓ) - WEB KHÔNG CẦN
# ==================================================================
echo "[4/7] Go bo PyQt (khong can thiet cho web)..."
sudo apt remove -y python3-pyqt5 python3-pyqt5-sip python3-pyqt5.qtsvg 2>/dev/null || true
sudo apt autoremove -y 2>/dev/null || true
sudo pip3 uninstall -y PyQt6 PyQt5 PyQt6-sip 2>/dev/null || true
echo "   ✅ Da xoa PyQt (neu co)"

# ==================================================================
# 5. CÀI THƯ VIỆN PYTHON (TỪ PIP - MỚI NHẤT)
# ==================================================================
echo "[5/7] Cai thu vien Python (numpy, pillow, opencv)..."
sudo pip3 install --upgrade pip 2>/dev/null || true
sudo pip3 install numpy pillow 2>/dev/null

# ==================================================================
# 6. CÀI YOLO + WEB SERVER (THEO ĐÚNG THỨ TỰ)
# ==================================================================
echo "[6/7] Cai YOLOv11 + FastAPI + WebSocket..."
# Ultralytics (YOLO)
sudo pip3 install ultralytics 2>/dev/null
# Web server
sudo pip3 install fastapi uvicorn websockets python-multipart jinja2 2>/dev/null

# ==================================================================
# 7. KIỂM TRA TẤT CẢ
# ==================================================================
echo "[7/7] Kiem tra cai dat..."
echo ""

# Check Python
python3 --version && echo "   ✅ Python3 OK"

# Check OpenCV
python3 -c "import cv2; print('   ✅ OpenCV', cv2.__version__)" 2>/dev/null || echo "   ⚠️  OpenCV chua OK"

# Check YOLO
python3 -c "from ultralytics import YOLO; print('   ✅ YOLO OK')" 2>/dev/null || echo "   ⚠️  YOLO chua OK"

# Check FastAPI
python3 -c "from fastapi import FastAPI; print('   ✅ FastAPI OK')" 2>/dev/null || echo "   ⚠️  FastAPI chua OK"

# Check webcam
echo ""
echo "📷 Kiem tra webcam USB..."
ls -la /dev/video* 2>/dev/null && echo "   ✅ Webcam detected!" || echo "   ⚠️  Chua co webcam. Cam USB vao."

# Check PyQt đã bị xóa chưa
echo ""
echo "🔍 Kiem tra PyQt con khong..."
python3 -c "import PyQt5" 2>/dev/null && echo "   ⚠️  PyQt5 VAN CON! Thu lai: sudo pip3 uninstall PyQt5" || echo "   ✅ PyQt5 da duoc go"
python3 -c "import PyQt6" 2>/dev/null && echo "   ⚠️  PyQt6 VAN CON! Thu lai: sudo pip3 uninstall PyQt6" || echo "   ✅ PyQt6 da duoc go"

echo ""
echo "============================================"
echo "  ✅ SETUP HOAN TAT!"
echo ""
echo "  Chay server:"
echo "    ./run.sh"
echo "============================================"