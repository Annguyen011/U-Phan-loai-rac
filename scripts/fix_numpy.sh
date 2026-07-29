#!/bin/bash
# =============================================
# FIX NUMPY CHO RASPBERRY PI 4 (Cortex-A72)
# Gỡ numpy lỗi, cài lại từ source với ARM flags
# =============================================
set -e

echo "============================================"
echo "  FIX NUMPY - Raspberry Pi 4 Cortex-A72"
echo "============================================"

# 1. Gỡ numpy cũ đã cài qua pip (bị compile sai)
echo ""
echo "[1/4] Đang gỡ numpy lỗi..."
pip3 uninstall numpy -y 2>/dev/null || true
pip3 uninstall numpy -y --break-system-packages 2>/dev/null || true

# 2. Cài numpy từ apt của Raspberry Pi OS (đã compile đúng cho ARM)
echo ""
echo "[2/4] Cài numpy từ apt (tương thích ARM)..."
sudo apt update -qq
sudo apt install -y python3-numpy python3-pip build-essential python3-dev libopenblas-dev 2>&1 | tail -5

# 3. Kiểm tra numpy
echo ""
echo "[3/4] Kiểm tra numpy..."
python3 -c "
import numpy as np
print(f'  ✅ NumPy {np.__version__}')
print(f'  ✅ Config: {np.show_config()}')
a = np.array([1,2,3])
print(f'  ✅ Test OK: {a.sum()}')
" 2>&1

# 4. Cài lại ultralytics với numpy mới
echo ""
echo "[4/4] Cài ultralytics..."
pip3 install ultralytics --no-deps 2>/dev/null || true
pip3 install ultralytics 2>&1 | tail -5

echo ""
echo "============================================"
echo "  ✅ NUMPY DA FIX XONG!"
echo "  Chay: scripts/run.sh"
echo "============================================"