#!/bin/bash
# =============================================================================
# RUN AI PHAN LOAI RAC - RASPBERRY PI 4
# =============================================================================
# Chỉ cần chạy: ./run.sh
# =============================================================================

cd "$(dirname "$0")"

echo "============================================"
echo "  AI PHAN LOAI RAC - YOLOv11 NANO"
echo "  Raspberry Pi 4 + Webcam USB"
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
ls -la /dev/video* 2>/dev/null || echo "⚠️  Khong thay webcam!"

# Chạy GUI
echo ""
echo "🚀 Dang khoi dong GUI..."
python3 gui_webcam.py