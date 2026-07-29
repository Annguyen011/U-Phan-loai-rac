"""
ARDUINO CONTROL - Raspberry Pi 4 ↔ Arduino Uno via USB Serial
================================================================
Gửi lệnh SORT đến Arduino dựa trên kết quả AI phân loại.
"""

import serial, json, time, threading, os, glob
from pathlib import Path

ROOT = Path(__file__).parent.parent
BAUD = 115200
TIMEOUT = 1.0

def find_arduino_ports():
    """Quét tất cả port có thể là Arduino"""
    ports = []
    # Tất cả các port serial phổ biến trên Pi
    for pattern in ['/dev/ttyACM*', '/dev/ttyUSB*', '/dev/ttyAMA*']:
        ports.extend(glob.glob(pattern))
    # Lọc theo port thực tế
    return sorted(set(ports))

class ArduinoController:
    def __init__(self, port=None):
        self.port = port
        self.ser = None
        self.lock = threading.Lock()
        self.connect(port)
    
    def connect(self, port=None):
        """Tìm và kết nối Arduino"""
        if port:
            # Nếu port được chỉ định, thử kết nối trực tiếp
            if self._try_connect(port):
                return True
        
        # Tự động tìm
        ports = find_arduino_ports()
        print(f"[ARDUINO] 🔍 Quét {len(ports)} port: {ports}")
        
        for p in ports:
            if self._try_connect(p):
                return True
        
        print(f"[ARDUINO] ⚠️  Không tìm thấy Arduino trong {ports if ports else '/dev/ttyACM*,/dev/ttyUSB*,/dev/ttyAMA*'}")
        print(f"[ARDUINO] 💡 Kiểm tra: dây USB, quyền truy cập (sudo usermod -aG dialout $USER)")
        return False
    
    def _try_connect(self, port):
        """Thử kết nối tới 1 port"""
        if not os.path.exists(port):
            return False
        try:
            self.ser = serial.Serial(port, BAUD, timeout=TIMEOUT)
            self.port = port
            time.sleep(2)  # Arduino reset delay
            # Đọc boot message
            boot_msg = ""
            t0 = time.time()
            while time.time() - t0 < 1.5:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    if line:
                        boot_msg += line + " | "
            if boot_msg:
                print(f"[ARDUINO] ✅ Port {port} - Boot: {boot_msg[:80]}")
            else:
                print(f"[ARDUINO] ✅ Port {port} - Kết nối OK (không có boot message)")
            return True
        except Exception as e:
            print(f"[ARDUINO] ⚠️  Port {port} - Lỗi: {e}")
            self.ser = None
            return False
    
    def send(self, cmd: dict, wait_ack=True) -> dict:
        """Gửi JSON command, đợi ACK"""
        if self.ser is None:
            return {"ack": "ERROR", "msg": "not_connected"}
        
        with self.lock:
            try:
                msg = json.dumps(cmd) + "\n"
                self.ser.write(msg.encode())
                self.ser.flush()
                
                if not wait_ack:
                    return {"ack": "SENT"}
                
                # Đợi phản hồi
                t0 = time.time()
                while time.time() - t0 < TIMEOUT:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode().strip()
                        if line:
                            try:
                                return json.loads(line)
                            except json.JSONDecodeError:
                                pass
                
                return {"ack": "TIMEOUT"}
            except Exception as e:
                return {"ack": "ERROR", "msg": str(e)}
    
    def sort(self, label: str) -> dict:
        """Gửi lệnh SORT theo class AI đã nhận diện"""
        return self.send({"cmd": "SORT", "class": label})
    
    def ping(self) -> dict:
        return self.send({"cmd": "PING"})
    
    def status(self) -> dict:
        return self.send({"cmd": "STATUS"})
    
    def close(self):
        if self.ser:
            self.ser.close()

# Singleton
_arduino = None

def get_controller():
    global _arduino
    if _arduino is None:
        _arduino = ArduinoController()
    return _arduino

# Test
if __name__ == "__main__":
    print("=" * 50)
    print("  TEST ARDUINO CONTROLLER")
    print("=" * 50)
    ctrl = ArduinoController()
    if ctrl.ser:
        print(f"✅ Kết nối Arduino OK!")
        pong = ctrl.ping()
        print(f"   PING → {pong}")
        status = ctrl.status()
        print(f"   STATUS → {status}")
        print(f"\nTest SORT nhua:")
        result = ctrl.sort("nhua")
        print(f"   → {result}")
        time.sleep(1)
        print(f"Test SORT giay (không gạt):")
        result = ctrl.sort("giay")
        print(f"   → {result}")
        ctrl.close()
    else:
        print("❌ Không kết nối được Arduino")