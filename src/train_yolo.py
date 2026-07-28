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
                project=str(ROOT), plots=True)  # plots=True = tạo biểu đồ
    
    # Tìm best.pt trong thư mục runs
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
    
    try:
        # 1. Confusion Matrix
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from sklearn.metrics import confusion_matrix, classification_report
        import pandas as pd
        
        # Load validation results
        model = YOLO(str(OUTPUT_MODEL)) if OUTPUT_MODEL.exists() else YOLO("yolo11n.pt")
        val_results = model.val(data=str(DATA_YAML), plots=True, save=False, verbose=False)
        
        # 2. Loss curves (từ results)
        if hasattr(results, 'results_dict'):
            df = pd.DataFrame(results.results_dict)
            df.to_csv(report_dir / "training_metrics.csv", index=False)
            print(f"   ✅ training_metrics.csv")
        else:
            # Tạo dummy data nếu không có
            epochs_list = range(1, EPOCHS+1)
            df = pd.DataFrame({'epoch': epochs_list})
            df.to_csv(report_dir / "training_metrics.csv", index=False)
            print(f"   ⚠️  training_metrics.csv (basic)")
        
        # 3. Export metrics summary
        with open(report_dir / "metrics_summary.txt", "w") as f:
            f.write(f"Model: YOLOv11 Nano\n")
            f.write(f"Classes: 4 (nhua, kim_loai, giay, khong_phai_rac)\n")
            f.write(f"Epochs trained: {EPOCHS}\n")
            f.write(f"Image size: {IMG_SIZE}x{IMG_SIZE}\n")
            f.write(f"Batch size: {BATCH}\n")
            f.write(f"Model saved to: {OUTPUT_MODEL}\n")
            f.write(f"Model size: {OUTPUT_MODEL.stat().st_size/1e6:.2f} MB\n")
            
            if hasattr(val_results, 'results_dict'):
                for k, v in val_results.results_dict.items():
                    f.write(f"{k}: {v}\n")
        
        print(f"   ✅ metrics_summary.txt")
        
        # 4. Copy training plots từ runs
        runs_dir = ROOT / "runs/detect/yolo_waste"
        if runs_dir.exists():
            import glob
            for img_file in runs_dir.glob("*.jpg"):
                shutil.copy(str(img_file), report_dir / img_file.name)
                print(f"   ✅ {img_file.name}")
            
            # Copy confusion matrix nếu có
            cm_path = runs_dir / "confusion_matrix.png"
            if cm_path.exists():
                shutil.copy(str(cm_path), report_dir / "confusion_matrix.png")
                print(f"   ✅ confusion_matrix.png")
        
        print(f"\n📂 Báo cáo đã lưu trong: {report_dir}/")
        print(f"   Gồm: *.csv, *.txt, *.jpg, confusion_matrix.png")
        
    except Exception as e:
        print(f"   ⚠️  Lỗi xuất báo cáo: {e}")

if __name__=="__main__":
    print("="*50); print("🚀 YOLOv11 NANO TRAINING"); print("="*50)
    auto_label()
    train()
    print("\n✅ HOÀN TẤT! Chạy: ./run.sh")