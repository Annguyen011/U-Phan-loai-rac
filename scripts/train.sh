#!/bin/bash
# =============================================================================
# TRAIN AI - CHỈ CHẠY KHI CHƯA CÓ MODEL HOẶC MUỐN TRAIN LẠI
# =============================================================================
cd "$(dirname "$0")/.."

echo "============================================"
echo "  TRAIN AI - YOLOv11 NANO"
echo "============================================"

if [ -f "models/yolo_best.pt" ]; then
    echo ""
    echo "✅ Model da co: models/yolo_best.pt"
    echo "   Kich thuoc: $(du -h models/yolo_best.pt | cut -f1)"
    echo ""
    read -p "   Ban co muon TRAIN LAI khong? (y/N): " answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        echo "   👌 Giữ model cũ, không train lại."
        echo "   Chay server: scripts/run.sh"
        exit 0
    fi
    echo "   🗑️  Dang train lai..."
fi

echo ""
echo "📊 Dang train..."
python3 src/train_yolo.py

echo ""
echo "============================================"
echo "  ✅ TRAIN XONG!"
echo "  Model: models/yolo_best.pt"
echo "  Reports: reports/"
echo "  Chay server: scripts/run.sh"
echo "============================================"