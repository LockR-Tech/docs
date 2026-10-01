# Hồ sơ bộ điều khiển tủ `lockr-tu01` — Raspberry Pi 5

| | |
|---|---|
| **Dựng ngày** | 2026-09-26 → 2026-09-27 trên USB flash; **dựng lại trên thẻ microSD 2026-09-27** (bản USB hỏng, sự cố 18) |
| **Cách dựng chuẩn** | [controller-wiring-guide.md § 4](controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm) — file này chỉ ghi những gì **riêng** của máy này |
| **Code** | `iot` tại `f76eaaa` ([iot#8](https://github.com/LockR-Tech/iot/pull/8) GPIO, [iot#9](https://github.com/LockR-Tech/iot/pull/9) hợp đồng MQTT, [iot#10](https://github.com/LockR-Tech/iot/pull/10) bàn phím ảo kiosk) |
| **Gap** | F2-G09 |

## 1. Trạng thái

| Mục | Hiện tại |
|---|---|
| Chế độ | **GPIO** (`HARDWARE_BACKEND=gpio`, `LID_ENABLED=true`) — chưa nối dây tủ nên 7 cửa báo mở, nắp `UNKNOWN` |
| `main.py` | `System is READY`, MQTT TLS `broker.hivemq.com:8883`, discovery `slaveId 1, 7 ngăn`, API `:8000`. **Chưa phục vụ tủ nào** (`NOT CONFIGURED`, không đặt `LOCKER_ID`) — chờ nối dây xong rồi gán vào tủ `CAB-TU01` |
| Tủ trên production | **`CAB-TU01`** "Tủ thật TU01 (7 ô)", id **7**, store 1, `MAINTENANCE`, tạo 2026-10-01. Ô 1–2 `DRONE`, ô 3 `XL`, ô 4–7 `STANDARD` (boxId 38–44) theo bố cục CAB-PROD trong `CellType.java`. Chưa gán Pi |
| Kiosk | Chromium toàn màn hình `http://localhost:3002/` trên màn Waveshare (lắp 2026-09-30), từ 2026-10-01 trỏ vào tủ thật **`CAB-TU01`** (id 7). Cảm ứng + bàn phím ảo trong trang chạy được mọi màn hình. Tủ còn `MAINTENANCE` và chưa gán Pi nên kiosk hiện "0 Trống / 7 ô", mở tủ chưa chạy |
| Khởi động | lên mạng sau ~25 giây; kiosk hiện sau ~1,5 phút |
| Hệ điều hành | khoẻ, cập nhật được bằng `apt` bình thường |

Kiểm 2026-09-30 22:42 sau khi lắp màn và khởi động lại: kernel `forcing HDMI-A-1 connector on`, 1024×600, cảm ứng nhận từ lúc khởi động, `lockr-controller`, `lockr-kiosk`, `lockr-display-watchdog`, PostgreSQL `active`, kiosk hiện sau ~1,5 phút; chạm thử (thiết bị cảm ứng ảo qua `uinput`) mọi nút trang chủ, ô chọn tủ, gõ OTP/số điện thoại/email bằng bàn phím ảo đều chạy.

Kiểm 2026-09-27 21:12 sau khi dựng lại trên thẻ: khởi động lại → `lockr-controller`, `lockr-kiosk`, PostgreSQL tự chạy, hệ thống `running`, `GPIO hardware initialized (lid: on)`, kiosk hiện dữ liệu thật của `CAB-DEMO-01`; `POST /hardware/lid/*` từ máy khác trong LAN bị chặn 403.

## 2. Truy cập

| Mục | Giá trị |
|---|---|
| Hostname | `lockr-tu01` — `ssh lockr@lockr-tu01.local` trong cùng mạng |
| User | `lockr`, `sudo` không hỏi mật khẩu |
| Mật khẩu user, mật khẩu PostgreSQL, Wi-Fi | **Lưu ngoài git** — hỏi chủ dự án (giữ nguyên khi dựng lại trên thẻ) |
| SSH không mật khẩu | Khoá của laptop người dựng (cloud-init `ssh_authorized_keys`) |
| Mạng | Wi-Fi, IP DHCP. Tủ chuyển chỗ 2026-10-01: đã thêm Wi-Fi của chỗ mới (hồ sơ NetworkManager, ưu tiên tự kết nối 10; tên mạng và mật khẩu **lưu ngoài git**). Hồ sơ Wi-Fi cũ giữ lại làm dự phòng: phát một điểm truy cập trùng tên và mật khẩu cũ từ laptop hoặc điện thoại là Pi bắt được. Thêm mạng khác: `sudo nmcli device wifi connect "<tên>" password "<mật khẩu>"`. Tủ thật cần mạng riêng (LAN hoặc router 4G) |
| MAC `wlan0` / `eth0` | `2C:CF:67:DB:C5:C3` (ghim làm `MAC_ADDRESS`) / `2C:CF:67:DB:C5:C2` |

## 3. Phần cứng

| Mục | Thông số |
|---|---|
| Bo mạch | Raspberry Pi 5 Model B Rev 1.1, RAM 8 GB, serial `62c226be7b2c1dc7`, Active Cooler |
| Nguồn | Raspberry Pi 27W USB-C (5,1 V 5 A) |
| Ổ hệ thống | **Thẻ microSD SanDisk Ultra 64 GB** (58 GB sau khi nới phân vùng); 200 lần ghi đồng bộ file nhỏ mất 1,5 s |
| USB flash 32 GB cũ | đã rút ra, cất làm dự phòng — bản cài trên đó hỏng cơ sở dữ liệu gói (sự cố 18). **Không cắm lại cùng lúc với thẻ**: hai ổ ghi từ cùng một image |
| Bootloader | 2026-09-12 (cập nhật từ 2025-11-05; lưu trong EEPROM nên giữ nguyên khi đổi ổ) |
| Màn hình | **Waveshare 7inch HDMI LCD (C) Rev 4.1** — 1024×600, cảm ứng điện dung qua USB, cổng HDMI thường + micro-USB (nguồn + cảm ứng), công tắc Backlight. **Đã lắp 2026-09-30**: `HDMI0` (`HDMI-A-1`) qua đầu chuyển micro-HDMI, 1024×600@59,85 Hz từ EDID; cảm ứng `WaveShare WS170120` (`0eef:0005`) ở cổng USB, nguồn không sụt (`throttled=0x0`) |

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
| `lockr-display-watchdog` | phiên desktop mất labwc ~30 giây → `systemctl restart lightdm` để tự đăng nhập lại | — |

## 5. Cách dựng lại trên thẻ microSD (2026-09-27)

1. Ghi image `2026-09-15-raspios-trixie-arm64.img.xz` (SHA-256 khớp file `.sha256` chính thức) bằng `rpi-imager --cli` — cần quyền admin trên Windows.
2. Ghi vào `bootfs`: `user-data` (hostname, user `lockr` **có mật khẩu** — tránh sự cố 13, khoá SSH, `sudo` không mật khẩu), `network-config` (Wi-Fi + DHCP `eth0`), file rỗng `ssh`.
3. Tắt Pi, **rút USB cũ**, cắm thẻ, bật: lên mạng sau ~5 phút, cloud-init `done`, desktop tự đăng nhập ngay.
4. Chạy script dựng (`/root/pi-setup.sh`, log `/var/log/lockr-setup.log`) làm đúng các bước guide § 4.2–4.6: cập nhật hệ thống, PostgreSQL, Node 22, uv, clone `iot`, `.env` GPIO, kiosk, 2 dịch vụ + `ExecStopPost`, `kiosk.sh`, policy Chromium, tự đăng nhập, tắt tự tắt màn, journal vĩnh viễn, giới hạn dữ liệu chờ ghi. **Hết 5 phút** (trên USB cùng việc đó mất gần 8 giờ).

## 6. Cấu hình riêng của máy này

Ngoài các bước ở [controller-wiring-guide § 4](controller-wiring-guide.md#4-nạp-firmware-và-cấu-hình-phần-mềm):

| Mục | Giá trị |
|---|---|
| `~/iot/.env` | `HARDWARE_BACKEND=gpio`, `LID_ENABLED=true`, `SERIAL_PORT=AUTO` (không dùng), `MAC_ADDRESS=2C:CF:67:DB:C5:C3`, `MQTT_BROKER=broker.hivemq.com`, `BACKEND_API_URL=https://api.locker-drone.tech`, `POSTGRES_*`. Từ 2026-10-01 thêm chân theo người làm tủ ([spec § 6.1](cabinet-wiring-spec.md#61-tủ-lockr-tu01-chân-theo-người-làm-tủ)): `GPIO_RELAY_PINS=5,6,13,19,26,22,23`, `GPIO_DOOR_PINS=4,12,16,20,21,24,25`, `LID_PUL_PIN=18`, `LID_DIR_PIN=27`, `LID_HOME_PIN=17`, `LID_END_PIN=10` (bản cũ `.env.bak-20261001-pins`) |
| `~/iot/ui/.env.local` | `VITE_API_URL=` (trống), `VITE_LOCAL_API_URL=http://localhost:8000`, `VITE_LOCKER_ID=7`, `VITE_LOCKER_CODE=CAB-TU01` (trước 2026-10-01: tủ demo id 1), bộ `VITE_FIREBASE_*` |
| `lockr-controller.service` | `ExecStopPost=/usr/bin/pinctrl set 5,6,13,19,26,22,23 op dl` — ngắt mọi relay khi dịch vụ dừng/chết; danh sách chân theo `GPIO_RELAY_PINS` (bản cũ `.service.bak-20261001`) |
| `/etc/sysctl.d/90-lockr-dirty-limits.conf` | `vm.dirty_background_bytes=4194304`, `vm.dirty_bytes=16777216` |
| `~/.config/kanshi/config` | `profile kiosk { output HDMI-A-1 enable mode 1024x600 position 0,0 }` — giữ 1024×600 cả khi không đọc được EDID (sự cố 26) |
| `~/.config/labwc/rc.xml` | `<touch deviceName="WaveShare WS170120 (USB 3-1)" mapToOutput="HDMI-A-1" mouseEmulation="no"/>` |
| `/boot/firmware/cmdline.txt` | thêm `video=HDMI-A-1:1024x600@60D` (bản gốc: `cmdline.txt.bak-20260930`) |
| `/root/pi-setup.sh` | script đã dùng để dựng (không chứa mật khẩu) — chạy lại được; **chưa có** các bước 2026-09-30 (`kiosk.sh` mới, watchdog, `cmdline.txt`, `rc.xml`) |

## 7. Sự cố đã gặp

Sự cố 1–18 xảy ra trên bản cài USB flash đầu tiên; 19–21 khi dựng lại trên thẻ; 22–26 khi lắp màn hình.

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
| 22 | Kiosk tự về ô đăng nhập ~10 phút sau khi cắm màn | Màn cắm nóng: HDMI chập chờn nhiều lần, rồi labwc 0.20.1 crash `wlr_swapchain_create: Assertion 'width > 0 && height > 0'` khi tắt output `HDMI-A-1` không được. LightDM không tự đăng nhập lại; `kiosk.sh` cũ vẫn lặp mở Chromium vào compositor đã chết | `video=HDMI-A-1:1024x600@60D`, `lockr-display-watchdog`, `kiosk.sh` thoát theo labwc ([guide § 4.5](controller-wiring-guide.md#45-kiosk-trên-pi)). Thử `kill -ABRT` labwc: kiosk tự lên lại sau ~40 giây |
| 23 | Chạm vào thẻ trang chủ được, nhưng không gõ được mã OTP, số điện thoại, email | Không có bàn phím. squeekboard có chạy và báo `Visible`, nhưng labwc ẩn lớp `top` của nó khi có cửa sổ toàn màn hình — thêm `--enable-wayland-ime` cũng không hiện | Bàn phím ảo trong trang `ui/src/components/VirtualKeyboard.jsx` |
| 24 | Trang chủ: ô chọn tủ bị cắt mép trên, thẻ "Gửi Đồ / Thuê Tủ" bị cắt mép dưới | Cột phải cao ~650 px, khung chỉ 548 px; `justify-content: center` đẩy phần thừa ra cả hai đầu | Thu gọn khoảng cách, `justify-content: safe center` |
| 25 | Bàn phím ảo không hiện khi chạm bằng tay (chạm ảo qua `uinput` thì hiện) | `autotouch` của Raspberry Pi OS tự ghi `~/.config/labwc/rc.xml` với `mouseEmulation="yes"` cho `WaveShare WS170120 (USB 3-1)` lúc desktop khởi động có màn cắm sẵn — labwc đổi chạm thành click chuột; log trong trang (DevTools) toàn `pointerdown mouse`. Thiết bị ảo tên khác nên không dính | `mouseEmulation="no"` (bản cũ `rc.xml.bak-20260930`); bàn phím hiện theo `navigator.maxTouchPoints > 0`. Kiểm bằng tay 23:08: `pointerdown touch` → `osk SHOWN`, gõ được |
| 26 | Sau khi tắt hẳn rồi bật lại, hình ra 1024×768: kiosk chỉ chiếm phần trên, bị bóp méo trên màn 1024×600 | Màn lấy nguồn từ USB của Pi nên lúc kernel dò cổng (giây 0,9) màn chưa lên, không có EDID. Cổng đang bị ép "đã kết nối" (`video=…D`, sự cố 22) nên không có sự kiện cắm lại để dò lần nữa; labwc chọn chế độ dự phòng đầu tiên là 1024×768. Khởi động lại nóng không bị vì màn vẫn có điện | `~/.config/kanshi/config` đặt cứng `mode 1024x600`; áp dụng ngay, không cần khởi động lại |

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
| Nối dây theo [hướng dẫn có ảnh](tu01-wiring-photos.md) (jumper relay **H**, `PUL+`/`DIR+` về **3,3 V**, đo dây tín hiệu khoá trước; 6 điểm ảnh chưa trả lời được ở § 8 của hướng dẫn), bring-up theo guide § 5 | Code GPIO đã thử trên chip thật nhưng chưa có phần cứng tủ nối vào |
| Lắp màn vào tủ, cố định đầu chuyển micro-HDMI | Đầu chuyển lỏng làm HDMI chập chờn (sự cố 22) |
| Cân nhắc ẩn ô chọn tủ trên kiosk thật | Khách đứng trước tủ chọn được tủ khác trong danh sách |
| Khi nối relay: kiểm K1, K2 không kêu lúc Pi khởi động | Người làm tủ dùng GPIO5, GPIO6 cho `IN1`, `IN2`; hai chân này kéo lên lúc khởi động ([spec § 6.1](cabinet-wiring-spec.md#61-tủ-lockr-tu01-chân-theo-người-làm-tủ)) |
| Hỏi người làm tủ: chân của nắp trượt (TB6600, 2 công tắc hành trình), vị trí jumper relay, dây nâu thứ bảy | Hướng dẫn 2026-10-01 mới nêu relay và dây tín hiệu khoá |
| Nối dây xong: gán Pi vào tủ `CAB-TU01` (id 7) trên admin ([guide § 5.8](controller-wiring-guide.md#5-kiểm-tra-từng-bước-bring-up)), rồi chuyển tủ từ `MAINTENANCE` sang `ACTIVE`. **Không** đặt `LOCKER_ID=1` — tủ #1 `CAB-DEMO-01` do giả lập demo trả lời, hai bên cùng trả lời thì demo lỗi | Code hợp đồng MQTT đã có trên Pi (`137d945`, [ADR-0008](../adr/0008-hop-dong-mqtt-backend-tu.md)) |
| Chuyển sang broker riêng: cấp tài khoản `2CCF67DBC5C3` bằng `mqtt-device.sh`, đổi 5 biến `MQTT_*` trong `~/iot/.env` | SEC-04 — [mqtt-contract § 6](../01-overview/mqtt-contract.md#6-bật-broker-riêng-trên-vm) |
| Đặt tủ trong mạng riêng | Cổng `:8000` không xác thực, có `/setup/clear`, `/test/open-otp` |
