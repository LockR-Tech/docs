# Sơ đồ đấu nối tủ locker — bản nhà cung cấp, đối chiếu với firmware

| | |
|---|---|
| **Nguồn** | "Tài liệu kỹ thuật & hướng dẫn đấu nối hệ thống tủ locker thông minh" đi kèm tủ, chủ dự án nhận 2026-09-25 |
| **Đối chiếu code** | `iot` tại `454c49a`: `arduino/locker_controller/locker_controller.ino`, `infracstructure/serial_manager.py`, `services/locker_service.py` |
| **Hướng dẫn thao tác** | [controller-wiring-guide.md](controller-wiring-guide.md) — chuẩn bị gì, nối theo thứ tự nào, kiểm tra ra sao |

Mục 1–3 chép nguyên bảng của nhà cung cấp, chỉ đổi sang Markdown. Mục 4–5 là phần đối chiếu với code: tài liệu này mô tả **Raspberry Pi cắm thẳng GPIO** vào relay và driver, còn firmware trong repo nói chuyện với tủ qua **RS485 tới Arduino**. Nối theo mục 2 mà không đọc mục 4 thì phần mềm hiện có không mở được ngăn nào.

## 1. Tổng quan kiến trúc phần cứng

| STT | Thiết bị / linh kiện | Vai trò chính trong hệ thống |
|---|---|---|
| 1 | Nguồn tổ ong 12 V | Cung cấp nguồn điện chính (12 V) cho động cơ bước và hệ thống khoá điện từ |
| 2 | Driver TB6600 | Nhận tín hiệu xung/hướng từ bo điều khiển để điều khiển động cơ bước Nema 17 |
| 3 | Module relay 8 kênh | Đóng/mở mạch âm nguồn để kích hoạt độc lập từng ổ khoá điện tử |
| 4 | Thanh domino trung chuyển | Gom nhóm, phân phối nguồn điện và tập trung đường dây gọn gàng, chống nhiễu |
| 5 | 7 khoá điện tử 12 V | Cơ cấu chấp hành khoá/mở các ngăn tủ (tích hợp cả dây nguồn và dây tín hiệu trạng thái) |
| 6 | Động cơ bước Nema 17 & trục vít me | Cơ cấu cơ khí dịch chuyển nắp trượt theo trục Z |

## 2. Bảng đấu nối tổng hợp (bản nhà cung cấp)

| Khu vực / thiết bị | Tín hiệu / dây dẫn | Điểm kết nối (từ đâu → đến đâu) | Chức năng kỹ thuật |
|---|---|---|---|
| **Khối nguồn** | Nguồn điện lưới (AC) | Ổ điện 220 V → cổng `L`, `N`, `GND` của nguồn tổ ong | Cấp nguồn xoay chiều đầu vào cho hệ thống |
| | Nguồn 12 V (DC) | Cổng `+V` / `-V` của nguồn → driver TB6600 và thanh domino | Cấp nguồn một chiều cho toàn bộ động cơ và khoá |
| **Động cơ bước** | Dây động cơ Nema 17 | 4 dây của motor → `A+`, `A-`, `B+`, `B-` trên TB6600 | Truyền động cơ khí dịch chuyển nắp trượt |
| | Tín hiệu điều khiển | `PUL-`, `DIR-` (driver) → chân GPIO của bo điều khiển · `PUL+`, `DIR+` → nối chung +5 V | Nhận lệnh bước và chiều quay từ bo mạch chủ |
| **Module relay** | Nguồn nuôi relay | `DC+`, `DC-` → cấp 5 V | Cấp nguồn cho mạch opto cách ly relay |
| | Tín hiệu kích hoạt | `IN1` … `IN7` → chân GPIO của bo điều khiển | Nhận lệnh đóng/mở từng kênh relay từ phần mềm |
| **Khoá điện tử** | 1. Dây nguồn khoá (cặp dây to) | Dây dương (+) → thẳng vào +12 V · Dây âm (−) → qua tiếp điểm `COM` và `NO` của relay | Cấp điện để mở chốt khoá khi có lệnh |
| | 2. Dây tín hiệu khoá (cặp dây nhỏ) | Kéo toàn bộ về **thanh domino tín hiệu**, theo thứ tự lần lượt từ thanh domino nằm ngang và **từ phải qua trái nếu nhìn từ sau tủ vào**; mỗi khoá một cặp → chân digital input của bo điều khiển | Phản hồi trạng thái thực tế của hộc tủ (đóng kín hay đang mở) về phần mềm |

