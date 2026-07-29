s #!/bin/bash
cd "$(dirname "$0")/.."
echo "============================================"
echo "  AI PHAN LOAI RAC - YOLOv11 NANO"
echo "============================================"

PID=$(lsof -ti:8080 2>/dev/null)
[ -n "$PID" ] && kill -9 $PID 2>/dev/null && echo "🔧 Da giai phong port 8080"

if [ -f "models/yolo_best.pt" ]; then
    echo "✅ Model da co san!"
elif [ -f "models/yolo11n.pt" ]; then
    echo "⚠️  Dung pretrained. Train: python3 src/train_yolo.py"
fi

# === KIỂM TRA NUMPY TRƯỚC ===
echo ""
echo "[CHECK] Kiem tra numpy..."
python3 -c "
import numpy as np
a = np.array([1,2,3])
print(f'  ✅ NumPy {np.__version__} OK')
" 2>&1 || {
    echo "⚠️  NumPy LỖI! Dang fix..."
    bash scripts/fix_numpy.sh
}

# === KIỂM TRA ARDUINO + CAMERA ===
echo ""
echo "[CHECK] Thiet bi:"
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null && echo "  🔌 Arduino da cam" || echo "  ⚠️  Khong thay Arduino"
ls /dev/video* 2>/dev/null && echo "  📷 Camera da cam" || echo "  ⚠️  Khong thay Camera"

MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "🌐 http://$MY_IP:8080"
echo "🚀 Dang khoi dong..."
echo ""

# Fix lỗi Illegal instruction trên ARM (Pi 4 Cortex-A72)
export OPENBLAS_CORETYPE=ARMV8
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export NUMEXPR_NUM_THREADS=2

# Chạy server
python3 src/server.py 2>&1
