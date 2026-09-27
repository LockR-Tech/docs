# Hướng dẫn nối dây bộ điều khiển tủ — Pi, relay, nắp trượt, màn cảm ứng

| | |
|---|---|
| **Dùng khi** | Lắp tủ vật lý theo [sơ đồ nhà cung cấp](cabinet-wiring-spec.md) và đưa phần mềm trong repo `iot` lên chạy trên tủ đó |
| **Quyết định** | [ADR-0007](../adr/0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md) — tủ Nam Việt dùng **GPIO trực tiếp** (`HARDWARE_BACKEND=gpio`); Arduino/RS485 giữ làm tuỳ chọn |
| **Đối chiếu code** | `iot` tại `e7b04c8` + nhánh `feat/f2-g09-gpio-truc-tiep` (cách GPIO, `hardware/*.py`, `debug_gpio.py`) · `backend` gateway CORS tại `api-gateway/src/main/resources/application.yml:186-196` |
| **Đã dựng thử** | Pi 5 `lockr-tu01` ngày 2026-09-27, Raspberry Pi OS Trixie — hồ sơ và sự cố: [pi-lockr-tu01.md](pi-lockr-tu01.md). § 4.2–4.6 viết theo lần dựng đó |
| **Gap** | F2-G09 (tủ thật chạy end-to-end) — [flow-2](../02-flows/flow-2-locker-send.md) |

`main.py` điều khiển tủ theo một trong hai cách, chọn bằng `HARDWARE_BACKEND` trong `.env`:

