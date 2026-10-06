# Changelog

Mỗi thay đổi ở repo docs thêm **một dòng** vào ngày tương ứng (mới nhất ở trên). Ghi mã gap/SEC/ADR nếu có.

## 2026-10-06

- F2-G09: bảng điều khiển kỹ thuật `/service` trên Pi ([iot#12](https://github.com/LockR-Tech/iot/pull/12)) — mở từng ô với thời gian kích tuỳ chọn, sơ đồ 40 chân theo cấu hình đang chạy, chạy/chỉnh tốc độ trục nắp (vòng/giây, xung, tăng tốc, số vòng), chỉ nhận lệnh từ chính Pi qua SSH tunnel. Tủ `lockr-tu01` có **hai trục, 4 công tắc hành trình** (module 3 dây): `tu01-wiring-photos` § 6 viết lại (6.1 trục 1, 6.2 trục 2 với driver TB6600 thứ hai, GPIO9/11/7/8), § 8, § 9 (`LID_PULSE_US` 1000, `LID2_ENABLED`); guide § 3.E, § 4.3, § 5, § 6, § 7; hồ sơ Pi § 8. Không đổi verdict/%.

## 2026-10-04

- Hạ tầng: production chuyển sang VM Azure mới `85.211.182.170` (Malaysia West, Ubuntu 24.04, `Standard_B2as_v2`) vì subscription cũ hết credit; chép nguyên dữ liệu 9 DB + `assistant-db`, RabbitMQ, nginx/Let's Encrypt; DNS `api.locker-drone.tech` và secret `AZURE_VM_HOST` đã trỏ sang máy mới. `architecture.md` § 3, `release-deploy.md` § 1.

## 2026-10-02

- Mobile · L3 (xử lý sự cố ô tủ & điều chuyển ô): khắc phục lỗi gán nhầm phiếu sự cố ô tủ đang mở vào các đơn hàng đã hủy (`CANCELED`) hoặc hoàn tất (`COMPLETED`) trong quá khứ; bổ sung cơ chế liên kết phiếu sự cố theo mã đơn `orderCode` và tự động nhận diện đơn đích khi KTV thực hiện `[ĐIỀU CHUYỂN Ô] ... sang ô #X`; bổ sung hồ sơ điều chuyển ô an toàn trong chi tiết đơn hàng (`_OrderRelocationCard`), gồm ô ban đầu, mã PIN cũ đã vô hiệu hoá, ô mới tiếp nhận, mốc thời gian KTV mở ô cũ kiểm tra hiện trường, mốc thời gian hoàn tất chuyển ô, mã PIN mở ô mới đang kích hoạt, ảnh KTV chụp minh chứng và nút mở trực tiếp phiếu sự cố.

## 2026-10-01

- F1-G01 (một phần) · F1-G03 · F1-G04 (một phần) · F1-G07 · F1-G09 (local, chưa merge): đơn drone STANDARD được điều phối viên xác nhận từng chặng (`…/advance`), chặng cuối đặt ô nhận OCCUPIED; đơn DEMO phát vị trí nội suy lên STOMP và app bật bản đồ trực tiếp; huỷ đơn drone đã PAID hoàn về ví (`payment-service` thêm `/internal/payments/orders/{id}/refund`); người nhận khác người đặt. flow-1 thêm mục "Cập nhật 2026-10-01"; `drone-mission.mmd` D5–D9, `drone-status.mmd` T4 + PDF; `architecture.md` § 6. Verdict và % giữ nguyên, chờ nghiệm thu.
- F1-G07 (local, chưa merge): đơn drone giữ thêm ô DRONE ở tủ gửi (`orders.source_box_id`, order `V17`) từ lúc tạo tới khi nạp hàng/huỷ, nên ô vừa đặt chuyển xám trên sơ đồ tủ; job đối soát ô tính cả đơn `AWAITING_DISPATCH`; đơn drone `COMPLETED`/`CANCELED`/`EXPIRED` kéo `deliveryStage` theo (trước đây đơn đã lấy hàng vẫn hiện "Chờ nhận hàng"). flow-1 § 3 bước 1; `drone-mission.mmd` D1, D3, D5, D11 + PDF. Không đổi %.
- F1-G07 · F1-G10 (local, nhánh `feat/f1-g07-live-drone-tracking`, chưa merge): một read model hành trình drone cho khách, điều phối viên và admin (lộ trình A → B, số ô, tên người, hồ sơ nạp hàng, mốc giờ, nhật ký mới nhất trước); gateway thêm `/api/admin/drone-orders/**`; web `/admin/drone-orders`; app bấm thông báo chặng giao mở màn theo dõi drone; khách huỷ đơn drone đặt `deliveryStage = CANCELED`. flow-1 F1.05 (bằng chứng, verdict giữ PARTIAL), § 3, F1-G07, F1-G10; `architecture.md` dòng gateway; `drone-mission.mmd` D6 + note, `order-status.mmd` O5 + PDF render lại; STATUS § 3. Không đổi %.
- F2-G09: Pi `lockr-tu01` ép 7 chân relay về mức thấp từ firmware (`gpio=5,6,13,19,26,22,23=op,dl` trong `config.txt`) — GPIO5, GPIO6 của người làm tủ kéo lên lúc khởi động. Đo: giây thứ 3 đã `op dl`, `main.py` chạy ở giây 64. Spec § 6.1, tu01-wiring-photos § 3, § 8, § 9, hồ sơ Pi § 6, § 9.
- F2-G09: kiosk của Pi `lockr-tu01` trỏ vào tủ thật `CAB-TU01` (id 7). Hồ sơ Pi thêm sự cố 26 (bật nguội ra 1024×768 vì cổng HDMI bị ép mà không đọc được EDID ⇒ kanshi đặt cứng 1024×600); guide § 3.F, § 6. STATUS § 3.
- F2-G09: bản đồ chân tủ `lockr-tu01` đổi theo **hướng dẫn của người làm tủ** — `IN1…IN7` về GPIO 5, 6, 13, 19, 26, 22, 23; dây nâu tín hiệu khoá về GPIO 4, 12, 16, 20, 21, 24, 25; dây vàng sọc xanh gom về GND. `cabinet-wiring-spec` thêm § 6.1; `tu01-wiring-photos` § 3–6, § 8, thêm § 9 (`.env` trên Pi), ảnh `04-domino-1.jpg` đổi nhãn; hồ sơ Pi § 6, § 9. `DIR−` và công tắc gốc của nắp dời sang GPIO27, GPIO17 vì trùng chân cửa. Không đổi verdict/%. Pi đã vào Wi-Fi của chỗ đặt tủ mới.
- F2-G09: [03-hardware/tu01-wiring-photos.md](03-hardware/tu01-wiring-photos.md) — nối dây tủ `lockr-tu01` theo ảnh; ảnh gốc ở `locker/`, ảnh đánh nhãn ở `03-hardware/img/tu01/` (sinh bằng `scripts/annotate-tu01-photos.py`). Guide § 3.F, § 4.5 (kiosk.sh thoát theo labwc, watchdog, `mouseEmulation`), § 6; hồ sơ Pi: sự cố 22–25, tủ `CAB-TU01` id 7, Pi lên `f76eaaa` ([iot#10](https://github.com/LockR-Tech/iot/pull/10)), Pi đổi chỗ. STATUS § 0 mốc iot `137d945` → `f76eaaa`, § 3, § 4, § 5. Không đổi verdict/%.

## 2026-09-29

- Trang đăng nhập admin thiết kế lại theo Lock.R, bỏ đăng nhập Partner ([frontend#24](https://github.com/LockR-Tech/frontend/pull/24)): STATUS § 5 thêm một dòng. Không đổi verdict/%.

## 2026-09-27

- F2-G09 · SEC-04: iot#9, backend#33, frontend#22 đã merge và deploy (backend 16:03 UTC xanh), Pi `lockr-tu01` lên `137d945`. [ADR-0008](adr/0008-hop-dong-mqtt-backend-tu.md) → Accepted. STATUS § 0 mốc iot `c843447` → `137d945`, § 2 SEC-04, § 3 (việc lắp tủ; thêm việc bật broker riêng), § 4 mục 5, § 5; flow-1 F1.10, flow-2 F2.10/F2-G09 (verdict giữ nguyên), `architecture.md`, guide § 7, hồ sơ Pi (cảnh báo không đặt `LOCKER_ID=1`).
- F2-G09 · SEC-04 · [ADR-0008](adr/0008-hop-dong-mqtt-backend-tu.md) (Proposed): hợp đồng MQTT backend ↔ tủ — topic vận hành `cabinet/{lockerId}`, lệnh mở mang `boxId` + `slotIndex = boxNumber − 1`, admin gán Pi vào tủ bằng MAC (`iot/{mac}/…`), trạng thái cửa `OPEN/CLOSED` về đúng ô, broker Mosquitto riêng qua `wss://…/mqtt` với tài khoản + ACL theo tủ (tắt mặc định). Đặc tả mới [mqtt-contract.md](01-overview/mqtt-contract.md) (topic, payload, mã lỗi, ACL, các bước bật broker). Cập nhật `architecture.md` (iot-service: bảng `gateway_devices`, endpoint `/api/admin/iot/gateways`, dòng MQTT broker, lệnh test iot), [controller-wiring-guide](03-hardware/controller-wiring-guide.md) (§ 4.3 `LOCKER_ID`, `REQUIRE_DOOR_SENSOR`, broker riêng; § 5.8 gán Pi trên admin; § 5.9; § 7 việc 3–5), `cau-hinh-dich-vu-ngoai.md` § 9 + bảng tra, `chay-he-thong-cuc-bo.md` (`main.py` đã trả lời được backend), flow-1 F1.10, flow-2 F2.10/F2-G09, STATUS § 0 § 2 § 3 § 4, [hồ sơ Pi](03-hardware/pi-lockr-tu01.md). Code: [iot#9](https://github.com/LockR-Tech/iot/pull/9), [backend#33](https://github.com/LockR-Tech/backend/pull/33), [frontend#22](https://github.com/LockR-Tech/frontend/pull/22) — chưa merge nên chưa đổi verdict/%.
- F2-G09: Pi `lockr-tu01` dựng lại trên thẻ microSD SanDisk 64 GB — bản USB flash hỏng cơ sở dữ liệu gói sau mất điện. Ghi image bằng `rpi-imager --cli`, cloud-init đặt sẵn mật khẩu user (tránh lỗi mất tự đăng nhập), script dựng theo guide § 4 chạy hết 5 phút (trên USB gần 8 giờ); khởi động lại lên mạng sau ~25 giây. [pi-lockr-tu01](03-hardware/pi-lockr-tu01.md) viết lại theo bản cài mới (bỏ cảnh báo cấm `apt`, thêm 3 sự cố 19–21, § 5 cách dựng lại); sửa model màn thành Waveshare 7inch HDMI LCD (C) ở hồ sơ và guide § 1, § 3.F.
- F2-G09 · [ADR-0007](adr/0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md): tủ Nam Việt dùng **GPIO trực tiếp** như tài liệu nhà cung cấp, Arduino/RS485 giữ làm tuỳ chọn (`HARDWARE_BACKEND`) — thay đề xuất (a) ở cabinet-wiring-spec § 4 vì tủ giao không kèm Arduino/MAX485/adapter. [cabinet-wiring-spec](03-hardware/cabinet-wiring-spec.md): điểm quyết định 1 và 3 chốt, thêm § 6 bản đồ chân GPIO (chân relay trong GPIO9–27 vì kéo xuống lúc khởi động — kiểm bằng `pinctrl` trên Pi 5) và 3 chỉnh sửa so với nhà cung cấp (jumper relay H, `PUL+`/`DIR+` về 3,3 V, đo dây tín hiệu khoá). [controller-wiring-guide](03-hardware/controller-wiring-guide.md): danh sách mua tách phần chỉ cho RS485, sơ đồ khối GPIO, nối nguồn 24 V motor, nắp trượt, màn Waveshare HDMI, `.env` GPIO, `ExecStopPost` ép relay về LOW, bảng bring-up bằng `debug_gpio.py`, 6 lỗi hay gặp; mục 7 việc 6 còn lệnh MQTT. `architecture.md` dòng iot, STATUS § 3, hồ sơ `pi-lockr-tu01`.
- Gộp hướng dẫn chạy cục bộ cũ (`HUONG-DAN-CHAY-LOCAL.md`, chưa từng nằm trong repo) vào [chay-he-thong-cuc-bo.md](04-engineering/chay-he-thong-cuc-bo.md): thêm § chạy backend trên máy (build, `APP_SECURITY_JWT_SECRET` giờ bắt buộc, cổng, seed, biến môi trường chỉ ghi tên, trỏ web/mobile/kiosk về backend local, 9 lỗi hay gặp), đối chiếu lại với code hiện tại; sửa câu "admin web proxy `/api`" (thực ra gọi `VITE_API_BASE_URL`). Không chép tài khoản/mật khẩu mẫu của bản cũ. README: sơ đồ thư mục thêm 4 file `01-overview/`, `chay-he-thong-cuc-bo.md`, `handoff/`. Sửa dòng bảng lạc dính trước tiêu đề `cau-hinh-dich-vu-ngoai.md`.
- F2-G09: dựng thử Pi 5 `lockr-tu01` (Raspberry Pi OS Trixie) theo [controller-wiring-guide](03-hardware/controller-wiring-guide.md) và sửa § 4 theo kết quả: PostgreSQL cài bằng `apt` thay `docker-compose.postgres.yml` (file đó mở 5432 ra mạng với mật khẩu mặc định); gói `chromium` thay `chromium-browser`; kiểm cloud-init khi Imager không ghi Customisation; `SIMULATION=true` khi chưa có adapter RS485. **Kiosk**: gateway production trả 403 CORS cho `localhost:8000` (kiểm 2026-09-27) nên bỏ cách `:8000/ui`, chạy bản build bằng `vite preview` :3002 dùng lại proxy `/api` — việc nợ `base: '/ui/'` không còn chặn. Thêm § 4.6 (giới hạn dữ liệu chờ ghi, tắt máy đúng cách, journal vĩnh viễn, bootloader) và 8 dòng lỗi hay gặp. Thêm hồ sơ máy [pi-lockr-tu01.md](03-hardware/pi-lockr-tu01.md) với 18 sự cố, gồm hỏng hệ thống file trên USB flash sau mất điện. STATUS § 0 mốc iot `454c49a` → `e7b04c8`, § 3 cập nhật việc lắp tủ.

## 2026-09-25

- F1-G08 (local, chưa merge/deploy): thêm bước `AWAITING_LOADING → READY_TO_LAUNCH` bắt buộc trước khi phóng; lưu trạm nguồn, người nạp, khối lượng, mã niêm phong và checklist đúng kiện/cố định/khóa khoang; chặn quá tải, sai người phụ trách và launch thiếu hồ sơ; migration V15 đưa mission cũ về chờ nạp; mobile thêm hàng đợi và form xác nhận. F1.04 MISSING → DONE, L1 60 → 70 %; cập nhật sơ đồ drone mission.

- F2-G09: firmware tủ khớp sơ đồ đấu nối ([iot#7](https://github.com/LockR-Tech/iot/pull/7)) — `LOCK_PINS` / `MAGNETIC_PINS` đủ 7 ngăn theo bản đồ ở [cabinet-wiring-spec § 5](03-hardware/cabinet-wiring-spec.md), `MAX_SLOTS` 6 → 7, `SLAVE_ID` 2 → 1 (Pi chỉ quét từ 1 tới `MAX_CABINETS`). Sửa kèm một lỗi tiềm ẩn: mảng trạng thái cảm biến khai cứng `[6]` trong khi mọi vòng lặp chạy tới `NUM_SLOTS` — nâng lên 7 mà giữ `[6]` là ghi tràn mảng; giờ khai `[NUM_SLOTS]`. `RELAY_ON` giữ `HIGH` và đánh dấu **chưa xác minh với module thật**. Hai tài liệu phần cứng cập nhật theo, mục 7 của hướng dẫn gạch việc 1.

- F2-G09: thêm thư mục [03-hardware/](03-hardware/) — [cabinet-wiring-spec.md](03-hardware/cabinet-wiring-spec.md) chép sơ đồ đấu nối của nhà cung cấp (nguồn 12 V, TB6600, relay 8 kênh, 7 khoá) và đối chiếu với firmware: code điều khiển tủ qua **Arduino trên RS485** (`locker_controller.ino`, `serial_manager.py`) chứ không phải Pi cắm thẳng GPIO như tài liệu gốc; firmware mới khai 3 ngăn, trần 6 (`MAX_SLOTS`), chưa có gì cho động cơ bước. [controller-wiring-guide.md](03-hardware/controller-wiring-guide.md): chọn Pi thay Jetson, danh sách chuẩn bị, thứ tự nối dây, bảng bring-up dùng các script sẵn có, kiosk trên Pi (ba bẫy đã kiểm trong code: build thiếu `base: '/ui/'`, kiosk nhận tủ qua `?lockerId=`, origin `localhost:8000` chưa trong CORS gateway), và danh sách việc còn nợ trong code. Rà `iot` tới `454c49a`; STATUS § 0 cập nhật mốc iot, § 3 nhận việc lắp tủ.

## 2026-09-24

- Thêm [04-engineering/chay-he-thong-cuc-bo.md](04-engineering/chay-he-thong-cuc-bo.md): lệnh dựng admin web / landing / kiosk / mobile / giả lập tủ trên máy cá nhân, cổng mặc định theo `vite.config` từng repo, và 5 cái bẫy đã gặp (giả lập ghi thật vào production qua broker công khai — SEC-04; `flutter run` mất kết nối khi app bị kill; `adb` ngoài PATH; cổng không được nhả sau Ctrl+C; bẫy toolchain máy SA-KT32). Ghi rõ `flutter run -d chrome` nổ ở màn đăng nhập vì `main.dart` bỏ qua `Firebase.initializeApp` khi `kIsWeb` còn `login_screen` vẫn dựng `FirebaseAuth.instance`. Thêm dòng tra cứu vào AGENTS.md.
- STATUS § 5: ghi đợt sửa lỗi 2026-09-23 đã merge (mobile #24–#26, frontend #19, backend #26). **Chưa tính lại %** vì chưa rà lại checklist từng luồng.

## 2026-09-22

- F3-G06: cập nhật STATUS và flow 3 theo phần ADMIN quản lý drone đã merge trước 2026-09-21 22:51 (backend #24, frontend #17): route admin đổi trạng thái/pin không cần claim, giữ phân công KTV, chặn sửa/ngừng drone đang `RESERVED`/`IN_FLIGHT`; chưa tính các chỉnh sửa sau mốc này.

## 2026-09-21

- L2 (gửi hàng + thuê ô, 65 → 70 %): F2.04 DONE; cập nhật F2.03, F2.08, F2.09 và mục "luồng chạy" theo backend #20/#21, mobile #19, iot #5 — đơn thuê không bị kết thúc khi mở lại, xác nhận bỏ hàng cần đã mở ô, chặn mã của đơn chưa trả/thuê quá hạn, kiosk xác nhận bỏ hàng và kết thúc thuê bằng mã, app bỏ CASH chờ PAID. F2-G01 xong; F2-G04, F2-G07, F2-G11 xong một phần.
- L3 (phần KTV tủ, % giữ 45): F3.07, F3.08, F3.10 thêm bằng chứng backend #22, frontend #15, mobile #20 — KTV phụ trách tủ, định tuyến + thông báo phiếu, đóng phiếu trả tài sản, kiểm tra định kỳ ĐẠT/KHÔNG ĐẠT, nhắc hạn; F3-G08 xong; F3-G02, F3-G04, F3-G07 xong một phần. Ma trận vai trò và vòng đời phiếu viết lại.
- L4 (trợ lý RAG, 0 → 94 %): file luồng viết lại theo backend #23, frontend #16, mobile #21. [ADR-0006](adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md): Claude + Voyage AI, kho vector là container pgvector riêng (đóng STATUS Q2 phần LLM).
- `architecture.md`: thêm `assistant-service`, `assistant-db`, sự kiện `locker.report.routed/assigned`, `locker.schedule.due`, đường kiosk công khai mới, RBAC mới; bỏ hai dòng bảng lạc lên đầu file. Runbook dịch vụ ngoài thêm mục Anthropic/Voyage. Sơ đồ `order-status`, `locker-cell-status`, `architecture` cập nhật và render lại.

## 2026-09-20

- F1-G02 (backend #18, mobile #15, đã deploy): bổ sung trạng thái drone `RESERVED`, khóa cả order và drone để chống nhận trùng, giữ drone bằng compare-and-set khi nhận đơn; kiểm tra lại pin/bãi đáp/reservation trước cất cánh; hủy nhả reservation; simulator không ghi đè FAULT. Cập nhật flow 1 và hai sơ đồ drone; ghi nhận chu kỳ DEMO 3 giây.

## 2026-09-16

- Bàn giao: phần mobile đã kiểm tra đầy đủ (analyze 259 = baseline, 154 test pass, build Android thành công) nên bỏ cảnh báo "chưa qua kiểm tra máy móc". Ghi chú môi trường thêm bẫy Java 25 làm `flutter run` chết với thông báo `25.0.2` mà `flutter doctor` không phát hiện được.

- STATUS và bàn giao: ghi rõ cả ba repo đều đang đi trước production (kèm commit từng bên), và đánh dấu `mobile #7` là thay đổi duy nhất chưa qua kiểm tra máy móc.

- Trang `/admin/services` dựng lại theo mô hình thật (ba loại đơn, quy tắc ở `system_settings`) thay cho trang cũ gọi endpoint không tồn tại; `business-settings.md` thêm mục 7 mô tả trang này và cảnh báo `GET /api/admin/services` trả 404. Giao diện admin và app bỏ mã số nội bộ, hiện tên tủ, tên cửa hàng và số ô in trên tủ.

- Thêm [bàn giao trạng thái đầy đủ](handoff/2026-09-16-trang-thai-day-du-va-viec-con-lai.md): mốc commit từng repo, nút thắt quota Actions, thứ tự việc còn lại, kết quả kiểm tra, nợ kỹ thuật, ghi chú môi trường. STATUS § 3 gọn lại còn hai nút thắt vận hành; § 4 đặt deploy backend lên đầu; § 5 nhận hai mốc mới; SEC-01 và SEC-07 ghi rõ đã merge, chờ deploy.

- SEC-01, SEC-07 và FCM: ghi nhận backend #10 đã vá bằng code — STATUS § 2 và § 4, `architecture.md` (JWT secret, hàng FCM push). Thêm [`04-engineering/cau-hinh-dich-vu-ngoai.md`](04-engineering/cau-hinh-dich-vu-ngoai.md): runbook nạp khoá cho từng dịch vụ ngoài (JWT, Cloudinary, Twilio, SMTP, Azure, Cloudflare, MQTT, VNPay/MoMo, Firebase) — nơi đặt, cách kiểm tra đã ăn chưa, thứ tự ưu tiên theo rủi ro, và việc phải làm khi khoá bị lộ. AGENTS và README thêm con trỏ.

- F2-G03: thêm hợp đồng [`01-overview/receiver-pickup-code.md`](01-overview/receiver-pickup-code.md) — kênh gửi mã mở tủ cho người nhận chưa có tài khoản (SMS Twilio + email dùng chung SMTP auth-service), quy tắc bật/tắt trên admin, biến môi trường; `architecture.md` cập nhật hàng Email và SMS. Flow 2 cập nhật F2.06 và F2-G03; STATUS Q2 chốt nhà cung cấp SMS là Twilio và nhận việc mới.

- STATUS: mốc cập nhật 2026-09-16; F2-G08 (phần web) chuyển từ § 3 sang § 5 sau khi merge `43e5d00` và deploy Cloudflare xanh; § 5 ghi thêm API báo cáo backend và ADR-0005 đã lên production.

- F2-G08 (phần web): 3 trang `/admin/orders`, `/admin/payments`, `/admin/revenue` chuyển sang dữ liệu thật theo [`01-overview/admin-reporting-api.md`](01-overview/admin-reporting-api.md); F2.09 bỏ "web thiếu EXPIRED" khỏi cột còn thiếu; F2-G08 ghi rõ phần enum web đã xong và phần legacy còn lại. Thêm [bàn giao 2026-09-16](handoff/2026-09-16-bao-cao-admin-web-va-mobile-con-lai.md).

## 2026-09-15

- Thêm ADR-0005 (Proposed) và hợp đồng [`01-overview/business-settings.md`](01-overview/business-settings.md): quy tắc nghiệp vụ cấu hình trên admin, mỗi service sở hữu bảng `system_settings`; STATUS § 3 nhận 2 việc (cấu hình nghiệp vụ, trang đơn hàng/thanh toán/doanh thu dữ liệu thật).

- Bàn giao lưu ảnh Cloudinary: ghi nhận đã merge + deploy backend #3, frontend #4, mobile #4; smoke test backend đỏ do race Eureka (không rollback); việc còn lại là cấu hình `CLOUDINARY_URL` trên VM.

- Thêm `handoff/2026-09-15-luu-anh-cloudinary.md`: trạng thái PR, việc còn lại theo thứ tự, ghi chú môi trường để người/AI khác tiếp tục việc lưu ảnh Cloudinary; STATUS § 3 trỏ tới file này.

- Thêm ADR-0004 (Proposed) và hợp đồng API [`01-overview/media-storage.md`](01-overview/media-storage.md): lưu ảnh trên Cloudinary bằng signed direct upload; cập nhật `architecture.md` (route `/api/media/**`, bảng `report_attachments`, biến `CLOUDINARY_URL`); STATUS § 3 nhận việc.

## 2026-09-13

- Khởi tạo repo `docs`: README, AGENTS/CLAUDE, STATUS, tổng quan sản phẩm, kiến trúc, luật Git/commit/deploy/tài liệu, ADR-0001…0003.
- Rà soát code 4 luồng tại backend `705c556`, frontend `e1b9a73`, mobile `5890184`, iot `927b057`: L1 60 %, L2 65 %, L3 45 %, L4 0 %.
- L2 hạ F2.04 từ DONE xuống PARTIAL sau khi xác minh bug `send_parcel_page.dart:377-382` (xác nhận bỏ hàng bằng id payment).
- Ghi nhận rủi ro SEC-01…SEC-08.
- Thêm 5 sơ đồ A4: kiến trúc, trạng thái đơn hàng, vòng đời giao hàng drone, trạng thái drone, trạng thái ô tủ; script `render-a4.mjs` + CI kiểm tra 1 trang.
