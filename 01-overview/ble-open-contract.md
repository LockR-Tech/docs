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

### 4.1 Phía app (điện thoại thật)

Code: mobile `lib/core/services/locker_ble_open_service.dart`.

- **Chọn tủ khi quét (10 s):** đúng tên `deviceName` ⇒ dừng quét ngay. Chỉ khớp một phần tên (`LockerBleService.isDeviceMatchingLocker`) hoặc chỉ có service UUID ⇒ chờ thêm 1,5 s rồi chọn: khớp chắc hơn trước, cùng mức thì RSSI mạnh hơn (tủ đang đứng trước). Mọi Pi quảng bá cùng service UUID nên không lấy bừa thiết bị đầu tiên.
- **Không đòi bật Vị trí:** quét với `androidCheckLocationServices: false` — Android 12+ có `BLUETOOTH_SCAN neverForLocation`. Android 11 trở xuống không quét ra gì khi tắt Vị trí ⇒ báo `NOT_FOUND_LOCATION_OFF`.
- **Kết nối:** thử tối đa 3 lần (Android hay báo GATT 133 ở lần đầu). Cần MTU ≥ 94; Android xin 512 khi kết nối, thiếu thì xin lại 247, vẫn thiếu ⇒ `MTU_TOO_SMALL`. Không thấy service ⇒ Android xoá bộ nhớ GATT (`clearGattCache`) rồi tìm lại một lần.
- **Chờ kết quả:** bật notify RESULT; không bật được thì đọc RESULT mỗi 0,8 s. Mất kết nối sau khi đã ghi ⇒ `DISCONNECTED` (ô có thể đã mở).
- **iOS:** quyền Bluetooth đọc từ trạng thái CoreBluetooth (`unauthorized`), không qua `permission_handler` (cần macro `PERMISSION_BLUETOOTH` trong Podfile, repo không commit Podfile).

Mã lỗi phía app (ngoài mã Pi ở § 3): `NOT_FOUND`, `NOT_FOUND_LOCATION_OFF`, `CONNECT_FAILED`, `NO_SERVICE`, `MTU_TOO_SMALL`, `WRITE_FAILED`, `DISCONNECTED`, `TIMEOUT`, `BLUETOOTH_OFF`, `PERMISSION_DENIED`, `UNSUPPORTED`. Trang thử in kèm mã lỗi dưới câu báo.

## 5. Cài đặt Pi

- Thư viện: `bless` + `bleak < 1` (chỉ Linux) và `cryptography` — `uv sync` sau khi pull.
- `.env`: `BLE_GATT_ENABLED` (mặc định `true`), `BLE_PUBLIC_KEY` (base64, ghi đè khoá tải về — để thử khi chưa có backend), `BLE_PUBLIC_KEY_FILE` (mặc định `config/ble_public_key.json`, không commit). Khoá tải từ `BACKEND_API_URL` (trống ⇒ `https://api.locker-drone.tech`).
- GATT server tự quảng bá tên `LOCKR_<mã tủ>`; chạy được thì không bật quảng bá kiểu cũ (`BleAdvertiserService`), không chạy được (không có Bluetooth, thiếu thư viện, BlueZ từ chối) thì quay về quảng bá cũ để app vẫn nhận ra tủ ở gần.
- Tài khoản `lockr` không cần thêm nhóm: chính sách D-Bus mặc định của BlueZ trên Raspberry Pi OS cho mọi người dùng gửi tới `org.bluez`.

## 6. Thử bằng điện thoại khi chưa có tủ

`iot/simulate_ble_cabinet.py` chạy đúng `BleGattService` của Pi trên laptop có Bluetooth (Windows, macOS, Linux): tải khoá công khai production, kiểm chữ ký, tủ, hạn, nonce như Pi; relay giả chỉ in `MỞ Ô n`. Điện thoại dùng mã thật xin từ production, nên chạy được ở đây thì sang tủ thật cũng chạy.

1. Admin web → `/admin/lockers/7` (`CAB-TU01`) → khung "Thử mở ô qua Bluetooth" → cấp cho tài khoản khách sẽ thử.
2. Trên laptop, trong thư mục `iot` (Python ≥ 3.11, không cần `uv`):
   ```bash
   python -m venv .venv-ble
   .venv-ble\Scripts\pip install "bless==0.2.6" "bleak<1" "cryptography>=43"   # Windows
   .venv-ble\Scripts\python simulate_ble_cabinet.py --locker-id 7 --locker-code CAB-TU01 --boxes 8
   ```
   Bỏ `--locker-id` ⇒ nhận mã của tủ bất kỳ. `--fail-box 3` ⇒ ô 3 báo `HARDWARE_ERROR`.
3. App: Hồ sơ → **Thử mở ô qua Bluetooth** → chọn ô → Mở. Cửa sổ laptop in mã nhận được và câu trả lời cho app.

Giới hạn: Windows không cho đặt tên quảng bá (bless cần `pysetupdi`, không có trên PyPI; script thay bằng adapter rỗng) ⇒ app nhận ra tủ giả theo service UUID, chỉ bật **một** tủ giả mỗi lần. Adapter phải hỗ trợ vai peripheral (đa số adapter Intel/Realtek từ Windows 10 trở lên).
