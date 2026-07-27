"""
SERVER WEB - AI PHÂN LOẠI RÁC (YOLOv11 NANO)
Chạy trên Raspberry Pi 4, phát kết quả qua mạng cho laptop xem
"""

import sys, os, time, asyncio, json, base64, cv2, numpy as np
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

sys.path.insert(0, '/var/data/python/bin')
from ultralytics import YOLO

# ============================================================
# CONFIG
# ============================================================
MODEL_PATH = "models/yolo_best.pt"
if not os.path.exists(MODEL_PATH):
    print(f"⚠️  Không tìm thấy {MODEL_PATH}, dùng yolo11n.pt (pretrained)")
    MODEL_PATH = "yolo11n.pt"

print(f"📥 Đang load YOLO model: {MODEL_PATH}")
yolo_model = YOLO(MODEL_PATH)
CLASS_NAMES = list(yolo_model.names.values())
print(f"   Classes ({len(CLASS_NAMES)}): {CLASS_NAMES}")

# Nếu model là pretrained COCO (80 classes), dùng filter class
OUR_CLASSES = {"nhua", "kim_loai", "giay", "khong_phai_rac"}
is_pretrained = len(CLASS_NAMES) > 10  # COCO có 80 classes

if is_pretrained:
    print(f"⚠️  Model là pretrained COCO ({len(CLASS_NAMES)} classes).")
    print(f"   Server vẫn chạy, nhưng KÉM CHÍNH XÁC.")
    print(f"   👉 Hãy train model:  python3 train_yolo.py")
    print(f"   (Cần ảnh trong dataset/images/train/nhua/, kim_loai/, ...)")

app = FastAPI(title="AI Phân Loại Rác")
os.makedirs("templates", exist_ok=True)

# Counter global
counter = {"nhua": 0, "kim_loai": 0, "giay": 0, "khong_phai_rac": 0}
cap = None


def init_camera():
    global cap
    
    # Thử tất cả camera index + backend
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_ANY, "ANY"),
        (cv2.CAP_FFMPEG, "FFMPEG"),
    ]
    
    for backend, name in backends:
        for cid in range(20):
            try:
                cam = cv2.VideoCapture(cid, backend)
                if cam.isOpened():
                    # Thử đọc frame
                    ret, _ = cam.read()
                    if ret:
                        cap = cam
                        w = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        print(f"[CAM] ✅ Camera {cid} OK ({name} backend, {w}x{h})")
                        return cid
                    cam.release()
            except Exception:
                pass
    
    print("[CAM] ❌ KHÔNG TÌM THẤY CAMERA NÀO!")
    return -1