Tài liệu gốc ghi "GPIO Raspberry Pi" ở các ô *bo điều khiển*; xem mục 4 để biết chân thật trong firmware.

## 3. Quy chuẩn vận hành và lưu ý an toàn (bản nhà cung cấp)

- **Nguyên tắc ngắt điện.** Tuyệt đối không tháo rút giắc cắm động cơ bước hoặc chỉnh sửa mạch điện khi nguồn tổng 12 V đang bật, để tránh sốc điện gây hỏng driver TB6600.
- **Kiểm tra domino định kỳ.** Các thanh domino là cầu nối trung gian; kiểm tra độ siết của ốc vít định kỳ để tiếp xúc tốt, tránh sụt áp làm yếu lực hút/mở của khoá.
- **Quản lý hành trình cơ khí.** Hệ thống đã có mốc định vị phần mềm kết hợp giới hạn vật lý; không tự ý thay đổi kết cấu cơ khí hoặc dịch chuyển công tắc hành trình nếu không cấu hình lại thông số trong mã nguồn điều khiển.

## 4. Đối chiếu với firmware trong repo

Kiến trúc thật của phần mềm (`iot/main.py:52-58`, `iot/AGENTS.md`):

```
backend ⇄ MQTT ⇄ Raspberry Pi (main.py) ⇄ USB-RS485 ⇄ MAX485 ⇄ Arduino ⇄ relay → khoá
                                                                          ⇐ reed / công tắc cửa
```

Pi **không** cắm chân GPIO nào vào relay hay cảm biến. `hardware/rpi_locker.py` chỉ là lớp giả lập (`iot/hardware/rpi_locker.py:9-11`); đường mở khoá thật là `LockerService._handle_open_command` → `serial.open_slot` (`iot/services/locker_service.py:170`) → Arduino.

