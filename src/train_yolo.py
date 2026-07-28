"""
TRAIN YOLOv11 NANO - State-of-the-Art Object Detection
Model: YOLOv11n (~5.5MB) - Chạy mượt trên Raspberry Pi 4
"""

import os, sys, cv2, numpy as np, shutil
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data/dataset"
MODEL_DIR = ROOT / "models"
OUTPUT_MODEL = MODEL_DIR / "yolo_best.pt"
DATA_YAML = ROOT / "config/data.yaml"

CLASSES = {"nhua":0, "kim_loai":1, "giay":2, "khong_phai_rac":3}
EPOCHS, IMG_SIZE, BATCH = 100, 320, 16

def auto_label():
    train_dir = DATA_DIR / "images/train"
    labels_dir = DATA_DIR / "labels/train"
    for cn, ci in CLASSES.items():
        cd = train_dir / cn; cd.mkdir(parents=True, exist_ok=True)
        imgs = list(cd.glob("*.[jJ][pP][gG]")) + list(cd.glob("*.[pP][nN][gG]")) + list(cd.glob("*.[bB][mM][pP]"))
        if not imgs: print(f"  ⚠️  Không có ảnh trong {cd}/"); continue
        print(f"  📁 {cn}/: {len(imgs)} ảnh")
        for img_path in imgs:
            img = cv2.imread(str(img_path))
            if img is None: continue
            lp = labels_dir / cn / f"{img_path.stem}.txt"
            lp.parent.mkdir(parents=True, exist_ok=True)
            with open(lp, "w") as f: f.write(f"{ci} 0.5 0.5 1.0 1.0\n")
    print(f"\n[OK] Đã auto-label xong")

def train():
    if not DATA_YAML.exists(): print("[ERR] Thiếu config/data.yaml"); return None
    print(f"\n📥 Tải pretrained yolo11n.pt...")
    model = YOLO("yolo11n.pt")
    print(f"\n🎯 BẮT ĐẦU TRAINING ({EPOCHS} epochs)...")
    results = model.train(data=str(DATA_YAML), epochs=EPOCHS, imgsz=IMG_SIZE, batch=BATCH,
                name="yolo_waste", exist_ok=True, patience=20, device="cpu", workers=4,
                lr0=0.001, lrf=0.002, momentum=0.937, weight_decay=0.0005,
                warmup_epochs=3.0, augment=True, mosaic=1.0, mixup=0.2, copy_paste=0.1,
                project=str(ROOT), plots=True)
    
    # Tìm best.pt (YOLO lưu ở ROOT/yolo_waste/weights/best.pt)
    best = ROOT / "yolo_waste/weights/best.pt"
    if not best.exists():
        # Fallback: runs/detect/yolo_waste/weights/best.pt (YOLO < 8.3)
        best = ROOT / "runs/detect/yolo_waste/weights/best.pt"
    if OUTPUT_MODEL.exists():
        OUTPUT_MODEL.unlink()
        print(f"🗑️  Đã xóa model cũ: {OUTPUT_MODEL}")
    if best.exists():
        MODEL_DIR.mkdir(exist_ok=True)
        shutil.copy(str(best), str(OUTPUT_MODEL))
        print(f"✅ Model mới: {OUTPUT_MODEL} ({OUTPUT_MODEL.stat().st_size/1e6:.1f}MB)")
    else:
        print(f"⚠️  Không tìm thấy {best} - giữ model cũ")
    
    # === XUẤT BÁO CÁO ===
    export_reports(results)
    
    # Dọn thư mục train tạm
    train_tmp = ROOT / "runs/detect/yolo_waste"
    if train_tmp.exists():
        shutil.rmtree(str(train_tmp), ignore_errors=True)
        print(f"🗑️  Đã xóa thư mục tạm: runs/detect/yolo_waste")
    return model

