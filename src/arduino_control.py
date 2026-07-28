"""
ARDUINO CONTROL - Raspberry Pi 4 ↔ Arduino Uno via USB Serial
================================================================
Gửi lệnh SORT đến Arduino dựa trên kết quả AI phân loại.
"""

import serial, json, time, threading, os
from pathlib import Path

ROOT = Path(__file__).parent.parent
ARDUINO_PORT = "/dev/ttyACM0"
BAUD = 115200
TIMEOUT = 1.0

class ArduinoController:
    def __init__(self, port=ARDUINO_PORT):
        self.port = port
        self.ser = None
        self.lock = threading.Lock()
        self.connect()
    
    def connect(self):
        if not os.path.exists(self.port):
            print(f"[ARDUINO] ⚠️  Không tìm thấy {self.port}")
            return False
        try:
            self.ser = serial.Serial(self.port, BAUD, timeout=TIMEOUT)
            time.sleep(1)  # Arduino reset delay
            # Boot ack
            if self.ser.in_waiting:
                line = self.ser.readline().decode().strip()
                if line: print(f"[ARDUINO] Boot: {line}")
            return True
        except Exception as e:
            print(f"[ARDUINO] ❌ Lỗi kết nối: {e}")
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