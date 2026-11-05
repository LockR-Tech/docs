# Cấu hình ô tủ và nắp trượt — tủ `CAB-TU01`

| | |
|---|---|
| **Dùng khi** | Cần tra nhanh ô nào nối chân nào, nắp trượt nào nằm trên ô nào, đang chạy tốc độ bao nhiêu, chiều nào là mở/đóng — hoặc cần khôi phục cấu hình sau khi Pi bị cài lại |
| **Hiệu lực** | **2026-11-04 (tối)** — cấu hình đọc trực tiếp từ Pi tủ đang chạy, sau khi chạy thử thật cả 2 nắp |
| **Nguồn** | `~/iot/config/hardware_config.json`, `lid_tuning.json`, `lid_position.json`, `.env` trên Pi `lockr-tu01` + code `iot/hardware/lid_controller.py` |
| **Liên quan** | Sơ đồ nối dây, breadboard, driver: [tu01-so-do-tong-quan.md](tu01-so-do-tong-quan.md) |
| **Gap** | F1-G03 (nắp trượt thật theo ArUco), F2-G09 |

Tủ `CAB-TU01` là **tủ #7** trên hệ thống: 7 ô có khoá điện từ 12 V, trong đó **ô 2 và ô 3 là ô drone** có nắp trượt trên nóc chạy bằng trục vít me (motor bước + driver TB6600).

Quy ước:
- **Số chân** = số chân vật lý trên header 40 chân của Pi; **GPIO** = số BCM phần mềm dùng.
- **Ô N** trên admin = khoá N = relay `IN N` = `slot N − 1` trong code = **box ID `37 + N`** trên hệ thống.
- **Mở nắp** = bàn trượt rời đầu gốc, lộ miệng ô; **đóng nắp** = bàn trượt về đầu gốc, che kín ô.

## 1. Từng ô tủ

| Ô | Box ID | Slot | Loại | Relay `IN` → chân (GPIO) | Phản hồi cửa → chân (GPIO) | Nắp trượt | Mã ArUco |
|---|---|---|---|---|---|---|---|
| 1 | 38 | 0 | XL (cửa cao) | `IN1` → 29 (5) | 7 (4) | — | — |
| 2 | 39 | 1 | **DRONE** | `IN2` → 31 (6) | 12 (18) | **Trục 2** | **#0** |
| 3 | 40 | 2 | **DRONE** | `IN3` → 33 (13) | 18 (24) | **Trục 1** | **#1** ¹ |
| 4 | 41 | 3 | | `IN4` → 35 (19) | 22 (25) | — | — |
| 5 | 42 | 4 | | `IN5` → 37 (26) | 32 (12) | — | — |
| 6 | 43 | 5 | | `IN6` → 36 (16) | 40 (21) | — | — |
| 7 | 44 | 6 | | `IN7` → 38 (20) | 24 (8) | — | — |

¹ Mã #1 → ô 3 là cấu hình của chế độ thử nắp (`app.drone.lid-test.markers = 0:39,1:40`) và đã chạy thật ngày 04/11. Mã ArUco gán cho ô 3 trong locker-service (dùng cho đơn thật) chưa được kiểm; khung "Chế độ thử nắp" ở `/admin/drone-logs` báo vàng nếu hai nơi lệch nhau.

Thông số chung của khoá:

| Mục | Giá trị | Ý nghĩa |
|---|---|---|
| `relayActiveHigh` | `true` | Jumper module relay ở **H**: GPIO lên cao thì relay đóng, khoá nhả |
| `unlockMs` | `1000` | Kích relay 1 giây mỗi lần mở ô |
| `doorClosedLow` | `true` | Phản hồi đọc **thấp** khi cửa đóng, **cao** khi cửa bật ra |
| `requireDoorSensor` | `true` | Chỉ báo "đã mở" khi phản hồi cửa đổi trạng thái |
| Giữ relay thấp lúc khởi động | `/boot/firmware/config.txt`: `gpio=5,6,13,19,26,16,20=op,dl` | Pi khởi động không tự kích khoá |

Lệnh **"Mở ô"** (khách, KTV, admin) chỉ kích relay, **không bao giờ** chạy nắp trượt. Nắp ô drone chỉ chạy khi có lệnh nắp (luồng drone, trang Điều khiển tủ, bảng `/service`).

## 2. Hai nắp trượt

