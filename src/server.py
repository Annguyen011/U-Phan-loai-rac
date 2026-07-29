"""
SERVER WEB - AI PHÂN LOẠI RÁC (YOLOv11 NANO + ARDUINO CONTROL)
Chạy trên Raspberry Pi 4, phát kết quả qua mạng + điều khiển Arduino
"""

import sys, os, time, asyncio, json, base64, cv2, numpy as np, socket, threading
from pathlib import Path

# === PHẢI ĐẶT TRƯỚC KHI IMPORT NUMPY/ULTRALYTICS ===
# Fix "Illegal instruction" trên ARM Cortex-A72 (Pi 4)
os.environ.setdefault('OPENBLAS_CORETYPE', 'ARMV8')
os.environ.setdefault('NPY_DISABLE_CPU_FEATURES', 'ASIMD')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse
import uvicorn

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, '/var/data/python/bin')
from ultralytics import YOLO

# === Import Arduino Controller ===
try: from src.arduino_control import ArduinoController
except: pass

# === CONFIG ===
MODEL_PATH = ROOT / "models/yolo_best.pt"
if not MODEL_PATH.exists():
    MODEL_PATH = ROOT / "models/yolo11n.pt"

print(f"📥 Load YOLO: {MODEL_PATH}")
yolo_model = YOLO(str(MODEL_PATH))
CLASS_NAMES = list(yolo_model.names.values())
print(f"   Classes: {len(CLASS_NAMES)}")

app = FastAPI(title="AI Phân Loại Rác")
counter = {"nhua":0,"kim_loai":0,"giay":0,"khong_phai_rac":0}
cap, arduino = None, None

# === CAMERA (quét giống hệt camera_test.py) ===
def init_camera():
    global cap
    for cam_id in range(10):
        cam = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
        if not cam.isOpened():
            cam.release()
            continue
        ret, frame = cam.read()
        if not ret or frame is None or frame.size == 0:
            cam.release()
            continue
        cap = cam
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[CAM] ✅ Camera {cam_id} OK ({w}x{h})")
        print(f"[CAM] Frame test: shape={frame.shape}, size={frame.size}")
        return cam_id
    print("[CAM] ❌ KHÔNG TÌM THẤY CAMERA NÀO!")
    return -1

# === ARDUINO ===
def init_arduino():
    global arduino
    try:
        arduino = ArduinoController()
        if arduino.ser: print("[ARDUINO] ✅"); return True
    except: pass
    return False

def sort_by_class(label):
    if arduino and arduino.ser:
        threading.Thread(target=lambda: arduino.sort(label), daemon=True).start()

# === HTML ===
HTML_PAGE = (ROOT / "web/templates/index.html").read_text()

@app.get("/")
async def index():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    import shutil
    d = ROOT / "uploads"; d.mkdir(exist_ok=True)
    p = d / f"{int(time.time())}_{file.filename}"
    with open(p,"wb") as f: shutil.copyfileobj(file.file, f)
    frame = cv2.imread(str(p))
    if frame is None: return {"error":"Không đọc được ảnh"}
    h,w=frame.shape[:2]; s=min(640/w,480/h,1.0)
    if s<1: frame=cv2.resize(frame,(int(w*s),int(h*s)))
    results=yolo_model(frame,verbose=False,conf=0.25,iou=0.45)
    dets=[]
    if len(results[0].boxes)>0:
        for box in results[0].boxes:
            c=int(box.cls[0]); f=float(box.conf[0]); xy=box.xyxy[0].tolist()
            dets.append({"label":CLASS_NAMES[c] if c<len(CLASS_NAMES) else "unknown","confidence":round(f,4),"bbox":[round(x,1) for x in xy]})
    _,b=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,70])
    return {"image":base64.b64encode(b).decode(),"detections":dets,"count":len(dets)}

