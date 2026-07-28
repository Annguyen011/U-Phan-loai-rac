#!/bin/bash
# =============================================================================
# FLASH ARDUINO - Nap code vao Arduino Uno
# =============================================================================
# Cach 1: Tu LAPTOP → mo Arduino IDE → mo file → Ctrl+U (Don gian nhat)
# Cach 2: Tu PI 4 → chay script nay
# =============================================================================
cd "$(dirname "$0")/.."
INO_FILE="arduino_firmware/arduino_firmware.ino"

echo "============================================"
echo "  NAP CODE ARDUINO"
echo "============================================"
echo ""

# Kiểm tra Arduino đã kết nối chưa
if [ ! -e /dev/ttyACM0 ] && [ ! -e /dev/ttyUSB0 ]; then
    echo "❌ KHONG TIM THAY ARDUINO!"
    echo "   Cam USB tu Pi 4 vao Arduino truoc."
    echo ""
    echo "💡 Cach khac: Nap tu LAPTOP (de hon):"
    echo "   1. Mo Arduino IDE tren laptop"
    echo "   2. Mo file: $INO_FILE"
    echo "   3. Bam Ctrl+U de nap"
    exit 1
fi

PORT=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | head -1)
echo "✅ Found Arduino at $PORT"
echo ""

# Kiểm tra arduino-cli
if ! command -v arduino-cli &> /dev/null; then
    echo "❌ Chua cai arduino-cli. Dang cai..."
    sudo apt install -y arduino-cli 2>/dev/null || {
        curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
    }
fi

# Cài đặt core Arduino Uno
echo "📦 Cai dat Arduino Uno core..."
arduino-cli core install arduino:avr 2>/dev/null || true

# Cài thư viện cần thiết
echo "📦 Cai thu vien ArduinoJson..."
arduino-cli lib install ArduinoJson 2>/dev/null || true

# Compile
echo ""
echo "🔨 Dang bien dich..."
arduino-cli compile --fqbn arduino:avr:uno "$INO_FILE"
if [ $? -ne 0 ]; then
    echo "❌ Loi bien dich! Thu nap bang Arduino IDE tren laptop."
    exit 1
fi

# Upload
echo ""
echo "📤 Dang nap code..."
arduino-cli upload -p "$PORT" --fqbn arduino:avr:uno "$INO_FILE"
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "  ✅ NAP CODE THANH CONG!"
    echo "  Arduino ready! Chay: scripts/run.sh"
    echo "============================================"
else
    echo "❌ Loi nap code!"
fi