| | **Trục 1** | **Trục 2** |
|---|---|---|
| Nằm trên | **Ô 3** (box 40) | **Ô 2** (box 39) |
| Chân PUL / DIR | GPIO17 (chân 11) / GPIO27 (chân 13) | GPIO22 (chân 15) / GPIO23 (chân 16) |
| Transistor kích (C1815) | T1 (PUL) / T2 (DIR) | T3 (PUL) / T4 (DIR) |
| Công tắc gốc / cuối | GPIO2 / GPIO3 — **chưa lắp** | GPIO9 / GPIO11 — **chưa lắp** |
| Mức xung | active-high (`step_active_low = false`) | như trục 1 |
| Driver TB6600 — DIP | S1 ON, S2 ON, S3 OFF ⇒ **200 bước/vòng**; S4 ON, S5 OFF, S6 ON ⇒ **1,0 A** | như trục 1 |
| `steps_per_rev` | 200 | 200 |
| Dạng xung (`profile`) | **`chaydan`** (§ 3) | **`chaydan`** |
| Tốc độ chạy đều (`rps`) | **1,79 vòng/s** = 358 bước/s ≈ 2,8 ms/bước | **1,79 vòng/s** = 358 bước/s ≈ 2,8 ms/bước |
| Độ rộng xung | nửa chu kỳ ≈ 1,4 ms | nửa chu kỳ ≈ 1,4 ms |
| Chiều dài ray (`max_revs`) | **36 vòng** = 7200 bước | **36 vòng** = 7200 bước |
| Thời gian mở hết / đóng hết | ≈ **21 giây** | ≈ **21 giây** |
| **Chiều mở** (`open_dir_high`) | **`true`** — DIR **cao** = mở, DIR thấp = đóng | **`false`** — DIR **thấp** = mở, DIR cao = đóng |
| Thử tay bằng `chaydan` (§ 6) | mở: `chaydan 17 27 <bước> dh` · đóng: `… dl` | mở: `chaydan 22 23 <bước> dl` · đóng: `… dh` |
| Theo dõi vị trí | đếm bước (`positionTravel = true`) | đếm bước |
| Trạng thái lúc chốt tài liệu | đóng, vị trí 0 vòng | đóng, vị trí 0 vòng |

Hai trục **chiều ngược nhau** vì dây motor/driver của mỗi trục đấu khác nhau — đừng chép `open_dir_high` từ trục này sang trục kia. Đổi chiều chỉ bằng `open_dir_high`, không đổi dây.

Các khoá `start_rps = 0,2`, `ramp_steps = 100`, `pulse_us = 300` vẫn nằm trong `lid_tuning.json` nhưng **không có tác dụng** với `chaydan` (chỉ dùng cho `profile = "linear"`). `limit_active_low = true` dành cho công tắc hành trình khi lắp.

### Vị trí bàn trượt

Chưa có công tắc hành trình, Pi **đếm bước** để biết bàn trượt cách đầu gốc bao nhiêu vòng (0 = đóng hết, 36 = mở hết) và lưu ở `lid_position.json` sau mỗi lượt chạy:

- **Mở hết / Đóng hết** chỉ chạy phần còn thiếu tới đầu ray. Nắp đã ở đúng đầu thì không chạy motor (trả `alreadyInPosition`).
- **Chạy N vòng** chạy đủ N vòng; vượt đầu ray thì motor tì vào điểm chặn phần còn lại, vị trí được kẹp trong 0–36.
- **Về gốc** luôn chạy đủ 36 vòng về phía đóng rồi lấy làm mốc 0 — dùng khi không biết nắp đang ở đâu.
- Đẩy tay nắp, mất điện giữa chừng, hoặc nghe motor trượt bước ⇒ vị trí đếm bị sai: **đặt lại** ở bảng `/service` → mục **Vị trí bàn trượt** (hoặc `PUT /service/api/lids/{trục}/position {"revolutions": …}` trên Pi).

## 3. Dạng xung `chaydan`

Đúng lệnh `chaydan` kỹ thuật tủ đã kiểm chứng ngày 03/11 (cần tăng tốc dần để motor tự khởi động):

| Đoạn | Số bước | Chu kỳ 1 bước | Thời gian |
|---|---|---|---|
| Nấc 1 | 100 | 10,8 ms | 1,08 s |
| Nấc 2 | 100 | 4,8 ms | 0,48 s |
| Chạy đều | còn lại (7000 với 36 vòng) | `1 / (rps × 200)` = 2,79 ms | 19,6 s |
| **Tổng 36 vòng** | 7200 | | **≈ 21,1 s** (đo trên tủ: 21,2 s) |

