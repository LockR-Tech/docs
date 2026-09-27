# ADR-0008: Hợp đồng MQTT backend ↔ tủ — topic theo `lockerId`, ô theo `slotIndex`, gán thiết bị bằng MAC, broker riêng

| | |
|---|---|
| **Trạng thái** | Proposed — chuyển Accepted khi PR backend được review và merge |
| **Ngày** | 2026-09-27 |
| **Người quyết định** | Chủ dự án (chọn "sửa toàn bộ" cả ba giai đoạn) |
| **Liên quan** | F2-G09, F2.10, F1.10 · SEC-04 · [ADR-0007](0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md) · đặc tả: [mqtt-contract.md](../01-overview/mqtt-contract.md) · [iot#9](https://github.com/LockR-Tech/iot/pull/9), [backend#33](https://github.com/LockR-Tech/backend/pull/33), [frontend#22](https://github.com/LockR-Tech/frontend/pull/22) |

## Bối cảnh

Nối dây đúng rồi app vẫn chưa mở được tủ thật, vì hai phía nói hai thứ tiếng:

- **Lệnh mở.** iot-service gửi `cabinet/{lockerId}/command/open` với `{commandId, box_id, action, timeout}` (`backend/iot-service/…/LockerMqttService.java:179-192`). Pi lấy **tên** tủ từ topic, tìm trong các tủ đã setup, rồi đòi `slotIndex` (`iot/services/locker_service.py:160-181`). Không ai gửi lệnh setup (`iot/{mac}/command/setup`), nên Pi không có tủ nào và bỏ qua mọi lệnh. Chỉ `simulate_demo_cabinet.py` trả lời được backend.
- **Trạng thái cửa.** Backend lấy `slotIndex` trong payload làm `boxId` (`LockerMqttService.java:104-107`). Pi gửi `hwState` là `OPENING/CLOSING`, trong khi locker-service tìm cửa quên đóng bằng chữ `OPEN` (`backend/locker-service/…/LockerService.java:2153`).
- **Pi tự làm rơi kết nối.** Pi chỉ subscribe lệnh tủ một lần lúc khởi động. Kết nối lại (clean session) là mất subscription. Mạng chưa lên lúc khởi động thì `connect()` ném lỗi và không thử lại. Khi cửa đóng, Pi tự publish lệnh `close` vào chính topic nó đang nghe.
- **Broker công khai** `broker.hivemq.com`, không xác thực, không TLS (SEC-04): ai cũng publish được lệnh mở tủ.
- **Hạ tầng sẵn có.** VM Azure chỉ mở cổng 22/80/443; Nginx + Let's Encrypt đã lo TLS cho `api.locker-drone.tech` (`backend/infra/azure/bootstrap-vm.sh`, `provision-vm.sh:95-123`).

## Các phương án đã cân nhắc

**1. Topic vận hành đặt theo gì**

| Phương án | Ưu | Nhược |
|---|---|---|
| Tên/mã tủ (Pi đang dùng) | Đọc dễ | Backend phải tra mã; đổi mã là đứt kết nối |
| **`lockerId` số** (backend và giả lập đang dùng) | Không phải sửa backend; id không đổi | Pi phải biết `lockerId` của mình |
| MAC của Pi | ACL gọn nhất | Backend phải biết MAC mới mở được ô; giả lập phải đăng ký như thiết bị thật |

**2. Ô nào ứng với chân nào**

| Phương án | Ưu | Nhược |
|---|---|---|
| **Backend gửi `slotIndex = boxNumber − 1`**, Pi đổi thứ tự chân trong `.env` | Không đổi DB; số trên cửa là số ô trên app | Đấu lệch thứ tự thì sửa `.env` trên Pi |
| Cột `slot_index` mới trong `locker_boxes` | Linh hoạt nhất | Migration + màn admin; thêm một chỗ cấu hình dễ lệch |
| Pi giữ bảng `boxId → slot` từ lệnh setup | Backend không cần tính | Chưa setup thì không mở được |

**3. Pi biết mình là tủ nào**

| Phương án | Ưu | Nhược |
|---|---|---|
| `LOCKER_ID` trong `.env` | Chạy được ngay | Người dựng Pi phải tra id; dễ gõ sai |
| **Admin gán Pi (theo MAC) vào tủ trên web**, backend gửi lệnh setup kèm sơ đồ ô | Không sửa file trên Pi; admin thấy Pi nào online, đang ở tủ nào, kết quả thử từng ô | Cần bảng thiết bị, API và màn admin |

**4. Broker**

| Phương án | Ưu | Nhược |
|---|---|---|
| Giữ HiveMQ công khai | Không làm gì | SEC-04 |
| Dịch vụ MQTT trả phí | Không vận hành | Thêm chi phí, thêm tài khoản ngoài |
| Mosquitto trên VM, TLS riêng ở cổng 8883 | Chuẩn MQTT | Mở cổng mới ở NSG + ufw; Mosquitto tự đọc chứng chỉ Let's Encrypt (quyền file, reload khi gia hạn) |
| **Mosquitto trên VM, WebSocket qua Nginx** `wss://api.locker-drone.tech/mqtt` | Không mở cổng; dùng lại chứng chỉ và gia hạn đang chạy | Thêm một lớp WebSocket (paho Python và Java đều hỗ trợ) |

**5. Phân quyền trên broker**

| Phương án | Ưu | Nhược |
|---|---|---|
| Một tài khoản chung cho mọi tủ | Đơn giản | Lộ một Pi là lộ cả hệ thống, kể cả quyền gửi lệnh mở |
| **Mỗi Pi một tài khoản (username = MAC viết liền)**, khối ACL riêng từng thiết bị sinh từ danh sách trên VM | Thiết bị **không bao giờ** gửi được lệnh mở; mỗi Pi chỉ thấy tủ và namespace `iot/{mac}` của mình | Gán Pi sang tủ khác thì phải sửa danh sách trên VM |
| Plugin dynamic-security, backend tạo quyền khi admin gán | Gán trên web là đủ | Backend giữ quyền quản trị broker; nhiều code hơn hẳn |

## Quyết định

1. **Topic vận hành là `cabinet/{lockerId}/…`**, trong đó `lockerId` là id số của tủ trong locker-service. **Topic cấp phát là `iot/{mac}/…`**.
2. **Lệnh mở mang cả `boxId` lẫn `slotIndex`**, với `slotIndex = boxNumber − 1`. iot-service tra `boxNumber` qua `GET /internal/lockers/{id}/layout`. Nếu tra không được thì vẫn gửi `boxId`, và Pi tra `boxId` trong sơ đồ đã setup. Không tra được thì trả `FAILED / UNKNOWN_SLOT` ngay, để backend không phải chờ hết giờ. Đấu lệch thứ tự thì đổi thứ tự `GPIO_RELAY_PINS`, `GPIO_DOOR_PINS` trong `.env`, **không** đánh số lại ô.
3. **Gán thiết bị trên admin web.** Khi khởi động, Pi báo `iot/{mac}/discovery/result`. iot-service lưu thiết bị. Admin chọn tủ, iot-service gửi `iot/{mac}/command/setup` kèm sơ đồ `[{boxId, slotIndex, row, column, label}]`. Pi (tuỳ chọn) mở thử từng ô, báo kết quả, rồi lưu `lockerId` và sơ đồ. `LOCKER_ID` trong `.env` chỉ là dự phòng khi Pi chưa được gán. Mỗi tủ gắn một Pi; nhiều tủ chung một Pi qua RS485 (`BULK_SETUP_LOCKERS`) để sau.
4. **Trạng thái cửa** gửi lên `cabinet/{lockerId}/locker/{slotIndex}/status`, `hwState` là `OPEN | CLOSED`. Pi gửi kèm `boxId` khi biết. Backend ưu tiên `boxId`, nếu thiếu thì tra theo `boxNumber = slotIndex + 1`.
5. **Broker riêng.** Chạy Mosquitto 2 trong `backend/docker-compose.yml` dưới profile `mqtt`, `allow_anonymous false`. Trong mạng Docker, iot-service vào `tcp://mosquitto:1883`. Từ Internet, Pi vào `wss://api.locker-drone.tech/mqtt` qua Nginx. Mỗi Pi một tài khoản; username là MAC **viết liền** (`2CCF67DBC5C3`), vì file mật khẩu Mosquitto cấm dấu `:` — cũng vì thế không dùng được ACL mẫu `%u` cho topic `iot/{MAC có dấu :}`, nên mỗi thiết bị có khối ACL riêng do `infra/mosquitto/mqtt-device.sh` sinh. Thiết bị chỉ **đọc** lệnh và chỉ **ghi** result/status/heartbeat/discovery/setup. Pi đã đặt mật khẩu thì không bao giờ rơi về kết nối không mã hoá.
6. **Chuyển đổi không gây đứt.** Merge code không đổi broker đang dùng. Chuyển sang broker riêng là bước vận hành, làm bằng biến trong `.env` của VM và của Pi. Lệnh mở vẫn gửi kèm `box_id` cho giả lập cũ; bỏ ở phiên bản hợp đồng sau.

Đặc tả đầy đủ (topic, payload, mã lỗi, ACL): [mqtt-contract.md](../01-overview/mqtt-contract.md).

Kiểm chứng trước khi đề xuất (2026-09-27): contract test ở hai repo (Pi 18, backend 18) dùng chung payload mẫu; chạy thật `LockerMqttService` + `GatewayProvisioningService` của backend với `main.py` của Pi qua Mosquitto 2.1 có ACL và Nginx TLS trên Docker — mở đúng ô, gán tủ thử 3/3 ô, thiết bị không gửi được lệnh mở, Pi tự nối lại sau khi broker khởi động lại.

## Hệ quả

- Tích cực:
  - App, kiosk và KTV mở được ô trên tủ thật. Trạng thái cửa về đúng ô, nên "cửa quên đóng" của locker-service có dữ liệu thật.
  - Admin thấy Pi nào online, đang gắn tủ nào, kết quả thử từng ô.
  - Hết SEC-04 khi bật broker riêng. Lộ một Pi không gửi được lệnh mở cho bất kỳ tủ nào.
- Tiêu cực / đánh đổi chấp nhận:
  - `slotIndex` gắn với `boxNumber`: đổi số ô trên admin là đổi ô vật lý mà lệnh trỏ tới.
  - ACL theo tủ nằm trong danh sách thiết bị trên VM, tách khỏi thao tác gán trên web. Gán Pi sang tủ khác thì phải sửa cả hai chỗ. Nâng lên dynamic-security thì hết việc này.
  - Mỗi lệnh mở thêm một lời gọi Feign sang locker-service (vài ms).
  - Giả lập bản cũ gửi `slotIndex` = id ô. Sau khi backend deploy, trạng thái cửa của nó sẽ bị tra sai ô. Đây chỉ là dữ liệu theo dõi, và giả lập đã sửa trong cùng đợt.
- Việc phải làm theo sau:
  - Bật broker riêng trên VM, cấp tài khoản cho Pi `lockr-tu01` rồi đổi `.env` trên Pi (các bước: [mqtt-contract § 6](../01-overview/mqtt-contract.md#6-bật-broker-riêng-trên-vm)).
  - Tạo tủ 7 ô cho tủ Nam Việt trên admin, gán Pi, cho kiosk trỏ đúng `lockerId`.
  - Lệnh MQTT cho nắp trượt (F1.06). Sự kiện cửa điều khiển vòng đời đơn/ô (F2-G09, F3-G03) vẫn còn nợ.
