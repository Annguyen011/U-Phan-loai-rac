"""
=============================================================================
AI PHÂN LOẠI RÁC - YOLOv11 NANO + SEGMENTATION
=============================================================================
Model: YOLOv11 Nano (~5.5MB) - Chạy mượt trên Raspberry Pi 4
Pipeline: Webcam -> Segmentation (nền đen) -> YOLO -> Kết quả
Classes: nhua, kim_loai, giay, khong_phai_rac
=============================================================================
"""

import sys
import time
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame,
                             QGridLayout, QGroupBox, QSizePolicy)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

import segmentation_engine as seg

sys.path.insert(0, '/var/data/python/bin')
from ultralytics import YOLO

# ============================================================
# LOAD YOLO MODEL (cache sau lần đầu)
# ============================================================
MODEL_PATH = "models/yolo_best.pt"

if not os.path.exists(MODEL_PATH):
    print(f"⚠️  Không tìm thấy {MODEL_PATH}, dùng pretrained yolo11n.pt")
    MODEL_PATH = "yolo11n.pt"

print(f"📥 Đang load YOLO model: {MODEL_PATH}")
yolo_model = YOLO(MODEL_PATH)
print(f"   Model loaded! Classes: {yolo_model.names}")

CLASS_NAMES = list(yolo_model.names.values())


