# Hướng dẫn nối dây bộ điều khiển tủ — Pi/Jetson, Arduino, relay, màn cảm ứng

| | |
|---|---|
| **Dùng khi** | Lắp tủ vật lý theo [sơ đồ nhà cung cấp](cabinet-wiring-spec.md) và đưa phần mềm trong repo `iot` lên chạy trên tủ đó |
| **Đối chiếu code** | `iot` tại `454c49a` · `backend` gateway CORS tại `api-gateway/src/main/resources/application.yml:186-196` |
| **Gap** | F2-G09 (tủ thật chạy end-to-end) — [flow-2](../02-flows/flow-2-locker-send.md) |

Đọc [cabinet-wiring-spec.md § 4](cabinet-wiring-spec.md#4-đối-chiếu-với-firmware-trong-repo) trước: firmware điều khiển tủ qua **Arduino trên bus RS485**, Pi/Jetson chỉ cần **một cổng USB** và màn hình. Hướng dẫn này đi theo kiến trúc đó.

## 0. Chọn Raspberry Pi hay Jetson

| Tiêu chí | Raspberry Pi 4B / 5 (4 GB) | Jetson Nano / Orin Nano |
|---|---|---|
| Vai trò trong hệ thống | `main.py` (MQTT, RS485, FastAPI :8000, Postgres) + kiosk Chromium | như nhau |
| GPIO cần dùng | **Không** — relay/cảm biến nằm bên Arduino | không; nếu sau này cắm TB6600 thẳng vào bo thì GPIO Jetson yếu (≈1 mA), phải qua đệm |
| Python 3.13 (`iot/.python-version`) | `uv sync` tự tải bản arm64 | như nhau (JetPack là Ubuntu arm64) |
| Docker cho Postgres cục bộ (`docker-compose.postgres.yml`) | cài `docker.io` | có sẵn trong JetPack |
| Bluetooth cho BLE beacon (`simulate_ble_advertiser.py:11-15`, BlueZ) | tích hợp | Nano gốc **không có** (cần card M.2 / USB dongle); Orin Nano dev kit có |
| Màn cảm ứng | DSI (màn chính hãng 7") **hoặc** HDMI + USB touch | chỉ HDMI/DP + USB touch |
| Nguồn | 5 V 3 A (Pi 4) · 5 V 5 A USB-C PD (Pi 5) | 5 V 4 A jack (Nano) · 19 V (Orin) |
| Giá, độ sẵn có ở Việt Nam | thấp, dễ mua | cao gấp 3–8 lần |

**Kết luận:** dùng **Raspberry Pi 4B hoặc 5, bản 4 GB**. Jetson không mang lại gì cho tủ vì phần mềm không chạy mô hình AI tại tủ (trợ lý RAG chạy ở backend). Chỉ cân nhắc Jetson khi có kế hoạch gắn camera nhận diện — hiện không có trong luồng nào.

## 1. Danh sách chuẩn bị

Đã có theo tài liệu nhà cung cấp: nguồn tổ ong 12 V, TB6600, Nema 17 + vít me, relay 8 kênh, domino, 7 khoá 12 V. Cần thêm:

| Nhóm | Hạng mục | SL | Thông số / vì sao |
|---|---|---|---|
| **Bo điều khiển** | Raspberry Pi 4B hoặc 5, 4 GB | 1 | xem § 0 |
| | Nguồn chính hãng cho Pi | 1 | Pi 4: 5 V 3 A USB-C · Pi 5: 27 W USB-C PD. **Không** kéo Pi từ nguồn 12 V qua buck rẻ — sụt áp là Pi reboot giữa chừng |
| | Thẻ microSD 32 GB A2 + Raspberry Pi OS 64-bit (Bookworm) | 1 | |
| | Tản nhiệt / quạt (Pi 5 bắt buộc) | 1 | tủ kín, nóng |
| | Arduino Uno R3 (hoặc Nano) | 1 | firmware `locker_controller.ino`; Uno đủ chân cho 7 ngăn ([spec § 5](cabinet-wiring-spec.md#5-bản-đồ-chân-arduino-uno-cho-7-ngăn)) |
| **RS485** | Bộ chuyển USB ↔ RS485 **tự đảo chiều** (auto-direction, chip CH340/CP2102) | 1 | firmware chờ 50 ms cho adapter phía Pi tự chuyển TX→RX (`locker_controller.ino:432-434`); `main.py` tự nhận chip CH340/CP210x/FTDI (`serial_manager.py:100`) |
| | Module MAX485 (TTL ↔ RS485) cho Arduino | 1 | DE và RE nối chung vào `D7` |
| | Dây xoắn đôi 2 lõi + 1 dây GND | ~2 m | A/B xoắn đôi; GND đi kèm để hai đầu bus cùng mức |
| | Điện trở 120 Ω | 1–2 | chỉ cần nếu bus dài hơn ~3 m |
| **Nguồn phụ** | Bộ hạ áp 12 V → 5 V, ≥ 3 A (buck) | 1 | nuôi module relay `JD-VCC` (7 relay ≈ 0,5 A) — **không** lấy 5 V từ Pi hay Arduino như tài liệu gốc |
| | Cầu chì 12 V (10 A) + đế | 1 | ngay sau `+V` nguồn tổ ong |
| | Diode 1N4007 | 7 | mắc song song từng khoá (cathode về +12 V) — dập xung ngược khi relay ngắt, tuổi thọ tiếp điểm |
| | Thanh domino / cầu đấu GND chung | 1 | GND của 12 V, buck 5 V, Arduino, MAX485 phải chung |
| **Màn hình** | *Chọn A:* Raspberry Pi Touch Display 2 (7", DSI) | 1 | cắm cáp DSI + 5 V từ header, không tốn USB/HDMI; chỉ cho Pi |
| | *Chọn B:* màn HDMI 7–10,1" có cảm ứng USB (1024×600 trở lên) | 1 | chạy được cả Pi lẫn Jetson; Pi 4/5 cần cáp micro-HDMI; màn ăn ~1 A 5 V → cấp nguồn riêng, đừng rút từ USB Pi |
| **Mạng** | Ethernet tới tủ (ưu tiên) hoặc Wi-Fi ổn định | 1 | Pi ra Internet tới `api.locker-drone.tech` và broker MQTT |
| **Dụng cụ** | Đồng hồ vạn năng, tuốc-nơ-vít domino, kìm bấm cos, dây bút test | | kiểm cực tính và mức logic trước khi cấp 12 V |

Khoá 12 V: mỗi lần chỉ **một** khoá hút tối đa 1 s (`locker_controller.ino:354-369`, lệnh tuần tự `serial_manager.py:407-440`), nên nguồn tổ ong **12 V 10 A** là đủ cho 7 khoá + động cơ bước; kiểm dòng danh định trên nhãn khoá để chắc.

## 2. Sơ đồ khối

```
220 V ─► Nguồn tổ ong 12 V ─┬─► cầu chì 10 A ─► domino +12 V ─► [7 khoá +] 
                            │                                  [TB6600 VCC]  (nắp trượt, § 3.E)
                            └─► Buck 12→5 V ─► relay JD-VCC (+5 V), GND chung

Pi ──USB──► adapter USB-RS485 ──A/B/GND──► MAX485 ──► Arduino Uno
 │                                                     ├─ D2 D4 D5 D3 D8 D10 A5 ─► relay IN1…IN7 ─► COM/NO ─► [khoá −]
 │                                                     └─ D11 D12 A0 A1 A2 A3 A4 ◄─ dây tín hiệu khoá (về GND)
 ├──USB──► Arduino (nguồn + cổng debug /dev/ttyACM0, tuỳ chọn)
 ├──DSI hoặc HDMI+USB──► màn cảm ứng
 └──LAN/Wi-Fi──► Internet (backend, MQTT)
```

## 3. Thứ tự nối dây

Làm theo thứ tự, **tắt 220 V** trong suốt các bước A–E. Mỗi bước có một phép kiểm tra trước khi sang bước sau.

### A. Nguồn

1. Nối `L`, `N`, `GND` (tiếp địa thật) vào nguồn tổ ong. Chưa cắm điện.
2. `+V` → cầu chì 10 A → domino +12 V. `-V` → domino GND chung.
3. Buck 12→5 V: vào từ domino 12 V, chỉnh ra **đúng 5,0 V** (đo bằng đồng hồ trước khi nối tải), GND về domino GND chung.
4. **Kiểm:** cắm 220 V, đo domino 12 V = 12,0 ± 0,5 V; buck = 5,0 ± 0,1 V. Rút điện.

### B. Relay và khoá

1. Module relay: rút jumper `VCC–JD-VCC`. `JD-VCC` ← buck 5 V, `GND` ← domino GND. `VCC` (phía tín hiệu) ← `5V` của Arduino, `GND` ← `GND` Arduino. Cách ly opto chỉ có tác dụng khi làm đúng bước này.
2. Mỗi khoá: dây **+** → domino +12 V; dây **−** → `NO` của relay kênh tương ứng; `COM` của relay → domino GND. Mắc diode 1N4007 song song hai dây nguồn khoá, **vạch trắng (cathode) về phía +12 V**.
3. Ghi số ngăn `0…6` lên relay và lên domino tín hiệu, theo đúng thứ tự dây nhà cung cấp kéo (từ phải qua trái, nhìn từ sau tủ).
4. **Kiểm:** chưa nối Arduino. Cấp 12 V. Chạm dây từ `IN1` xuống `GND` (nếu module kích LOW) hoặc lên `5 V` (nếu kích HIGH) trong **dưới 1 giây** → relay kêu tách, khoá 0 giật chốt. Ghi lại module kích LOW hay HIGH — cần cho bước 4.2. Rút điện.

### C. Cảm biến cửa (dây tín hiệu khoá)

1. Mỗi khoá có một cặp dây nhỏ: một dây → chân `MAGNETIC_PINS[slot]` của Arduino, dây kia → `GND` Arduino. Không cần điện trở — firmware bật `INPUT_PULLUP` (`locker_controller.ino:55`).
2. Firmware coi **LOW = cửa đóng** (`:150`). Nếu công tắc trong khoá *đóng mạch khi cửa mở* thì kết quả sẽ ngược — sẽ thấy ở bước 5.2 và sửa bằng cách đổi sang cặp tiếp điểm còn lại (nếu khoá có 3 dây) hoặc đảo phép so sánh trong firmware.

### D. Arduino ↔ RS485 ↔ Pi

| MAX485 | Arduino Uno | Ghi chú |
|---|---|---|
| `RO` | `D6` | `SSerialRX` (`locker_controller.ino:4`) |
| `DI` | `D9` | `SSerialTX` (`:5`) |
| `DE` + `RE` nối chung | `D7` | `SSerialTxControl` (`:6`) — LOW = nhận |
| `VCC` | `5V` | |
| `GND` | `GND` | |
| `A`, `B` | ↔ `A`, `B` adapter USB-RS485 | xoắn đôi; nhầm A/B thì im lặng chứ không hỏng — thử đảo |
| — | GND ↔ GND adapter | dây thứ ba đi kèm A/B |

1. Cắm adapter USB-RS485 vào Pi. Trên Pi: `ls /dev/serial/by-id/` → ghi lại đường dẫn `usb-…CH340…` — dùng nó thay vì `AUTO` ở bước 4.4.
2. Nguồn cho Arduino: cắm USB Arduino vào Pi (vừa cấp nguồn vừa có cổng debug `/dev/ttyACM0`). Relay không ăn dòng từ Arduino vì đã tách `JD-VCC` ở B.1.
3. Bus dài hơn ~3 m: điện trở 120 Ω giữa A–B ở đầu xa nhất.

### E. Nắp trượt — TB6600 + Nema 17 (tuỳ chọn, làm sau)

Chưa có code nào điều khiển động cơ bước, và luồng drone (F1.06) đang chạy giả lập. Ba đường, chọn một khi tới lúc:

| | Cách | Cần làm | Khi nào hợp |
|---|---|---|---|
| E1 | **Arduino Mega** thay Uno, TB6600 nối vào Mega | chuyển `SoftwareSerial` sang `Serial1`, thêm lệnh nắp (`L0`/`L1`) vào giao thức RS485 + `serial_manager.py`, công tắc hành trình 2 đầu | muốn nắp chạy trong học kỳ này |
| E2 | Pi cắm thẳng GPIO như tài liệu gốc | `PUL+`/`DIR+` nối **3,3 V** (không phải 5 V — GPIO Pi 3,3 V để lại 1,7 V dư trên opto, TB6600 không tắt hẳn), `PUL-`/`DIR-` → GPIO; viết module Python mới (`lgpio`/`gpiozero`, Pi 5 không có `pigpio`) | không muốn đổi Arduino |
| E3 | Nắp vận hành tay cho buổi demo | không | trước mắt |

Chỉnh DIP TB6600 theo dòng ghi trên nhãn Nema 17 (thường 1,2–1,7 A) và vi bước 1/8; **rút điện 12 V** trước khi tháo giắc động cơ (mục 3 tài liệu gốc).

### F. Màn cảm ứng

- **DSI (Pi Touch Display 2):** cáp DSI vào cổng `DISP`; `5V`/`GND` từ header 40 chân theo sơ đồ đi kèm màn. Xong.
- **HDMI + USB:** HDMI vào cổng `HDMI0` của Pi (cáp micro-HDMI với Pi 4/5), cáp USB touch vào Pi, nguồn màn từ adapter riêng 5 V ≥ 2 A.
- Chưa cần xoay màn ở bước này; kiosk UI hiện dùng bố cục ngang.

### G. Mạng và nguồn Pi

Ethernet vào Pi, nguồn chính hãng vào cổng USB-C. Chưa bật.

## 4. Nạp firmware và cấu hình phần mềm

### 4.1 Firmware Arduino

Sketch trong repo **đã khớp sơ đồ đấu nối**: 7 ngăn, `SLAVE_ID = 1`, mảng trạng thái bám `NUM_SLOTS` ([spec § 5](cabinet-wiring-spec.md#5-bản-đồ-chân-arduino-uno-cho-7-ngăn)). Mở `iot/arduino/locker_controller/locker_controller.ino` bằng Arduino IDE rồi nạp qua USB.

Chỉ còn hai chỗ phải tự quyết theo phần cứng thật:

| Dòng | Khi nào sửa | Vì sao |
|---|---|---|
| `:32-33` `RELAY_ON` / `RELAY_OFF` | Bước B.4 cho thấy module kích **LOW** ⇒ đổi thành `LOW` / `HIGH` | Repo để `HIGH`/`LOW` và **chưa xác minh với module thật**. Sai chiều = 7 khoá có điện liên tục từ lúc cấp nguồn |
| `:15` `#define SLAVE_ID 1` | Chỉ khi lắp **board thứ hai** trên cùng bus ⇒ đặt `2` | Pi quét từ 1 tới `MAX_CABINETS` (`settings.py:38`, `discovery_service.py:29`); tủ đầu tiên giữ `1` |

Mở Serial Monitor 9600 baud, phải thấy `AISL Locker Controller v2.1` và 7 dòng `Slot n: … door=CLOSED/OPEN` (`:66-80`).

### 4.2 Pi — hệ điều hành và runtime

```bash
sudo apt update && sudo apt install -y git docker.io chromium-browser
sudo usermod -aG docker,dialout $USER      # dialout: quyền mở /dev/ttyUSB*; đăng xuất/đăng nhập lại
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/LockR-Tech/iot.git ~/iot && cd ~/iot
uv sync                                    # tự tải Python 3.13 theo .python-version
docker compose -f docker-compose.postgres.yml up -d
```

### 4.3 `.env` trên Pi

Tạo `~/iot/.env` (không commit). Ba dòng dưới đây là những chỗ hay hỏng; các biến còn lại xem `config/settings.py`:

```
SERIAL_PORT=/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0   # đường dẫn ghi ở bước D.1
MAC_ADDRESS=aa:bb:cc:dd:ee:ff                                    # MAC của cổng mạng đang dùng
MQTT_BROKER=<broker>  MQTT_PORT_SSL=8883  MQTT_USE_TLS=true
BACKEND_API_URL=https://api.locker-drone.tech
```

- `SERIAL_PORT=AUTO` ưu tiên thiết bị có chữ "arduino" (`serial_manager.py:100-108`) — nếu USB Arduino cũng cắm vào Pi, `AUTO` có thể mở nhầm `/dev/ttyACM0` thay vì adapter RS485. Ghim đường dẫn `by-id`.
- `MAC_ADDRESS`: backend gửi lệnh setup theo MAC và Pi bỏ qua lệnh không khớp (`locker_service.py:119-123`); để trống thì `uuid.getnode()` tự chọn eth0 hay wlan0 (`settings.py:11-20`) và có thể đổi giữa hai lần khởi động. Ghim vào MAC đã đăng ký với admin.
- Broker: mặc định vẫn là `broker.hivemq.com` công khai (SEC-04) — tủ thật chỉ chạy demo cho tới khi có broker riêng ([STATUS § 4](../STATUS.md)).

### 4.4 Chạy `main.py` như dịch vụ

`/etc/systemd/system/lockr-controller.service`:

```ini
[Unit]
Description=Lock.R cabinet controller
After=network-online.target docker.service
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/iot          # python-dotenv đọc .env theo thư mục này
ExecStart=/home/pi/.local/bin/uv run python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`sudo systemctl enable --now lockr-controller` · xem log: `journalctl -u lockr-controller -f`.

### 4.5 Kiosk trên Pi

`main.py` tự phục vụ bản build của kiosk tại `http://localhost:8000/ui/` nếu có thư mục `ui/dist` (`config_api.py:152-155`). Ba việc phải làm trước, đều đã kiểm trong code:

1. **`vite.config.js` chưa có `base`** nên `ui/dist/index.html` trỏ `/assets/…` — mở ở `/ui/` sẽ trắng màn vì 404 JS/CSS. Thêm `base: '/ui/'` vào `defineConfig` rồi mới build. (Chưa có trong repo — [§ 7](#7-việc-còn-nợ-trong-code).)
2. **`ui/.env.local`** trên Pi: `VITE_API_URL=https://api.locker-drone.tech` (bản build không còn Vite proxy — ghi chú ngay trong file mẫu), `VITE_LOCAL_API_URL=http://localhost:8000`, `VITE_LOCKER_ID=<id tủ trong admin>` (hoặc thêm `?lockerId=<id>` vào URL — `KioskScreen.jsx:22-25`). Đăng nhập bằng số điện thoại trên kiosk cần thêm bộ `VITE_FIREBASE_*` của một Firebase *Web app* — hiện chưa tạo.
3. **CORS trên VM:** kiosk chạy ở origin `http://localhost:8000`, gateway chỉ cho origin trong `APP_CORS_ALLOWED_ORIGINS` (`application.yml:186-196`). Thêm `http://localhost:8000` vào biến đó trong `.env` VM rồi `docker compose up -d api-gateway`. Không làm thì mọi gọi `/api/...` từ kiosk bị chặn dù backend vẫn sống.

Build và tự chạy khi bật máy:

```bash
cd ~/iot/ui && npm install && npm run build
# lệnh kiosk — thêm vào autostart của phiên desktop
# (Bookworm: ~/.config/wayfire.ini mục [autostart], hoặc ~/.config/labwc/autostart tuỳ bản)
chromium-browser --kiosk --noerrdialogs --disable-infobars --incognito \
  --disable-session-crashed-bubble "http://localhost:8000/ui/?lockerId=<id>"
```

Tắt tắt màn: `sudo raspi-config` → Display Options → Screen Blanking → No.

## 5. Kiểm tra từng bước (bring-up)

Làm đúng thứ tự; mỗi bước xanh mới sang bước sau. Các script đều có sẵn trong repo.

| # | Kiểm gì | Lệnh / thao tác | Kết quả đúng | Nếu sai |
|---|---|---|---|---|
| 5.1 | Arduino sống, đủ ngăn | Serial Monitor (9600): gõ `S1:PING` | `{"slave":1,"slots":7,"result":"OK","ms":0}` (`locker_controller.ino:298-301`, `:388-391`) | `slots` ≠ 7 → chưa nạp firmware mới; không trả lời → `SLAVE_ID` sai |
| 5.2 | Cảm biến từng cửa | đóng/mở tay từng ngăn, nhìn Serial Monitor | `Door OPENED: slot n` / `Door CLOSED: slot n` (`:160-172`) đúng ngăn, đúng chiều | ngược chiều → mục 3.C.2; nhảy loạn → dây tín hiệu lỏng ở domino |
| 5.3 | Relay + khoá từng ngăn | Serial Monitor: `S1:T0` … `S1:T6` | relay tách, khoá giật ~1 s, trả `{"slot":0,"result":"OK","door":false,…}` (`:329-350`) | relay kêu nhưng khoá không giật → dây − chưa qua `NO`, hoặc cầu chì; `door:true` sau khi mở → cửa không bật ra hoặc cảm biến ngược |
| 5.4 | Bus RS485 từ Pi | `cd ~/iot && uv run python debug_rs485_rx.py` (sửa `PORT`, `SLAVE_ID` ở `:12-14`) | in JSON PING trả về | không có gì → đảo A/B; có rác → thiếu GND chung |
| 5.5 | `SerialManager` quét slave | `uv run python debug_scan.py` | tìm thấy slave 1 với `availableSlots: 7` | |
| 5.6 | Toàn bộ `main.py` | `uv run python main.py` (hoặc `journalctl -u lockr-controller -f`) | `RS485 connected: … @ 9600` (`serial_manager.py:150`), `Discovery results reported`, `System is READY` | `No serial ports found` → `dialout` chưa có hiệu lực, đăng nhập lại |
| 5.7 | API cục bộ | `curl localhost:8000/system/info` | JSON có `macAddress` trùng `.env` | |
| 5.8 | Backend thấy tủ | admin web → tủ → thiết bị; hoặc `GET /api/manage/iot/device-status` | tủ `ONLINE` sau heartbeat | Pi có gửi (`heartbeat_service.py:18`) mà backend không thấy → khác broker hoặc khác **tên tủ**/MAC |
| 5.9 | Mở bằng mã từ kiosk | kiosk nhập PIN của một đơn test | ngăn đúng mở, đơn đổi trạng thái | kiosk trắng → § 4.5.1; gọi API lỗi CORS → § 4.5.3; Pi nhận lệnh nhưng bỏ qua → payload thiếu `slotIndex` (F2-G09, [§ 7](#7-việc-còn-nợ-trong-code)) |

## 6. Lỗi hay gặp

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| Cấp nguồn xong cả 7 relay hút, khoá nóng | `RELAY_ON` ngược chiều module (§ 4.1) |
| Relay 7 kêu tách mỗi lần Arduino reset | dùng `D13` cho khoá — đổi sang `A5` |
| Pi reboot khi khoá hút | Pi lấy nguồn chung với 12 V qua buck yếu — dùng nguồn chính hãng riêng |
| Arduino nóng, treo khi nhiều relay | relay lấy 5 V từ Arduino — tách `JD-VCC` (§ 3.B.1) |
| `main.py` mở được cổng nhưng PING timeout | mở nhầm `/dev/ttyACM0` (USB Arduino) thay vì adapter RS485 — ghim `SERIAL_PORT` |
| PING lúc được lúc không | adapter không tự đảo chiều; thiếu GND chung; A/B không xoắn đôi |
| Backend không gửi lệnh setup tới Pi | MAC trong lệnh ≠ `MAC_ADDRESS` của Pi (`locker_service.py:119-123`) |
| Kiosk trắng màn ở `/ui/` | thiếu `base: '/ui/'` khi build |
| Kiosk hiện nhưng mọi nút báo lỗi mạng | origin `localhost:8000` chưa trong `APP_CORS_ALLOWED_ORIGINS` |

## 7. Việc còn nợ trong code

Nối dây xong vẫn chưa mở được ngăn bằng mã từ app cho tới khi các mục dưới đây có PR. Chưa mục nào được làm; thứ tự là thứ tự nên làm.

| # | Việc | Ở đâu | Gap |
|---|---|---|---|
| 1 | ~~Nâng trần 6 → 7 ngăn~~ — **đã làm** ([iot#7](https://github.com/LockR-Tech/iot/pull/7)): `MAX_SLOTS = 7`, hai mảng chân đủ 7, mảng trạng thái bám `NUM_SLOTS` | `iot/infracstructure/serial_manager.py:21`, `locker_controller.ino:24-25,45-47` | F2-G09 |
| 2 | `base: '/ui/'` cho bản build kiosk | `iot/ui/vite.config.js` | F2-G09 |
| 3 | Thống nhất payload lệnh mở: backend gửi `{commandId, box_id, action}` tới `cabinet/{lockerId}/command/open`, Pi cần `slotIndex` và dùng **tên** tủ trong topic | `backend/iot-service/…/LockerMqttService.java:30,183` · `iot/services/locker_service.py:170-181` | **F2-G09** — chặn toàn bộ |
| 4 | Broker MQTT riêng có auth + TLS | `backend/docker-compose.yml` | SEC-04 |
| 5 | Sự kiện cửa (`DOOR_CLOSED`) điều khiển vòng đời đơn/ô | `iot/services/locker_service.py:229-264` · iot-service | F2-G09, F3-G03 |
| 6 | Nắp trượt: firmware + lệnh MQTT + luồng drone thật | mới hoàn toàn | F1.06 |

Việc 3 là nút cổ chai: không có nó thì lệnh mở từ backend tới Pi bị bỏ qua ngay ở `if slot_index is None: return` (`locker_service.py:167`), dù dây đã đúng và `T<n>` chạy hoàn hảo.
