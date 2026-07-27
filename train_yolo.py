"""
=============================================================================
TRAIN YOLOv11 NANO - State-of-the-Art Object Detection
=============================================================================
Model: YOLOv11n (Nano) - ~5.5MB, chạy mượt trên Raspberry Pi 4
Kiến trúc sư: Ultralytics (2025) - SOTA trong object detection

Cách dùng:
  1. Bỏ ảnh vào dataset/images/train/
     Đặt tên file theo format: <ten_class>_<so>.jpg
     Ví dụ: nhua_001.jpg, kim_loai_005.jpg, khong_phai_rac_010.jpg

  2. Train:
     python train_yolo.py

  3. Model sẽ lưu vào models/yolo_best.pt (chỉ cần train 1 lần)
     GUI sẽ tự load model này để phân loại
=============================================================================
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# ================================================================
# CONFIG
# ================================================================
MODEL_NAME = "yolo11n"  # YOLOv11 Nano (~5.5MB)
EPOCHS = 100
IMG_SIZE = 320  # Pi 4 optimized (vẫn đủ chính xác)
BATCH = 16
OUTPUT_MODEL = "models/yolo_best.pt"

CLASSES = {
    "nhua": 0,
    "kim_loai": 1,
    "giay": 2,
    "khong_phai_rac": 3,
}

DATA_YAML = "data.yaml"

print("=" * 60)
print("🚀 YOLOv11 NANO TRAINING PIPELINE")
print(f"   Model:     {MODEL_NAME}")
print(f"   Epochs:    {EPOCHS}")
print(f"   Img Size:  {IMG_SIZE}")
print(f"   Classes:   {len(CLASSES)} ({list(CLASSES.keys())})")
print("=" * 60)


# ================================================================
# STEP 1: Auto-label images (YOLO format)
# ================================================================
def auto_label_dataset():
    """
    Tự động tạo labels YOLO format từ CẤU TRÚC THƯ MỤC:
    
    dataset/images/train/
        nhua/               # Ảnh chai nhựa, túi nilon (tên gì cũng đc)
            hinh_1.jpg
            anh_bat_ky.png
        kim_loai/           # Ảnh lon, vỏ hộp
            lon_coca.jpg
        giay/               # Ảnh giấy, bìa carton
            giay_viet.png
        khong_phai_rac/     # Ảnh tay, bút, đồ khác
            tay_1.jpg
    
    Mỗi ảnh được tự động gán label = class_id của thư mục chứa nó.
    Ảnh tên GÌ CŨNG ĐƯỢC, không cần chứa tên class.
    """
    train_dir = Path("dataset/images/train")
    
    # Đảm bảo các thư mục class tồn tại
    for class_name in CLASSES.keys():
        class_dir = train_dir / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo thư mục labels
    labels_dir = Path("dataset/labels/train")
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    labeled_count = 0
    total_images = 0
    
    # Duyệt từng thư mục class
    for class_name, class_id in CLASSES.items():
        class_dir = train_dir / class_name
        if not class_dir.exists():
            print(f"  ⚠️  Thư mục {class_dir} không tồn tại, đã tạo.")
            class_dir.mkdir(parents=True, exist_ok=True)
            continue
        
        # Lấy tất cả ảnh trong thư mục
        images = (list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.jpeg")) + 
                  list(class_dir.glob("*.png")) + list(class_dir.glob("*.JPG")) +
                  list(class_dir.glob("*.PNG")) + list(class_dir.glob("*.bmp")))
        
        if not images:
            print(f"  ⚠️  Không có ảnh trong {class_dir}/ - cần ít nhất 1 ảnh!")
            continue
        
        print(f"\n  📁 {class_name}/ ({class_id}): {len(images)} ảnh")
        total_images += len(images)
        
        for img_path in images:
            # Đọc ảnh để lấy kích thước
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"     ⚠️  Không đọc được: {img_path.name}")
                continue
            h, w = img.shape[:2]
            
            # Tạo label YOLO format (full image = 1 object)
            label_line = f"{class_id} 0.5 0.5 1.0 1.0"
            
            # Lưu label file
            label_path = labels_dir / img_path.parent.name / f"{img_path.stem}.txt"
            label_path.parent.mkdir(parents=True, exist_ok=True)
            with open(label_path, "w") as f:
                f.write(label_line + "\n")
            
            labeled_count += 1
    
    print(f"\n[OK] Đã auto-label: {labeled_count}/{total_images} ảnh thành công")
    
    # Cập nhật data.yaml
    yaml_content = f"""# YOLOv11 Dataset Config
path: {Path('.').resolve() / 'dataset'}

train: images/train
val: images/train