@app.websocket("/ws")
async def ws_handler(ws: WebSocket):
    global counter
    await ws.accept()
    last_label, paused, last_sorted = "", False, ""
    while True:
        try:
            data = await asyncio.wait_for(ws.receive_text(), timeout=0.01)
            msg = json.loads(data); act = msg.get("action","")
            if act=="reset": counter={k:0 for k in counter}
            elif act=="pause": paused=msg.get("paused",False)
            elif act=="count":
                l=msg.get("label","")
                if l in counter and l!=last_label: last_label=l; counter[l]+=1; await ws.send_text(json.dumps({"counter":counter}))
        except asyncio.TimeoutError: pass
        
        if paused: await asyncio.sleep(0.1); continue
        if cap is None or not cap.isOpened():
            await asyncio.sleep(0.5); continue
        
        t0=time.time()
        r,frame=cap.read()
        if not r or frame is None:
            if not hasattr(ws_handler, '_err_count'): ws_handler._err_count=0
            ws_handler._err_count += 1
            if ws_handler._err_count == 1:
                print("[CAM] ⚠️  Không đọc được frame từ camera!")
            await asyncio.sleep(0.1); continue
        ws_handler._err_count = 0
        h,w=frame.shape[:2]; s=min(640/w,480/h,1.0)
        if s<1: frame=cv2.resize(frame,(int(w*s),int(h*s)))
        results=yolo_model(frame,verbose=False,conf=0.25,iou=0.45)
        label,conf,disp = "khong_phai_rac",0.0,"❌ KHÔNG PHẢI RÁC"
        cm={'nhua':(233,30,99),'kim_loai':(33,150,243),'giay':(76,175,80),'khong_phai_rac':(158,158,158)}
        dn={'nhua':'NHỰA','kim_loai':'KIM LOẠI','giay':'GIẤY','khong_phai_rac':'❌ KHÔNG PHẢI'}
        if len(results[0].boxes)>0:
            b=results[0].boxes; ci=int(b.cls[0]); cf=float(b.conf[0]); xy=b.xyxy[0].tolist()
            if cf>0.25 and ci<len(CLASS_NAMES):
                label=CLASS_NAMES[ci]; conf=cf; cr=cm.get(label,(158,158,158)); cb=(cr[2],cr[1],cr[0])
                disp=dn.get(label,label.upper())
                cv2.rectangle(frame,(int(xy[0]),int(xy[1])),(int(xy[2]),int(xy[3])),cb,2)
                cv2.putText(frame,f"{disp} ({cf:.1%})",(int(xy[0]),int(xy[1])-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,cb,2)
                # → GỬI LỆNH ARDUINO
                if label!=last_sorted and conf>0.4: last_sorted=label; sort_by_class(label)
        _,b=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,60])
        await ws.send_text(json.dumps({"image":base64.b64encode(b).decode(),"label":label,"label_display":disp,"confidence":round(conf,4),"counter":counter,"fps":round(1.0/max(time.time()-t0,0.001),1)}))

def get_lan_ip():
    """Lấy IP LAN thực (không phải 127.0.0.1)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

ARDUINO_PORT = "/dev/ttyACM0"

@app.get("/api/arduino")
async def arduino_status():
    try:
        if arduino and arduino.ser and arduino.ser.is_open:
            stat = arduino.ping()
            return {"connected": True, "port": ARDUINO_PORT, "status": stat}
    except: pass
    return {"connected": False, "port": ARDUINO_PORT}

if __name__ == "__main__":
    init_camera()
    arduino_ok = init_arduino()
    ip = get_lan_ip()
    print(f"\n{'='*60}")
    print(f"  🚀  SERVER DA SAN SANG!")
    print(f"  📱  Mo trinh duyet tren LAPTOP:")
    print(f"      👉 http://{ip}:8080")
    print(f"  🔌 Arduino: {'✅ Connected' if arduino_ok else '❌ Not found'}")
    print(f"{'='*60}\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
