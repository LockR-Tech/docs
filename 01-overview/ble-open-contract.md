# Hợp đồng mở ô qua Bluetooth (BLE) — app ⇄ Pi

> Phiên bản 1.0 · 2026-10-24 · gap **F3-G11** · code: backend `iot-service` (`BleTestService`, `BleTokenSigner`), iot `services/ble_gatt_service.py` + `services/ble_open_token.py`, mobile `lib/core/services/locker_ble_open_service.dart`, web admin `BluetoothTestPanel.tsx`.

Chế độ **thử mở ô qua Bluetooth**: admin cho từng tài khoản khách thử trên từng tủ; tài khoản được cấp mở được **ô bất kỳ** của tủ đó bằng điện thoại, đứng cạnh tủ, không cần đơn. Lúc mở, Pi không cần mạng: nó tự kiểm chữ ký của mã do máy chủ cấp.

## 1. Luồng

```
Admin web  ── POST /api/admin/iot/ble-test/lockers/{lockerId}/users {userId} ──▶ iot-service (lưu quyền)
App (Hồ sơ) ── GET  /api/iot/ble-test/lockers ──▶ [] ⇒ ẩn nút · [≥1 tủ] ⇒ hiện "Thử mở ô qua Bluetooth"
App        ── POST /api/iot/ble-test/lockers/{lockerId}/boxes/{boxNumber}/token ──▶ mã 91 byte (sống 120 s)
App        ── BLE: quét LOCKR_<mã tủ> → kết nối → bật notify RESULT → ghi mã vào OPEN
Pi         ── kiểm chữ ký + tủ + hạn + chưa dùng ⇒ kích relay ô boxNumber ⇒ notify {"nonce","result","box"}
Pi         ── nhật ký điều khiển BOX_OPEN_BLE (kèm tài khoản) ──MQTT event/control──▶ iot-service
```

## 2. API (iot-service)

| Phương thức + đường dẫn | Ai gọi | Ghi chú |
|---|---|---|
| `GET /api/admin/iot/ble-test/lockers/{lockerId}/users` | ADMIN (gateway) | `[{lockerId, userId, grantedBy, createdAt}]` — web ghép tên/email từ danh sách người dùng |
| `POST /api/admin/iot/ble-test/lockers/{lockerId}/users` body `{userId}` | ADMIN | Cấp lại cho người đã có quyền là no-op |
| `DELETE /api/admin/iot/ble-test/lockers/{lockerId}/users/{userId}` | ADMIN | Mã đã cấp trước đó vẫn dùng được tới khi hết hạn (≤ 120 s) |
| `GET /api/iot/ble-test/lockers` | mọi JWT | Tủ của tài khoản đang đăng nhập: `[{lockerId, code, name}]` |
| `POST /api/iot/ble-test/lockers/{lockerId}/boxes/{boxNumber}/token` | mọi JWT, service kiểm quyền | 403 `BLE_TEST_NOT_GRANTED`, 404 `BOX_NOT_IN_LOCKER`, 503 `LOCKER_LOOKUP_FAILED`. Mỗi lần cấp ghi nhật ký điều khiển `BLE_TOKEN` / `ISSUED` |
| `GET /api/iot/ble/public-key` | **công khai** (Pi) | `{algorithm: "Ed25519", publicKey: <32 byte base64>, tokenVersion: 1}` |

Trả lời của `…/token`: `token` (base64url, không padding), `nonce` (hex), `expiresAt`, `lockerId`, `lockerCode`, `boxNumber`, `boxId`, `boxStatus` (app hỏi lại khi `OCCUPIED`), `deviceName` (`LOCKR_<mã tủ>`), `serviceUuid`, `openCharUuid`, `resultCharUuid`.

Không chặn ô đang có hàng — đây là chế độ thử do admin cấp; app bắt người dùng xác nhận trước khi mở ô `OCCUPIED`.

## 3. Mã mở ô (91 byte, big-endian)

| Byte | Trường |
|---|---|
| 0 | phiên bản = `1` |
| 1–4 | `lockerId` (u32) |
| 5–6 | `boxNumber` (u16) |
| 7–14 | `userId` (u64) |
| 15–18 | hết hạn, giây Unix (u32) — cấp lúc này + 120 s |
| 19–26 | nonce 8 byte ngẫu nhiên |
| 27–90 | chữ ký **Ed25519** trên byte 0–26 |

Khoá ký: một cặp Ed25519 sinh lần đầu cần dùng, lưu ở `iot_schema.ble_signing_keys` (Flyway iot **V8**, cùng bảng quyền `ble_test_grants`). Pi chỉ giữ **khoá công khai** nên lộ thẻ nhớ của Pi cũng không tự làm ra mã mở được. Đổi khoá = xoá dòng `id = 1` rồi khởi động lại iot-service; Pi tải khoá mới ở lần làm mới kế tiếp (6 giờ/lần, hoặc khởi động lại `lockr-controller`).

Pi từ chối (mã lỗi gửi lại app):

| Mã | Khi nào |
|---|---|
| `BAD_FORMAT` · `BAD_VERSION` | không đủ 91 byte / phiên bản lạ |
| `BAD_SIGNATURE` | chữ ký không khớp khoá công khai |
| `NO_KEY` | Pi chưa tải được khoá (cần có mạng ít nhất một lần) |
| `NOT_CONFIGURED` · `WRONG_LOCKER` | Pi chưa gán tủ / mã cho tủ khác |
| `EXPIRED` · `BAD_EXPIRY` | quá hạn (cho lệch đồng hồ 30 s) / hạn xa hơn 600 s |
| `REPLAYED` | nonce đã dùng (Pi nhớ tới khi mã hết hạn) |
| `INVALID_SLOT` · `HARDWARE_ERROR` | ô không có relay / lỗi phần cứng |

## 4. GATT trên Pi

| | UUID | Thuộc tính |
|---|---|---|
| Service | `06776521-9674-432d-b886-5e951244ffa3` | quảng bá kèm tên `LOCKR_<mã tủ>` |
| OPEN | `54af4ad7-dcde-47dc-ad44-fa2c7438dd36` | write (có phản hồi) — 91 byte trong **một** lần ghi (MTU ≥ 94; app Android xin MTU 247) |
| RESULT | `8a6e33a5-1b26-4e80-8faa-026bab93ad4e` | read + notify — JSON `{"nonce","result":"OK"\|"FAIL","box","error"}` |

App chỉ nhận kết quả có đúng `nonce` của mã vừa gửi; không có thông báo sau 15 s thì đọc RESULT một lần rồi báo `TIMEOUT`.

## 5. Cài đặt Pi

- Thư viện: `bless` + `bleak < 1` (chỉ Linux) và `cryptography` — `uv sync` sau khi pull.
- `.env`: `BLE_GATT_ENABLED` (mặc định `true`), `BLE_PUBLIC_KEY` (base64, ghi đè khoá tải về — để thử khi chưa có backend), `BLE_PUBLIC_KEY_FILE` (mặc định `config/ble_public_key.json`, không commit). Khoá tải từ `BACKEND_API_URL` (trống ⇒ `https://api.locker-drone.tech`).
- GATT server tự quảng bá tên `LOCKR_<mã tủ>`; chạy được thì không bật quảng bá kiểu cũ (`BleAdvertiserService`), không chạy được (không có Bluetooth, thiếu thư viện, BlueZ từ chối) thì quay về quảng bá cũ để app vẫn nhận ra tủ ở gần.
- Tài khoản `lockr` không cần thêm nhóm: chính sách D-Bus mặc định của BlueZ trên Raspberry Pi OS cho mọi người dùng gửi tới `org.bluez`.