# ============================================================
# GUI APPLICATION
# ============================================================
class WebcamApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 YOLOv11 NANO - Phân Loại Rác THẢI")
        self.setMinimumSize(1200, 800)

        self.cap = None
        self.timer = None
        self.is_running = False
        self.fps_counter = []
        self.seg_time = 0
        self.inf_time = 0

        self.colors = {
            'nhua':             ('#e91e63', 'NHỰA'),
            'kim_loai':         ('#2196f3', 'KIM LOẠI'),
            'giay':             ('#4caf50', 'GIẤY'),
            'khong_phai_rac':   ('#9e9e9e', '❌ KHÔNG PHẢI RÁC'),
        }

        self.build_ui()
        self.init_camera()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Title ---
        title = QLabel("🤖 YOLOv11 NANO - PHÂN LOẠI RÁC THẢI")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2e7d32; padding: 6px;")
        main_layout.addWidget(title)

        # --- Video Grid ---
        grid = QGridLayout(); grid.setSpacing(6)

        views = ["📷 WEBCAM GỐC", "🎭 MASK", "🔍 ĐÃ XỬ LÝ"]
        self.lbl_original   = self._make_vid()
        self.lbl_mask       = self._make_vid()
        self.lbl_processed  = self._make_vid()

        for c, (t, l) in enumerate(zip(views,
                [self.lbl_original, self.lbl_mask, self.lbl_processed])):
            grid.addWidget(QLabel(t, alignment=Qt.AlignmentFlag.AlignCenter), 0, c)
            grid.addWidget(l, 1, c)

        main_layout.addLayout(grid)

        # --- Result Bar ---
        res = QFrame()
        res.setStyleSheet("QFrame{background:#f5f5f5;border:2px solid #4caf50;border-radius:8px;padding:8px;}")
        rl = QHBoxLayout(res)
        self.result_label = QLabel("🔄 Đang khởi động...")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size:24px;font-weight:bold;color:#333;")
        rl.addWidget(self.result_label)
        self.fps_label = QLabel("FPS:0|Seg:0ms|Inf:0ms")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet("font-size:13px;color:#666;")
        rl.addWidget(self.fps_label)
        main_layout.addWidget(res)

        # --- Controls ---
        ctrl = QFrame()
        ctrl.setStyleSheet("QFrame{background:#fafafa;border:1px solid #ccc;border-radius:8px;padding:6px;}")
        cl = QHBoxLayout(ctrl); cl.setSpacing(10)
        cl.addWidget(QLabel("⚡ YOLOv11 NANO | TỰ ĐỘNG SEGMENTATION", 
                   styleSheet="font-size:13px;font-weight:bold;color:#555;"))
        cl.addStretch()
        self.btn_toggle = self._btn("⏸ Tạm dừng", "#ff9800")
        self.btn_toggle.clicked.connect(self.toggle_camera)
        cl.addWidget(self.btn_toggle)
        self.btn_capture = self._btn("📸 Chụp ảnh", "#2196f3")
        self.btn_capture.clicked.connect(self.capture_image)
        cl.addWidget(self.btn_capture)
        self.btn_quit = self._btn("❌ Thoát", "#f44336")
        self.btn_quit.clicked.connect(self.close)
        cl.addWidget(self.btn_quit)
        main_layout.addWidget(ctrl)

        # --- Stats ---
        sg = QGroupBox("📊 HIỆU NĂNG"); sg.setStyleSheet("QGroupBox{font-weight:bold;color:#555;}")
        sl = QHBoxLayout(sg)
        self.lbl_fps_v = QLabel("FPS:--"); self.lbl_seg = QLabel("Seg:--ms"); 
        self.lbl_inf = QLabel("Inf:--ms"); self.lbl_cls = QLabel("Classes:4")
        for l in [self.lbl_fps_v, self.lbl_seg, self.lbl_inf, self.lbl_cls]:
            l.setStyleSheet("font-size:13px;color:#333;padding:0 10px;"); sl.addWidget(l)
        main_layout.addWidget(sg)

    def _make_vid(self):
        l = QLabel(); l.setMinimumSize(320,240); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setStyleSheet("border:2px solid #4caf50;border-radius:8px;background:#1a1a1a;color:white;font-size:14px;")
        l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return l

    def _btn(self, t, c):
        b = QPushButton(t)
        b.setStyleSheet(f"QPushButton{{font-size:14px;padding:8px 20px;background:{c};color:white;border-radius:6px;font-weight:bold;}}")
        return b

    # ============================================================
    def init_camera(self):
        # Quét tất cả camera USB (0-5)
        found = False
        for cid in range(6):
            cap = cv2.VideoCapture(cid)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    self.cap = cap
                    found = True
                    print(f"[CAM] ✅ Camera {cid} OK (USB)")
                    self.is_running = True
                    self.timer = QTimer()
                    self.timer.timeout.connect(self.update_frame)
                    self.timer.start(50)
                    self.result_label.setText(f"✅ SẴN SÀNG (Camera {cid})")
                    return
                cap.release()
        
        if not found:
            self.lbl_original.setText(
                "❌ KHÔNG TÌM THẤY WEBCAM USB!\n\n"
                "Kiểm tra:\n"
                "• Cắm webcam vào cổng USB\n"
                "• Chạy: ls /dev/video*\n"
                "• Nếu có /dev/video0: sudo chmod 666 /dev/video*")
            self.result_label.setText("❌ No Camera")
            self.btn_toggle.setEnabled(False)

    def toggle_camera(self):
        self.is_running = not self.is_running
        self.btn_toggle.setText("⏸ Tạm dừng" if self.is_running else "▶ Tiếp tục")
        if self.timer: self.timer.start(50) if self.is_running else self.timer.stop()

    def capture_image(self):
        if self.cap is None: return
        ret, frame = self.cap.read()
        if ret:
            os.makedirs("captures", exist_ok=True)
            ts = int(time.time())
            cv2.imwrite(f"captures/original_{ts}.jpg", frame)
            try:
                rgba = seg.extract_foreground(frame)
                proc = seg.rgba_to_bgr_white_bg(rgba)
                cv2.imwrite(f"captures/processed_{ts}.jpg", proc)
                cv2.imwrite(f"captures/mask_{ts}.jpg", seg.get_mask(rgba))
            except: pass
            self.result_label.setText("📸 Đã chụp!")

    # ============================================================
    def update_frame(self):
        if not self.is_running or self.cap is None: return
        ret, frame = self.cap.read()
        if not ret: return

        t_start = time.time(); h, w = frame.shape[:2]

        # --- 1) Segmentation ---
        t0 = time.time()
        try:
            rgba = seg.extract_foreground(frame)
            mask = seg.get_mask(rgba)
            processed = seg.rgba_to_bgr_white_bg(rgba)
            self.seg_time = (time.time() - t0) * 1000
        except:
            mask = np.ones((h,w), dtype=np.uint8)*255
            processed = frame.copy()
            self.seg_time = 0

        # --- 2) YOLO Inference ---
        t1 = time.time()
        results = yolo_model(processed, verbose=False, conf=0.25, iou=0.45)
        self.inf_time = (time.time() - t1) * 1000

        # --- 3) Parse results ---
        label = "khong_phai_rac"
        confidence = 0.0
        display_name = "❌ KHÔNG PHẢI RÁC"

        if len(results[0].boxes) > 0:
            boxes = results[0].boxes
            cls_id = int(boxes.cls[0])
            conf = float(boxes.conf[0])
            if conf > 0.25:
                label = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else "khong_phai_rac"
                confidence = conf
                display_name = self.colors.get(label, (None, label.upper()))[1]

        color_info = self.colors.get(label, ('#9e9e9e', display_name))
        bg_color, _ = color_info
        r,g,b = int(bg_color[1:3],16), int(bg_color[3:5],16), int(bg_color[5:7],16)

        # FPS
        elapsed = (time.time() - t_start) * 1000
        self.fps_counter.append(elapsed)
        if len(self.fps_counter) > 30: self.fps_counter.pop(0)
        fps = 1000.0 / max(np.mean(self.fps_counter), 1e-3)

        # --- 4) Build displays ---
        orig = frame.copy(); cv2.rectangle(orig, (0,0), (w,h), (b,g,r), 3)

        mc = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR); mc[mask>128] = (0,255,0)
        md = cv2.addWeighted(frame, 0.3, mc, 0.7, 0)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(md, cnts, -1, (0,255,255), 2)

        proc = processed.copy()
        ov = proc.copy(); cv2.rectangle(ov, (0,0), (proc.shape[1], 50), (0,0,0), -1)
        proc = cv2.addWeighted(ov, 0.6, proc, 0.4, 0)
        cv2.putText(proc, f"{display_name} ({confidence:.1%})", (10,35),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (b,g,r), 2)

        self._set(self.lbl_original, orig); self._set(self.lbl_mask, md)
        self._set(self.lbl_processed, proc)

        icons = {'nhua':'🥤','kim_loai':'🔩','giay':'📄'}
        icon = icons.get(label, '❓')
        self.result_label.setText(f"{icon} {display_name}  |  {confidence:.1%}")
        self.result_label.setStyleSheet(
            f"font-size:24px;font-weight:bold;color:{bg_color};background:white;padding:8px 16px;border-radius:6px;")
        self.fps_label.setText(f"FPS:{fps:.0f}|Seg:{self.seg_time:.0f}ms|Inf:{self.inf_time:.0f}ms")
        self.lbl_fps_v.setText(f"FPS:{fps:.0f}"); self.lbl_seg.setText(f"Seg:{self.seg_time:.0f}ms")
        self.lbl_inf.setText(f"Inf:{self.inf_time:.0f}ms")

    def _set(self, lbl, bgr):
        h,w,ch = bgr.shape; rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        qt = QImage(rgb.data, w, h, ch*w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qt).scaled(lbl.size(), 
               Qt.AspectRatioMode.KeepAspectRatio, 
               Qt.TransformationMode.SmoothTransformation)
        lbl.setPixmap(pix)

    def closeEvent(self, e):
        if self.timer: self.timer.stop()
        if self.cap and self.cap.isOpened(): self.cap.release()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle('Fusion')
    w = WebcamApp(); w.show(); sys.exit(app.exec())