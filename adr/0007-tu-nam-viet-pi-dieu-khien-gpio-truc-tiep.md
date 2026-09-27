# ADR-0007: Tủ Nam Việt — Pi điều khiển khoá, cảm biến và nắp trượt bằng GPIO trực tiếp

| | |
|---|---|
| **Trạng thái** | Accepted |
| **Ngày** | 2026-09-27 |
| **Người quyết định** | Chủ dự án |
| **Liên quan** | F2-G09, F1.06 · [cabinet-wiring-spec § 4](../03-hardware/cabinet-wiring-spec.md#4-đối-chiếu-với-firmware-trong-repo) (điểm quyết định 1) · [iot#8](https://github.com/LockR-Tech/iot/pull/8) |

## Bối cảnh

- Tủ mua của Công ty TNHH Công nghệ Năng lượng Nam Việt (báo giá 3/07/BG-NV, 2026-07-06) gồm: khung tủ, 7 khoá điện tử 12 V, module relay 8 kênh, driver TB6600 + Nema 17, ray MGN12H, đai + puli GT2, nắp trượt, 2 công tắc hành trình, nguồn 24 V 5 A riêng cho motor. **Không có** Arduino, MAX485, adapter USB-RS485.
- Tài liệu đấu nối của nhà cung cấp cho Pi nối **thẳng GPIO**: `IN1…IN7` của relay, dây tín hiệu khoá, `PUL-`/`DIR-` của TB6600.
- Code `iot` lại điều khiển tủ qua **Arduino trên RS485** (`locker_controller.ino`, `serial_manager.py`). [cabinet-wiring-spec § 4](../03-hardware/cabinet-wiring-spec.md#4-đối-chiếu-với-firmware-trong-repo) đề xuất giữ Arduino (phương án (a)); iot#7 đã làm firmware 7 ngăn theo hướng đó. Đi theo (a) phải mua thêm Arduino Uno, MAX485, adapter tự đảo chiều, dây xoắn, mạch hạ áp 5 V.
- Chưa có dòng code nào điều khiển nắp trượt ở cả Pi lẫn Arduino.
- Chủ dự án muốn dùng đúng linh kiện đã giao, chỉ mua thứ bắt buộc.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| (a) Giữ Arduino + RS485 | Khớp code đang có; nhiều tủ chung một bus (`SLAVE_ID`); Pi hay Jetson đều dùng được; Pi cách xa mạch khoá | Phải mua và nối thêm 4–5 linh kiện; lệch tài liệu nhà cung cấp; nắp trượt vẫn phải viết mới (Uno thiếu chân ⇒ đổi Mega) |
| (b) Pi nối thẳng GPIO, **thay** hẳn RS485 | Đúng sơ đồ nhà cung cấp, không mua thêm | Mất đường Arduino đã làm; tủ sau muốn dùng Arduino phải viết lại |
| (c) Pi nối thẳng GPIO, **giữ RS485 làm tuỳ chọn** | Như (b); tủ khác vẫn chọn được Arduino bằng một biến môi trường | Hai đường code phải cùng giữ đúng một giao diện |

## Quyết định

Chọn **(c)**. `main.py` chọn phần cứng bằng `HARDWARE_BACKEND`: `gpio` cho tủ Nam Việt, `rs485` (mặc định) cho Arduino. Lớp GPIO (`iot/hardware/gpio_locker.py`) có **cùng giao diện và dạng kết quả** với `SerialManager`, giữ nguyên hành vi firmware (relay 1 s, chờ 2 s rồi đọc cảm biến, một khoá có điện tại một thời điểm, LOW = cửa đóng). Nắp trượt điều khiển bằng GPIO (`iot/hardware/lid_controller.py`) qua API cục bộ, chưa có lệnh MQTT.

Ba điểm nối dây **khác** tài liệu nhà cung cấp, vì GPIO của Pi chỉ lên 3,3 V trong khi tài liệu giả định 5 V:

1. Jumper relay đặt **H** (kích mức cao) — ở chế độ L, 3,3 V không tắt được relay.
2. `PUL+`, `DIR+` của TB6600 nối **3,3 V** (không phải +5 V).
3. Dây tín hiệu khoá phải là tiếp điểm khô — đo trước khi nối; có điện áp thì không được nối vào Pi.

## Hệ quả

- Tích cực: không mua Arduino, MAX485, adapter, mạch hạ áp; sơ đồ nối khớp tài liệu nhà cung cấp (trừ 3 điểm trên); nắp trượt có code lần đầu; `LockerService`, `SetupHandler`, `DiscoveryService` không đổi.
- Tiêu cực / đánh đổi chấp nhận:
  - Chỉ chạy trên Raspberry Pi (gói `gpiod`, chip RP1/BCM); Jetson không dùng được cách này.
  - Một Pi một tủ — không còn nhiều tủ chung bus.
  - Pi nối thẳng vào mạch khoá 12 V: nhiễu cuộn khoá có thể làm Pi treo ⇒ nên có diode 1N4007 song song mỗi khoá.
  - Pi 5 giữ nguyên mức chân GPIO sau khi tiến trình thoát ⇒ service phải ép chân relay về LOW khi dừng (`ExecStopPost`).
- Việc phải làm theo sau:
  - Nối dây và bring-up theo [controller-wiring-guide](../03-hardware/controller-wiring-guide.md) (phần GPIO), xác minh mức kích relay và chiều cảm biến trên phần cứng thật.
  - Lệnh MQTT cho nắp trượt khi làm luồng drone thật (F1.06).
  - F2-G09 (thống nhất payload lệnh mở) vẫn chặn mở tủ từ app — không đổi bởi ADR này.