| Tài liệu nhà cung cấp ghi | Trong firmware là | Bằng chứng |
|---|---|---|
| `PUL-`, `DIR-` TB6600 → GPIO Pi | **Chưa có dòng code nào** điều khiển động cơ bước — không ở Pi, không ở Arduino | không có `step`, `lid`, `nắp` trong `iot/` |
| `IN1` … `IN7` → GPIO Pi | Chân **Arduino** `LOCK_PINS = {2, 4, 5, 3, 8, 10, A5}` — đủ 7 ngăn | `locker_controller.ino:24` |
| Dây tín hiệu khoá → GPIO Pi | Chân **Arduino** `MAGNETIC_PINS = {11, 12, A0, A1, A2, A3, A4}`, chế độ `INPUT_PULLUP`, **LOW = cửa đóng** | `locker_controller.ino:25`, `:66`, `:161` |
| `DC+` / `DC-` relay lấy 5 V "từ Raspberry Pi" | Pi không nằm trên mạch relay; cấp 5 V từ nguồn riêng ([hướng dẫn § 3.A](controller-wiring-guide.md#3-thứ-tự-nối-dây)) | — |
| 7 khoá | Khớp: `MAX_SLOTS = 7`, mảng trạng thái khai theo `NUM_SLOTS` nên tự bám số ngăn, lệnh setup nhận layout tới 7 | `serial_manager.py:21`, `locker_controller.ino:45-47`, `setup_handler.py:60-64` |
| Pi ↔ tủ | Pi ↔ **USB-RS485** ↔ MAX485 ↔ Arduino: `D6` RX, `D9` TX, `D7` DE/RE, 9600 baud; giao thức `S<id>:PING` / `T<n>` / `O<n>` / `C<n>`, trả JSON `{slave, slot, result, gpio, door, ms}` | `locker_controller.ino:4-7`, `:271-331`, `:399-411`; `serial_manager.py:22-36` |
| Mức kích relay | `RELAY_ON = HIGH` — **chưa xác minh với module thật** (nhiều module 8 kênh kích **LOW**); sai chiều thì mọi khoá bị cấp điện liên tục ngay khi Arduino khởi động. Đo ở [hướng dẫn § 3.B.4](controller-wiring-guide.md#3-thứ-tự-nối-dây) rồi sửa nếu cần | `locker_controller.ino:29-33`, `:65` |

Hành vi mở một ngăn: relay `ON` 1000 ms → `OFF` → chờ 2000 ms cho lò xo bật cửa → đọc cảm biến → trả `door` (`locker_controller.ino:365-390`). Cuộn khoá không bao giờ có điện quá 1 s, và lệnh đi tuần tự từng ngăn (`serial_manager.py:407-440`) nên **tại một thời điểm chỉ một khoá hút** — con số này quyết định cỡ nguồn 12 V.

### Ba điểm phải quyết trước khi nối

| # | Điểm lệch | Lựa chọn | Đề xuất |
|---|---|---|---|
| 1 | **Ai điều khiển relay và đọc cảm biến** | (a) Giữ Arduino như firmware — Pi chỉ cần một cổng USB · (b) Pi cắm thẳng GPIO như tài liệu — phải viết lại `hardware/rpi_locker.py` thành GPIO thật và đổi `locker_service.py` đang gọi serial | **(a)**: khớp code đang có, Pi hay Jetson đều dùng được, nhiều tủ chung một bus phân biệt bằng `SLAVE_ID` |
| 2 | ~~**7 ngăn vs trần 6**~~ | **Đã chọn (a) và làm** — `MAX_SLOTS = 7`, hai mảng chân đủ 7, mảng trạng thái bám `NUM_SLOTS` ([iot#7](https://github.com/LockR-Tech/iot/pull/7)) | xong |
| 3 | **Nắp trượt (TB6600 + Nema 17)** | Chưa có firmware, chưa có lệnh MQTT, luồng drone F1.06 đang DEMO. Ba đường ở [hướng dẫn § 3.E](controller-wiring-guide.md#3-thứ-tự-nối-dây) | Làm sau khi 7 ngăn đã mở được bằng mã |

## 5. Bản đồ chân Arduino Uno cho 7 ngăn

Chân đã dùng: `D0`/`D1` (USB debug), `D6`/`D7`/`D9` (RS485). Còn `D2 D3 D4 D5 D8 D10 D11 D12 D13 A0–A5` = 15 chân cho 14 tín hiệu.

| Ngăn (`slot`) | Relay | Chân khoá (`LOCK_PINS`) | Chân cảm biến (`MAGNETIC_PINS`) | Ghi chú |
|---|---|---|---|---|
| 0 | `IN1` | `D2` | `D11` | |
| 1 | `IN2` | `D4` | `D12` | |
| 2 | `IN3` | `D5` | `A0` | |
| 3 | `IN4` | `D3` | `A1` | |
| 4 | `IN5` | `D8` | `A2` | |
| 5 | `IN6` | `D10` | `A3` | |
| 6 | `IN7` | `A5` | `A4` | **không dùng `D13`** cho khoá: bootloader nháy LED trên chân đó mỗi lần reset, relay 7 sẽ kêu tách và khoá giật |

Thứ tự `slot` đi theo đúng thứ tự dây tín hiệu trên thanh domino của nhà cung cấp (mục 2: từ phải qua trái, nhìn từ sau tủ) — ghi số `slot` lên domino để kỹ thuật viên sau này không phải đoán.

Bản đồ này **đã nằm trong firmware** ([iot#7](https://github.com/LockR-Tech/iot/pull/7)): `locker_controller.ino:24-25` (hai mảng), `:45-47` (mảng trạng thái khai `[NUM_SLOTS]` nên thêm ngăn không còn ghi tràn), `serial_manager.py:21` (`MAX_SLOTS = 7`). Nạp lại sketch là dùng được, không phải sửa tay nữa.