# ============================================================
# HTML TEMPLATE (nhúng trực tiếp)
# ============================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🤖 AI PHÂN LOẠI RÁC</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #eee; overflow-x: hidden; }
.header { background: linear-gradient(135deg, #16213e, #0f3460); padding: 15px; text-align: center; border-bottom: 3px solid #4caf50; }
.header h1 { color: #4caf50; font-size: 28px; margin-bottom: 5px; }
.header p { color: #aaa; font-size: 14px; }
.main { display: flex; flex-wrap: wrap; gap: 15px; padding: 15px; max-width: 1400px; margin: 0 auto; }
.video-box { flex: 2; min-width: 400px; background: #16213e; border-radius: 12px; padding: 10px; border: 2px solid #0f3460; }
.video-box img { width: 100%; border-radius: 8px; display: block; }
.result-box { flex: 1; min-width: 280px; display: flex; flex-direction: column; gap: 15px; }
.card { background: #16213e; border-radius: 12px; padding: 20px; border: 2px solid #0f3460; text-align: center; }
.card h2 { font-size: 20px; margin-bottom: 10px; color: #4caf50; }
.current-label { font-size: 48px; font-weight: bold; margin: 10px 0; }
.current-conf { font-size: 18px; color: #aaa; }
.counters { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.counter-item { background: #0f3460; border-radius: 10px; padding: 15px; text-align: center; border-left: 4px solid; }
.counter-item .icon { font-size: 32px; }
.counter-item .count { font-size: 36px; font-weight: bold; margin: 5px 0; }
.counter-item .name { font-size: 14px; color: #aaa; text-transform: uppercase; }
.c-nhua { border-color: #e91e63; } .c-nhua .count { color: #e91e63; }
.c-kim_loai { border-color: #2196f3; } .c-kim_loai .count { color: #2196f3; }
.c-giay { border-color: #4caf50; } .c-giay .count { color: #4caf50; }
.c-khong { border-color: #9e9e9e; } .c-khong .count { color: #9e9e9e; }
.controls { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.btn { padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; color: white; }
.btn-reset { background: #ff9800; }
.btn-capture { background: #2196f3; }
.btn-pause { background: #f44336; }
.status { font-size: 13px; color: #888; text-align: center; margin-top: 10px; }
.fps { font-size: 12px; color: #666; }
@media (max-width: 768px) { .main { flex-direction: column; } .video-box { min-width: auto; } }
</style>
</head>
<body>

<div class="header">
    <h1>🤖 AI PHÂN LOẠI RÁC THẢI</h1>
    <p>YOLOv11 Nano | Raspberry Pi 4 | Real-time</p>
</div>

<div class="main">
    <div class="video-box">
        <img id="video" src="" alt="Webcam">
        <div class="fps" id="fps">FPS: --</div>
    </div>
    <div class="result-box">
        <div class="card">
            <h2>🔍 ĐANG PHÁT HIỆN</h2>
            <div class="current-label" id="currentLabel">--</div>
            <div class="current-conf" id="currentConf">0%</div>
        </div>
        <div class="counters">
            <div class="counter-item c-nhua">
                <div class="icon">🥤</div>
                <div class="count" id="cnt_nhua">0</div>
                <div class="name">Nhựa</div>
            </div>
            <div class="counter-item c-kim_loai">
                <div class="icon">🔩</div>
                <div class="count" id="cnt_kim_loai">0</div>
                <div class="name">Kim Loại</div>
            </div>
            <div class="counter-item c-giay">
                <div class="icon">📄</div>
                <div class="count" id="cnt_giay">0</div>
                <div class="name">Giấy</div>
            </div>
            <div class="counter-item c-khong">
                <div class="icon">❓</div>
                <div class="count" id="cnt_khong_phai_rac">0</div>
                <div class="name">Không Phải</div>
            </div>
        </div>
        <div class="controls">
            <button class="btn btn-reset" onclick="doReset()">🔄 Reset</button>
            <button class="btn btn-capture" onclick="doCapture()">📸 Chụp ảnh</button>
            <button class="btn btn-pause" onclick="doPause()">⏯️ Pause</button>
        </div>
        <div class="status" id="status">🔌 Đang kết nối...</div>
    </div>
</div>

<script>
let ws = null;
let paused = false;
let lastLabel = '';

function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws`);
    
    ws.onopen = () => { 
        document.getElementById('status').textContent = '✅ Đã kết nối'; 
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            if (data.image) {
                document.getElementById('video').src = 'data:image/jpeg;base64,' + data.image;
            }
            
            if (data.label) {
                const lbl = document.getElementById('currentLabel');
                const conf = document.getElementById('currentConf');
                lbl.textContent = data.label_display || data.label;
                conf.textContent = (data.confidence * 100).toFixed(1) + '%';
                
                // Màu
                const colors = {
                    'nhua': '#e91e63', 'kim_loai': '#2196f3', 
                    'giay': '#4caf50', 'khong_phai_rac': '#9e9e9e'
                };
                lbl.style.color = colors[data.label] || '#eee';
                
                // Chỉ đếm khi label thay đổi
                if (data.label !== lastLabel && data.confidence > 0.4) {
                    lastLabel = data.label;
                    // Gửi yêu cầu đếm lên server
                    ws.send(JSON.stringify({action: 'count', label: data.label}));
                }
            }
            
            if (data.counter) {
                for (const [k, v] of Object.entries(data.counter)) {
                    const el = document.getElementById('cnt_' + k);
                    if (el) el.textContent = v;
                }
            }
            
            if (data.fps) {
                document.getElementById('fps').textContent = 'FPS: ' + data.fps;
            }
        } catch(e) {}
    };
    
    ws.onclose = () => { 
        document.getElementById('status').textContent = '⏳ Đang kết nối lại...'; 
        setTimeout(connect, 2000); 
    };
    
    ws.onerror = () => { ws.close(); };
}

function doReset() { if (ws) ws.send(JSON.stringify({action: 'reset'})); }
function doCapture() { if (ws) ws.send(JSON.stringify({action: 'capture'})); }
function doPause() { 
    paused = !paused; 
    if (ws) ws.send(JSON.stringify({action: 'pause', paused: paused})); 
}

connect();
</script>
</body>
</html>"""


@app.get("/")
async def index():
    return HTMLResponse(content=HTML_PAGE)


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload ảnh để phân loại (không cần webcam)"""
    import shutil
    os.makedirs("uploads", exist_ok=True)
    
    # Lưu ảnh tạm
    file_path = f"uploads/{int(time.time())}_{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Đọc ảnh
    frame = cv2.imread(file_path)
    if frame is None:
        return {"error": "Không đọc được ảnh"}
    
    # Resize
    h, w = frame.shape[:2]
    scale = min(640 / w, 480 / h, 1.0)
    if scale < 1.0:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    
    # YOLO Inference
    results = yolo_model(frame, verbose=False, conf=0.25, iou=0.45)
    
    detections = []
    if len(results[0].boxes) > 0:
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            label = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else "unknown"
            detections.append({
                "label": label,
                "confidence": round(conf, 4),
                "bbox": [round(x, 1) for x in xyxy]
            })
    
    # Encode ảnh kết quả
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    img_b64 = base64.b64encode(buffer).decode()
    
    return {
        "image": img_b64,
        "detections": detections,
        "count": len(detections)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global counter, cap
    await websocket.accept()
    print("[WS] Client connected")
    
    last_label = ""
    paused = False
    
    try:
        while True:
            # Nhận message từ client
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                msg = json.loads(data)
                action = msg.get("action", "")
                
                if action == "reset":
                    counter = {k: 0 for k in counter}
                    print("[WS] Counter reset")
                elif action == "capture":
                    if cap and cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            os.makedirs("captures", exist_ok=True)
                            cv2.imwrite(f"captures/cap_{int(time.time())}.jpg", frame)
                elif action == "pause":
                    paused = msg.get("paused", False)
                    print(f"[WS] Paused: {paused}")
                elif action == "count":
                    lbl = msg.get("label", "")
                    if lbl in counter and lbl != last_label:
                        last_label = lbl
                        counter[lbl] += 1
                        await websocket.send_text(json.dumps({"counter": counter}))
            except asyncio.TimeoutError:
                pass
            
            if paused or cap is None or not cap.isOpened():
                await asyncio.sleep(0.1)
                continue
            
            # ================================================================
            # Đọc frame + AI Inference
            # ================================================================
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Resize frame để giảm bandwidth
            h, w = frame.shape[:2]
            scale = min(640 / w, 480 / h, 1.0)
            if scale < 1.0:
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            
            # YOLO Inference
            results = yolo_model(frame, verbose=False, conf=0.25, iou=0.45)
            
            label = "khong_phai_rac"
            confidence = 0.0
            display_name = "❌ KHÔNG PHẢI RÁC"
            colors_map = {'nhua': (233,30,99), 'kim_loai': (33,150,243), 
                         'giay': (76,175,80), 'khong_phai_rac': (158,158,158)}
            
            if len(results[0].boxes) > 0:
                boxes = results[0].boxes
                cls_id = int(boxes.cls[0])
                conf = float(boxes.conf[0])
                xyxy = boxes.xyxy[0].tolist()
                if conf > 0.25 and cls_id < len(CLASS_NAMES):
                    label = CLASS_NAMES[cls_id]
                    confidence = conf
                    color_rgb = colors_map.get(label, (158,158,158))
                    color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])
                    display_name = {'nhua':'NHỰA','kim_loai':'KIM LOẠI','giay':'GIẤY','khong_phai_rac':'❌ KHÔNG PHẢI'}.get(label, label.upper())
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), 
                                (int(xyxy[2]), int(xyxy[3])), color_bgr, 2)
                    cv2.putText(frame, f"{display_name} ({conf:.1%})", 
                               (int(xyxy[0]), int(xyxy[1]) - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr, 2)
            
            # Encode ảnh sang base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            img_b64 = base64.b64encode(buffer).decode()
            
            fps_val = 1.0 / max(time.time() - t0, 0.001)
            
            # Gửi kết quả
            await websocket.send_text(json.dumps({
                "image": img_b64,
                "label": label,
                "label_display": display_name,
                "confidence": round(confidence, 4),
                "counter": counter,
                "fps": round(fps_val, 1)
            }))
            
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")


if __name__ == "__main__":
    import socket
    
    cam_id = init_camera()
    
    print(f"\n{'='*60}")
    print(f"🚀 SERVER ĐÃ KHỞI ĐỘNG")
    print(f"{'='*60}")
    
    if cam_id < 0:
        print(f"\n⚠️  CHƯA CÓ WEBCAM USB!")
        print(f"   Server vẫn chạy, nhưng không có hình ảnh.")
        print(f"   Hãy cắm webcam USB vào Pi 4 và chạy lại.")
    else:
        print(f"   📷 Webcam: /dev/video{cam_id} OK")
    
    if is_pretrained:
        print(f"\n⚠️  MODEL CHƯA ĐƯỢC TRAIN!")
        print(f"   Đang dùng pretrained COCO (80 classes).")
        print(f"   👉 Train model:  python3 train_yolo.py")
    
    # Lấy IP
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname + ".local")
    except:
        ip = "không tìm thấy"
    
    print(f"\n📱 Mở trình duyệt trên LAPTOP:")
    print(f"   http://{hostname}.local:8080")
    print(f"   hoặc http://{ip}:8080")
    print(f"\n{'='*60}\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
