"""
TEST WEBCAM - Kiểm tra camera USB hoạt động
Chạy: python3 src/camera_test.py
Thoát: Nhấn 'q'
"""

import cv2, sys, time

print("=" * 50)
print("  📷 KIỂM TRA WEBCAM")
print("=" * 50)

found = False

# Thử tất cả camera với V4L2 backend (tốt nhất cho Pi 4)
for cam_id in range(10):
    cap = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap.release()
        continue
    
    # Thử đọc frame
    ret, frame = cap.read()
    if not ret or frame is None or frame.size == 0:
        print(f"  ⚠️  Camera {cam_id}: mở được nhưng KHÔNG đọc được frame")
        cap.release()
        continue
    
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\n✅ CAMERA {cam_id} HOẠT ĐỘNG!")
    print(f"   Kích thước: {w}x{h}")
    print(f"   FPS: {fps}")
    print(f"   Backend: V4L2")
    print(f"   Nhấn 'q' để thoát, 's' để chụp ảnh\n")
    
    found = True
    
    # Hiển thị webcam
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("   ⚠️  Mất kết nối camera!")
            break
        
        # Hiển thị thông tin lên frame
        cv2.putText(frame, f"Camera {cam_id} | {w}x{h} | Nhan Q thoat", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {count}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        cv2.imshow(f"Webcam Test - Camera {cam_id}", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"test_capture_{cam_id}_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"   📸 Đã chụp: {filename}")
        
        count += 1
    
    cap.release()
    cv2.destroyAllWindows()
    break

if not found:
    print("\n❌ KHÔNG TÌM THẤY CAMERA NÀO!")
    print("\n🔍 Kiểm tra:")
    print("  1. Webcam đã cắm chặt vào USB chưa?")
    print("  2. Chạy: ls /dev/video*")
    print("  3. Chạy: lsusb")
    print("  4. Nếu có /dev/video0: sudo chmod 666 /dev/video*")
    print("  5. Webcam cần hỗ trợ UVC (USB Video Class)")
    print("     Logitech C270, Microsoft LifeCam đều OK")