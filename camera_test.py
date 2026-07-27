"""
=============================================================================
TEST CAMERA - HIEN THI WEBCAM USB TREN RASPBERRY PI 4
=============================================================================
Chạy: python3 camera_test.py
Thoát: Nhấn 'q'
=============================================================================
"""
import cv2
import sys

print("=" * 50)
print("  📷 KIEM TRA CAMERA")
print("=" * 50)

# Thử tất cả camera với backend phù hợp
found = False

for backend_id, backend_name in [(cv2.CAP_V4L2, "V4L2"), (cv2.CAP_ANY, "ANY"), (cv2.CAP_FFMPEG, "FFMPEG")]:
    for cam_id in range(10):
        cap = cv2.VideoCapture(cam_id, backend_id)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"\n✅ TIM THAY CAMERA {cam_id} ({backend_name})")
                print(f"   Kich thuoc: {w}x{h}")
                print(f"   Nhan 'q' de thoat\n")
                
                found = True
                try:
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        cv2.imshow(f"Webcam {cam_id} ({w}x{h}) - Nhan q de thoat", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                except KeyboardInterrupt:
                    pass
                cap.release()
                cv2.destroyAllWindows()
                
                if found:
                    sys.exit(0)
            cap.release()

# Nếu không tìm thấy camera nào
if not found:
    print("\n❌ KHONG TIM THAY CAMERA NAO!")
    print("\nKiem tra:")
    print("  1. Webcam da cam chat vao USB chua?")
    print("  2. Thu tat ca 4 cong USB cua Pi 4")
    print("  3. Chay: lsusb  (xem co thiet bi webcam khong)")
    print("  4. Chay: dmesg | tail -20  (xem kernel log)")
    print("  5. Webcam can ho tro UVC (USB Video Class)")
    print("     Logitech C270, Microsoft LifeCam deu OK")
    
    # Thử hiển thị danh sách USB
    import os
    print("\n📋 Danh sach thiet bi USB:")
    os.system("lsusb 2>/dev/null || echo 'Khong chay duoc lsusb'")