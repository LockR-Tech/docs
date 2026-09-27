# Hợp đồng MQTT — backend ↔ tủ

Nguồn sự thật cho mọi topic và payload giữa **iot-service** (backend) và **bộ điều khiển tủ** (Pi chạy `iot/main.py`, hoặc `iot/simulate_demo_cabinet.py`). Lý do chọn: [ADR-0008](../adr/0008-hop-dong-mqtt-backend-tu.md). Đổi bất kỳ thứ gì ở đây ⇒ sửa **cả hai phía** và contract test ở cả hai repo:

- backend: `iot-service/src/test/java/…/iot/service/LockerMqttServiceTest.java`, `GatewayProvisioningServiceTest.java` ([backend#33](https://github.com/LockR-Tech/backend/pull/33))
- iot: `tests/test_mqtt_contract.py` ([iot#9](https://github.com/LockR-Tech/iot/pull/9))
- giao diện gán thiết bị: [frontend#22](https://github.com/LockR-Tech/frontend/pull/22)

Phiên bản hợp đồng: **1** (2026-09-27).

## 1. Định danh

| Tên | Ý nghĩa | Ai đặt |
|---|---|---|
| `lockerId` | id số của **tủ** trong locker-service (`lockers.id`) | admin tạo tủ |
| `boxId` | id số của **ô** (`locker_boxes.id`), duy nhất toàn hệ thống | admin tạo ô |
| `boxNumber` | số ô in trên cửa, bắt đầu từ 1 | admin |
| `slotIndex` | vị trí ô trên bộ điều khiển, bắt đầu từ 0 — **luôn bằng `boxNumber − 1`** | iot-service tính |
| `mac` | MAC `wlan0` của Pi, chữ HOA, có dấu `:` (ví dụ `2C:CF:67:DB:C5:C3`) | Pi |

Pi đổi `slotIndex` ra chân phần cứng: `GPIO_RELAY_PINS[slotIndex]` và `GPIO_DOOR_PINS[slotIndex]` (GPIO), hoặc lệnh `T<slotIndex>` (Arduino). Đấu lệch thứ tự thì đổi thứ tự hai danh sách đó trong `.env` của Pi, **không** đánh số lại ô trên admin.

## 2. Vận hành — `cabinet/{lockerId}/…`

### 2.1 Backend → tủ (QoS 1)

**Mở ô** — `cabinet/{lockerId}/command/open`

```json
{ "commandId": "5f0c…", "boxId": 12, "box_id": 12, "slotIndex": 3, "action": "OPEN", "timeout": 15 }
```

- `timeout`: số giây cửa được phép mở, lấy từ `app.iot.door-open-timeout-seconds`. Pi hiện chưa dùng.
- `box_id`: bản sao của `boxId` cho giả lập cũ; sẽ bỏ ở phiên bản 2.
- Nếu iot-service không tra được `boxNumber` thì payload **không có** `slotIndex`. Khi đó Pi tra `boxId` trong sơ đồ đã setup (§ 3); không tra được thì trả `FAILED / UNKNOWN_SLOT`.

**Đồng bộ trạng thái ô** — `cabinet/{lockerId}/command/sync` (không cần phản hồi)

```json
{ "boxId": 12, "state": "OCCUPIED", "orderId": 99 }
```

`state` ∈ `RESERVED | OCCUPIED | AVAILABLE | FAULT`; `orderId` có thể thiếu. Không kèm `slotIndex` để luồng đặt chỗ khỏi thêm một lời gọi sang locker-service; Pi vẫn chấp nhận nếu sau này có.

**Đóng ô** — `cabinet/{lockerId}/command/close`: dành sẵn; backend hiện chưa gửi. Payload và kết quả giống lệnh mở; `SUCCESS` khi cảm biến thấy cửa đóng.

### 2.2 Tủ → backend

**Kết quả mở** — `cabinet/{lockerId}/command/open/result` (QoS 1)

```json
{
  "commandId": "5f0c…", "boxId": 12, "slotIndex": 3,
  "status": "SUCCESS", "hwState": "OPEN",
  "errorCode": null, "errorMessage": "Door opened",
  "timestamp": "2026-09-27T10:00:03+00:00"
}
```

- Backend khớp bằng `commandId`, chờ tối đa `app.iot.unlock-wait-seconds`. `status = "FAILED"` ⇒ "Hardware failed to open"; hết giờ ⇒ "IoT device timeout".
- `SUCCESS` nghĩa là relay đã chạy **và** cảm biến thấy cửa mở sau thời gian chờ lò xo. Nếu đặt `REQUIRE_DOOR_SENSOR=false` trên Pi thì chỉ cần relay chạy (dùng khi cảm biến chưa nối).

| `errorCode` | Khi nào |
|---|---|
| `JAMMED` | Relay chạy nhưng cảm biến vẫn thấy cửa đóng (kẹt cửa, hoặc cảm biến chưa nối — khi đó đặt `REQUIRE_DOOR_SENSOR=false`) |
| `UNKNOWN_SLOT` | Không có `slotIndex` và không tra được `boxId` trong sơ đồ |
| `INVALID_SLOT` | `slotIndex` vượt số ô phần cứng |
| `UNKNOWN_SLAVE`, `GPIO_NOT_STARTED` | Cấu hình GPIO sai hoặc chưa khởi động (`HARDWARE_BACKEND=gpio`) |
| `TIMEOUT`, `SERIAL_ERROR` | Arduino không trả lời hoặc lỗi cổng RS485 (`HARDWARE_BACKEND=rs485`) |
| `HW_ERROR` | Lỗi phần cứng khác; chi tiết nằm ở `errorMessage` |

Lệnh mở xếp hàng trên Pi: mỗi lúc chỉ một khoá có điện, lệnh sau chờ lệnh trước (khoảng 3 giây mỗi lệnh).

**Trạng thái cửa** — `cabinet/{lockerId}/locker/{slotIndex}/status` (QoS 1), gửi mỗi khi cảm biến đổi trạng thái

```json
{ "slotIndex": 3, "boxId": 12, "hwState": "OPEN", "doorOpen": true, "timestamp": "…" }
```

- `hwState` ∈ `OPEN | CLOSED`. locker-service coi `OPEN` kéo dài là "cửa quên đóng".
- Pi chỉ gửi `boxId` khi biết (từ sơ đồ setup, hoặc từ lệnh gần nhất cho ô đó). Backend dùng `boxId` nếu có, nếu không thì tra ô có `boxNumber = slotIndex + 1` trong tủ `lockerId`.

**Nhịp tim** — `cabinet/{lockerId}/heartbeat` (QoS 0, mỗi 60 giây)

```json
{
  "cabinetId": "1", "status": "online", "macAddress": "2C:CF:67:DB:C5:C3",
  "firmwareVersion": "v1.0.0", "uptime": 3600,
  "lockers": [ { "slotIndex": 0, "boxId": 12, "hwState": "CLOSED" } ],
  "timestamp": "…"
}
```

Backend ghi `device_statuses` với `deviceId` = `macAddress` (nếu thiếu thì lấy đoạn `{lockerId}` của topic) và `lockerId` = đoạn topic; đồng thời cập nhật "thấy lần cuối" của thiết bị trong `gateway_devices`. Pi gửi một nhịp ngay mỗi lần (lại) kết nối broker.

## 3. Cấp phát — `iot/{mac}/…`

Trình tự: Pi khởi động → báo discovery → admin gán Pi vào tủ trên web → backend gửi setup → Pi mở thử từng ô (tuỳ chọn) → báo kết quả → lưu `lockerId` và sơ đồ ô → subscribe `cabinet/{lockerId}/command/#`.

**Pi báo mình** — `iot/{mac}/discovery/result` (QoS 1). Gửi mỗi lần (lại) kết nối broker, khi phần cứng kết nối lại, sau setup/clear-setup, và khi được yêu cầu. iot-service lưu vào bảng `gateway_devices`; màn admin gọi `GET /api/admin/iot/gateways`, gán bằng `POST /api/admin/iot/gateways/{id}/assign {lockerId, testDoors}` (cùng `…/unassign`, `…/discover`, `DELETE …/{id}`).

```json
{
  "macAddress": "2C:CF:67:DB:C5:C3", "firmwareVersion": "v1.0.0", "hardware": "gpio",
  "lockerId": 1, "slaves": [ { "slaveId": 1, "availableSlots": 7 } ],
  "timestamp": "…"
}
```

`lockerId` là tủ Pi đang phục vụ (đã setup, hoặc lấy từ `LOCKER_ID` trong `.env`); `null` nếu chưa có.

**Yêu cầu báo lại** — `iot/{mac}/discovery/start`: `{ "maxCabinets": 1 }`

**Gán tủ** — `iot/{mac}/command/setup` (QoS 1)

```json
{
  "action": "SETUP_LOCKERS", "commandId": "…", "macAddress": "2C:CF:67:DB:C5:C3",
  "lockerId": 1, "cabinetId": "1", "cabinetCode": "CAB-TU01", "slaveId": 1,
  "totalRows": 7, "totalColumns": 1, "testDoors": true, "testTimeout": 10,
  "lockerLayout": [ { "boxId": 12, "slotIndex": 0, "row": 1, "column": 0, "label": "1" } ]
}
```

- `macAddress` phải khớp MAC của Pi, nếu không Pi bỏ qua.
- `testDoors = true`: Pi mở lần lượt từng ô và đọc cảm biến. `false`: chỉ lưu sơ đồ, không mở ô nào.
- Sơ đồ có ô vượt số ô phần cứng ⇒ Pi từ chối với `FAILED`.

**Tiến độ và kết quả** — `iot/{mac}/setup/progress` (mỗi ô) và `iot/{mac}/setup/result`

```json
{
  "commandId": "…", "cabinetId": "1", "lockerId": 1, "status": "COMPLETED",
  "summary": { "total": 7, "totalOk": 7, "totalFail": 0, "duration": 24 },
  "lockers": [ { "slotIndex": 0, "boxId": 12, "row": 1, "column": 0, "testResult": "OK",
                 "hwState": "CLOSED", "responseTimeMs": 3012, "errorCode": null, "errorMessage": null } ],
  "timestamp": "…"
}
```

`status` ∈ `COMPLETED | PARTIAL | FAILED`. Pi chỉ lưu khi khác `FAILED`, và **lưu xong mới gửi kết quả** — thấy `COMPLETED` là gửi lệnh mở được ngay. Sơ đồ sai (ô vượt phần cứng, `slotIndex` hỏng) ⇒ `FAILED` kèm `errorMessage`, không có `lockers`.

**Gỡ khỏi tủ** — `iot/{mac}/command/clear-setup`: `{ "action": "CLEAR_SETUP", "commandId": "…" }`. Pi xoá sơ đồ, quay về `LOCKER_ID` trong `.env` (nếu có).

## 4. Kết nối và phân quyền

| | Dev / hiện tại | Production (sau § 6) |
|---|---|---|
| Broker | `broker.hivemq.com` công khai | Mosquitto 2 trong `backend/docker-compose.yml` (profile `mqtt`) |
| iot-service vào | `tcp://broker.hivemq.com:1883` | `tcp://mosquitto:1883` trong mạng Docker, tài khoản `iot-service` |
| Pi vào | TLS `broker.hivemq.com:8883` | `wss://api.locker-drone.tech/mqtt` (Nginx 443 → `127.0.0.1:9001`) |
| Xác thực | không | mỗi Pi một tài khoản, username = **MAC viết liền** (`2CCF67DBC5C3`); `allow_anonymous false` |

File mật khẩu của Mosquitto cấm dấu `:` trong tên, nên tên đăng nhập bỏ dấu `:`; topic vẫn dùng MAC có dấu `:`. Client id của Pi cũng là MAC viết liền — hai tiến trình cùng MAC sẽ đá nhau ra khỏi broker.

**ACL** (`backend/infra/mosquitto/acl.base` + `devices.acl` do `mqtt-device.sh` sinh):

| Ai | Đọc | Ghi |
|---|---|---|
| `iot-service` | `cabinet/#`, `iot/#` | `cabinet/#`, `iot/#` |
| Pi `2CCF67DBC5C3` gắn tủ `{lockerId}` | `cabinet/{lockerId}/command/#`, `iot/{MAC}/command/#`, `iot/{MAC}/discovery/start` | `cabinet/{lockerId}/command/+/result`, `cabinet/{lockerId}/locker/+/status`, `cabinet/{lockerId}/heartbeat`, `iot/{MAC}/discovery/result`, `iot/{MAC}/setup/#` |
| Tài khoản không phải MAC (giả lập) | `cabinet/{lockerId}/command/#` | `cabinet/{lockerId}/command/+/result`, `…/locker/+/status`, `…/heartbeat` |

Thiết bị **không** ghi được `…/command/open` và không nhận lệnh của tủ khác. Mosquitto vẫn trả SUBACK thành công khi subscribe ngoài quyền nhưng không giao tin — muốn kiểm quyền thì xem tin có tới hay không. `lockerId` = `*` cho quyền mọi tủ, chỉ dùng cho giả lập `simulate_demo_cabinet.py` (nó nghe `cabinet/+/command/open`).

Kiểm chứng 2026-09-27 trên Docker (Mosquitto 2.1 + Nginx TLS): ẩn danh và sai mật khẩu bị từ chối; Pi không gửi được lệnh mở, không nhận lệnh tủ khác, không giả được discovery của Pi khác; Pi tự nối và subscribe lại sau khi broker khởi động lại.

## 5. Biến môi trường

**iot-service** (`.env` của VM, truyền qua `docker-compose.yml`): `MQTT_BROKER_URL` (mặc định HiveMQ công khai), `MQTT_USERNAME`, `MQTT_PASSWORD` (secret). Mosquitto: `COMPOSE_PROFILES=mqtt`, `MQTT_IOT_SERVICE_PASSWORD` (secret, cùng giá trị với `MQTT_PASSWORD`), tuỳ chọn `MQTT_DEVICES_DIR` (mặc định `/etc/lockr/mosquitto`) và `MQTT_WS_PORT` (mặc định `9001`).

**Pi** (`~/iot/.env`):

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `LOCKER_ID` | tủ dự phòng khi chưa được gán trên admin | trống |
| `REQUIRE_DOOR_SENSOR` | mở/thử ô chỉ `SUCCESS` khi cảm biến thấy cửa mở | `true` |
| `MQTT_BROKER`, `MQTT_PORT_SSL` | máy chủ và cổng TLS | — , `8883` |
| `MQTT_USE_TLS` | bật TLS | `true` |
| `MQTT_TRANSPORT` | `tcp` hoặc `websockets` | `tcp` |
| `MQTT_WS_PATH` | đường dẫn WebSocket | `/mqtt` |
| `MQTT_USERNAME`, `MQTT_PASSWORD` | tài khoản thiết bị (username = MAC viết liền) | trống |
| `MQTT_CA_CERTS` | file CA (PEM) nếu broker dùng chứng chỉ riêng | trống = kho CA hệ điều hành |

## 6. Bật broker riêng trên VM

Chưa bật thì hệ thống vẫn chạy trên HiveMQ công khai như trước. Các bước (chạy trên VM, trong thư mục backend đã deploy):

1. Thêm vào `.env` của VM: `COMPOSE_PROFILES=mqtt`, `MQTT_IOT_SERVICE_PASSWORD=<openssl rand -hex 24>`.
2. Cấp tài khoản cho từng Pi: `sudo infra/mosquitto/mqtt-device.sh add 2C:CF:67:DB:C5:C3 <lockerId>`. Script in `MQTT_USERNAME=…` và `MQTT_PASSWORD=…` **một lần** — chép vào `.env` của Pi. Gán Pi sang tủ khác trên admin thì chạy `mqtt-device.sh move <MAC> <lockerId mới>` cho khớp.
3. `sudo infra/azure/enable-mqtt-websocket.sh` — thêm `location = /mqtt` vào vhost HTTPS của certbot, chạy `nginx -t` (lỗi thì trả lại file cũ), reload.
4. `docker compose up -d mosquitto`, rồi thêm `MQTT_BROKER_URL=tcp://mosquitto:1883`, `MQTT_USERNAME=iot-service`, `MQTT_PASSWORD=<như bước 1>` và `docker compose up -d iot-service`.
5. Trên Pi, trong `~/iot/.env`: `MQTT_BROKER=api.locker-drone.tech`, `MQTT_PORT_SSL=443`, `MQTT_TRANSPORT=websockets`, cùng hai dòng ở bước 2; rồi `sudo systemctl restart lockr-controller`.
6. Kiểm tra: `journalctl -u lockr-controller` có `MQTT Connected`; admin → Tủ → sơ đồ → khung **Bộ điều khiển tủ** thấy Pi online. Giả lập (nếu dùng): `mqtt-device.sh add sim-demo '*'`, chạy với `MQTT_BROKER_URL=wss://api.locker-drone.tech/mqtt`.

Quay lại HiveMQ: xoá ba biến `MQTT_*` của iot-service trong `.env` rồi `docker compose up -d iot-service`; trên Pi đặt lại `MQTT_BROKER=broker.hivemq.com`, `MQTT_PORT_SSL=8883`, `MQTT_TRANSPORT=tcp` và bỏ tài khoản.
