#!/bin/bash
cd "$(dirname "$0")"
echo "============================================"
echo "  AI PHAN LOAI RAC - YOLOv11 NANO"
echo "============================================"

PID=$(lsof -ti:8080 2>/dev/null)
[ -n "$PID" ] && kill -9 $PID 2>/dev/null && echo "🔧 Da giai phong port 8080"

if [ -f "models/yolo_best.pt" ]; then
    echo "✅ Model da co san!"
elif [ -f "models/yolo11n.pt" ]; then
    echo "⚠️  Dung pretrained model. Train: python3 src/train_yolo.py"
fi

MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "🌐 http://$MY_IP:8080"
echo "🚀 Dang khoi dong..."
echo ""
python3 src/server.py