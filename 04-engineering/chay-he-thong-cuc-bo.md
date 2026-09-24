# Chạy hệ thống trên máy cá nhân

Lệnh để dựng từng thành phần Lock.R trên máy mình, cổng mặc định, và những cái bẫy đã thực sự gặp. Dành cho người vừa vào dự án hoặc vừa đổi máy.

> **Không cần dựng backend local.** Admin web và kiosk đều proxy `/api` sang `https://api.locker-drone.tech`; app mobile đọc `API_BASE_URL` từ `.env` cũng trỏ production. Cả nhóm dùng chung một server + một database — **thao tác trên máy bạn là thao tác trên dữ liệu thật**.

## Yêu cầu công cụ

| Công cụ | Bản đã kiểm | Dùng cho |
|---|---|---|
| Flutter | 3.44.9 stable (Dart SDK `^3.11.5`) | mobile |
| Node.js | 24.x | admin web, landing page, kiosk |
| uv | 0.12.x | giả lập tủ IoT (Python) |
| Android SDK | có emulator `Pixel_9` | mobile trên máy ảo |

## Bảng tra nhanh

| Thành phần | Thư mục | Lệnh | Cổng |
|---|---|---|---|
| Admin web | `frontend/fe` | `npm run dev` | 3000 (`strictPort`) |
| Landing page | `frontend/landingPage` | `npm run dev` | 5173 |
| Kiosk (màn hình tại tủ) | `iot/ui` | `npm run dev` | 3002 |
| Mobile (máy ảo) | `mobile` | `flutter run -d emulator-5554` | — |
| Mobile (trình duyệt) | `mobile` | `flutter run -d chrome` | ngẫu nhiên |
| Giả lập tủ IoT | `iot` | `uv run python simulate_demo_cabinet.py` | — (MQTT) |

Cổng lấy từ `vite.config` của từng repo nên chạy mặc định là đủ, không đụng nhau. Đừng ép `--port` nếu không có lý do.

## Admin web

```powershell
cd D:\LockR\frontend\fe
npm install      # lần đầu
npm run dev
```

→ http://localhost:3000

## Landing page

```powershell
cd D:\LockR\frontend\landingPage
npm run dev
```

→ http://localhost:5173

## Kiosk

```powershell
cd D:\LockR\iot\ui
npm install      # lần đầu
npm run dev
```

→ http://localhost:3002 — chọn tủ ở dropdown đầu trang, hai luồng **Mở Tủ / Nhận Đồ** (mã PIN hoặc QR) và **Gửi Đồ / Thuê Tủ**.

## Mobile

```powershell
cd D:\LockR\mobile
flutter pub get                         # lần đầu hoặc khi pubspec đổi
flutter emulators --launch Pixel_9
flutter run -d emulator-5554
```

Máy ảo mất ~30–60 giây để boot; `flutter run` báo không thấy thiết bị thì chờ rồi chạy lại. Trong lúc `flutter run` chạy: `r` hot reload · `R` hot restart · `q` thoát.

`API_BASE_URL` đọc từ `mobile/.env` (gitignore). Mặc định trỏ production; chạy backend local thì dùng `http://10.0.2.2:18080` cho máy ảo Android, và **đổi `.env` xong phải chạy lại**:

```powershell
dart run build_runner build --delete-conflicting-outputs
```

### Mobile trên web

`flutter run -d chrome` dựng được, **nhưng màn đăng nhập nổ**: `main.dart` bỏ qua `Firebase.initializeApp` khi `kIsWeb`, trong khi `login_screen` vẫn dựng `FirebaseAuth.instance` trong `initState`.

```
TypeError: Instance of 'FirebaseException': type 'FirebaseException'
is not a subtype of type 'JavaScriptObject'
```

Dùng máy ảo Android để test luồng khách.

## Giả lập tủ IoT

Không có Raspberry Pi + Arduino thì đây là cách duy nhất chạy trọn vòng mở tủ.

```powershell
cd D:\LockR\iot
uv sync                                        # lần đầu
uv run python simulate_demo_cabinet.py
```

Nó nối `broker.hivemq.com:1883` — **đúng broker mà `iot-service` production dùng** (`application.yml` → `${MQTT_BROKER_URL:tcp://broker.hivemq.com:1883}`, compose không override) — rồi subscribe `cabinet/+/command/open` và `cabinet/+/command/sync`, trả lời như tủ thật.

| Biến | Tác dụng |
|---|---|
| `SIM_HEARTBEAT_CABINETS=1,2,3,4,5` | báo các tủ ONLINE ngay khi kết nối |
| `SIM_FORCE_FAIL=true` | luôn trả FAILED — test đường lỗi |
| `SIM_DELAY_SECONDS=8` | cửa mở chậm; đặt > 20 để ép timeout phía backend |

```powershell
$env:SIM_HEARTBEAT_CABINETS = "1,2,3,4,5"
uv run python simulate_demo_cabinet.py
```

⚠️ **Đừng dùng `SIMULATION=true uv run python main.py`** cho việc này: hợp đồng MQTT của `main.py` lệch với backend (cần `slotIndex`, dùng **tên** tủ trong topic) và nó còn chờ handshake `SETUP_LOCKERS` mà hiện không ai gửi — gap **F2-G09**. Chỉ `simulate_demo_cabinet.py` chạy end-to-end.

## Năm cái bẫy đã gặp

1. **Giả lập trả lời cho *mọi* tủ trên broker công khai dùng chung.** Hai người cùng chạy thì cả hai cùng trả lời một lệnh mở tủ. Nó cũng ghi thật vào production: heartbeat làm tủ hiện ONLINE ở `GET /api/manage/iot/device-status`, mỗi lần mở ghi `hwState` cho ô. Đây chính là **SEC-04** — ai publish vào `cabinet/{id}/command/open` cũng mở được tủ.

2. **`flutter run` tự thoát** với `Lost connection to device` khi app bị vuốt tắt hoặc Android kill tiến trình nền. App vẫn nằm trên máy ảo nhưng mất hot reload; chạy lại `flutter run` là xong.

3. **`adb` không có trong PATH.** Dùng đường dẫn đầy đủ:
   ```powershell
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" emu kill     # tắt máy ảo
   ```

4. **Ctrl+C không phải lúc nào cũng nhả cổng** — `node` và `dartvm` sống sót sau khi shell cha bị tắt. Chạy lại mà báo cổng bận:
   ```powershell
   Get-NetTCPConnection -LocalPort 3000 -State Listen |
     ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
   ```

5. **Máy SA-KT32**: `cmdline-tools` bản 23 bỏ `--licenses`, giữ bản 19. Smart App Control từng chặn binary không ký — đã tắt vĩnh viễn 21/09/2026.

## Tắt sạch

```powershell
foreach ($p in 3000,3002,5173) {
  Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
}
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" emu kill
```

Giả lập IoT thì Ctrl+C trong cửa sổ đang chạy.
