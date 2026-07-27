#!/bin/bash
# =============================================================================
# SETUP SCRIPT CHO RASPBERRY PI 4
# =============================================================================
# Copy toàn bộ thư mục do_an_tot_nghiep sang Pi 4 rồi chạy:
#   chmod +x setup_pi.sh
#   ./setup_pi.sh
# =============================================================================

echo "============================================"
echo "  SETUP AI PHAN LOAI RAC - RASPBERRY PI 4"
echo "============================================"
echo ""

# Cập nhật hệ thống
echo "[1/5] Cap nhat he thong..."
sudo apt update -y && sudo apt upgrade -y

# Cài Python + pip
echo "[2/5] Cai Python3 + pip..."
sudo apt install -y python3 python3-pip python3-pyqt5 python3-opengl

# Cài OpenCV (cách nhanh nhất)
echo "[3/5] Cai OpenCV..."
sudo apt install -y python3-opencv libopencv-dev

# Cài các thư viện Python cần thiết
echo "[4/5] Cai thu vien Python..."
pip3 install --user numpy pillow 2>/dev/null
pip3 install --user ultralytics fastapi uvicorn websockets python-multipart 2>/dev/null

# Kiểm tra webcam
echo "[5/5] Kiem tra webcam USB..."
echo ""
ls -la /dev/video* 2>/dev/null && echo "✅ Webcam detected!" || echo "⚠️  Khong thay webcam. Cam USB vao va thu lai."
echo ""

echo "============================================"
echo "  ✅ SETUP HOAN TAT!"
echo ""
echo "  Cach chay:"
echo "    python3 gui_webcam.py"
echo ""
echo "  Hoac chay bang script:"
echo "    ./run.sh"
echo "============================================"