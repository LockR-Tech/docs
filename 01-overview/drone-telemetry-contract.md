# Hợp đồng telemetry drone — Pi trên drone → backend

Nguồn sự thật cho topic, payload và chữ ký giữa **Pi đi kèm trên drone** (`iot/drone-iot/`) và **order-service** (`DroneTelemetry*`). Tách hẳn khỏi [hợp đồng MQTT của tủ](mqtt-contract.md): topic riêng, kết nối riêng, không đi qua iot-service. Đổi bất kỳ thứ gì ở đây ⇒ sửa **cả hai phía** và test hai phía:

- backend: `order-service/src/test/java/…/order/service/DroneTelemetryMqttListenerTest.java`, `DroneTelemetryServiceTest.java`
- iot: `drone-iot/tests/test_telemetry.py`, `test_signing.py`

Phiên bản hợp đồng: **1** (2026-10-04). Trả lời câu hỏi Q3 của STATUS: drone nói **MAVLink** với Pi, Pi nói **MQTT** với backend.

## 1. Đường đi

```
Pixhawk 6C (ArduPilot) ──USB/MAVLink 2──> Pi 5 (drone-iot) ──MQTT 5 + TLS──> broker ──> order-service
                                                                                          ├─ đẩy chặng bay (DroneMissionProgressService)
                                                                                          ├─ vị trí ⇒ notification-service ⇒ STOMP /topic/deliveries/{orderId}/position
                                                                                          └─ pin ⇒ locker-service /internal/drones/telemetry
```

Pi **chỉ đọc** autopilot. Thứ duy nhất nó gửi xuống là `MAV_CMD_SET_MESSAGE_INTERVAL` (xin tần suất message). Không gửi heartbeat kiểu trạm mặt đất, không có lệnh arm, đổi mode, servo.

## 2. Topic

| Topic | QoS | Retained | Nội dung |
|---|---|---|---|
| `lockr/drones/{droneId}/telemetry` | 0 | không | số đo, mỗi giây một bản tin |
| `lockr/drones/{droneId}/status` | 1 | có | `online` khi Pi kết nối, `offline` khi tắt hoặc rớt mạng (Last Will) |

`droneId` = mã drone trên admin (`drone_units.code`), 1–50 ký tự chữ, số, `-`, `_`. Backend hiện chỉ nghe `lockr/drones/+/telemetry`; "drone còn tín hiệu" tính từ bản tin telemetry gần nhất (`app.drone.telemetry.live-window-seconds`, mặc định 15 giây), không dựa vào topic `status`.

Telemetry không gửi bù: Pi mất kết nối broker lúc nào thì bản tin lúc đó bị bỏ.

### 2.1 Telemetry

```json
{
  "schemaVersion": 1, "droneId": "DRONE-S550-01", "sequence": 42,
  "observedAt": "2026-10-04T08:25:35.946Z",
  "link":     { "mavlink": "connected", "heartbeatAgeMs": 642 },
  "position": { "lat": 10.8412345, "lng": 106.8098765, "relativeAltM": 25.34, "headingDeg": 87.5, "ageMs": 109, "stale": false },
  "gps":      { "fixType": 3, "satellites": 14, "ageMs": 109, "stale": false },
  "battery":  { "percent": 76, "voltageV": 15.83, "currentA": 12.5, "ageMs": 109, "stale": false },
  "velocity": { "groundSpeedMs": 6.23, "climbMs": -0.5, "ageMs": 109, "stale": false },
  "flight":   { "mode": "AUTO", "armed": true, "systemStatus": "ACTIVE", "ageMs": 642, "stale": false },
  "landed":   { "landedState": "IN_AIR", "ageMs": 109, "stale": false },
  "warnings": [ { "severity": "WARNING", "text": "PreArm: …", "at": 1791102683594 } ]
}
```

- `observedAt`: lúc Pi chụp số đo (UTC). Backend bỏ bản tin lệch giờ máy chủ quá `app.drone.telemetry.max-clock-skew-seconds` (120 giây) ⇒ **Pi phải đồng bộ NTP**.
- `link.mavlink`: `connected` · `heartbeat_lost` (cổng mở nhưng autopilot im quá 5 giây) · `disconnected` (không mở được cổng).
- Mỗi nhóm kèm `ageMs` (tuổi số đo) và `stale` (quá 5 giây chưa được làm mới, hoặc chưa từng nhận). Nhóm stale vẫn giữ giá trị cuối; backend **không dùng** nhóm stale.
- Giá trị autopilot báo "không biết" là `null`: toạ độ (0, 0), hướng 65535, số vệ tinh 255, pin −1, `landedState` UNDEFINED.
- `landed.landedState` ∈ `ON_GROUND | IN_AIR | TAKEOFF | LANDING | null` (MAVLink `EXTENDED_SYS_STATE`). Đây là căn cứ **duy nhất** để nói drone đang bay hay đã đáp — không suy từ `armed` hay độ cao.
- `gps.fixType` theo MAVLink `GPS_FIX_TYPE`; backend chỉ dùng toạ độ khi ≥ 3.
- `battery.voltageV` < 1 V (drone cấp điện qua USB, chưa cắm pin) ⇒ backend bỏ qua `percent`.

