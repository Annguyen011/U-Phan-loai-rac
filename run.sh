#!/bin/bash
# =============================================================================
# RUN AI PHAN LOAI RAC - CHAY NHANH
# =============================================================================
cd "$(dirname "$0")"

echo "============================================"
echo "  AI PHAN LOAI RAC - YOLOv11 NANO"
echo "============================================"

# Kill port 8080 cũ
PID=$(lsof -ti:8080 2>/dev/null)
if [ -n "$PID" ]; then
    kill -9 $PID 2>/dev/null
    echo "🔧 Da giai phong port 8080"
fi

# Kiểm tra model
if [ ! -f "models/yolo_best.pt" ]; then
    echo "⚠️  Chua co model, dang train..."
    python3 train_yolo.py
fi

# Lấy IP
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo "🌐 IP: http://$MY_IP:8080"
echo "🚀 Dang khoi dong server..."
echo ""

python3 server.py