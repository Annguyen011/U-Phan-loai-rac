#!/bin/bash
# =============================================================================
# RUN AI PHAN LOAI RAC - RASPBERRY PI 4 (WEB SERVER)
# =============================================================================
# Chỉ cần chạy: ./run.sh
# =============================================================================

cd "$(dirname "$0")"

echo "============================================"
echo "  AI PHAN LOAI RAC - YOLOv11 NANO"
echo "  Raspberry Pi 4 + Webcam USB → WEB"
echo "============================================"

# Kiểm tra model đã train chưa
if [ ! -f "models/yolo_best.pt" ]; then
    echo ""
    echo "⚠️  Chua co model da train!"
    echo "   Tien hanh train voi dataset hien co..."
    echo ""
    python3 train_yolo.py
    echo ""
fi

# Kiểm tra webcam
echo ""
echo "📷 Kiem tra webcam..."
ls -la /dev/video* 2>/dev/null || echo "⚠️  Khong thay webcam! Cam USB vao."

# Lấy IP của Pi 4 (show toàn bộ IP để user copy)
echo ""
echo "🌐 IP cua Raspberry Pi 4:"
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -n "$MY_IP" ]; then
    echo "   👉 http://$MY_IP:8080"
else
    echo "   (khong tim thay IP - kiem tra WiFi)"
fi

echo ""

# Kill port 8080 nếu đang bị chiếm
echo "🔧 Kiem tra port 8080..."
PID=$(lsof -ti:8080 2>/dev/null)
if [ -n "$PID" ]; then
    echo "   Port 8080 đang bị chiếm bởi PID $PID. Đang kill..."
    kill -9 $PID 2>/dev/null
    sleep 1
    echo "   ✅ Đã giải phóng port 8080"
fi

echo ""
echo "============================================"
echo "🚀 Dang khoi dong WEB SERVER..."
echo ""
echo "📱 Tren LAPTOP, mo trinh duyet (3 cach):"
echo ""
echo "   CACH 1 (on dinh nhat - hostname):"
echo "   http://raspberrypi.local:8080"
echo ""
echo "   CACH 2 (IP hien tai):"
echo "   http://$MY_IP:8080"
echo ""
echo "   CACH 3 (localhost - neu Pi co man hinh):"
echo "   http://localhost:8080"
echo ""
echo "============================================"
echo ""
echo "💡 TIP: hostname 'raspberrypi.local' LUON CO DINH,"
echo "   khong can biet IP thay doi!"

python3 server.py