### 2.2 Status

```json
{ "schemaVersion": 1, "droneId": "DRONE-S550-01", "state": "online", "at": 1791102683594 }
```

## 3. Chữ ký

Broker mặc định là broker công khai (SEC-04) nên ai cũng ghi được vào topic. Backend chỉ nhận bản tin có chữ ký đúng, gửi kèm dưới dạng **MQTT 5 user property `sig`**:

```
deviceKey = hex(HMAC-SHA256(DRONE_TELEMETRY_SECRET, "lockr-drone:" + droneId))
sig       = hex(HMAC-SHA256(deviceKey, topic + "\n" + payload))
```

Mỗi Pi chỉ giữ `deviceKey` của drone mình (`DEVICE_KEY` trong `.env`, quyền 600); khoá gốc chỉ nằm ở backend. Lộ khoá một Pi không giả được drone khác. Vector kiểm chéo hai ngôn ngữ nằm trong `test_signing.py` và `DroneTelemetryMqttListenerTest`.

Bật mà không có `DRONE_TELEMETRY_SECRET` lẫn tài khoản broker riêng ⇒ order-service **từ chối nghe**.

## 4. Backend làm gì với telemetry

Chỉ áp dụng cho mission đang bay của đơn **STANDARD** có `drone_code = droneId`. Đơn DEMO vẫn do bộ giả lập chạy.

| Chặng | Điều kiện (bản tin còn mới) |
|---|---|
| LAUNCHING → DEPARTED | `landedState` ∈ IN_AIR / TAKEOFF / LANDING |
| DEPARTED → EN_ROUTE | cách tủ gửi ≥ `departed-distance-m` (30 m) |
| EN_ROUTE → APPROACHING | cách tủ nhận ≤ `approach-distance-m` (150 m) |
| APPROACHING → ARRIVED | `landedState = ON_GROUND` và cách tủ nhận ≤ `arrival-radius-m` (30 m) |
| ARRIVED → hàng vào ô | **không tự động** — điều phối viên xác nhận (`POST …/advance`); telemetry không biết kiện đã vào ô |

Tuyến ngắn thì ngưỡng co theo chiều dài tuyến. Tủ thiếu toạ độ hoặc GPS chưa khoá ⇒ chỉ chặng cất cánh tự đẩy; điều phối viên vẫn xác nhận tay được mọi chặng khi mất tín hiệu. Mỗi lần đẩy ghi nhật ký hành trình "Telemetry drone {mã}: …".

Ngoài ra: vị trí thật phát lên STOMP tối đa 1 lần/giây (ETA = quãng còn lại ÷ tốc độ đo được); pin thật đồng bộ về `drone_units.battery_percent` khi đổi, tối đa 30 giây/lần; read model trả `liveTracking` để app chỉ mời xem bản đồ khi có tín hiệu.

## 5. Biến môi trường

**order-service** (`.env` của VM, qua `docker-compose.yml`):

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `APP_DRONE_TELEMETRY_ENABLED` | bật nghe telemetry | `false` |
| `DRONE_TELEMETRY_SECRET` | khoá gốc ký bản tin (**secret**) | trống |
| `DRONE_MQTT_BROKER_URL` | broker | `MQTT_BROKER_URL` của iot-service, rồi HiveMQ công khai |
| `DRONE_MQTT_USERNAME`, `DRONE_MQTT_PASSWORD` | tài khoản khi dùng broker riêng (**secret**) | trống |

**Pi** (`~/lockr-drone/.env`): `DRONE_ID`, `MAVLINK_PORT` (đường dẫn `/dev/serial/by-id/…`), `MAVLINK_BAUD`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_TLS`, `DEVICE_KEY` (**secret**); tuỳ chọn `MQTT_TRANSPORT`, `MQTT_WS_PATH`, `MQTT_USERNAME`, `MQTT_PASSWORD`. Mẫu: `iot/drone-iot/.env.example`.

Cấp khoá cho một drone mới: tính `deviceKey` từ khoá gốc theo công thức § 3 (`lockr_drone.signing.device_key`) rồi ghi vào `.env` của Pi đó.

## 6. Chưa có

- Broker riêng chưa cấp tài khoản/ACL cho topic `lockr/drones/…` (`infra/mosquitto` mới chỉ có tủ) — khi bật broker riêng phải bổ sung trước khi chuyển drone sang.
- Chưa có lệnh từ backend xuống drone, chưa có topic `events`.
- Hạ cánh sai chỗ, mất tín hiệu giữa chuyến, quay về trạm: backend chưa có trạng thái FAILED/DELAYED (F1-G04) nên chỉ dừng đẩy chặng.
