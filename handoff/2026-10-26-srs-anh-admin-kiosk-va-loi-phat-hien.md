# 2026-10-26 — Ảnh SRS (admin web, kiosk, Bluetooth) và lỗi phát hiện khi chụp

Người làm: binhtntse182370 (cùng Claude Code). Mốc code đã rà: backend `main` @ `102ca0a`, mobile `main` @ `53520aa`, iot `main` @ `806d7d9`, frontend `main` @ `20805b4`.

## 1. Tóm tắt

| Việc | Trạng thái | PR |
|---|---|---|
| Sửa `GET /api/admin/revenue/*` trả 503 lúc được lúc không | Xong, **chờ duyệt** (merge là deploy) | [backend#110](https://github.com/LockR-Tech/backend/pull/110) |
| Chèn ảnh admin web (3.6) và kiosk (3.5) vào SRS Report 3 | Xong, **chờ duyệt** | [docs#75](https://github.com/LockR-Tech/docs/pull/75) |
| Ảnh 3.2.34 Bluetooth Open Test, thay ảnh 3.2.28 Loyalty Points | Xong (cùng docs#75) | |
| Ảnh 3.4.1 Dispatch & Home Pickup | **Chưa làm** — xem § 6 | |
| Lỗi kiosk nhập sai mã báo "Hệ thống đang bận"; TimeLimiter 1 s ở 6 service còn lại | Đã sửa, **chờ duyệt** — § 5.1–5.2 | [backend#111](https://github.com/LockR-Tech/backend/pull/111) |
| Nhãn `OUT_OF_SERVICE` thô ở màn Bluetooth | Đã sửa, **chờ duyệt** — § 5.3 | [mobile#101](https://github.com/LockR-Tech/mobile/pull/101) |
| DRONE-05 kẹt `IN_FLIGHT`, KTV drone bị coi là "bận" | Đã sửa, **chưa PR** — § 5.4 | backend `fix/ktv-drone-ban-sai-va-drone-ket-bay` |

## 2. Ảnh đã chèn vào `rp3/Report3_Software Requirement Specification_LockR.docx`

Ảnh gốc nằm trong `rp3/srs-assets/`. Trong mọi ảnh, email, số điện thoại, số tài khoản ngân hàng và mã VietQR đều đã được che.

| Mục | Số ảnh | File gốc | Chú thích |
|---|---|---|---|
| 3.2.28 Loyalty Points | 1 (thay) | `mobile-customer/c20-loyalty-points.png` | Quy tắc mới: tích 10 %, 1 điểm = 1đ |
| 3.2.34 Bluetooth Open Test | 4 | `mobile-customer/c33*.png` | Bước "Đã mở ô" được **giả lập** vì không có tủ thật cạnh emulator (bản build tạm, không commit) |
| 3.5.1 Pick Up Parcel at Kiosk | 2 | `kiosk/k01*.png` | Trang chủ kiosk, ô nhập mã |
| 3.5.2 Kiosk Login, Send & Rent | 8 | `kiosk/k02*.png` | Đăng nhập (3 tab), QR app, OTP email, chọn ô, thời gian thuê, VietQR, mở ô, xác nhận bỏ hàng |
| 3.6.1 – 3.6.11 Admin web | 40 | `admin-web/a01…a11*.png` | Mỗi chức năng 1–6 ảnh, khớp từng thao tác ❖ |

Mục lục, List of Figures / Tables và Record of Changes đã được cập nhật bằng Word. File hiện có 171 trang, nặng khoảng 37 MB.

## 3. Mô tả đã sửa cho khớp màn hình thật

| Mục | Trước | Nay | Bằng chứng |
|---|---|---|---|
| 3.5.1 | Bàn phím số + camera QR | Một ô nhập mã (PIN / OTP / mã QR do máy quét gõ vào) + 'Mở khóa' | `iot/ui/src/screens/KioskScreen.jsx:1880` (`StaffScreen`) |
| 3.5.1 | Trả phí quá hạn bằng VietQR tại kiosk | Kiosk chỉ báo "Đơn đã quá hạn lấy hàng. Vui lòng thanh toán phụ phí quá hạn trên ứng dụng để mở ô." | `backend/iot-service/.../IotService.java:521` |
| 3.5.2 | Email OTP, QR, đăng ký nhanh | Thêm tab 'Số điện thoại'; sau khi mở ô có 'Đã bỏ hàng xong' hoặc xác nhận sau trên app | `KioskScreen.jsx:289`, `:1566` |
| 3.6.4 | 'Assign Controller' | 'Gán vào tủ' (khung 'Bộ điều khiển tủ'), 'Cho tài khoản thử' (khung 'Thử mở ô qua Bluetooth') | trang `/admin/lockers/{id}` |
| 3.6.8 | Tab pending / approved / rejected / withdrawals | 'Yêu cầu chờ xử lý', 'Lịch sử hoàn tiền'; rút tiền nằm ở tab 'Yêu cầu rút tiền' của trang Thanh toán | `/admin/refunds`, `/admin/payments` |
| 3.6.10 | 'Reset' | 'Khôi phục mặc định' | `/admin/business-settings` |

## 4. Dữ liệu production đã thay đổi trong lúc chụp

| Thay đổi | Ghi chú / cách hoàn tác |
|---|---|
| Đơn thuê `ORD-20261026-39TSZ1`, ô 4 tủ CAB-DEMO-01, 4 giờ, 4.000đ (tài khoản khách của binhtntse182370) | Đã thanh toán thật, mở bằng PIN trên kiosk, đang "Đang trong tủ" |
| Đơn thuê `ORD-20261026-LSWO83`, ô 5 tủ CAB-DEMO-01, 2 giờ, 2.000đ, tạo trên kiosk | Đã thanh toán thật, đang "Đang trong tủ" |
| Quyền thử Bluetooth ở CAB-DEMO-01 cho tài khoản khách trên | Bấm 'Thu quyền' ở `/admin/lockers/1` khi không cần nữa |
| Vài phiên QR đăng nhập kiosk và 2 mã mở ô Bluetooth (một lần, sống 120 s) | Tự hết hạn |

Để tủ demo trả lời lệnh mở, mình chạy `iot/simulate_demo_cabinet.py` nhưng **chỉ cho tủ 1 và tủ 2**: bản sao trong thư mục tạm có topic `cabinet/1/…`, `cabinet/2/…` thay cho `cabinet/+/…`. Cả hai đã tắt sau khi chụp. Nếu chạy bản gốc, simulator sẽ trả "SUCCESS" cho **mọi** tủ trên broker công khai, kể cả tủ thật.

## 5. Lỗi phát hiện và đề xuất sửa

### 5.1 Báo cáo doanh thu trả 503 lúc được lúc không — đã có PR

- **Hiện tượng:** `/admin/revenue` (vd `daily?from=2026-01-01&to=2026-12-31`) lúc ra số, lúc báo "Không lấy được dữ liệu thanh toán".
- **Nguyên nhân:** Feign của order-service chạy qua circuit breaker Resilience4j. Order-service lại không khai báo `resilience4j.timelimiter`, nên mọi lời gọi bị cắt ở mức mặc định **1 s** (`TimeLimiterConfig.ofDefaults()`, spring-cloud-circuitbreaker-resilience4j 3.3.2). Trang doanh thu gọi song song 7 API, mỗi API tải `/internal/payments/collected` của cả kỳ. Lúc server nguội, mình đo được 4,9 s.
- **Sửa:** [backend#110](https://github.com/LockR-Tech/backend/pull/110) đặt `timeout-duration: ${APP_RESILIENCE4J_TL_TIMEOUT:20s}`, lớn hơn readTimeout dài nhất (15 s), và thêm `FeignTimeoutConfigTest`.
- **Việc kèm theo:** `iot-service`, `loyalty-service`, `notification-service`, `payment-service`, `store-service` và `user-service` cũng bật circuit breaker cho Feign nhưng chưa có TimeLimiter. [backend#111](https://github.com/LockR-Tech/backend/pull/111) thêm `${APP_RESILIENCE4J_TL_TIMEOUT:10s}` cho cả 6 service.

### 5.2 Kiosk nhập sai mã báo "Hệ thống đang bận" thay vì "Mã không hợp lệ"

- **Hiện tượng:** trên kiosk CAB-DEMO-01, nhập `000000` hoặc `123987` rồi 'Mở khóa'. `POST /api/iot/unlock-with-code` trả `accepted=false, reasonCode=ORDER_LOOKUP_UNAVAILABLE`, message "Hệ thống đang bận, chưa kiểm tra được mã. Vui lòng thử lại sau ít phút." Lặp lại ổn định ở cả 2 lần thử.
- **Đã loại trừ:** `FeignCircuitBreakerInvocationHandler.unwrapAndRethrow` (openfeign-core 4.3.2) đã gỡ `NoFallbackAvailableException` và ném lại `FeignException` gốc, nên `isOrderLookupUnavailable` (`IotService.java:324`) vẫn nhận ra lỗi 4xx. Giả thuyết "bị bọc exception" mà mình nêu trước đó là **sai**.
- **Nguyên nhân khả dĩ** (cần xác nhận bằng log):
  1. **TimeLimiter 1 s** giống § 5.1: `iot-service` không có `resilience4j.timelimiter`. Nếu order-service tra mã chậm quá 1 s, lỗi sẽ là `TimeoutException`, tức không phải `FeignException`, nên bị coi là "không tra được".
  2. **Circuit breaker đếm lỗi 4xx là thất bại.** Mã sai khiến order-service ném `BusinessException("ORDER_NOT_FOUND")`, mặc định trả **400**. Resilience4j mặc định ghi mọi exception là thất bại. Sau 10 lần gọi với ≥ 50 % thất bại (vd nhiều người gõ sai mã), circuit `OrderClient#getByAccess` mở 30 s. Lúc đó **cả mã đúng** cũng bị từ chối với "Hệ thống đang bận".
- **Xác nhận:** trên VM, xem log iot-service. `IotService.java:225` in nguyên message:
  ```bash
  docker compose logs --since 2h iot-service | grep "Order lookup unavailable"
  # "...did not complete within..." ⇒ TimeLimiter ;  "CircuitBreaker '...' is OPEN" ⇒ circuit mở
  ```
- **Đã sửa ở [backend#111](https://github.com/LockR-Tech/backend/pull/111)**: `ignore-exceptions` áp cho cả 9 service có Feign circuit breaker, TimeLimiter cho iot-service. Test `FeignResilienceConfigTest` kiểm: 30 lỗi 400 ⇒ circuit vẫn đóng; 30 lỗi 500 ⇒ mở. Cấu hình (`backend/iot-service/src/main/resources/application.yml`):
  ```yaml
  resilience4j:
    circuitbreaker:
      configs:
        default:
          # 4xx là câu trả lời hợp lệ của service kia (mã sai, hết hạn…), không phải dấu hiệu nó sập.
          ignore-exceptions:
            - feign.FeignException$FeignClientException
    timelimiter:
      configs:
        default:
          timeout-duration: ${APP_RESILIENCE4J_TL_TIMEOUT:20s}
          cancel-running-future: true
  ```
  Sau deploy, thử tay: gõ sai mã hơn 10 lần trên kiosk rồi nhập một PIN đúng ⇒ ô vẫn mở.
- **Phía kiosk** (iot `fix/kiosk-o-nhap-ma-mo-o`, chờ duyệt): gặp `ORDER_LOOKUP_UNAVAILABLE` hoặc lỗi mạng thì giữ nguyên mã, nút đổi thành 'Thử lại', thông báo màu xanh. Trước đây kiosk báo đỏ như mã sai và xoá mã sau 2 s.

### 5.3 Màn "Thử mở ô qua Bluetooth" hiện nhãn thô `OUT_OF_SERVICE`

- **Hiện tượng:** ô 6 và ô 9 của CAB-DEMO-01 hiện `OUT_OF_SE…` (xem ảnh 3.2.34).
- **Nguyên nhân:** `LockerLayoutHelper.statusLabel` (`mobile/lib/features/locker/domain/utils/locker_layout_helper.dart:136`) thiếu nhánh `OUT_OF_SERVICE` nên rơi vào `_ => st`. Màn KTV đã có nhãn này ở `ops_widgets.dart:60`.
- **Đã sửa ở [mobile#101](https://github.com/LockR-Tech/mobile/pull/101)**: thêm `'OUT_OF_SERVICE' => 'Ngưng dùng'` (màu giữ mặc định xám) và test cho helper.

### 5.4 DRONE-05 kẹt `IN_FLIGHT`; KTV drone `KTVdrone@gmail.com` ("Vi KTV") không nhận được việc

- **Hiện tượng:**
  - Tab Điều phối của Vi KTV có 0 đơn, công tắc ghi "Đang trong ca · đang bận một việc nên chưa được mời thêm."
  - Drone duy nhất của KTV này, DRONE-05 (trạm CAB-VGP-01), có trạng thái `IN_FLIGHT`. Nhưng nhiệm vụ duy nhất của nó thuộc đơn `ORD-DRN-0021`: đơn đã `COMPLETED`, còn nhiệm vụ vẫn `LAUNCHING`.
  - Đơn `ORD-20261026-KUGXYB` (lấy tại nhà, nguồn tủ demo) đang ở `SEARCHING`, tức chưa KTV nào nhận.
- **Nguyên nhân khả dĩ:**
  1. Dữ liệu cũ (nhiều khả năng là seed `ORD-DRN-*`): nhiệm vụ không được đóng khi đơn kết thúc, nên drone không được trả về `IDLE`.
  2. `DronePickupService.busy()` (`order-service/.../DronePickupService.java:147`) coi KTV là bận nếu còn nhiệm vụ ở `ACTIVE_MISSION` (gồm cả **`DROP_REPORTED`**) trên một đơn chưa kết thúc. Nếu KTV này từng báo rơi kiện (vd đơn `ORD-20261024-8P2CM8`, sự cố DPI-113), KTV sẽ bị khoá cho tới khi sự cố đóng. Đơn `DROP_REPORTED` lại bị ẩn khỏi tab Điều phối (`DroneDeliveryQueryService.java:123`), nên KTV không thấy mình đang "bận" vì việc gì.
- **Xác nhận** (DB order-service):
  ```sql
  SELECT m.order_id, m.status, o.order_code, o.status AS order_status, o.delivery_stage
  FROM drone_missions m JOIN orders o ON o.id = m.order_id
  WHERE m.assigned_by_user_id = <id Vi KTV>
    AND m.status IN ('AWAITING_LOADING','READY_TO_LAUNCH','LAUNCHING','DEPARTED','EN_ROUTE','APPROACHING','ARRIVED','DROP_REPORTED');
  SELECT * FROM drone_pickups WHERE technician_id = <id Vi KTV> AND status IN ('OFFERED','ACCEPTED','PICKED_UP');
  ```
- **Đề xuất sửa:**
  - **Dữ liệu:** đóng nhiệm vụ của `ORD-DRN-0021` và đưa DRONE-05 về `IDLE` qua trang admin (chi tiết drone) hoặc migration sửa seed.
  - **Code:** khi đơn drone vào trạng thái kết thúc (`COMPLETED` / `CANCELED` / `EXPIRED`) thì đóng nhiệm vụ và trả drone. Thêm việc đối soát định kỳ (giống đối soát ô tủ mỗi giờ) để dọn nhiệm vụ mồ côi.
  - **Sản phẩm:** quyết định KTV có đơn `DROP_REPORTED` có bị chặn nhận việc mới hay không. Nếu có, hiện lý do trên công tắc (vd "đang xử lý sự cố DPI-113") thay cho câu chung chung.
- **Đã kiểm trên production (29/10):** cả hai KTV drone `KTVdrone@gmail.com` và `se180211nguyenquocbaohuy@gmail.com` đang trong ca, `busy: true`, tab Điều phối 0 đơn. Nguyên nhân là khả năng 2: mỗi người còn một nhiệm vụ `DROP_REPORTED` trên đơn `AWAITING_DISPATCH` (Vi KTV: `ORD-20261024-RLC58R` / DPI-111; KTV kia: `ORD-20261024-8P2CM8` / DPI-113). Cả hai sự cố đã giao thu hồi cho KTV tủ khác. Nhiệm vụ `LAUNCHING` của `ORD-DRN-0021` không làm KTV bận (`busy()` đã bỏ qua đơn kết thúc) nhưng giữ DRONE-05 ở `IN_FLIGHT`.
- **Đã sửa (backend `fix/ktv-drone-ban-sai-va-drone-ket-bay`, chưa PR):**
  - **Sản phẩm:** KTV có đơn `DROP_REPORTED` **không** bị chặn nhận việc mới. Báo rơi kiện đã đóng nhiệm vụ (`endedAt`) và chuyển drone sang `FAULT`; việc thu hồi đi qua sự cố. `DronePickupService.ACTIVE_MISSION` bỏ `DROP_REPORTED`.
  - **Code:** `DroneMissionReconciler` (cron `app.order.drone-mission-reconcile-cron`, mặc định phút 40 mỗi giờ) đóng nhiệm vụ còn mở mà đơn đã rời `AWAITING_DISPATCH` (`CANCELED` + ghi chú) và trả drone: chưa phóng `RESERVED → IDLE`; đã phóng, kiện đã vào tủ (`STORING`/`COMPLETED`/`EXPIRED`) `IN_FLIGHT → IDLE`; đã phóng mà đơn huỷ `IN_FLIGHT → FAULT`. Drone đang thuộc nhiệm vụ khác còn chạy thì giữ nguyên.
  - **Dữ liệu:** không cần migration. Sau khi deploy, hai KTV hết "bận" ngay; DRONE-05 về `IDLE` ở lượt đối soát đầu tiên.

### 5.5 Khác (nhỏ)

| # | Vấn đề | Đề xuất |
|---|---|---|
| a | `PinScreen` (bàn phím nhập số ô + PIN, `KioskScreen.jsx:1633`) không còn được nối từ màn nào; nút 'Mở Tủ / Nhận Đồ' đi thẳng `StaffScreen` | **Đã sửa, chờ duyệt** (iot `fix/kiosk-o-nhap-ma-mo-o`): xoá `PinScreen`; ô nhập của `StaffScreen` đặt `inputMode="numeric"` nên bàn phím ảo hiện dạng số (khách chỉ tự gõ PIN 6 số, mã `LLQR…` do máy quét gõ) |
| b | Kiosk không thu phụ phí quá hạn; khách phải mở app để trả | Nếu muốn đúng mô tả cũ: hiện VietQR phụ phí ngay trên kiosk (dùng lại `PaymentScreen`) khi `reasonCode = OVERTIME_FEE_UNPAID` |
| c | Kiosk chạy local báo `[firebase] Chưa cấu hình Firebase Web app — đăng nhập bằng số điện thoại sẽ không dùng được` | Kiểm tra `VITE_FIREBASE_*` trong `ui/.env.local` của Pi production; nếu thiếu thì tab 'Số điện thoại' không dùng được |
| d | Đặt drone trên app giờ chỉ còn "KTV đến lấy kiện tại nhà" | Cập nhật lại mô tả 3.2.x (đặt drone) nếu còn nhắc gửi tại tủ |
| e | Docx SRS đã nặng 37 MB | Khi thêm ảnh: chèn JPEG ~1280 px (ngang) / 620 px (điện thoại), chất lượng 88 |

## 6. Còn thiếu trong SRS

| Mục | Thiếu | Cần gì để làm |
|---|---|---|
| 3.4.1 Dispatch & Home Pickup | Ảnh thẻ đơn drone, hộp xác nhận nạp hàng, phóng drone, nhận việc lấy hàng tại nhà; còn dòng "Screenshots of the order card, loading and launch dialogs will be added in the next revision." | Một tài khoản KTV drone **rảnh** có drone `IDLE` ở trạm nguồn (hoặc sửa § 5.4 trước), rồi nhận đơn lấy tại nhà → lấy hàng → nạp → phóng |
| 3.6.5 Cabinet Control | Ảnh có nút điều khiển nắp (mở / đóng / về gốc / dừng / chạy N vòng / tốc độ). Ảnh hiện tại chỉ có danh sách ô + nhật ký vì TU01 mất kết nối | Chụp lại khi tủ thật TU01 online |
| 3.5.1 Overdue pickup | Ảnh thông báo quá hạn trên kiosk | Một đơn quá hạn chưa trả phụ phí ở tủ demo |
| 3.2.34 | Ảnh mở ô Bluetooth thật (ảnh hiện tại là giả lập) | Chụp lại cạnh tủ thật có Pi bật dịch vụ BLE |

Sau khi bổ sung ảnh: chèn theo đúng định dạng đang có (bảng 3 cột không viền cho ảnh điện thoại, ảnh ngang 15,5 cm), thêm dòng Record of Changes, cập nhật mục lục bằng Word (Ctrl+A → F9 → "Update entire table") và thêm 1 dòng CHANGELOG.

## 7. Cách đã chụp (để chụp lại)

- **Admin web:** mở một cửa sổ Edge riêng với `--remote-debugging-port` và profile tạm, đăng nhập admin, rồi dùng `playwright-core` (`connectOverCDP`) để chụp ở khung 1440×900. Trước mỗi lần chụp, chạy JS **che trong DOM**: email → `ab***@domain`, SĐT → `090*****12`, dãy 8–16 số (STK) → `*****123`; ảnh VietQR làm mờ bằng CSS.
- **Kiosk:** `cd iot/ui && npx vite --port 3002`, mở `http://localhost:3002/?lockerId=1&lockerCode=CAB-DEMO-01` ở khung 1024×600. Tủ demo cần simulator (chỉ cho đúng id tủ, xem § 4).
- **Mobile:** emulator Android + `adb shell uiautomator dump` để tìm toạ độ theo nhãn, `adb exec-out screencap -p` để chụp.
