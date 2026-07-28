/*
 * arduino_firmware/arduino_firmware.ino
 * =====================================================================
 * FruitSorter — Arduino Slave Firmware v4.0 (CLASS-BASED SORTING)
 * =====================================================================
 * 
 * NEW v4.0 — CLASS-BASED SORTING:
 *   - Nhựa (plastic)  → Servo 1 gạt
 *   - Kim loại (metal) → Servo 2 gạt
 *   - Giấy (paper)     → KHÔNG GẠT (cho qua)
 *   - Không phải rác   → KHÔNG GẠT
 *
 * Protocol: JSON one-liner + '\n' @ 115200 baud
 *
 * Commands from Raspberry Pi:
 *   {"cmd":"SORT","class":"nhua"}       → Servo 1 gạt
 *   {"cmd":"SORT","class":"kim_loai"}   → Servo 2 gạt
 *   {"cmd":"SORT","class":"giay"}       → KHÔNG GẠT (bỏ qua)
 *   {"cmd":"SORT","class":"khong_phai_rac"} → KHÔNG GẠT
 *   {"cmd":"PING"}
 *   {"cmd":"STATUS"}
 *
 * =====================================================================
 * HOW TO FLASH:
 *   - LAPTOP: Mở Arduino IDE → mở file này → Ctrl+U (Upload)
 *   - PI 4:   arduino-cli compile --fqbn arduino:avr:uno &&
 *             arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno
 *   Kết nối: Cáp USB từ Arduino vào máy tính đang chạy AI
 *            (tốt nhất là Raspberry Pi vì Pi cần gửi lệnh qua Serial)
 * =====================================================================
 */

#include <Servo.h>
#include <ArduinoJson.h>

// ── Pin definitions ───────────────────────────────────────────────────────
#define PIN_IR1         2
#define PIN_IR2         3
#define PIN_SERVO1      9   // Servo 1: gạt NHỰA
#define PIN_SERVO2      10  // Servo 2: gạt KIM LOẠI
#define PIN_STATUS_LED  13

// ── Servo config ──────────────────────────────────────────────────────────
#define SERVO1_HOME  0     // Servo 1 home (nhựa)
#define SERVO2_HOME  0     // Servo 2 home (kim loại)
#define SWEEP_ANGLE  90    // Góc gạt (90°)
#define MAX_ANGLE    180   // Servo 180° (SG90/MG996R)
#define PULSE_MIN    500
#define PULSE_MAX    2500
#define SWEEP_MS     400   // Thời gian gạt
#define RETURN_MS    500   // Thời gian về home

// ── Serial ────────────────────────────────────────────────────────────────
#define SERIAL_BAUD  115200
char   serial_buffer[256];
uint8_t serial_buf_index = 0;

// ── Servo objects ─────────────────────────────────────────────────────────
Servo servo1, servo2;

// ── Servo state (non-blocking) ────────────────────────────────────────────
enum ServoPhase { IDLE, SWEEPING, RETURNING };

struct ServoState {
  ServoPhase phase = IDLE;
  uint32_t phase_start_ms = 0;
  uint8_t  pin;
};

ServoState s1, s2;

// ── Boot ──────────────────────────────────────────────────────────────────
uint32_t boot_ms = 0;

// ── Helper: map angle → microsecond pulse ────────────────────────────────
void write_servo_angle(Servo& srv, int angle) {
  long pulse = map(constrain(angle, 0, MAX_ANGLE), 0, MAX_ANGLE, PULSE_MIN, PULSE_MAX);
  srv.writeMicroseconds(pulse);
}

// ── Setup ─────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial) { ; }

  servo1.attach(PIN_SERVO1);
  servo2.attach(PIN_SERVO2);
  write_servo_angle(servo1, SERVO1_HOME);
  write_servo_angle(servo2, SERVO2_HOME);

  s1.pin = PIN_SERVO1;
  s2.pin = PIN_SERVO2;

  pinMode(PIN_STATUS_LED, OUTPUT);
  digitalWrite(PIN_STATUS_LED, LOW);

  boot_ms = millis();

  // Boot ack
  StaticJsonDocument<64> doc;
  doc["boot"] = "ok";
  doc["firmware"] = "FruitSorter-v4.0-class";
  serializeJson(doc, Serial);
  Serial.println();

  // Blink
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_STATUS_LED, HIGH); delay(100);
    digitalWrite(PIN_STATUS_LED, LOW);  delay(100);
  }
}

