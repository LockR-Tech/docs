# Hồ sơ bộ điều khiển tủ `lockr-tu01` — Raspberry Pi 5

| | |
|---|---|
| **Dựng ngày** | 2026-09-26 → 2026-09-27 trên USB flash; **dựng lại trên thẻ microSD 2026-09-27** (bản USB hỏng, sự cố 18) |
| **Cách dựng chuẩn** | [controller-wiring-guide.md § 4](controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm) — file này chỉ ghi những gì **riêng** của máy này |
| **Code** | `iot` tại `c843447` ([iot#8](https://github.com/LockR-Tech/iot/pull/8)) |
| **Gap** | F2-G09 |

## 1. Trạng thái

| Mục | Hiện tại |
|---|---|
| Chế độ | **GPIO** (`HARDWARE_BACKEND=gpio`, `LID_ENABLED=true`) — chưa nối dây tủ nên 7 cửa báo mở, nắp `UNKNOWN` |
| `main.py` | `System is READY`, MQTT TLS `broker.hivemq.com:8883`, discovery `slaveId 1, 7 ngăn`, API `:8000` |
| Kiosk | Chromium toàn màn hình `http://localhost:3002/`, tủ **tạm** `CAB-DEMO-01` (id 1) |
| Khởi động | lên mạng sau ~25 giây; kiosk hiện trong khoảng 3 phút |
| Hệ điều hành | khoẻ, cập nhật được bằng `apt` bình thường |

Kiểm lần cuối 2026-09-27 21:12 sau khi dựng lại trên thẻ: khởi động lại → `lockr-controller`, `lockr-kiosk`, PostgreSQL tự chạy, hệ thống `running`, `GPIO hardware initialized (lid: on)`, kiosk hiện dữ liệu thật của `CAB-DEMO-01`; `POST /hardware/lid/*` từ máy khác trong LAN bị chặn 403.

## 2. Truy cập

| Mục | Giá trị |
|---|---|
| Hostname | `lockr-tu01` — `ssh lockr@lockr-tu01.local` trong cùng mạng |
| User | `lockr`, `sudo` không hỏi mật khẩu |
| Mật khẩu user, mật khẩu PostgreSQL, Wi-Fi | **Lưu ngoài git** — hỏi chủ dự án (giữ nguyên khi dựng lại trên thẻ) |
| SSH không mật khẩu | Khoá của laptop người dựng (cloud-init `ssh_authorized_keys`) |
| Mạng | Wi-Fi tạm 2.4 GHz của người dựng, IP DHCP. Tủ thật cần mạng riêng (LAN hoặc router 4G) |
| MAC `wlan0` / `eth0` | `2C:CF:67:DB:C5:C3` (ghim làm `MAC_ADDRESS`) / `2C:CF:67:DB:C5:C2` |

## 3. Phần cứng

| Mục | Thông số |
|---|---|
| Bo mạch | Raspberry Pi 5 Model B Rev 1.1, RAM 8 GB, serial `62c226be7b2c1dc7`, Active Cooler |
| Nguồn | Raspberry Pi 27W USB-C (5,1 V 5 A) |
| Ổ hệ thống | **Thẻ microSD SanDisk Ultra 64 GB** (58 GB sau khi nới phân vùng); 200 lần ghi đồng bộ file nhỏ mất 1,5 s |
| USB flash 32 GB cũ | đã rút ra, cất làm dự phòng — bản cài trên đó hỏng cơ sở dữ liệu gói (sự cố 18). **Không cắm lại cùng lúc với thẻ**: hai ổ ghi từ cùng một image |
| Bootloader | 2026-09-12 (cập nhật từ 2025-11-05; lưu trong EEPROM nên giữ nguyên khi đổi ổ) |
| Màn hình | **Waveshare 7inch HDMI LCD (C) Rev 4.1** — 1024×600, cảm ứng điện dung qua USB, cổng HDMI thường + micro-USB (nguồn + cảm ứng), công tắc Backlight. Chưa lắp; cần cáp micro-HDMI → HDMI |

Linh kiện tủ quan sát qua ảnh 2026-09-26 (chưa nối vào Pi): module relay 8 kênh cuộn 5 V (`SRD-05VDC-SL-C`), có opto, jumper chọn kích H/L, ngõ vào cọc vít `DC+ DC− IN1…IN8` — **khác loại `JD-VCC`** mà [§ 3.B](controller-wiring-guide.md#b-relay-và-khoá) giả định; driver TB6600 (9–42 VDC); nguồn tổ ong có công tắc 110/220 V; cầu đấu TB-2512L. Tủ dùng **GPIO trực tiếp** ([ADR-0007](../adr/0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md)) — không cần Arduino, MAX485, adapter USB-RS485.

## 4. Phần mềm và dịch vụ

| Thành phần | Phiên bản |
|---|---|
| Hệ điều hành | Raspberry Pi OS 64-bit (Debian 13 Trixie), image 2026-09-15, desktop labwc |
| Kernel | `6.18.50+rpt-rpi-2712` |
| Python · uv | 3.13.5 · 0.12.19 |
| Node.js · npm | 22.23.3 (NodeSource) · 10.9.9 |
| PostgreSQL | 17.11 (`apt`), chỉ nghe `127.0.0.1:5432` |
| Chromium | 153 |

| Dịch vụ | Làm gì | Cổng |
|---|---|---|
| `lockr-controller` | `uv run python main.py` | `0.0.0.0:8000` |
| `lockr-kiosk` | `vite preview` bản build kiosk | `127.0.0.1:3002` |
| `postgresql` | database `iot_locker` | `127.0.0.1:5432` |
| phiên desktop | `~/kiosk.sh` → Chromium kiosk | — |

## 5. Cách dựng lại trên thẻ microSD (2026-09-27)

1. Ghi image `2026-09-15-raspios-trixie-arm64.img.xz` (SHA-256 khớp file `.sha256` chính thức) bằng `rpi-imager --cli` — cần quyền admin trên Windows.
2. Ghi vào `bootfs`: `user-data` (hostname, user `lockr` **có mật khẩu** — tránh sự cố 13, khoá SSH, `sudo` không mật khẩu), `network-config` (Wi-Fi + DHCP `eth0`), file rỗng `ssh`.
3. Tắt Pi, **rút USB cũ**, cắm thẻ, bật: lên mạng sau ~5 phút, cloud-init `done`, desktop tự đăng nhập ngay.
4. Chạy script dựng (`/root/pi-setup.sh`, log `/var/log/lockr-setup.log`) làm đúng các bước guide § 4.2–4.6: cập nhật hệ thống, PostgreSQL, Node 22, uv, clone `iot`, `.env` GPIO, kiosk, 2 dịch vụ + `ExecStopPost`, `kiosk.sh`, policy Chromium, tự đăng nhập, tắt tự tắt màn, journal vĩnh viễn, giới hạn dữ liệu chờ ghi. **Hết 5 phút** (trên USB cùng việc đó mất gần 8 giờ).

## 6. Cấu hình riêng của máy này

Ngoài các bước ở [controller-wiring-guide § 4](controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm):

| Mục | Giá trị |
|---|---|
| `~/iot/.env` | `HARDWARE_BACKEND=gpio`, `LID_ENABLED=true`, `SERIAL_PORT=AUTO` (không dùng), `MAC_ADDRESS=2C:CF:67:DB:C5:C3`, `MQTT_BROKER=broker.hivemq.com`, `BACKEND_API_URL=https://api.locker-drone.tech`, `POSTGRES_*` |
| `~/iot/ui/.env.local` | `VITE_API_URL=` (trống), `VITE_LOCAL_API_URL=http://localhost:8000`, `VITE_LOCKER_ID=1`, `VITE_LOCKER_CODE=CAB-DEMO-01`, bộ `VITE_FIREBASE_*` |
| `lockr-controller.service` | `ExecStopPost=/usr/bin/pinctrl set 17,27,22,23,24,25,16 op dl` — ngắt mọi relay khi dịch vụ dừng/chết |
| `/etc/sysctl.d/90-lockr-dirty-limits.conf` | `vm.dirty_background_bytes=4194304`, `vm.dirty_bytes=16777216` |
| `/root/pi-setup.sh` | script đã dùng để dựng (không chứa mật khẩu) — chạy lại được |

## 7. Sự cố đã gặp

Sự cố 1–18 xảy ra trên bản cài USB flash đầu tiên; 19–21 khi dựng lại trên thẻ.

| # | Hiện tượng | Nguyên nhân | Đã xử lý |
|---|---|---|---|
| 1 | Dây jumper cắm vào header 2×2 cạnh cổng mạng | Đó là header **PoE (J14)**, không phải GPIO | Rút ra |
| 2 | Imager không thấy ổ ở bước Storage | Laptop không có đầu đọc thẻ | Ghi lên USB flash thay thẻ (về sau mua đầu đọc) |
| 3 | Không tìm thấy Pi qua `ping lockr-tu01.local` trên Wi-Fi công ty | Mạng công ty chặn thiết bị nhìn thấy nhau / chặn `.local` | Dùng Wi-Fi riêng |
| 4 | Pi không vào Wi-Fi, không có SSH | Customisation của Imager không được ghi — `user-data`, `network-config` vẫn là mẫu trống | Tự ghi hai file cloud-init + file `ssh` vào `bootfs` |
| 5 | Pi không bao giờ đọc USB (phân vùng Linux vẫn 5,9 GB, `cmdline.txt` còn `resize`) | Có thẻ nhớ trong khe — Pi 5 ưu tiên thẻ | Rút thẻ |
| 6 | Imager ghi "Device: Raspberry Pi 4" | Chọn nhầm | Vô hại — cùng image 64-bit |
| 7 | Pi tự khởi động lại khi đang tải gói lần đầu | Ổ bị ngắt đột ngột; không có log (journal chỉ ở RAM) — không rõ nguyên nhân | Chạy lại; bật log vĩnh viễn |
| 8 | `git clone` lỗi `GnuTLS recv error (-110)` | Mạng chập chờn khi đang tải `apt` | Thử lại |
| 9 | `apt` hơn 2 giờ, `main.py` khởi động gần 10 phút | USB flash ghi file nhỏ 66 KB/s – 0,8 MB/s | Tạm giữ USB; về sau chuyển sang thẻ |
| 10 | Kiosk ở `:8000/ui` bị chặn khi gọi API | Gateway production trả 403 cho origin `localhost:8000` | `vite preview` :3002 ([guide § 4.5](controller-wiring-guide.md#45-kiosk-trên-pi)) |
| 11 | Tủ `1001` trong `ui/.env` của máy dev không có trên production | Dữ liệu backend local | Kiosk tạm trỏ `CAB-DEMO-01` |
| 12 | `reboot` xong Pi không lên, phải rút nguồn; kiosk trắng trang | ~329 MB `node_modules` + bản build còn trong RAM, Pi mải ghi xuống USB chậm nên trông như treo; rút nguồn mất dữ liệu (`dist/index.html` 0 byte, 6.973/14.135 file rỗng) | Giới hạn dữ liệu chờ ghi ([guide § 4.6](controller-wiring-guide.md#46-ổ-đĩa-mất-điện-log)), build lại, `sync`; cập nhật bootloader |
| 13 | Màn hình hiện ô đăng nhập thay vì kiosk | Sau `apt full-upgrade` mất `autologin-user`; user `lockr` đang bị khoá mật khẩu | Đặt mật khẩu, `raspi-config` B4. Bản thẻ: đặt mật khẩu ngay trong cloud-init |
| 14 | `Firmware rejected country setting` | Firmware Wi-Fi không nhận mã VN | Vô hại |
| 15 | `usb 3-1: device descriptor read/64, error -110` mỗi lần khởi động | USB flash trả lời chậm | Hết khi bỏ USB |
| 16 | Khung "Vietnamese / English" trên kiosk | Chromium mặc định tiếng Anh; cờ `--disable-features=Translate` vô tác dụng | Policy `TranslateEnabled: false` |
| 17 | Sau khi bật máy kiosk kẹt màu xám | Chromium mở lúc máy còn khởi động → `Network service crashed` | `kiosk.sh` chờ `systemctl is-system-running --wait` |
| 18 | PostgreSQL không chạy; `dpkg -l` báo 0 gói; ~200 mục trong `/lost+found` | Lần rút nguồn ở sự cố 12 **hỏng hệ thống file** trên USB flash: `fsck` dời gần hết `/var/lib` và `/var/backups` vào `/lost+found`; `/var/lib/dpkg/status` mất hẳn | Tạm chạy tiếp (tạo lại PostgreSQL, chặn `apt`), rồi **dựng lại trên thẻ microSD** |
| 19 | Ngay sau khi ghi thẻ, Windows báo một phân vùng FAT16 60 GB, `bootfs` thiếu `issue.txt` | Windows chưa đọc lại bảng phân vùng | Đợi vài giây tới khi hiện đúng 2 phân vùng rồi mới ghi file vào `bootfs` |
| 20 | `rpi-imager.exe --cli` báo "requires elevation" | Imager trên Windows luôn cần quyền admin | Chạy qua `Start-Process -Verb RunAs`, người dùng bấm Yes |
| 21 | Lần khởi động đầu sau khi bật journal vĩnh viễn không được lưu | Đổi cấu hình journald nhưng không `journalctl --flush` | Từ lần khởi động sau lưu bình thường |

## 8. Vận hành

| Việc | Lệnh |
|---|---|
| Xem trạng thái | `systemctl status lockr-controller lockr-kiosk postgresql --no-pager` |
| Log | `journalctl -u lockr-controller -f` · `journalctl -u lockr-kiosk -f` |
| Tắt máy | `sudo sync && sudo poweroff` — **không rút nguồn ngang** |
| Cập nhật code | `cd ~/iot && git pull && uv sync`, rồi `cd ui && npm ci --no-audit --no-fund && npm run build && sync` (~40 giây), `sudo systemctl restart lockr-controller lockr-kiosk lightdm` |
| Cập nhật hệ thống | `sudo apt update && sudo apt full-upgrade -y` |
| Đổi tủ trên kiosk | sửa `VITE_LOCKER_ID`, `VITE_LOCKER_CODE` trong `~/iot/ui/.env.local` → `npm run build && sync` → `sudo systemctl restart lockr-kiosk lightdm` |
| Xem kiosk khi chưa có màn hình | `ssh -N -L 3002:127.0.0.1:3002 -L 8000:127.0.0.1:8000 lockr@lockr-tu01.local`, mở `http://localhost:3002` trên laptop |
| Kiểm phần cứng khi lắp tủ | `sudo systemctl stop lockr-controller`, rồi `cd ~/iot && uv run python debug_gpio.py pins / doors / open N / lid …` ([guide § 5](controller-wiring-guide.md#5-kiểm-tra-từng-bước-bring-up)) |

## 9. Việc còn lại

| Việc | Vì sao |
|---|---|
| Nối dây theo [spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio) và [guide § 3](controller-wiring-guide.md#3-thứ-tự-nối-dây) (jumper relay **H**, `PUL+`/`DIR+` về **3,3 V**, đo dây tín hiệu khoá trước), bring-up theo guide § 5 | Code GPIO đã thử trên chip thật nhưng chưa có phần cứng tủ nối vào |
| Lắp màn Waveshare (C): cáp micro-HDMI → HDMI vào `HDMI0`, micro-USB của màn vào USB của Pi, Backlight ON | Kiosk mới kiểm qua ảnh chụp màn hình ảo |
| Tạo tủ riêng cho tủ 7 ngăn trên admin (ô số 1–7), đổi `VITE_LOCKER_ID` của kiosk | Đang trỏ tạm `CAB-DEMO-01` (10 ô) |
| Sau khi [iot#9](https://github.com/LockR-Tech/iot/pull/9) + [backend#33](https://github.com/LockR-Tech/backend/pull/33) merge: `cd ~/iot && git pull && sudo systemctl restart lockr-controller`, thêm `LOCKER_ID=<id tủ 7 ô>` vào `~/iot/.env`, rồi gán Pi trên admin ([guide § 5.8](controller-wiring-guide.md#5-kiểm-tra-từng-bước-bring-up)) | Hợp đồng MQTT mới ([ADR-0008](../adr/0008-hop-dong-mqtt-backend-tu.md)); bản `main` hiện tại trên Pi vẫn bỏ qua lệnh mở của backend |
| Chuyển sang broker riêng: cấp tài khoản `2CCF67DBC5C3` bằng `mqtt-device.sh`, đổi 5 biến `MQTT_*` trong `~/iot/.env` | SEC-04 — [mqtt-contract § 6](../01-overview/mqtt-contract.md#6-bật-broker-riêng-trên-vm) |
| Đặt tủ trong mạng riêng | Cổng `:8000` không xác thực, có `/setup/clear`, `/test/open-otp` |
