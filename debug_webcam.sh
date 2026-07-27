#!/bin/bash
echo "=== KIEM TRA WEBCAM USB ==="
echo ""
echo "1. Danh sach /dev/video*:"
ls -la /dev/video* 2>/dev/null
echo ""
echo "2. Kiem tra bang v4l2-ctl:"
for dev in /dev/video*; do
    echo "--- $dev ---"
    v4l2-ctl -d $dev --info 2>/dev/null | grep -E "Driver|Card|Bus|Capabilities" || echo "   Khong doc duoc"
done
echo ""
echo "3. Thu mo camera bang Python:"
python3 -c "
import cv2
for i in range(20):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f'   ✅ Camera {i}: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}')
        else:
            print(f'   ⚠️  Camera {i}: mo duoc nhung KHONG DOC DUOC frame')
        cap.release()
    else:
        pass  # Không in ra để tránh spam
"
echo ""
echo "4. Kiem tra quyen truy cap:"
groups | grep video && echo "   ✅ User thuoc group video" || echo "   ⚠️  User KHONG thuoc group video - can: sudo usermod -aG video \$USER"
