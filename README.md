# 🗑️ AI Phân Loại Rác Thải

> **YOLOv11 Nano** + **Raspberry Pi 4** + **Webcam USB** → **Web UI Real-time**

## 📦 Cấu Trúc Dự Án

```
U-Phan-loai-rac/
│
├── src/                    # 🧠 Mã nguồn Python
│   ├── server.py           #   🌐 Web server (FastAPI + YOLO)
│   ├── train_yolo.py       #   🎓 Training pipeline
│   └── camera_test.py      #   📷 Test webcam
│
├── web/                    # 🌍 Giao diện Web
│   └── templates/
│       └── index.html      #   🖥️ HTML + JS + CSS
│
├── config/                 # ⚙️ Cấu hình
│   └── data.yaml           #   📋 Config dataset YOLO
│
├── models/                 # 🤖 Model AI
│   └── yolo11n.pt          #   🧠 YOLOv11 Nano pretrained
│
├── data/                   # 📂 Dữ liệu
│   └── dataset/
│       ├── images/
│       │   └── train/
│       │       ├── nhua/          # 📁 Ảnh chai nhựa
│       │       ├── kim_loai/      # 📁 Ảnh lon kim loại
│       │       ├── giay/          # 📁 Ảnh giấy
│       │       └── khong_phai_rac/# 📁 Ảnh đồ không phải rác
│       └── labels/
│           └── train/             # 🏷️ Labels YOLO (tự động sinh)
│
├── captures/               # 📸 Ảnh chụp từ webcam
├── uploads/                # 📤 Ảnh upload từ laptop
├── scripts/                # 📜 Scripts tiện ích (mở rộng)
├── docs/                   # 📚 Tài liệu (mở rộng)
│
├── run.sh                  # 🚀 Chạy server
├── setup.sh                # ⚙️ Cài đặt (sudo)
└── README.md               # 📖 Hướng dẫn
```

## 🚀 Cách Dùng

### 🔴 Raspberry Pi 4:

```bash
# Lần đầu: Cài thư viện (sudo)
sudo ./setup.sh

# Mỗi ngày: Chạy server
./run.sh
```

### 🟢 Laptop (cùng WiFi):

```bash
Chrome → http://raspberrypi.local:8080
```

## 🎯 Tính Năng

| Tính năng | Mô tả |
|-----------|-------|
| 📷 **Webcam Real-time** | AI phân loại liên tục |
| 📤 **Upload Ảnh** | Test AI không cần webcam |
| 📊 **Bộ Đếm** | Đếm số lượng nhựa/giấy/kim loại |
| 🎓 **Train AI** | Train với ảnh riêng |

## 📊 Kiến Trúc

```
Webcam USB → Raspberry Pi 4 → YOLOv11 Nano → WebSocket → Laptop Browser
                                ↓
                           FastAPI Server
```

Yêu cầu: Python 3.8+, Raspberry Pi 4 (2GB+ RAM), Webcam UVC