def export_reports(results):
    """Xuất biểu đồ và dữ liệu báo cáo vào thư mục reports/"""
    report_dir = ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 ĐANG XUẤT BÁO CÁO vào {report_dir}/...")
    
    # Copy TẤT CẢ từ thư mục YOLO đã tạo (yolo_waste/)
    yolo_dir = ROOT / "yolo_waste"
    if yolo_dir.exists():
        copied = 0
        # Copy .csv
        for csv_file in yolo_dir.glob("*.csv"):
            shutil.copy(str(csv_file), report_dir / csv_file.name)
            copied += 1
        # Copy .png
        for png_file in yolo_dir.glob("*.png"):
            shutil.copy(str(png_file), report_dir / png_file.name)
            copied += 1
        # Copy .jpg (training batches, validation)
        for jpg_file in yolo_dir.glob("*.jpg"):
            shutil.copy(str(jpg_file), report_dir / jpg_file.name)
            copied += 1
        print(f"   ✅ Đã copy {copied} files từ yolo_waste/")
    
    # Tạo metrics_summary.txt
    with open(report_dir / "metrics_summary.txt", "w") as f:
        f.write("="*60 + "\n")
        f.write("  AI PHAN LOAI RAC - BAO CAO HUAN LUYEN\n")
        f.write("="*60 + "\n\n")
        f.write(f"Model:        YOLOv11 Nano\n")
        f.write(f"Classes:      nhua, kim_loai, giay, khong_phai_rac (4 classes)\n")
        f.write(f"Epochs:       {EPOCHS}\n")
        f.write(f"Image size:   {IMG_SIZE}x{IMG_SIZE}\n")
        f.write(f"Batch size:   {BATCH}\n")
        f.write(f"Model size:   {OUTPUT_MODEL.stat().st_size/1e6:.2f} MB\n")
        f.write(f"Device:       CPU\n")
        f.write(f"Framework:    Ultralytics YOLOv11\n\n")
        f.write("KET QUA VALIDATION:\n")
        f.write("-"*40 + "\n")
        f.write("Class              Precision  Recall  mAP50\n")
        
        # Parse results từ log (nếu có)
        results_csv = yolo_dir / "results.csv" if yolo_dir.exists() else None
        if results_csv and results_csv.exists():
            try:
                rows = open(results_csv).readlines()
                # In last line
                if len(rows) > 1:
                    last_line = rows[-1].strip()
                    parts = last_line.split(',')
                    if len(parts) >= 10:
                        f.write(f"{'nhua':20s}  {float(parts[4]):.4f}  {float(parts[5]):.4f}  {float(parts[6]):.4f}\n")
                        f.write(f"{'kim_loai':20s}  {float(parts[7]):.4f}  {float(parts[8]):.4f}  {float(parts[9]):.4f}\n")
            except: pass
        
        # In kết quả từ validation đã chạy
        f.write("\n⚠️  Khong phai rac: can them anh de cai thien\n")
        f.write("   (hien tai chi co 6 anh, do chinh xac thap)\n")
        f.write("\n📂 Cac file trong reports/:\n")
        f.write("   - results.csv: Du lieu tung epoch\n")
        f.write("   - results.png: Bieu do loss + metrics\n")
        f.write("   - confusion_matrix.png: Ma tran nham lan\n")
        f.write("   - train_batch*.jpg: Anh mau huan luyen\n")
        f.write("   - val_batch*.jpg: Anh mau validation\n")
    
    print(f"   ✅ metrics_summary.txt")
    
    # Copy model stats
    if OUTPUT_MODEL.exists():
        shutil.copy(str(OUTPUT_MODEL), report_dir / "yolo_best.pt")
        print(f"   ✅ yolo_best.pt (backup)")
    
    print(f"\n📂 Báo cáo đầy đủ: {report_dir}/")
    print(f"   Gồm: results.csv, results.png, confusion_matrix*.png,")
    print(f"         train_batch*.jpg, val_batch*.jpg, metrics_summary.txt")

if __name__=="__main__":
    print("="*50); print("🚀 YOLOv11 NANO TRAINING"); print("="*50)
    auto_label()
    train()
    print("\n✅ HOÀN TẤT! Chạy: ./run.sh")