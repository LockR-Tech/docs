# Chạy hệ thống trên máy cá nhân

Lệnh để dựng từng thành phần Lock.R trên máy mình, cổng mặc định, và những cái bẫy đã thực sự gặp. Dành cho người vừa vào dự án hoặc vừa đổi máy.

> **Chỉ sửa giao diện thì không cần dựng backend.** Admin web gọi `VITE_API_BASE_URL`, mặc định `https://api.locker-drone.tech` (`frontend/fe/src/constants/api-paths.ts:5-6`); kiosk proxy `/api` sang cùng địa chỉ; app mobile đọc `API_BASE_URL` từ `.env` cũng trỏ production. Cả nhóm dùng chung một server + một database — **thao tác trên máy bạn là thao tác trên dữ liệu thật**. Sửa backend hoặc không muốn đụng dữ liệu thật thì dựng backend trên máy: [§ Chạy backend trên máy](#chạy-backend-trên-máy).

Đường dẫn ví dụ `D:\LockR\…` — thay bằng thư mục bạn clone các repo. Dựng Raspberry Pi cho tủ thật: [03-hardware/controller-wiring-guide.md § 4](../03-hardware/controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm).

## Yêu cầu công cụ

| Công cụ | Bản đã kiểm | Dùng cho |
|---|---|---|
| Flutter | 3.44.9 stable (Dart SDK `^3.11.5`) | mobile |
| Node.js | 24.x | admin web, landing page, kiosk |
| uv | 0.12.x | giả lập tủ IoT (Python) |
| Android SDK | có emulator `Pixel_9` | mobile trên máy ảo |
| Docker Desktop | mới | chỉ khi chạy backend trên máy |
| JDK · Maven | 21 (`backend/pom.xml:38`) · 3.9+ — repo **không có** `mvnw` | chỉ khi chạy backend trên máy |

## Bảng tra nhanh

| Thành phần | Thư mục | Lệnh | Cổng |
|---|---|---|---|
| Admin web | `frontend/fe` | `npm run dev` | 3000 (`strictPort`) |
| Landing page | `frontend/landingPage` | `npm run dev` | 5173 |
| Kiosk (màn hình tại tủ) | `iot/ui` | `npm run dev` | 3002 |
| Mobile (máy ảo) | `mobile` | `flutter run -d emulator-5554` | — |
| Mobile (trình duyệt) | `mobile` | `flutter run -d chrome` | ngẫu nhiên |
| Giả lập tủ IoT | `iot` | `uv run python simulate_demo_cabinet.py` | — (MQTT) |
| Backend (tuỳ chọn) | `backend` | `mvn -B clean package -DskipTests` → `docker compose up -d --build` | 18080 (gateway) |

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

Cần API cục bộ `:8000` của Pi controller (kiosk gọi `/system/info`) thì chạy `main.py` ở chế độ giả lập, kèm Postgres riêng:

```powershell
cd D:\LockR\iot
docker compose -f docker-compose.postgres.yml up -d    # Postgres :5432, mật khẩu mặc định — chỉ dùng trên máy dev
$env:SIMULATION = "true"
uv run python main.py                                  # log "System is READY", API http://localhost:8000
```

## Chạy backend trên máy

Dùng khi sửa backend hoặc không muốn đụng dữ liệu production.

### Build và bật

```powershell
cd D:\LockR\backend
mvn -B clean package -DskipTests       # build jar TRƯỚC — Dockerfile chép target/*.jar
docker compose up -d --build           # Postgres, RabbitMQ, Eureka, gateway, 11 service
```

- `docker compose up` **từ chối chạy** khi thiếu `APP_SECURITY_JWT_SECRET` (`backend/docker-compose.yml:69,124,280`). Tạo `backend/.env` (đã gitignore) với secret sinh bằng `openssl rand -base64 48` — [cau-hinh-dich-vu-ngoai § 3](cau-hinh-dich-vu-ngoai.md#3-jwt-secret-sec-01--làm-trước-tiên).
- Jar cũ/hỏng ⇒ container restart liên tục với `ClassNotFoundException`, vì Dockerfile chỉ chép `${MODULE}/target/*.jar` (`backend/order-service/Dockerfile:5`). Build lại rồi `up --build`.
- Lần đầu mất vài phút; Flyway tự tạo schema khi từng service khởi động.

### Kiểm tra

```powershell
docker compose ps                       # mọi container "running", không restart liên tục
docker compose logs -f api-gateway      # log một service
```

| Địa chỉ | Là gì |
|---|---|
| `http://localhost:18080` | API gateway — cổng duy nhất để gọi API (`API_GATEWAY_PORT`, `docker-compose.yml:80`) |
| `http://localhost:8761` | Eureka — phải thấy 11 service đăng ký (auth, user, order, locker, payment, notification, iot, store, loyalty, assistant, gateway) |
| `http://localhost:15672` | RabbitMQ UI, tài khoản mặc định của RabbitMQ |
| `localhost:15432` · `localhost:15433` | Postgres chính (`ll-ms-postgres`) · Postgres pgvector của trợ lý |

Eureka, RabbitMQ và hai Postgres chỉ nghe `127.0.0.1` (`docker-compose.yml:12,33,53,407`). Service vừa lên cần 30–60 giây để đăng ký Eureka — gọi sớm hơn nhận `503`.

### Dữ liệu mẫu và tài khoản

```powershell
Get-Content scripts\seed-local-complete.sql -Raw | docker exec -i ll-ms-postgres psql -U postgres -v ON_ERROR_STOP=1
```

- Chạy sau khi backend đã lên ít nhất một lần (Flyway phải tạo xong schema — `scripts/seed-local-complete.sql:7-12`). Script **xoá sạch** dữ liệu nghiệp vụ rồi nạp lại; tài khoản mẫu ghi ở đầu file script.
- Admin mặc định do `AdminBootstrap` tạo lúc `auth-service` khởi động, lấy từ `BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` (`docker-compose.yml:117-120`). Seed xoá bảng tài khoản ⇒ admin mặc định mất cho tới khi restart `auth-service`.
- API đăng nhập nhận field **`identifier`**, không phải `email` (`auth-service/…/dto/LoginRequest.java:5`).

### Biến môi trường

Đặt trong `backend/.env`. Chỉ ghi **tên** biến ở đây; cách lấy giá trị thật: [cau-hinh-dich-vu-ngoai](cau-hinh-dich-vu-ngoai.md).

| Biến | Mặc định | Khi nào đổi |
|---|---|---|
| `APP_SECURITY_JWT_SECRET` | **không có — bắt buộc** | luôn phải đặt |
| `API_GATEWAY_PORT` | `18080` | cổng bị chiếm |
| `APP_CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:3001` (`docker-compose.yml:72`) | web chạy ở cổng khác — kiosk dev ở 3002 phải thêm vào |
| `BOOTSTRAP_ADMIN_EMAIL` · `BOOTSTRAP_ADMIN_PASSWORD` | giá trị dev trong compose | đặt riêng trên mọi môi trường không phải máy dev |
| `SPRING_MAIL_*` | auth: `localhost:1025`; notification: trống ⇒ tắt kênh email | gửi email thật |
| `FIREBASE_CREDENTIALS_JSON` | trống | đăng nhập số điện thoại / Google, push |
| `VNPAY_*` · `MOMO_*` | sandbox/demo, URL trả về mặc định `localhost:8080` | thử thanh toán thật |
| `MQTT_BROKER_URL` | `tcp://broker.hivemq.com:1883` (`iot-service/…/application.yml:81`) | broker riêng (SEC-04) |

### Sửa code rồi chạy lại một service

```powershell
mvn -B clean package -DskipTests -pl order-service -am
docker compose up -d --build order-service
```

### Trỏ ứng dụng về backend trên máy

| Ứng dụng | Đặt | Ghi chú |
|---|---|---|
| Admin web | `frontend/fe/.env`: `VITE_API_BASE_URL=http://localhost:18080` | xoá dòng ⇒ về production; khởi động lại `npm run dev` |
| Mobile | `mobile/.env`: `API_BASE_URL=` `http://10.0.2.2:18080` (máy ảo Android) · `http://localhost:18080` (iOS simulator, web) | app đọc `API_BASE_URL`, **không** phải `API_URL` (`mobile/lib/core/config/env_config.dart:9-10`); đổi `.env` xong chạy `dart run build_runner build --delete-conflicting-outputs` rồi `flutter run` lại |
| Mobile web | `flutter run -d chrome --web-port 3001` | cổng 3001 nằm trong CORS mặc định |
| Kiosk | `iot/ui/.env`: `VITE_API_URL=http://localhost:18080` | thêm `http://localhost:3002` vào `APP_CORS_ALLOWED_ORIGINS`; để trống ⇒ proxy về production (`iot/ui/src/api.js:18`) |

- `mobile/lib/core/config/env_config.g.dart` được commit sẵn với URL production. **Đừng commit** bản đã sinh với localhost.
- Điện thoại thật qua Wi-Fi (`http://192.168.x.x:18080`) bị Android chặn HTTP — `network_security_config.xml:8-12` chỉ cho `10.0.2.2`, `localhost`, `127.0.0.1`. Dùng `adb reverse tcp:18080 tcp:18080` rồi `API_BASE_URL=http://localhost:18080`.

### Lỗi hay gặp khi chạy backend

| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| `docker compose up` báo `APP_SECURITY_JWT_SECRET … chua dat` | Thiếu secret trong `backend/.env` |
| Container restart liên tục, `ClassNotFoundException` | Jar cũ/hỏng — `mvn -B clean package -DskipTests` rồi `up -d --build` |
| API trả `503` ngay sau khi bật | Service chưa đăng ký Eureka — đợi 30–60 giây |
| Web báo CORS khi gọi backend trên máy | Web phải chạy ở 3000/3001, hoặc thêm origin vào `APP_CORS_ALLOWED_ORIGINS` rồi bật lại gateway |
| Mobile vẫn gọi production dù đã sửa `.env` | Quên `build_runner`, hoặc sửa `API_URL` thay vì `API_BASE_URL` |
| Đăng nhập lỗi dù đúng mật khẩu | Body phải dùng field `identifier` |
| Seed báo thiếu bảng | Backend chưa khởi động xong lần nào — Flyway chưa tạo schema |
| Admin mặc định không đăng nhập được sau khi seed | Seed xoá bảng tài khoản — `docker compose restart auth-service` |
| Cổng `15432` / `5432` bị chiếm | Tắt Postgres cài sẵn trên máy, hoặc đổi cổng trong file compose |

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

Giả lập IoT thì Ctrl+C trong cửa sổ đang chạy. Backend trên máy:

```powershell
cd D:\LockR\backend
docker compose down        # tắt, GIỮ dữ liệu
docker compose down -v     # tắt và XOÁ database (volume postgres_data, assistant_db_data)
```
