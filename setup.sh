#!/bin/bash
# =============================================================================
# SETUP + RUN ALL-IN-ONE - RASPBERRY PI 4
# =============================================================================
# Chỉ cần:   sudo ./setup.sh
# Tự động:   Cài thư viện → Gỡ PyQt → Chạy server
# =============================================================================

echo "============================================"
echo "  AI PHAN LOAI RAC - Pi 4 (ALL IN ONE)"
echo "============================================"
echo ""

# ==================================================================
# 1. DỌN DẸP + TẠO TMPDIR (fix /tmp đầy)
# ==================================================================
echo "[1/6] Don dep /tmp..."
sudo rm -rf /tmp/pip-* /tmp/*.whl ~/.cache/pip 2>/dev/null || true
mkdir -p /home/pi/tmp
export TMPDIR=/home/pi/tmp
echo "   ✅ TMPDIR=$TMPDIR"

# ==================================================================
# 2. CÀI THƯ VIỆN
# ==================================================================
echo "[2/6] Cai thu vien Python..."
sudo apt update -y -qq && sudo apt upgrade -y -qq
sudo apt install -y -qq python3 python3-pip python3-opencv libopencv-dev lsof avahi-daemon 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages --upgrade pip 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages numpy pillow 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages ultralytics 2>/dev/null || true
sudo TMPDIR=$TMPDIR pip3 install --break-system-packages fastapi uvicorn websockets python-multipart jinja2 2>/dev/null || true
rm -rf $TMPDIR/pip-* 2>/dev/null || true
echo "   ✅ Thu vien OK"

# ==================================================================
# 3. GỠ PYQT (TRIỆT ĐỂ)
# ==================================================================
echo "[3/6] Go bo PyQt TRIET DE..."
# Gỡ bằng apt
sudo apt remove -y python3-pyqt5 python3-pyqt5-sip python3-pyqt5.qtsvg python3-pyqt5.qtquick 2>/dev/null || true
sudo apt autoremove -y 2>/dev/null || true
# Gỡ bằng pip (tất cả biến thể)
sudo pip3 uninstall --break-system-packages -y PyQt6 PyQt5 PyQt6-sip PyQt5-sip QtPy PyQtWebEngine 2>/dev/null || true
# Xóa thư mục còn sót
sudo rm -rf /usr/lib/python3*/dist-packages/PyQt* /usr/lib/python3*/dist-packages/QtPy* 2>/dev/null || true
echo "   ✅ PyQt da bi xoa HOAN TOAN"

# ==================================================================
# 4. KIỂM TRA WEBCAM
# ==================================================================
echo "[4/6] Kiem tra webcam USB..."
CAMERA_FOUND=false
for dev in /dev/video*; do
    INFO=$(v4l2-ctl -d $dev --info 2>/dev/null)
    if echo "$INFO" | grep -q "uvcvideo"; then
        echo "   ✅ Webcam USB: $dev"
        CAMERA_FOUND=true
        break
    fi
done
if [ "$CAMERA_FOUND" = false ]; then
    echo "   ⚠️  KHONG TIM THAY WEBCAM USB!"
    echo "   Web se co che do UPLOAD ANH (khong can webcam)"
fi
echo ""

# ==================================================================
# 5. TRAIN MODEL (nếu chưa có)
# ==================================================================
echo "[5/6] Kiem tra model..."
if [ ! -f "models/yolo_best.pt" ]; then
    echo "   Chua co model, dang train..."
    python3 train_yolo.py
else
    echo "   ✅ Model da co: models/yolo_best.pt"
fi

# ==================================================================
# 6. KILL PORT + CHẠY SERVER
# ==================================================================
echo "[6/6] Khoi dong WEB SERVER..."
PID=$(lsof -ti:8080 2>/dev/null)
if [ -n "$PID" ]; then kill -9 $PID 2>/dev/null; sleep 1; fi

MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "============================================"
echo "🚀 SERVER DA KHOI DONG!"
echo ""
echo "📱 Mo trinh duyet tren LAPTOP:"
echo "   http://$MY_IP:8080"
echo "   http://raspberrypi.local:8080"
echo "============================================"
echo ""

python3 server.py