nc: {len(CLASSES)}
names:
"""
    for name, idx in CLASSES.items():
        yaml_content += f"  {idx}: {name}\n"
    
    with open(DATA_YAML, "w") as f:
        f.write(yaml_content)
    
    print(f"[OK] Đã cập nhật {DATA_YAML}")
    return True


# ================================================================
# STEP 2: Train YOLOv11 Nano
# ================================================================
def train_model():
    """Train YOLOv11n với dataset đã có"""
    
    if not Path(DATA_YAML).exists():
        print("[ERR] Không tìm thấy data.yaml")
        return None
    
    # Tải pretrained model (nano)
    print(f"\n📥 Đang tải {MODEL_NAME}.pt (pretrained weights)...")
    model = YOLO(f"{MODEL_NAME}.pt")  # Tự download nếu chưa có
    
    # Train
    print(f"\n🎯 BẮT ĐẦU TRAINING ({EPOCHS} epochs)...")
    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        name="yolo_waste",
        exist_ok=True,
        patience=20,       # Early stopping
        lr0=0.001,         # Learning rate khởi tạo
        lrf=0.002,         # Final learning rate = lr0 * lrf
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        augment=True,       # Data augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,       # Random rotation
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,         # Mosaic augmentation
        mixup=0.2,          # MixUp augmentation
        copy_paste=0.1,     # Copy-paste augmentation
        device="cpu",       # CPU training (an toàn cho mọi máy)
        workers=4,
        project="models",
    )
    
    # Save best model vào OUTPUT_MODEL (xóa file cũ trước)
    best_path = Path("models/yolo_waste/weights/best.pt")
    save_path = Path(OUTPUT_MODEL)
    
    # Xóa model cũ nếu có
    if save_path.exists():
        save_path.unlink()
        print(f"\n🗑️  Đã xóa model cũ: {OUTPUT_MODEL}")
    
    if best_path.exists():
        os.makedirs("models", exist_ok=True)
        import shutil
        shutil.copy(str(best_path), OUTPUT_MODEL)
        print(f"✅ Model mới đã lưu vào: {OUTPUT_MODEL}")
        print(f"   Kích thước: {os.path.getsize(OUTPUT_MODEL) / (1024*1024):.1f} MB")
    else:
        # Fallback: tìm last.pt
        last_path = Path("models/yolo_waste/weights/last.pt")
        if last_path.exists():
            import shutil
            shutil.copy(str(last_path), OUTPUT_MODEL)
            print(f"\n✅ Model mới đã lưu vào: {OUTPUT_MODEL} (last epoch)")
        else:
            print(f"\n⚠️  KHÔNG TÌM THẤY model đã train! Giữ lại model cũ.")
    
    # Xóa thư mục train tạm để tiết kiệm dung lượng
    train_dir = Path("models/yolo_waste")
    if train_dir.exists():
        import shutil
        shutil.rmtree(str(train_dir), ignore_errors=True)
        print(f"🗑️  Đã xóa thư mục train tạm: models/yolo_waste")
    
    # Validate
    print("\n📊 Đánh giá model...")
    metrics = model.val(data=DATA_YAML)
    
    return model


# ================================================================
# STEP 3: Export to NCNN (tối ưu cho Raspberry Pi 4)
# ================================================================
def export_model():
    """Export model sang các format tối ưu cho Pi 4"""
    if not Path(OUTPUT_MODEL).exists():
        print("[ERR] Chưa có model! Train truớc đã.")
        return
    
    model = YOLO(OUTPUT_MODEL)
    
    print("\n📦 Exporting model...")
    
    # Export ONNX (dùng cho ONNX Runtime - nhanh nhất)
    try:
        model.export(format="onnx", imgsz=IMG_SIZE, simplify=True)
        print("  ✅ ONNX exported")
    except Exception as e:
        print(f"  ⚠️ ONNX failed: {e}")
    
    # Export TFLite (cho Raspberry Pi 4)
    try:
        model.export(format="tflite", imgsz=IMG_SIZE, int8=False)
        print("  ✅ TFLite exported")
    except Exception as e:
        print(f"  ⚠️ TFLite failed: {e}")
    
    # Export NCNN (siêu nhẹ, nhanh nhất trên Pi 4 nếu có Vulkan)
    try:
        model.export(format="ncnn", imgsz=IMG_SIZE)
        print("  ✅ NCNN exported")
    except Exception as e:
        print(f"  ⚠️ NCNN failed: {e}")


# ================================================================
# MAIN
# ================================================================
def main():
    global EPOCHS  # Phải đặt global TRƯỚC khi dùng EPOCHS
    
    import argparse
    
    parser = argparse.ArgumentParser(description="YOLOv11 Nano Training")
    parser.add_argument("--auto_label", action="store_true", help="Tự động tạo labels")
    parser.add_argument("--train", action="store_true", help="Train model")
    parser.add_argument("--export", action="store_true", help="Export model")
    parser.add_argument("--all", action="store_true", help="Auto-label + Train + Export")
    parser.add_argument("--epochs", type=int, default=EPOCHS, help="Số epochs")
    
    args = parser.parse_args()
    
    # Default: run all
    if not any([args.auto_label, args.train, args.export, args.all]):
        args.all = True
    
    EPOCHS = args.epochs
    
    # 1. Auto-label
    if args.auto_label or args.all:
        if not auto_label_dataset():
            print("\n❌ Không có ảnh để train. Vui lòng bỏ ảnh vào dataset/images/train/")
            print("   Đặt tên: nhua_001.jpg, kim_loai_001.jpg, giay_001.jpg, khong_phai_rac_001.jpg")
            return
    
    # 2. Train
    if args.train or args.all:
        model = train_model()
        if model is None:
            return
    
    # 3. Export
    if args.export or args.all:
        export_model()
    
    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT!")
    print(f"   Model:     {OUTPUT_MODEL}")
    print(f"   Chạy GUI:  python gui_webcam.py")
    print("=" * 60)


if __name__ == "__main__":
    main()