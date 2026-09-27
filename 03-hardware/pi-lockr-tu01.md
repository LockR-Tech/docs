# Hồ sơ bộ điều khiển tủ `lockr-tu01` — Raspberry Pi 5

| | |
|---|---|
| **Dựng ngày** | 2026-09-26 → 2026-09-27 |
| **Cách dựng chuẩn** | [controller-wiring-guide.md § 4](controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm) — file này chỉ ghi những gì **riêng** của máy này |
| **Code** | `iot` tại `c843447` ([iot#8](https://github.com/LockR-Tech/iot/pull/8)) |
| **Gap** | F2-G09 |

## 1. Trạng thái

| Mục | Hiện tại |
|---|---|
| Chế độ | **GPIO** (`HARDWARE_BACKEND=gpio`, `LID_ENABLED=true`) — chưa nối dây tủ nên 7 cửa báo mở, nắp `UNKNOWN` |
| `main.py` | `System is READY`, MQTT TLS `broker.hivemq.com:8883`, discovery `slaveId 1, 7 ngăn`, API `:8000` |
| Kiosk | Chromium toàn màn hình `http://localhost:3002/`, tủ **tạm** `CAB-DEMO-01` (id 1) |
| Khởi động → thấy kiosk | 2–9 phút (ổ USB chậm) |
| ⚠ Hệ điều hành | **Cơ sở dữ liệu gói hỏng — không chạy `apt`/`apt-get`/`dpkg`** (sự cố 18). Máy vẫn chạy đủ; muốn cập nhật hệ điều hành phải ghi lại từ đầu |

Kiểm lần cuối 2026-09-27: khởi động lại → `lockr-controller`, `lockr-kiosk`, PostgreSQL tự chạy, hệ thống `running`, kiosk hiện dữ liệu thật của `CAB-DEMO-01`. Chuyển sang GPIO 2026-09-27 17:06: `GPIO hardware initialized (lid: on)`, `System is READY`; `GET /hardware/status` trả 7 cửa + nắp; `POST /hardware/lid/*` từ máy khác trong LAN bị chặn 403.

## 2. Truy cập

| Mục | Giá trị |
|---|---|
| Hostname | `lockr-tu01` — `ssh lockr@lockr-tu01.local` trong cùng mạng |
| User | `lockr`, `sudo` không hỏi mật khẩu |
| Mật khẩu user, mật khẩu PostgreSQL, Wi-Fi | **Lưu ngoài git** — hỏi chủ dự án |
| SSH không mật khẩu | Khoá của laptop người dựng (cloud-init `ssh_authorized_keys`) |
| Mạng | Wi-Fi tạm 2.4 GHz của người dựng, IP DHCP. Tủ thật cần mạng riêng (LAN hoặc router 4G) |
| MAC `wlan0` / `eth0` | `2C:CF:67:DB:C5:C3` (ghim làm `MAC_ADDRESS`) / `2C:CF:67:DB:C5:C2` |

## 3. Phần cứng

| Mục | Thông số |
|---|---|
| Bo mạch | Raspberry Pi 5 Model B Rev 1.1, RAM 8 GB, serial `62c226be7b2c1dc7`, Active Cooler |
| Nguồn | Raspberry Pi 27W USB-C (5,1 V 5 A) |
| Ổ hệ thống | **USB flash 32 GB** ở cổng USB 3 — tạm thời; nên thay microSD A2 hoặc SSD USB |
| Bootloader | 2026-09-12 (cập nhật từ 2025-11-05) |

Linh kiện tủ quan sát qua ảnh 2026-09-26 (chưa nối vào Pi): module relay 8 kênh cuộn 5 V (`SRD-05VDC-SL-C`), có opto, jumper chọn kích H/L, ngõ vào cọc vít `DC+ DC− IN1…IN8` — **khác loại `JD-VCC`** mà [§ 3.B](controller-wiring-guide.md#b-relay-và-khoá) giả định; driver TB6600 (9–42 VDC); nguồn tổ ong có công tắc 110/220 V; cầu đấu TB-2512L. Tủ dùng **GPIO trực tiếp** ([ADR-0007](../adr/0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md)) — không cần Arduino, MAX485, adapter USB-RS485. Màn: Waveshare 7" HDMI LCD (H), cảm ứng USB, chưa lắp.

## 4. Phần mềm và dịch vụ

| Thành phần | Phiên bản |
|---|---|
| Hệ điều hành | Raspberry Pi OS 64-bit (Debian 13 Trixie), image 2026-09-15, desktop labwc |
| Kernel | `6.18.50+rpt-rpi-2712` |
| Python · uv | 3.13.5 · 0.12.19 |
| Node.js · npm | 22.23.3 (NodeSource) · 10.9.9 |
| PostgreSQL | 17.11 (`apt`), chỉ nghe `127.0.0.1:5432` |
| Chromium | 153.0.8010.52 |

| Dịch vụ | Làm gì | Cổng |
|---|---|---|
| `lockr-controller` | `uv run python main.py` | `0.0.0.0:8000` |
| `lockr-kiosk` | `vite preview` bản build kiosk | `127.0.0.1:3002` |
| `postgresql` | database `iot_locker` | `127.0.0.1:5432` |
| phiên desktop | `~/kiosk.sh` → Chromium kiosk | — |

## 5. Cấu hình riêng của máy này

Ngoài các bước ở [controller-wiring-guide § 4](controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm):

| Mục | Giá trị |
|---|---|
| `~/iot/.env` | `HARDWARE_BACKEND=gpio`, `LID_ENABLED=true`, `SERIAL_PORT=AUTO` (không dùng), `MAC_ADDRESS=2C:CF:67:DB:C5:C3`, `MQTT_BROKER=broker.hivemq.com`, `BACKEND_API_URL=https://api.locker-drone.tech`, `POSTGRES_*` (mật khẩu ngẫu nhiên) · bản chạy giả lập trước đó: `~/iot/.env.bak-20260927-1706` |
| `~/iot/ui/.env.local` | `VITE_API_URL=` (trống), `VITE_LOCAL_API_URL=http://localhost:8000`, `VITE_LOCKER_ID=1`, `VITE_LOCKER_CODE=CAB-DEMO-01`, bộ `VITE_FIREBASE_*` |
| Tắt vì cơ sở dữ liệu gói hỏng | `apt-daily.timer`, `apt-daily-upgrade.timer`, `packagekit.service` (mask); `/etc/motd` cảnh báo không chạy `apt` |
| `lockr-controller.service` | thêm `ExecStopPost=/usr/bin/pinctrl set 17,27,22,23,24,25,16 op dl` — ngắt mọi relay khi dịch vụ dừng/chết |
| Thử GPIO trước khi merge | worktree `~/iot-gpio-test` (đã xoá sau merge): 19 test đạt; chip thật 2026-09-27 — relay GPIO17 HIGH đúng 1 s, 800 bước động cơ trong 1,27 s, chân relay lúc khởi động `no pd` (kéo xuống) |
| `/root/pg-old-conf/` | cấu hình PostgreSQL cũ, cất đi khi tạo lại cụm (sự cố 18) |
| `/lost+found/` | ~200 mục `fsck` dời vào sau lần mất điện — giữ làm bằng chứng |

## 6. Sự cố đã gặp

| # | Hiện tượng | Nguyên nhân | Đã xử lý |
|---|---|---|---|
| 1 | Dây jumper cắm vào header 2×2 cạnh cổng mạng | Đó là header **PoE (J14)**, không phải GPIO | Rút ra; Pi không cần GPIO |
| 2 | Imager không thấy ổ ở bước Storage | Laptop không có đầu đọc thẻ | Ghi lên USB flash thay thẻ |
| 3 | Không tìm thấy Pi qua `ping lockr-tu01.local` trên Wi-Fi công ty | Mạng công ty chặn thiết bị nhìn thấy nhau / chặn `.local` | Dùng Wi-Fi riêng |
| 4 | Pi không vào Wi-Fi, không có SSH | Customisation của Imager không được ghi — `user-data`, `network-config` vẫn là mẫu trống | Tự ghi hai file cloud-init + file `ssh` vào `bootfs` |
| 5 | Pi không bao giờ đọc USB (phân vùng Linux vẫn 5,9 GB, `cmdline.txt` còn `resize`) | Có thẻ nhớ trong khe — Pi 5 ưu tiên thẻ | Rút thẻ |
| 6 | Imager ghi "Device: Raspberry Pi 4" | Chọn nhầm | Vô hại — cùng image 64-bit |
| 7 | Pi tự khởi động lại khi đang tải gói lần đầu | Ổ bị ngắt đột ngột; không có log (journal chỉ ở RAM) — không rõ nguyên nhân | Chạy lại; bật log vĩnh viễn |
| 8 | `git clone` lỗi `GnuTLS recv error (-110)` | Mạng chập chờn khi đang tải `apt` | Thử lại |
| 9 | `apt` hơn 2 giờ, `main.py` khởi động gần 10 phút | USB flash ghi file nhỏ 66 KB/s – 0,8 MB/s | Chủ dự án chọn giữ USB |
| 10 | Kiosk ở `:8000/ui` bị chặn khi gọi API | Gateway production trả 403 cho origin `localhost:8000` | `vite preview` :3002 ([guide § 4.5](controller-wiring-guide.md#45-kiosk-trên-pi)) |
| 11 | Tủ `1001` trong `ui/.env` của máy dev không có trên production | Dữ liệu backend local | Kiosk tạm trỏ `CAB-DEMO-01` |
| 12 | `reboot` xong Pi không lên, phải rút nguồn; kiosk trắng trang | ~329 MB `node_modules` + bản build còn trong RAM, Pi mải ghi xuống USB chậm nên trông như treo; rút nguồn mất dữ liệu (`dist/index.html` 0 byte, 6.973/14.135 file rỗng) | Giới hạn dữ liệu chờ ghi ([guide § 4.6](controller-wiring-guide.md#46-ổ-đĩa-mất-điện-log)), build lại, `sync`; cập nhật bootloader |
| 13 | Màn hình hiện ô đăng nhập thay vì kiosk | Sau `apt full-upgrade` mất `autologin-user`; user `lockr` đang bị khoá mật khẩu | Đặt mật khẩu, `raspi-config` B4 |
| 14 | `Firmware rejected country setting` | Firmware Wi-Fi không nhận mã VN | Vô hại |
| 15 | `usb 3-1: device descriptor read/64, error -110` mỗi lần khởi động | USB flash trả lời chậm | Linux tự thử lại; nghi USB đầu tiên nếu hay kẹt |
| 16 | Khung "Vietnamese / English" trên kiosk | Chromium mặc định tiếng Anh; cờ `--disable-features=Translate` vô tác dụng | Policy `TranslateEnabled: false` |
| 17 | Sau khi bật máy kiosk kẹt màu xám | Chromium mở lúc máy còn khởi động → `Network service crashed` | `kiosk.sh` chờ `systemctl is-system-running --wait` |
| 18 | PostgreSQL không chạy; `dpkg -l` báo 0 gói; ~200 mục trong `/lost+found` | Lần rút nguồn ở sự cố 12 **hỏng hệ thống file**: `fsck` dời gần hết `/var/lib` và `/var/backups` vào `/lost+found`; `/var/lib/dpkg/status` và `alternatives` mất hẳn | Tạo lại cụm PostgreSQL + `iot_locker` (dữ liệu cũ không đáng kể). Code `iot` (`git fsck` sạch), Python, Node, Chromium còn nguyên. Cơ sở dữ liệu gói **không khôi phục được** — tắt cập nhật tự động |

## 7. Vận hành

| Việc | Lệnh |
|---|---|
| Xem trạng thái | `systemctl status lockr-controller lockr-kiosk postgresql --no-pager` |
| Log | `journalctl -u lockr-controller -f` · `journalctl -u lockr-kiosk -f` |
| Tắt máy | `sudo sync && sudo poweroff` — **không rút nguồn ngang** |
| Cập nhật code | `cd ~/iot && git pull && uv sync`, rồi `cd ui && npm ci --no-audit --no-fund && npm run build && sync` (~46 phút trên USB này), `sudo systemctl restart lockr-controller lockr-kiosk lightdm` |
| Đổi tủ trên kiosk | sửa `VITE_LOCKER_ID`, `VITE_LOCKER_CODE` trong `~/iot/ui/.env.local` → `npm run build && sync` → `sudo systemctl restart lockr-kiosk lightdm` |
| Xem kiosk khi chưa có màn hình | `ssh -N -L 3002:127.0.0.1:3002 -L 8000:127.0.0.1:8000 lockr@lockr-tu01.local`, mở `http://localhost:3002` trên laptop |
| Sau khi nối Arduino + adapter | `ls /dev/serial/by-id/` → đặt `SERIAL_PORT`, xoá `SIMULATION=true`, restart `lockr-controller`, kiểm theo [guide § 5](controller-wiring-guide.md#5-kiểm-tra-từng-bước-bring-up) |

`git`, `uv`, `npm` không dùng cơ sở dữ liệu gói nên vẫn chạy được; chỉ `apt`/`dpkg` bị cấm.

## 8. Việc còn lại

| Việc | Vì sao |
|---|---|
| Ghi lại hệ điều hành lên microSD A2 32 GB hoặc SSD USB, dựng lại theo guide § 4 | Bản cài hiện tại không cập nhật bảo mật được; USB flash có thể hỏng tiếp khi mất điện |
| Nối dây theo [spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio) và [guide § 3](controller-wiring-guide.md#3-thứ-tự-nối-dây) (jumper relay **H**, `PUL+`/`DIR+` về **3,3 V**, đo dây tín hiệu khoá trước), bring-up theo guide § 5 | Code GPIO đã thử trên chip thật nhưng chưa có phần cứng tủ nối vào |
| Lắp màn Waveshare (cáp micro-HDMI → HDMI, USB cảm ứng, nguồn 5 V riêng) | Kiosk mới kiểm qua ảnh chụp màn hình ảo |
| Tạo tủ riêng cho tủ 7 ngăn trên admin, đổi id kiosk | Đang trỏ tạm `CAB-DEMO-01` |
| Thống nhất payload lệnh mở (F2-G09), broker riêng (SEC-04) | [guide § 7](controller-wiring-guide.md#7-việc-còn-nợ-trong-code) |
| Đặt tủ trong mạng riêng | Cổng `:8000` không xác thực, có `/setup/clear`, `/test/open-otp` |