// ── Non-blocking servo state machine ──────────────────────────────────────
void check_servo(ServoState& state, Servo& srv, int home_angle) {
  uint32_t now = millis();

  if (state.phase == SWEEPING) {
    if ((now - state.phase_start_ms) >= SWEEP_MS) {
      // Sweep done → return home
      write_servo_angle(srv, home_angle);
      state.phase = RETURNING;
      state.phase_start_ms = now;
    }
  }
  else if (state.phase == RETURNING) {
    if ((now - state.phase_start_ms) >= RETURN_MS) {
      state.phase = IDLE;
      if (s1.phase == IDLE && s2.phase == IDLE) {
        digitalWrite(PIN_STATUS_LED, LOW);
      }
    }
  }
}

// ── Actuate servo (non-blocking) ──────────────────────────────────────────
void actuate_servo(ServoState& state, Servo& srv) {
  // Restart sweep even if already in progress
  write_servo_angle(srv, SWEEP_ANGLE);
  digitalWrite(PIN_STATUS_LED, HIGH);
  state.phase = SWEEPING;
  state.phase_start_ms = millis();
}

// ── Main loop ─────────────────────────────────────────────────────────────
void loop() {
  // 1) Service servo state machines
  check_servo(s1, servo1, SERVO1_HOME);
  check_servo(s2, servo2, SERVO2_HOME);

  // 2) Process incoming Serial commands
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serial_buf_index > 0) {
        serial_buffer[serial_buf_index] = '\0';
        handle_command(serial_buffer);
        serial_buf_index = 0;
      }
    }
    else if (serial_buf_index < sizeof(serial_buffer) - 1) {
      serial_buffer[serial_buf_index++] = c;
    }
    else {
      serial_buf_index = 0;
      while (Serial.available() > 0 && Serial.read() != '\n') { ; }
    }
  }
}

// ── Parse and dispatch commands ───────────────────────────────────────────
void handle_command(const char* raw) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, raw);
  if (err) {
    StaticJsonDocument<64> resp;
    resp["ack"] = "ERROR";
    resp["msg"] = "json_parse_fail";
    serializeJson(resp, Serial);
    Serial.println();
    return;
  }

  const char* cmd = doc["cmd"] | "";

  // ── SORT command (CLASS-BASED) ────────────────────────────────────────
  if (strcmp(cmd, "SORT") == 0) {
    const char* cls = doc["class"] | "";

    StaticJsonDocument<128> resp;
    resp["ack"] = "SORT_DONE";
    resp["class"] = cls;

    if (strcmp(cls, "nhua") == 0) {
      // Nhựa → Servo 1 gạt
      actuate_servo(s1, servo1);
      resp["servo"] = 1;
      resp["action"] = "sweep";
    }
    else if (strcmp(cls, "kim_loai") == 0) {
      // Kim loại → Servo 2 gạt
      actuate_servo(s2, servo2);
      resp["servo"] = 2;
      resp["action"] = "sweep";
    }
    else {
      // Giấy hoặc không phải rác → KHÔNG GẠT
      resp["servo"] = 0;
      resp["action"] = "pass_through";
    }

    resp["total_ms"] = SWEEP_MS + RETURN_MS;
    serializeJson(resp, Serial);
    Serial.println();
  }

  // ── PING command ─────────────────────────────────────────────────────
  else if (strcmp(cmd, "PING") == 0) {
    StaticJsonDocument<80> resp;
    resp["ack"] = "PONG";
    resp["uptime_s"] = (millis() - boot_ms) / 1000UL;
    serializeJson(resp, Serial);
    Serial.println();
  }

  // ── STATUS command ───────────────────────────────────────────────────
  else if (strcmp(cmd, "STATUS") == 0) {
    StaticJsonDocument<256> resp;
    resp["ack"] = "STATUS";
    resp["servo1_busy"] = (s1.phase != IDLE);
    resp["servo2_busy"] = (s2.phase != IDLE);
    resp["uptime_s"] = (millis() - boot_ms) / 1000UL;
    serializeJson(resp, Serial);
    Serial.println();
  }

  // ── Unknown command ──────────────────────────────────────────────────
  else {
    StaticJsonDocument<64> resp;
    resp["ack"] = "ERROR";
    resp["msg"] = "unknown_cmd";
    serializeJson(resp, Serial);
    Serial.println();
  }
}