- Xung PUL rộng **nửa chu kỳ** (như `pinctrl … dh` rồi `… dl`).
- Nấc tăng tốc **không bao giờ nhanh hơn `rps`**: đặt `rps` thấp (ví dụ 0,5 vòng/s = 10 ms/bước) thì nấc 2 cũng chạy 10 ms, không vọt lên 4,8 ms (`iot/hardware/lid_controller.py`, `_interval`).
- Nếu nắp **khựng giữa ray** (motor rung, đứng hẳn mà Pi vẫn báo xong): motor thiếu lực ở tốc độ đó ⇒ hạ `rps` của trục đó (1,04 = 4,8 ms/bước; 0,5 = 10 ms/bước), kiểm tra ray có đoạn kẹt, hoặc tăng dòng driver (DIP S4–S6, theo dòng định mức motor). Chạy chậm thì thời gian mở/đóng tăng tương ứng (0,5 vòng/s ⇒ ≈ 73 giây); backend chờ nắp chạy xong tối đa 150 giây (`app.drone.delivery.lid-motion-timeout-seconds`).
- Tốc độ cũ 0,5 vòng/s với xung cố định 300 µs (`profile = "linear"`) làm motor kêu è è mà không quay — đừng quay lại dạng đó.

## 4. Nắp trong các luồng

| Luồng | Lệnh tới tủ | Nắp chạy |
|---|---|---|
| Giao hàng drone (đơn thật, chế độ "Mô phỏng & Thử nghiệm ArUco") | `cabinet/7/command/open {boxId, lid: true}` → `…/close {lid: true}` | Camera thấy đúng mã của ô trong đơn → mở hết → servo drone nhả hàng (Pi drone chưa bật servo: đơn DEMO giả lập theo cấu hình) → báo nhả xong → đóng hết |
| **Chế độ thử nắp** (`/admin/drone-logs`, không cần đơn) | như trên | Mã #0 → nắp ô 2, mã #1 → nắp ô 3: mở hết → giữ **5 giây** → đóng hết |
| Trang **Điều khiển tủ** (`/admin/cabinet-control`) | `cabinet/7/command/lid` · `lid-jog` · `lid-tune` | Mở hết / Đóng hết / Về gốc / Dừng / Chạy N vòng / chỉnh tốc độ |
| Bảng kỹ thuật `/service` trên Pi | gọi thẳng, không qua MQTT | như trên + đặt vị trí, đổi chiều, đổi dạng xung |

Mọi lối đều gọi cùng `LidController.open / close / jog` trên Pi, nên cùng tốc độ, cùng chiều, cùng vị trí đếm bước. Mỗi bước của luồng drone chỉ chạy khi bước trước báo thành công.

Cấu hình phía hệ thống (business settings, scope `order`, sửa ở trang cấu hình admin):

| Khoá | Giá trị | Ý nghĩa |
|---|---|---|
| `app.drone.lid-test.enabled` | bật/tắt ở `/admin/drone-logs` | Chế độ thử nắp |
| `app.drone.lid-test.locker-id` | `7` | Tủ dùng để thử |
| `app.drone.lid-test.markers` | `0:39,1:40` | Mã ArUco → box ID |
| `app.drone.lid-test.hold-seconds` | `5` | Giữ nắp mở trước khi đóng |
| `app.drone.delivery.lid-motion-timeout-seconds` | `150` | Chờ tủ báo nắp chạy xong |

## 5. Cấu hình nằm ở đâu, sửa thế nào

Trên Pi, thư mục `~/iot/config/`:

| File | Chứa | Ưu tiên |
|---|---|---|
| `lid_tuning.json` | Tốc độ, dạng xung, chiều mở, chiều dài ray, bước/vòng của từng trục | **Cao nhất** cho thông số trục — đọc lúc khởi động, ghi lại mỗi khi chỉnh |
| `hardware_config.json` | Chân relay/phản hồi, thời gian kích, chân và ô của từng trục, `openDirHigh` | Ghi đè `.env`. Lưu cấu hình phần cứng sẽ **chép `openDirHigh` sang `lid_tuning.json`** — hai file phải khớp chiều |
| `lid_position.json` | Vị trí bàn trượt (vòng cách gốc) | Ghi sau mỗi lượt chạy |
| `~/iot/.env` | Chân mặc định, `LID1_BOXES=3`, `LID2_BOXES=2` | Thấp nhất. `LID_STEPS_PER_REV=400` và `LID_BYPASS_PHYSICAL_MOTION=true` trong file này **không còn tác dụng** (bị `lid_tuning.json` ghi đè / bị bỏ qua) |