| Cách | Nối | Dùng cho |
|---|---|---|
| **`gpio`** | Pi cắm thẳng relay `IN1…IN7`, dây tín hiệu khoá, TB6600, 2 công tắc hành trình — đúng sơ đồ nhà cung cấp, bản đồ chân ở [spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio) | **Tủ Nam Việt** — không phải mua Arduino/RS485 |
| `rs485` (mặc định) | Pi ⇄ USB-RS485 ⇄ MAX485 ⇄ Arduino ⇄ relay/cảm biến ([spec § 4–5](cabinet-wiring-spec.md#4-đối-chiếu-với-firmware-trong-repo)) | tủ khác có Arduino; không có nắp trượt |

Các bước ghi **(RS485)** chỉ dành cho cách thứ hai; không ghi gì là dùng chung hoặc cho GPIO.

## 0. Chọn Raspberry Pi hay Jetson

| Tiêu chí | Raspberry Pi 4B / 5 (4 GB) | Jetson Nano / Orin Nano |
|---|---|---|
| Vai trò trong hệ thống | `main.py` (MQTT, GPIO hoặc RS485, FastAPI :8000, Postgres) + kiosk Chromium | như nhau |
| GPIO cần dùng | **Có** với cách `gpio`: 7 relay, 7 cảm biến, TB6600, 2 công tắc (gói `gpiod`, chạy trên chip RP1 của Pi 5 và BCM của Pi 4) · không với cách `rs485` | cách `gpio` **không** chạy trên Jetson (code dò chip của Pi); GPIO Jetson cũng yếu (≈1 mA) |
| Python 3.13 (`iot/.python-version`) | `uv sync` tự tải bản arm64 | như nhau (JetPack là Ubuntu arm64) |
| PostgreSQL cục bộ | `apt install postgresql` (§ 4.2) | có Docker sẵn trong JetPack |
| Bluetooth cho BLE beacon (`simulate_ble_advertiser.py:11-15`, BlueZ) | tích hợp | Nano gốc **không có** (cần card M.2 / USB dongle); Orin Nano dev kit có |
| Màn cảm ứng | DSI (màn chính hãng 7") **hoặc** HDMI + USB touch | chỉ HDMI/DP + USB touch |
| Nguồn | 5 V 3 A (Pi 4) · 5 V 5 A USB-C PD (Pi 5) | 5 V 4 A jack (Nano) · 19 V (Orin) |
| Giá, độ sẵn có ở Việt Nam | thấp, dễ mua | cao gấp 3–8 lần |

**Kết luận:** dùng **Raspberry Pi 4B hoặc 5, bản 4 GB**. Jetson không mang lại gì cho tủ vì phần mềm không chạy mô hình AI tại tủ (trợ lý RAG chạy ở backend), và không chạy được cách `gpio`. Chỉ cân nhắc Jetson khi có kế hoạch gắn camera nhận diện — hiện không có trong luồng nào.

## 1. Danh sách chuẩn bị

Đã có theo báo giá Nam Việt (3/07/BG-NV, 2026-07-06): khung tủ, 7 khoá 12 V, module relay 8 kênh, domino, nguồn tổ ong 12 V, Nema 17 + TB6600 + gá, ray MGN12H, đai + puli GT2, nắp trượt, 2 công tắc hành trình, **nguồn 24 V 5 A riêng cho motor**. Cần thêm:

| Nhóm | Hạng mục | SL | Thông số / vì sao |
|---|---|---|---|
| **Bo điều khiển** | Raspberry Pi 4B hoặc 5, 4 GB | 1 | xem § 0 |
| | Nguồn chính hãng cho Pi | 1 | Pi 4: 5 V 3 A USB-C · Pi 5: 27 W USB-C PD. **Không** kéo Pi từ nguồn 12 V qua buck rẻ — sụt áp là Pi reboot giữa chừng |
| | Thẻ microSD 32 GB **A1/A2** (hoặc SSD USB) + Raspberry Pi OS 64-bit có desktop | 1 | **Không dùng USB flash thường** làm ổ hệ thống: đo được 66 KB/s khi ghi file nhỏ, `apt` mất hơn 2 giờ, và một lần mất điện đã làm hỏng hệ thống file ([pi-lockr-tu01 sự cố 9, 18](pi-lockr-tu01.md#6-sự-cố-đã-gặp)) |
| | Đầu đọc thẻ microSD cho laptop | 1 | để ghi hệ điều hành bằng Raspberry Pi Imager |
| | Tản nhiệt / quạt (Pi 5 bắt buộc) | 1 | tủ kín, nóng |
| **Nối Pi ↔ tủ** | Dây Dupont cái (phía Pi) — đực/cái (phía domino, relay) | ~25 | 7 relay + 7 cảm biến + 4 nắp trượt + nguồn relay + GND |
| **Nên có** | Diode 1N4007 | 7 | song song mỗi khoá, vạch trắng (cathode) về +12 V — Pi nối thẳng mạch khoá nên xung ngược khi relay ngắt dễ làm Pi treo |
| | Cầu chì 12 V (10 A) + đế | 1 | ngay sau `+V` nguồn tổ ong |
| **Màn hình** | Màn HDMI 7" có cảm ứng USB, 1024×600 (kiosk thiết kế đúng cỡ này) | 1 | tủ `lockr-tu01` dùng Waveshare 7" HDMI LCD (H); Pi 4/5 cần cáp **micro-HDMI → HDMI**; cấp nguồn màn riêng 5 V ≥ 2 A. Hoặc Raspberry Pi Touch Display 2 (DSI) |
| **Mạng** | Ethernet tới tủ (ưu tiên) hoặc Wi-Fi ổn định | 1 | Pi ra Internet tới `api.locker-drone.tech` và broker MQTT |
| **Dụng cụ** | Đồng hồ vạn năng, tuốc-nơ-vít domino, kìm bấm cos | | kiểm cực tính, **đo dây tín hiệu khoá trước khi nối Pi** (§ 3.C) |
| **(RS485)** | Arduino Uno R3 + cáp USB | 1 | firmware `locker_controller.ino` ([spec § 5](cabinet-wiring-spec.md#5-bản-đồ-chân-arduino-uno-cho-7-ngăn)) — không cần với cách `gpio` |
| | Bộ chuyển USB ↔ RS485 **tự đảo chiều** (CH340/CP2102) + module MAX485 + dây xoắn đôi ~2 m | 1 | firmware chờ 50 ms cho adapter tự chuyển TX→RX (`locker_controller.ino:432-434`) |
| | Bộ hạ áp 12 V → 5 V ≥ 3 A | 1 | nuôi relay khi Arduino điều khiển; với `gpio` relay lấy 5 V từ Pi như nhà cung cấp |

Khoá 12 V: mỗi lần chỉ **một** khoá hút tối đa 1 s — cả firmware (`locker_controller.ino:354-369`) lẫn code GPIO (`hardware/gpio_locker.py`, khoá `_op_lock`) đều tuần tự — nên nguồn tổ ong **12 V 10 A** là đủ cho 7 khoá; kiểm dòng danh định trên nhãn khoá để chắc. Động cơ có nguồn 24 V 5 A riêng.

## 2. Sơ đồ khối

**GPIO** (tủ Nam Việt) — chân cụ thể ở [spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio):

```
220 V ─► Nguồn tổ ong 12 V ─► cầu chì 10 A ─► domino +12 V ─► [7 khoá +]
220 V ─► Nguồn 24 V 5 A ─────────────────────► TB6600 VCC/GND ─► Nema 17 (A±, B±)

Pi 5 ─ 5 V / GND ─────────────► relay DC+ / DC−   (jumper H)
 ├─ GPIO17 27 22 23 24 25 16 ─► relay IN1…IN7 ─► COM/NO ─► [khoá −]
 ├─ GPIO5 6 12 13 19 26 20 ◄── dây tín hiệu khoá (dây kia về GND Pi)
 ├─ 3,3 V ─► TB6600 PUL+ DIR+ · GPIO18 ─► PUL− · GPIO21 ─► DIR−
 ├─ GPIO4 ◄── công tắc gốc · GPIO10 ◄── công tắc cuối (chân kia về GND)
 ├─ micro-HDMI + USB ─► màn cảm ứng 7"
 └─ LAN/Wi-Fi ─► Internet (backend, MQTT)
```

**(RS485)**:

```
220 V ─► Nguồn tổ ong 12 V ─┬─► cầu chì 10 A ─► domino +12 V ─► [7 khoá +]
                            └─► Buck 12→5 V ─► relay JD-VCC (+5 V), GND chung

Pi ──USB──► adapter USB-RS485 ──A/B/GND──► MAX485 ──► Arduino Uno
                                                       ├─ D2 D4 D5 D3 D8 D10 A5 ─► relay IN1…IN7 ─► COM/NO ─► [khoá −]
                                                       └─ D11 D12 A0 A1 A2 A3 A4 ◄─ dây tín hiệu khoá (về GND)
```

## 3. Thứ tự nối dây

Làm theo thứ tự, **tắt 220 V** trong suốt các bước A–E. Mỗi bước có một phép kiểm tra trước khi sang bước sau.

### A. Nguồn

1. Nối `L`, `N`, `GND` (tiếp địa thật) vào nguồn tổ ong. **Gạt công tắc 110/220 V về 220 V.** Chưa cắm điện.
2. `+V` → cầu chì 10 A → domino +12 V. `-V` → domino GND chung.
3. Nguồn 24 V 5 A của motor: `+V`/`-V` → `VCC`/`GND` của TB6600 (driver nhận 9–42 V).
4. **(RS485)** Buck 12→5 V: vào từ domino 12 V, chỉnh ra **đúng 5,0 V** (đo trước khi nối tải), GND về domino GND chung.
5. **Kiểm:** cắm 220 V, đo domino 12 V = 12,0 ± 0,5 V; nguồn motor 24 V; (RS485) buck = 5,0 ± 0,1 V. Rút điện.

### B. Relay và khoá

1. **GPIO:** relay `DC+` ← 5 V của Pi (chân 2), `DC-` ← GND của Pi (chân 6) — mỗi lúc chỉ một relay hút nên Pi gánh được. **Gạt jumper chọn mức kích sang H**: ở L, 3,3 V của Pi không tắt được relay. `IN1…IN7` → GPIO theo [spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio) — nối sau bước 4.
   **(RS485):** rút jumper `VCC–JD-VCC`. `JD-VCC` ← buck 5 V, `GND` ← domino GND. `VCC` ← `5V` Arduino, `GND` ← `GND` Arduino.
2. Mỗi khoá: dây **+** → domino +12 V; dây **−** → `NO` của relay kênh tương ứng; `COM` của relay → domino GND. Nên mắc diode 1N4007 song song hai dây nguồn khoá, **vạch trắng (cathode) về phía +12 V**.
3. Ghi số ngăn `0…6` lên relay và lên domino tín hiệu, theo đúng thứ tự dây nhà cung cấp kéo (từ phải qua trái, nhìn từ sau tủ).
4. **Kiểm** (chưa nối `IN` vào Pi): cấp 12 V và bật Pi. Chạm dây từ `IN1` lên 3,3 V của Pi (chân 1) trong **dưới 1 giây** → relay kêu tách, khoá 0 giật chốt; bỏ ra → relay nhả. Không nhả ⇒ jumper còn ở L. Rút điện.

### C. Cảm biến cửa (dây tín hiệu khoá)

1. **Đo trước khi nối**: chỉnh đồng hồ sang đo điện áp DC, cấp 12 V cho tủ, đo giữa hai dây tín hiệu của một khoá — phải là **0 V**. Chuyển sang thang thông mạch: đóng/mở cửa thì kêu/tắt (hoặc ngược lại). Có điện áp ⇒ **không được nối vào Pi**.
2. Một dây → GPIO của ngăn đó ([spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio)), dây kia → GND của Pi. Không cần điện trở — code bật điện trở kéo lên. **(RS485):** vào `MAGNETIC_PINS[slot]` và GND của Arduino (`locker_controller.ino:55`).
3. Code coi **LOW = cửa đóng**. Công tắc trong khoá *đóng mạch khi cửa mở* thì kết quả ngược — thấy ở bước 5.2, sửa bằng `GPIO_DOOR_CLOSED_LOW=false` trong `.env` (RS485: đảo phép so sánh trong firmware).

### D. (RS485) Arduino ↔ RS485 ↔ Pi

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

### E. Nắp trượt — TB6600 + Nema 17 + 2 công tắc hành trình (GPIO)

Code: `iot/hardware/lid_controller.py` — về gốc, mở, đóng theo công tắc hành trình, tăng tốc dần, dừng được giữa chừng; chạy hết `LID_MAX_STEPS` mà không chạm công tắc thì dừng và báo `FAULT`. Chưa có lệnh MQTT (luồng drone F1.06 đang giả lập) — điều khiển qua `debug_gpio.py` hoặc API cục bộ (§ 5).

1. Motor: 4 dây → `A+ A- B+ B-` (tìm cặp cuộn bằng thang thông mạch). Nguồn 24 V ở bước A.3.
2. Tín hiệu: `PUL+`, `DIR+` → **3,3 V** của Pi (chân 1 hoặc 17) — **không** nối +5 V như tài liệu nhà cung cấp: GPIO Pi chỉ lên 3,3 V, để lại 1,7 V trên opto nên TB6600 không tắt hẳn. `PUL-` → GPIO18, `DIR-` → GPIO21. `ENA±` để trống.
3. Công tắc hành trình (loại thường mở): **gốc** (vị trí nắp đóng) → GPIO4, **cuối** (nắp mở) → GPIO10; chân còn lại của mỗi công tắc → GND của Pi. Loại thường đóng thì đặt `LID_LIMIT_ACTIVE_LOW=false`.
4. DIP TB6600: dòng theo nhãn Nema 17 (thường 1,2–1,7 A), vi bước 1/8. **Rút điện** trước khi tháo giắc động cơ (mục 3 tài liệu nhà cung cấp).
5. Bật trong `.env`: `LID_ENABLED=true` (§ 4.3). Nắp chạy ngược chiều ⇒ `LID_OPEN_DIR_HIGH=false`. `LID_MAX_STEPS` đặt lớn hơn số bước đi hết hành trình một chút (đo ở bước 5.5).

**(RS485)** không có đường điều khiển nắp — Uno thiếu chân; muốn thì đổi sang Mega và thêm lệnh vào giao thức.

### F. Màn cảm ứng

- **HDMI + USB** (Waveshare 7" HDMI LCD (H) của `lockr-tu01`): cáp micro-HDMI → HDMI vào cổng `HDMI0` của Pi (cạnh cổng nguồn), cáp USB của phần cảm ứng vào Pi, nguồn màn từ adapter riêng 5 V ≥ 2 A. Màn 1024×600 khớp khung cố định của kiosk. Chưa thử trên Pi — nếu hình sai độ phân giải, xem hướng dẫn Waveshare cho Pi 5 (KMS).
- **DSI (Pi Touch Display 2):** cáp DSI vào cổng `DISP`; `5V`/`GND` từ header 40 chân theo sơ đồ đi kèm màn — lưu ý header đã dùng nhiều chân cho tủ, kiểm không trùng.
- Chưa cần xoay màn ở bước này; kiosk UI dùng bố cục ngang.

### G. Mạng và nguồn Pi

Ethernet vào Pi, nguồn chính hãng vào cổng USB-C. Chưa bật.

## 4. Nạp firmware và cấu hình phần mềm

### 4.1 (RS485) Firmware Arduino

Cách `gpio` không có firmware — bỏ qua mục này. Sketch trong repo **đã khớp sơ đồ đấu nối**: 7 ngăn, `SLAVE_ID = 1`, mảng trạng thái bám `NUM_SLOTS` ([spec § 5](cabinet-wiring-spec.md#5-bản-đồ-chân-arduino-uno-cho-7-ngăn)). Mở `iot/arduino/locker_controller/locker_controller.ino` bằng Arduino IDE rồi nạp qua USB.

Chỉ còn hai chỗ phải tự quyết theo phần cứng thật:

| Dòng | Khi nào sửa | Vì sao |
|---|---|---|
| `:32-33` `RELAY_ON` / `RELAY_OFF` | Bước B.4 cho thấy module kích **LOW** ⇒ đổi thành `LOW` / `HIGH` | Repo để `HIGH`/`LOW` và **chưa xác minh với module thật**. Sai chiều = 7 khoá có điện liên tục từ lúc cấp nguồn |
| `:15` `#define SLAVE_ID 1` | Chỉ khi lắp **board thứ hai** trên cùng bus ⇒ đặt `2` | Pi quét từ 1 tới `MAX_CABINETS` (`settings.py:38`, `discovery_service.py:29`); tủ đầu tiên giữ `1` |

Mở Serial Monitor 9600 baud, phải thấy `AISL Locker Controller v2.1` và 7 dòng `Slot n: … door=CLOSED/OPEN` (`:66-80`).

### 4.2 Pi — hệ điều hành và runtime

**Ghi hệ điều hành** bằng Raspberry Pi Imager: Device **Raspberry Pi 5** (hoặc 4), OS **Raspberry Pi OS (64-bit)** bản có desktop, Storage là thẻ microSD. Ở bước Customisation điền hostname (`lockr-tuNN`), user **kèm mật khẩu** (thiếu mật khẩu thì desktop không tự đăng nhập — § 4.5), Wi-Fi nếu không cắm LAN, bàn phím `us` (không chọn `vn` — hàng phím số thành chữ có dấu), bật SSH.

- Imager 2.x ghi thiết lập qua **cloud-init** vào `user-data` và `network-config` trên phân vùng `bootfs`. Ghi xong mở hai file đó kiểm tra: nếu vẫn là mẫu toàn comment (lần dựng `lockr-tu01` bị vậy — có lẽ đã bấm *Skip customisation*) thì Pi sẽ không vào mạng, không có SSH. Tự điền hai file theo mẫu comment sẵn trong chính file đó, thêm một file rỗng tên `ssh`.
- Khởi động bằng USB/SSD thì **khe thẻ phải trống** — Pi 5 ưu tiên thẻ nhớ và bỏ qua USB.
- Lần đầu mất ~5 phút (nới phân vùng, khởi động lại rồi mới vào mạng). Tìm Pi bằng `ping <hostname>.local`. Wi-Fi công ty thường chặn thiết bị nhìn thấy nhau — khi cài dùng mạng riêng hoặc LAN.

**Cài runtime** (Raspberry Pi OS Trixie đã có sẵn `git` và `chromium` — tên gói không còn là `chromium-browser`):

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y postgresql
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs   # build kiosk
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo usermod -aG dialout $USER             # quyền mở /dev/ttyUSB*; đăng xuất/đăng nhập lại
git clone https://github.com/LockR-Tech/iot.git ~/iot && cd ~/iot
uv sync                                    # Python 3.13 có sẵn trên Trixie; bản khác uv tự tải

PW=$(openssl rand -hex 16)                  # mật khẩu DB — chỉ nằm trong ~/iot/.env (§ 4.3)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$PW';"
sudo -u postgres createdb iot_locker        # bảng do main.py tự tạo lần chạy đầu
```

- PostgreSQL cài bằng `apt` chỉ nghe `127.0.0.1`. **Không** dùng `docker-compose.postgres.yml` trên Pi: file đó mở cổng 5432 ra mọi mạng với mật khẩu mặc định (`iot/docker-compose.postgres.yml:10,13`) — tủ nằm trên Wi-Fi dùng chung là lộ database.
- `apt` rất lâu trên ổ chậm; chạy nền để rớt SSH không làm `dpkg` dừng giữa chừng: `sudo systemd-run --unit=apt-upgrade --collect bash -c 'apt-get update && apt-get -y full-upgrade'` rồi `journalctl -u apt-upgrade -f`.

### 4.3 `.env` trên Pi

Tạo `~/iot/.env` (không commit). Dòng chung cho cả hai cách; các biến còn lại xem `config/settings.py`:

```
SIMULATION=true                           # xoá khi đã nối phần cứng (relay/cảm biến hoặc adapter RS485)
MAC_ADDRESS=aa:bb:cc:dd:ee:ff             # MAC của cổng mạng đang dùng
MQTT_BROKER=<broker>  MQTT_PORT_SSL=8883  MQTT_USE_TLS=true
BACKEND_API_URL=https://api.locker-drone.tech
POSTGRES_PASSWORD=<mật khẩu tạo ở § 4.2>
```

**GPIO** (tủ Nam Việt) — thêm:

```
HARDWARE_BACKEND=gpio
LID_ENABLED=true                          # khi đã nối TB6600 + 2 công tắc hành trình
# Chỉ cần khi lệch mặc định (spec § 6):
# GPIO_RELAY_PINS=17,27,22,23,24,25,16    GPIO_DOOR_PINS=5,6,12,13,19,26,20
# GPIO_RELAY_ACTIVE_HIGH=true             GPIO_DOOR_CLOSED_LOW=true
# LID_OPEN_DIR_HIGH=true  LID_LIMIT_ACTIVE_LOW=true  LID_STEPS_PER_SEC=800  LID_MAX_STEPS=20000
```

- `HARDWARE_BACKEND=gpio` chỉ có tác dụng khi **không** đặt `SIMULATION=true`.
- Đổi `GPIO_RELAY_PINS` thì sửa luôn danh sách chân trong `ExecStopPost` của dịch vụ (§ 4.4).

**(RS485)** — thêm:

```
SERIAL_PORT=/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0   # đường dẫn ghi ở bước D.1
```

- Chưa cắm adapter RS485 mà không đặt `SIMULATION=true` thì `main.py` dừng ngay với `RS485 connection failed on AUTO` (`serial_manager.py:158,168`) — `AUTO` không dò được cổng nào.
- `SERIAL_PORT=AUTO` ưu tiên thiết bị có chữ "arduino" (`serial_manager.py:100-108`) — nếu USB Arduino cũng cắm vào Pi, `AUTO` có thể mở nhầm `/dev/ttyACM0` thay vì adapter RS485. Ghim đường dẫn `by-id`.
- `MAC_ADDRESS`: backend gửi lệnh setup theo MAC và Pi bỏ qua lệnh không khớp (`locker_service.py:119-123`); để trống thì `uuid.getnode()` tự chọn eth0 hay wlan0 (`settings.py:11-20`) và có thể đổi giữa hai lần khởi động. Ghim vào MAC đã đăng ký với admin.
- Broker: mặc định vẫn là `broker.hivemq.com` công khai (SEC-04) — tủ thật chỉ chạy demo cho tới khi có broker riêng ([STATUS § 4](../STATUS.md)).

### 4.4 Chạy `main.py` như dịch vụ

`/etc/systemd/system/lockr-controller.service`:

```ini
[Unit]
Description=Lock.R cabinet controller
After=network-online.target postgresql.service
Wants=network-online.target postgresql.service

[Service]
User=lockr
WorkingDirectory=/home/lockr/iot       # python-dotenv đọc .env theo thư mục này
ExecStart=/home/lockr/.local/bin/uv run python main.py
Restart=on-failure
RestartSec=5
# GPIO: ngắt mọi relay khoá khi dịch vụ dừng hoặc chết — Pi 5 giữ nguyên mức chân sau khi tiến trình thoát
ExecStopPost=/usr/bin/pinctrl set 17,27,22,23,24,25,16 op dl

[Install]
WantedBy=multi-user.target
```

`ExecStopPost` cần user thuộc nhóm `gpio` (user tạo bằng Imager có sẵn); danh sách chân phải khớp `GPIO_RELAY_PINS`. Không có dòng này thì `main.py` bị giết đúng lúc đang mở một ngăn sẽ để khoá có điện liên tục tới khi dịch vụ chạy lại. Đổi `lockr` thành user đã tạo ở Imager (Raspberry Pi OS mới không còn user `pi` mặc định). `sudo systemctl enable --now lockr-controller` · xem log: `journalctl -u lockr-controller -f`.

### 4.5 Kiosk trên Pi

**Không mở kiosk ở `http://localhost:8000/ui/`.** `main.py` có phục vụ `ui/dist` ở đường dẫn đó (`config_api.py:154`), nhưng ngày 2026-09-27 gateway production trả **403** cho preflight CORS từ origin `http://localhost:8000` — chỉ `localhost:3000/3001` được cho qua (`APP_CORS_ALLOWED_ORIGINS`, `application.yml:196`). Thay vào đó chạy bản build bằng **`vite preview` ở cổng 3002**: preview dùng lại proxy `/api` của `ui/vite.config.js:20-25` (trỏ `https://api.locker-drone.tech`, bỏ header `Origin`) nên không dính CORS và không phải sửa VM.

1. **`ui/.env.local`** trên Pi (không commit):

   ```
   VITE_API_URL=                               # để trống ⇒ gọi /api tương đối qua proxy (api.js:18)
   VITE_LOCAL_API_URL=http://localhost:8000
   VITE_LOCKER_ID=<id tủ có thật trên production>   # GET https://api.locker-drone.tech/api/lockers
   VITE_LOCKER_CODE=<mã tủ>
   ```

   URL `?lockerId=` / `?lockerCode=` ghi đè hai biến cuối (`KioskScreen.jsx:24-25`). Đăng nhập bằng số điện thoại trên kiosk cần thêm bộ `VITE_FIREBASE_*` của một Firebase *Web app* — hiện chưa tạo.

2. **Build:** `cd ~/iot/ui && npm ci --no-audit --no-fund && npm run build && sync`. Đổi `.env.local` phải build lại.

3. **Dịch vụ** `/etc/systemd/system/lockr-kiosk.service`:

   ```ini
   [Unit]
   Description=Lock.R kiosk UI (vite preview :3002)
   After=network-online.target lockr-controller.service
   Wants=network-online.target

   [Service]
   User=lockr
   WorkingDirectory=/home/lockr/iot/ui
   ExecStart=/home/lockr/iot/ui/node_modules/.bin/vite preview --port 3002 --strictPort --host 127.0.0.1
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

4. **Chromium toàn màn hình khi bật máy.** `~/kiosk.sh` — chờ máy khởi động xong mới mở (mở sớm trên ổ chậm thì network service của Chromium sập, trang kẹt màu xám), Chromium thoát thì mở lại:

   ```bash
   #!/bin/bash
   URL="http://localhost:3002/"
   systemctl is-system-running --wait >/dev/null 2>&1
   for i in $(seq 1 150); do curl -s -o /dev/null -m 2 "$URL" && break; sleep 2; done
   sleep 10
   while true; do
     /usr/bin/chromium --kiosk "$URL" --noerrdialogs --disable-infobars --no-first-run \
       --disable-session-crashed-bubble --incognito --password-store=basic --ozone-platform=wayland
     sleep 3
   done
   ```

   ```bash
   chmod +x ~/kiosk.sh
   echo "/home/lockr/kiosk.sh &" > ~/.config/labwc/autostart      # desktop Trixie là labwc
   sudo mkdir -p /etc/chromium/policies/managed                   # tắt khung "dịch trang"
   echo '{"TranslateEnabled": false}' | sudo tee /etc/chromium/policies/managed/lockr-kiosk.json
   sudo raspi-config nonint do_boot_behaviour B4                  # desktop tự đăng nhập
   sudo raspi-config nonint do_blanking 1                         # không tắt màn hình
   ```

   Cờ `--disable-features=Translate` không có tác dụng với Chromium 153 — phải dùng policy. Tự đăng nhập chỉ chạy khi user có mật khẩu; user bị khoá mật khẩu thì LightDM hiện màn đăng nhập.

Giao diện kiosk là khung cố định **1024×600** (màn 7"); màn lớn hơn thì phần dư để trống.

### 4.6 Ổ đĩa, mất điện, log

| Việc | Lệnh / file | Vì sao |
|---|---|---|
| Giới hạn dữ liệu chờ ghi | `/etc/sysctl.d/90-lockr-slow-usb.conf`: `vm.dirty_background_bytes = 4194304`, `vm.dirty_bytes = 16777216` | Mặc định Linux dồn hàng trăm MB trong RAM; mất điện là mất — lần dựng `lockr-tu01` mất nguyên bản build kiosk và hỏng hệ thống file |
| Tắt máy đúng cách | `sudo sync && sudo poweroff`, đợi đèn xanh tắt hẳn mới rút nguồn | Không rút nguồn ngang; Pi không lên sau `reboot` thì đợi ≥ 10 phút (có thể đang ghi dở) |
| Log qua các lần khởi động | `/etc/systemd/journald.conf.d/50-persistent.conf`: `[Journal]` `Storage=persistent` `SystemMaxUse=100M` | Raspberry Pi OS mặc định `Storage=volatile` (`/usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf`) — tạo thư mục `/var/log/journal` thôi là chưa đủ |
| Cập nhật bootloader | `sudo rpi-eeprom-update -a` rồi `reboot` | Bootloader cũ khởi động từ USB kém ổn định |

## 5. Kiểm tra từng bước (bring-up)

Làm đúng thứ tự; mỗi bước xanh mới sang bước sau. Các script đều có sẵn trong repo.

**GPIO** — dùng `debug_gpio.py` thay Serial Monitor. Chỉ một tiến trình được giữ chân GPIO, nên dừng dịch vụ trước bước 5.1 và bật lại ở bước 5.6. Sai chân hay mức kích thì sửa `.env` (§ 4.3), không sửa code.

| # | Kiểm gì | Lệnh / thao tác | Kết quả đúng | Nếu sai |
|---|---|---|---|---|
| 5.1 | Bản đồ chân khớp dây đã nối | `sudo systemctl stop lockr-controller` · `cd ~/iot && uv run python debug_gpio.py pins` | bảng ngăn → chân khớp với dây thật | sửa `GPIO_*_PIN(S)` trong `.env` |
| 5.2 | Cảm biến từng cửa | `uv run python debug_gpio.py doors`, đóng/mở tay từng ngăn | `→ DOOR_OPENED ngăn n` / `DOOR_CLOSED ngăn n` đúng ngăn, đúng chiều | ngược chiều → `GPIO_DOOR_CLOSED_LOW=false`; không đổi → dây lỏng/sai chân; `Device or resource busy` → dịch vụ chưa dừng |
| 5.3 | Relay + khoá từng ngăn | `uv run python debug_gpio.py open 0` … `open 6` | relay tách, khoá giật ~1 s, in `{'result': 'OK', 'door': False, …}` | relay hút mãi không nhả → jumper ở L; khoá không giật → dây − chưa qua `NO`, hoặc cầu chì; `door: True` sau khi mở → cửa không bật ra hoặc cảm biến ngược |
| 5.4 | Công tắc hành trình | `uv run python debug_gpio.py lid status`, bấm tay từng công tắc rồi chạy lại | `homeLimit` / `endLimit` = `True` đúng công tắc đang bấm | ngược → `LID_LIMIT_ACTIVE_LOW=false`; đổi chỗ → hoán `LID_HOME_PIN` / `LID_END_PIN` |
| 5.5 | Nắp về gốc, mở, đóng | `lid home` → `lid open` → `lid close` — tay để sẵn ở công tắc nguồn 24 V | dừng đúng tại công tắc; ghi lại `steps` của `open` ⇒ đặt `LID_MAX_STEPS` ≈ số đó × 1,2 | chạy ngược chiều → `LID_OPEN_DIR_HIGH=false`; `FAULT` → công tắc không nhận; motor rung không quay → giảm `LID_STEPS_PER_SEC`, kiểm DIP dòng |
| 5.6 | Toàn bộ `main.py` | `sudo systemctl start lockr-controller` · `journalctl -u lockr-controller -f` | `GPIO locker ready: 7 slots …`, `GPIO hardware initialized (lid: on)`, `System is READY` | `Không tìm thấy gpiochip` → không phải Pi hoặc đặt `GPIO_CHIP` |
| 5.7 | Trạng thái qua API | `curl localhost:8000/hardware/status` · nắp: `curl -X POST localhost:8000/hardware/lid/open` (`close`, `home`, `stop`) | `doors` đúng thực tế, `lid.state` đúng | `403` → đang gọi từ máy khác; dùng `ssh -L 8000:127.0.0.1:8000` |
| 5.8 | Backend thấy tủ | admin web → tủ → thiết bị; hoặc `GET /api/manage/iot/device-status` | tủ `ONLINE` sau heartbeat | Pi có gửi (`heartbeat_service.py:18`) mà backend không thấy → khác broker hoặc khác **tên tủ**/MAC |
| 5.9 | Mở bằng mã từ kiosk | kiosk nhập PIN của một đơn test | ngăn đúng mở, đơn đổi trạng thái | kiosk trắng/xám hoặc lỗi mạng → § 6; Pi nhận lệnh nhưng bỏ qua → payload thiếu `slotIndex` (F2-G09, [§ 7](#7-việc-còn-nợ-trong-code)) |

**(RS485)** — thay 5.1–5.7 ở trên bằng:

| # | Kiểm gì | Lệnh / thao tác | Kết quả đúng | Nếu sai |
|---|---|---|---|---|
| R1 | Arduino sống, đủ ngăn | Serial Monitor (9600): gõ `S1:PING` | `{"slave":1,"slots":7,"result":"OK","ms":0}` (`locker_controller.ino:298-301`, `:388-391`) | `slots` ≠ 7 → chưa nạp firmware mới; không trả lời → `SLAVE_ID` sai |
| R2 | Cảm biến từng cửa | đóng/mở tay từng ngăn, nhìn Serial Monitor | `Door OPENED: slot n` / `Door CLOSED: slot n` (`:160-172`) đúng ngăn, đúng chiều | ngược chiều → mục 3.C.3; nhảy loạn → dây tín hiệu lỏng ở domino |
| R3 | Relay + khoá từng ngăn | Serial Monitor: `S1:T0` … `S1:T6` | relay tách, khoá giật ~1 s, trả `{"slot":0,"result":"OK","door":false,…}` (`:329-350`) | relay kêu nhưng khoá không giật → dây − chưa qua `NO`, hoặc cầu chì; `door:true` sau khi mở → cửa không bật ra hoặc cảm biến ngược |
| R4 | Bus RS485 từ Pi | `cd ~/iot && uv run python debug_rs485_rx.py` (sửa `PORT`, `SLAVE_ID` ở `:12-14`) | in JSON PING trả về | không có gì → đảo A/B; có rác → thiếu GND chung |
| R5 | `SerialManager` quét slave | `uv run python debug_scan.py` | tìm thấy slave 1 với `availableSlots: 7` | |
| R6 | Toàn bộ `main.py` | `uv run python main.py` (hoặc `journalctl -u lockr-controller -f`) | `RS485 connected: … @ 9600` (`serial_manager.py:150`), `Discovery results reported`, `System is READY` | `No serial ports found` → `dialout` chưa có hiệu lực, đăng nhập lại |
| R7 | API cục bộ | `curl localhost:8000/system/info` | JSON có `macAddress` trùng `.env` | |

## 6. Lỗi hay gặp

| Triệu chứng | Nguyên nhân thường gặp |
|---|---|
| **GPIO:** cả 7 relay hút ngay khi cấp điện hoặc không nhả | jumper module relay ở L — gạt sang H (§ 3.B.1); hoặc `GPIO_RELAY_ACTIVE_HIGH` sai |
| **GPIO:** một khoá có điện mãi sau khi `main.py` chết | thiếu `ExecStopPost` ép chân relay về LOW (§ 4.4) — Pi 5 giữ mức chân sau khi tiến trình thoát |
| **GPIO:** `debug_gpio.py` báo `Device or resource busy` | `lockr-controller` đang giữ chân — `sudo systemctl stop lockr-controller` |
| **GPIO:** Pi treo hoặc khởi động lại khi khoá nhả | xung ngược của cuộn khoá — mắc diode 1N4007 song song mỗi khoá (§ 3.B.2) |
| **GPIO:** nắp rung mà không chạy, hoặc chạy lúc được lúc không | `PUL+`/`DIR+` đang ở 5 V thay vì 3,3 V (§ 3.E.2); tốc độ quá cao — giảm `LID_STEPS_PER_SEC`; DIP dòng quá thấp |
| **GPIO:** nắp báo `FAULT`, `LIMIT_NOT_REACHED` | chạy hết `LID_MAX_STEPS` mà không chạm công tắc: công tắc hỏng/lỏng, sai chân, hoặc `LID_MAX_STEPS` nhỏ hơn hành trình thật |
| **(RS485)** Cấp nguồn xong cả 7 relay hút, khoá nóng | `RELAY_ON` ngược chiều module (§ 4.1) |
| **(RS485)** Relay 7 kêu tách mỗi lần Arduino reset | dùng `D13` cho khoá — đổi sang `A5` |
| Pi reboot khi khoá hút | Pi lấy nguồn chung với 12 V qua buck yếu — dùng nguồn chính hãng riêng |
| Arduino nóng, treo khi nhiều relay | relay lấy 5 V từ Arduino — tách `JD-VCC` (§ 3.B.1) |
| `main.py` mở được cổng nhưng PING timeout | mở nhầm `/dev/ttyACM0` (USB Arduino) thay vì adapter RS485 — ghim `SERIAL_PORT` |
| PING lúc được lúc không | adapter không tự đảo chiều; thiếu GND chung; A/B không xoắn đôi |
| Backend không gửi lệnh setup tới Pi | MAC trong lệnh ≠ `MAC_ADDRESS` của Pi (`locker_service.py:119-123`) |
| Kiosk hiện nhưng mọi nút báo lỗi mạng | Mở kiosk ở `:8000/ui` hoặc `VITE_API_URL` trỏ thẳng production ⇒ CORS 403. Dùng `vite preview` :3002 với `VITE_API_URL=` trống (§ 4.5) |
| Kiosk trắng trang, `dist/index.html` 0 byte | Mất điện khi bản build còn trong RAM — build lại + `sync`, đặt giới hạn ghi (§ 4.6) |
| Kiosk kẹt màu xám sau khi bật máy, log `Network service crashed` | Chromium mở lúc máy còn đang khởi động — dùng `kiosk.sh` ở § 4.5 |
| Màn hình hiện ô đăng nhập thay vì kiosk | User chưa có mật khẩu hoặc tự đăng nhập bị tắt — `passwd`, rồi `raspi-config nonint do_boot_behaviour B4` |
| Khung "Vietnamese / English" trên kiosk | Policy `TranslateEnabled: false` (§ 4.5) |
| Pi không bao giờ đọc USB/SSD | Có thẻ nhớ trong khe — Pi 5 ưu tiên thẻ |
| Pi lên nhưng không vào mạng, không SSH được | Customisation của Imager không được ghi — kiểm `user-data`, `network-config` (§ 4.2) |
| `main.py` dừng ngay, `RS485 connection failed on AUTO` | Chưa cắm adapter RS485 — đặt `SIMULATION=true` (§ 4.3) |

## 7. Việc còn nợ trong code

Nối dây xong vẫn chưa mở được ngăn bằng mã từ app cho tới khi các mục dưới đây có PR. Chưa mục nào được làm; thứ tự là thứ tự nên làm.

| # | Việc | Ở đâu | Gap |
|---|---|---|---|
| 1 | ~~Nâng trần 6 → 7 ngăn~~ — **đã làm** ([iot#7](https://github.com/LockR-Tech/iot/pull/7)): `MAX_SLOTS = 7`, hai mảng chân đủ 7, mảng trạng thái bám `NUM_SLOTS` | `iot/infracstructure/serial_manager.py:21`, `locker_controller.ino:24-25,45-47` | F2-G09 |
| 2 | ~~`base: '/ui/'` cho bản build kiosk~~ — **không còn chặn**: kiosk chạy bằng `vite preview` (§ 4.5). Chỉ cần nếu muốn phục vụ kiosk qua `main.py :8000/ui` **và** đã thêm origin đó vào CORS gateway | `iot/ui/vite.config.js` | F2-G09 |
| 3 | Thống nhất payload lệnh mở: backend gửi `{commandId, box_id, action}` tới `cabinet/{lockerId}/command/open`, Pi cần `slotIndex` và dùng **tên** tủ trong topic | `backend/iot-service/…/LockerMqttService.java:30,183` · `iot/services/locker_service.py:170-181` | **F2-G09** — chặn toàn bộ |
| 4 | Broker MQTT riêng có auth + TLS | `backend/docker-compose.yml` | SEC-04 |
| 5 | Sự kiện cửa (`DOOR_CLOSED`) điều khiển vòng đời đơn/ô | `iot/services/locker_service.py:229-264` · iot-service | F2-G09, F3-G03 |
| 6 | Nắp trượt: ~~code điều khiển~~ — **có** cho cách GPIO (`hardware/lid_controller.py`, API cục bộ `/hardware/lid/*`, [ADR-0007](../adr/0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md)). Còn: lệnh MQTT mở/đóng nắp + luồng drone thật | backend iot-service · `iot/services/` | F1.06 |

Việc 3 là nút cổ chai: không có nó thì lệnh mở từ backend tới Pi bị bỏ qua ngay ở `if slot_index is None: return` (`locker_service.py:167`), dù dây đã đúng và `T<n>` chạy hoàn hảo.
