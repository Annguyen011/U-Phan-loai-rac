import sys, os, time, asyncio, json, base64, cv2, numpy as np,socket
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse
import uvicorn

# Thêm thư mục gốc vào path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, '/var/data/python/bin')

from ultralytics import YOLO

# === CONFIG ===
MODEL_DIR = ROOT / "models"
DATA_DIR = ROOT / "data/dataset"
MODEL_PATH = MODEL_DIR / "yolo_best.pt"
if not MODEL_PATH.exists():
    print("⚠️  Dùng pretrained yolo11n.pt")
    MODEL_PATH = ROOT / "yolo11n.pt"

print(f"📥 Load YOLO: {MODEL_PATH}")
yolo_model = YOLO(str(MODEL_PATH))
CLASS_NAMES = list(yolo_model.names.values())
print(f"   Classes: {len(CLASS_NAMES)}")

app = FastAPI(title="AI Phân Loại Rác")
counter = {"nhua": 0, "kim_loai": 0, "giay": 0, "khong_phai_rac": 0}
cap = None

# === CAMERA ===
def init_camera():
    global cap
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("[CAM] ✅ Camera 0 OK")
        return 0
    print("[CAM] ❌ Không mở được camera!")
    return -1

# === HTML (giao diện web) ===
HTML_PAGE = open(ROOT / "web/templates/index.html").read()

@app.get("/")
async def index():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    import shutil
    save_dir = ROOT / "uploads"; save_dir.mkdir(exist_ok=True)
    path = save_dir / f"{int(time.time())}_{file.filename}"
    with open(path, "wb") as f: shutil.copyfileobj(file.file, f)

    frame = cv2.imread(str(path))
    if frame is None: return {"error": "Không đọc được ảnh"}
    h,w = frame.shape[:2]
    s = min(640/w, 480/h, 1.0)
    if s<1: frame = cv2.resize(frame, (int(w*s), int(h*s)))
    results = yolo_model(frame, verbose=False, conf=0.25, iou=0.45)
    detections=[]
    if len(results[0].boxes)>0:
        for box in results[0].boxes:
            c=int(box.cls[0]); f=float(box.conf[0]); xy=box.xyxy[0].tolist()
            lbl=CLASS_NAMES[c] if c<len(CLASS_NAMES) else "unknown"
            detections.append({"label":lbl,"confidence":round(f,4),"bbox":[round(x,1) for x in xy]})
    _, b = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY,70])
    return {"image":base64.b64encode(b).decode(),"detections":detections,"count":len(detections)}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global counter, cap
    await ws.accept()
    print("[WS] Client connected")
    last_label, paused = "", False
    try:
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=0.01)
                msg = json.loads(data); act = msg.get("action","")
                if act=="reset": counter={k:0 for k in counter}
                elif act=="capture" and cap and cap.isOpened():
                    r,f=cap.read()
                    if r:
                        (ROOT/"captures").mkdir(exist_ok=True)
                        cv2.imwrite(str(ROOT/f"captures/cap_{int(time.time())}.jpg"),f)
                elif act=="pause": paused=msg.get("paused",False)
                elif act=="count":
                    l=msg.get("label","")
                    if l in counter and l!=last_label: last_label=l; counter[l]+=1; await ws.send_text(json.dumps({"counter":counter}))
            except asyncio.TimeoutError: pass
            if paused or cap is None or not cap.isOpened(): await asyncio.sleep(0.1); continue

            t0=time.time()
            r,frame = cap.read()
            if not r: continue
            h,w=frame.shape[:2]
            s=min(640/w,480/h,1.0)
            if s<1: frame=cv2.resize(frame,(int(w*s),int(h*s)))
            results=yolo_model(frame,verbose=False,conf=0.25,iou=0.45)
            label,confidence,display_name = "khong_phai_rac",0.0,"❌ KHÔNG PHẢI RÁC"
            cm={'nhua':(233,30,99),'kim_loai':(33,150,243),'giay':(76,175,80),'khong_phai_rac':(158,158,158)}
            dn={'nhua':'NHỰA','kim_loai':'KIM LOẠI','giay':'GIẤY','khong_phai_rac':'❌ KHÔNG PHẢI'}
            if len(results[0].boxes)>0:
                b=results[0].boxes; ci=int(b.cls[0]); cf=float(b.conf[0]); xy=b.xyxy[0].tolist()
                if cf>0.25 and ci<len(CLASS_NAMES):
                    label=CLASS_NAMES[ci]; confidence=cf
                    cr=cm.get(label,(158,158,158)); cb=(cr[2],cr[1],cr[0])
                    display_name=dn.get(label,label.upper())
                    cv2.rectangle(frame,(int(xy[0]),int(xy[1])),(int(xy[2]),int(xy[3])),cb,2)
                    cv2.putText(frame,f"{display_name} ({cf:.1%})",(int(xy[0]),int(xy[1])-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,cb,2)
            _,b = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY,60])
            fps=1.0/max(time.time()-t0,0.001)
            await ws.send_text(json.dumps({"image":base64.b64encode(b).decode(),"label":label,"label_display":display_name,"confidence":round(confidence,4),"counter":counter,"fps":round(fps,1)}))
    except: pass

if __name__=="__main__":
    init_camera()
    print(f"\n{'='*50}")
    print("🚀 SERVER SẴN SÀNG!")
    print(f"   http://{socket.gethostname()}.local:8080")
    print(f"{'='*50}\n")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")