Giá trị đang chạy — `lid_tuning.json`:

```json
{
  "1": {"rps": 1.79, "start_rps": 0.2, "ramp_steps": 100, "pulse_us": 300, "max_revs": 36.0,
        "steps_per_rev": 200, "open_dir_high": true,  "limit_active_low": true, "profile": "chaydan"},
  "2": {"rps": 1.79, "start_rps": 0.2, "ramp_steps": 100, "pulse_us": 300, "max_revs": 36.0,
        "steps_per_rev": 200, "open_dir_high": false, "limit_active_low": true, "profile": "chaydan"}
}
```

Sửa thông số trục — một trong các cách (đều ghi `lid_tuning.json`, không cần khởi động lại):
- bảng `/service` trên Pi → mục trục (mở qua SSH tunnel: `ssh -L 8800:127.0.0.1:8000 lockr@lockr-tu01.local` rồi vào `http://localhost:8800/service`);
- trên Pi: `curl -X PUT http://127.0.0.1:8000/service/api/lids/2/tuning -H 'Content-Type: application/json' -d '{"rps": 1.0}'`;
- web admin → **Điều khiển tủ** → mục trục → **Chỉnh thông số** (chỉ tốc độ, độ rộng xung, bước/vòng, chiều dài ray).

Đổi chiều mở (`open_dir_high`) thì sửa **cả** `lid_tuning.json` (qua `/service` hoặc API trên) **và** `openDirHigh` trong `hardware_config.json`, nếu không lần lưu cấu hình phần cứng sau sẽ đổi chiều trở lại. Sao lưu file trước khi sửa (`cp lid_tuning.json lid_tuning.json.bak-<mô tả>-<giờ>`).

## 6. Kiểm tra chiều và tốc độ trên tủ

Luôn có người đứng nhìn nắp khi chạy motor.

1. Xem trạng thái: trên Pi `curl -s http://127.0.0.1:8000/service/api/overview` (mục `lids[].status`: `state`, `positionRevs`, `config`).
2. Chạy thử 5 vòng về phía **đóng** khi nắp đang mở (hoặc về phía **mở** khi nắp đang đóng):
   `curl -X POST http://127.0.0.1:8000/service/api/lids/2/jog -H 'Content-Type: application/json' -d '{"revolutions":5,"direction":"close"}'`
   Nắp đi đúng hướng ⇒ chiều đúng. Đi ngược ⇒ đảo `open_dir_high` (§ 5). Đứng yên ⇒ có thể nắp đang ở sát đầu ray phía đó — thử chiều kia.
3. Thử tay không qua phần mềm (phải dừng `lockr-controller` trước, xong bật lại) — hàm `chaydan` ở [tu01-so-do-tong-quan § 8](tu01-so-do-tong-quan.md#8-kiểm-tra-trên-tủ); `dh`/`dl` ứng với mở/đóng theo bảng § 2.

## 7. Lịch sử chỉnh ngày 04/11

| Giờ | Trục | Thay đổi | Lý do |
|---|---|---|---|
| sáng | 1, 2 | `profile: "chaydan"`, `rps: 1,79` | Thông số cũ (0,5 vòng/s, xung 300 µs) làm motor kêu è è không quay |
| 16:15 | 1 | `open_dir_high: false → true` | Thử mã #1: lệnh mở đẩy nắp vào đầu đóng, lệnh đóng lại mở hết |
| 17:10 | 2 | `rps: 1,79 → 1,04` | Nắp ô 2 khởi động rung, chạy nửa ray rồi đứng |
| 17:27 | 2 | `open_dir_high: true → false` | Lệnh đóng kéo nắp ô 2 ra hết; sau khi đổi, lệnh đóng chạy đúng hướng |
| 17:39 | 2 | `rps: 1,04 → 0,5` + sửa code để nấc tăng tốc không nhanh hơn `rps` | Vẫn đứng giữa ray khi đóng |
| tối | 2 | `rps: 0,5 → 1,79` (giống trục 1) | Theo yêu cầu, sau khi các lượt mở/đóng ở 0,5 vòng/s chạy hết ray. Nếu lại khựng giữa ray ⇒ hạ `rps` (§ 3) |

Bản sao lưu các file cấu hình trước mỗi lần chỉnh: `~/iot/config/*.bak-*` trên Pi.
