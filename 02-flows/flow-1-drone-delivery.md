# L1 — Giao hàng bằng drone: lấy hàng tận nhà → bay → PIN → nhận hàng

> Sự cố rơi kiện trong chuyến bay được đặc tả riêng tại [Drone Parcel Drop Incident](../01-overview/drone-parcel-drop-incidents.md). Luồng này dừng order/mission ở `DROP_REPORTED`, tạo phiếu kiểm tra drone + nhiệm vụ thu hồi kiện và chỉ tiếp tục giao lại sau khi evidence, Hub handover và phương án khách hàng đều hợp lệ.

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **90 %** (9 / 10) — bay thật (STANDARD) và thả hàng bằng nắp trượt + servo đã có code, **chưa bay thử ngoài trời có đơn thật** | 2026-11-10 · backend `0ea9557` · mobile `main` · frontend `main` · iot `main` | [Vòng đời giao hàng](../diagrams/pdf/drone-mission.pdf) · [Trạng thái drone](../diagrams/pdf/drone-status.pdf) · [Trạng thái đơn](../diagrams/pdf/order-status.pdf) |

Viết tắt đường dẫn: `OS` = `backend/order-service/src/main/java/com/huynqb/laundrylocker/order`, `LS` = `backend/locker-service/…/locker`, `M` = `mobile/lib`, `FE` = `frontend/fe/src`.

## 1. Mục tiêu nghiệp vụ

Người gửi đặt giao hàng ngay tại nhà: chọn **điểm lấy hàng** (vị trí hiện tại hoặc ghim trên bản đồ) và **tủ nhận** có bãi đáp → thanh toán → hệ thống mời **KTV drone rảnh gần nhất** tới nhà lấy kiện (người gửi đọc mã lấy hàng) → KTV mang kiện về **tủ gửi** (tủ có bãi đáp gần điểm lấy hàng nhất, hệ thống tự chọn) và nạp thẳng lên drone → phóng → khách theo dõi hành trình → tới tủ nhận, camera drone nhận đúng mã ArUco của ô ⇒ tủ trượt mở nắp ⇒ servo nhả kiện ⇒ tủ đóng nắp ⇒ hệ thống cấp PIN và báo người nhận → người nhận nhập PIN ở kiosk (hoặc mở qua Bluetooth trong app), ô mở, đơn hoàn tất. Có nhánh ngoại lệ: huỷ trước khi KTV cầm kiện, KTV không lấy được kiện, đơn bị chặn vì sự cố/thời tiết, huỷ trước khi phóng, chuyến bay thất bại, rơi kiện, quá hạn không lấy.

> Luồng cũ (người gửi tự bỏ kiện vào ô DRONE ở tủ gửi rồi bấm "Tôi đã bỏ kiện vào ô") chỉ còn cho đơn tạo trước khi có lấy hàng tận nhà (đơn không có `pickupLatitude`) — `OS/service/DroneOrderMaintenanceService.java:537-558`.

## 2. Checklist

| # | Hạng mục | Bằng chứng chính | Verdict | Còn thiếu |
|---|---|---|---|---|
| F1.01 | Khách tạo đơn drone (lấy hàng tận nhà) | `POST /api/orders/drone-deliveries` (+ báo giá `…/quote`) → `OS/service/DroneOrderBookingService.java:106-236`: kiểm tạm dừng bay, số đơn mở, khai báo kiện, liên hệ người gửi/nhận (tên + SĐT Việt Nam + email bắt buộc), điểm lấy hàng; chọn tủ gửi `DroneSourceLockerSelector`; thời tiết + trạm dừng; giữ ô DRONE ở tủ nhận (`:147`); phí theo khối lượng, mã giảm giá theo tủ gửi, điểm thưởng. App `M/features/drone_delivery/presentation/pages/drone_booking_page.dart` (`_choosePickup`, `_refreshQuote`, `_submit`) + `pickup_location_picker_page.dart` | **DONE** | Phí chưa theo quãng đường |
| F1.02 | Bắt buộc thanh toán trước khi điều phối | Chỉ SePay VietQR (`app.payment.enabled-methods` mặc định `SEPAY`); chỉ đơn `PAID` mới mở lượt lấy hàng `OS/service/PaidOrderEffects.java:101` → `DronePickupService.java:217-237`; đơn 0đ (mã + điểm phủ hết) ghi đã trả ngay `DroneOrderBookingService.java:219`; chưa trả 30 phút tự huỷ `DroneOrderTimeoutSweeper`; launch chặn `DRONE_SURCHARGE_UNPAID` `DroneOrderMaintenanceService.java:215-218`; app mở bảng thanh toán ngay sau khi tạo đơn `drone_booking_page.dart` (`_payCreatedOrder`) | **DONE** | Admin bật lại `CASH` thì đơn drone vẫn tự xác nhận (payment-service không biết loại đơn); `POST /api/payments/checkout` không kiểm trạng thái đơn |
| F1.03 | Điều phối: KTV lấy hàng + gán drone, tạo mission | Mời KTV trong ca, vị trí còn hiệu lực, rảnh, trong bán kính, gần nhất `DronePickupService.java:305-383`; lời mời có hạn, mời người kế tiếp, quá 2 lượt báo admin `:762-786`; admin gán tay `:534-589` (`POST /api/admin/drone-orders/{id}/pickup/assign`). KTV đã cầm kiện mới gán drone: khoá đơn + drone `IDLE → RESERVED` compare-and-set, mission `AWAITING_LOADING` `DroneOrderMaintenanceService.java:66-132`; đổi drone trước khi phóng `:491-530`. App `M/…/widgets/drone_pickup_queue.dart`, `drone_pickup_sheet.dart`, `M/features/locker_ops/…/maintenance_home_page.dart` (`_acceptFlow`) | **DONE** | Gán drone vẫn do KTV chọn, chưa tự động |
| F1.04 | Lấy hàng tại nhà + nạp hàng tại tủ gửi | KTV nhập mã lấy hàng 6 số người gửi đọc, xác nhận đúng kiện, phải đứng trong `drone-pickup-confirm-max-distance-meters` (300 m) theo GPS ca trực, ảnh tuỳ chọn ⇒ `PICKED_UP` `DronePickupService.java:436-503`; không lấy được ⇒ báo lý do `:510-530`. Nạp: cân, mã niêm phong hệ thống cấp, 3 mục checklist ⇒ `READY_TO_LAUNCH`, cân lệch > 50 g ⇒ phụ thu `DroneOrderMaintenanceService.java:135-194`; launch kiểm lại hồ sơ `:210-213` | **DONE** | Giới hạn tải dùng một cấu hình chung cho cả đội, chưa theo model drone |
| F1.05 | Theo dõi hành trình gần thời gian thực | Một read model `OS/service/DroneDeliveryQueryService.java` cho khách / KTV / admin (tủ gửi–nhận, điểm lấy hàng, KTV lấy hàng, hồ sơ nạp, mốc giờ, nhật ký có toạ độ từng mốc `OrderHistoryLocator`). Telemetry thật `DroneTelemetryMqttListener` + `DroneTelemetryService` tự đẩy chặng STANDARD; DEMO nội suy `DroneDeliverySimulator`; vị trí phát STOMP `/topic/deliveries/{orderId}/position` (`DronePositionBroadcaster`), lưu đường bay `DroneFlightTrackRecorder` (V39). App `drone_delivery_detail.dart`, `drone_live_map_page.dart` (`droneLiveMapEnabled = true` `M/core/config/feature_flags.dart:44`); web `FE/pages/Admin/drone-orders/` (bản đồ, đường bay, camera trực tiếp `LiveCameraPanel.tsx`) | PARTIAL | Production chưa bật telemetry (`APP_DRONE_TELEMETRY_ENABLED` mặc định `false` trong `backend/docker-compose.yml:185`); chưa bay thử có GPS |
| F1.06 | Tới tủ nhận + thả hàng vào ô DRONE | Camera Pi drone thấy đúng ArUco của ô đích ⇒ phiên giao, chặng `ARRIVED`, lệnh mở **nắp trượt** `OS/service/DroneLockerCommunicationService.java:447-575`; tủ báo mở thật (`LIMIT_SWITCH`/`STEP_COUNT`, bỏ `BYPASS`) ⇒ `LID_OPENED` kèm lệnh nhả hàng `:1252-1313`; servo nhả xong `DROP_PHASE_COMPLETED` ⇒ đóng nắp `:951-998`; tủ đóng xong ⇒ `READY_FOR_PICKUP` `:1407`; servo lỗi ⇒ đóng nắp, phiên `PARCEL_RELEASE_FAILED`, đơn không vào ô `:1005-1063`. Pi drone `iot/drone-iot/lockr_drone/delivery.py`, `release.py`, `camera.py`. Dự phòng: KTV xác nhận tay `…/advance` | PARTIAL | Đã thử từng khâu trên bàn (servo, nắp CAB-TU01), **chưa chạy trọn với drone bay thật**; tủ chưa nối công tắc hành trình (`STEP_COUNT`) |
| F1.07 | Cấp PIN/QR + báo người nhận | Một chỗ cho mọi nguồn (giả lập, telemetry, tủ đóng nắp, KTV): ô nhận `OCCUPIED`, PIN 6 số, hạn lấy `drone-pickup-hours-limit` (24 giờ), drone `IN_FLIGHT → IDLE` `OS/service/DroneMissionProgressService.java:128-174`; gửi mã qua app (người nhận có tài khoản), email, SMS + ghi nhật ký đã gửi kênh nào `:300-331`; thông báo `READY_FOR_PICKUP` kèm số giờ lưu trữ và hạn lấy `:268-272` | **DONE** | SMS chỉ đi khi VM có đủ khoá Twilio |
| F1.08 | Nhập PIN mở ô → hoàn tất | Kiosk `/api/iot/unlock-with-code` mở ô rồi tự hoàn tất đơn `STORING` không phải RENTAL `backend/iot-service/…/IotService.java:560-575`; app "Mở ô" qua Bluetooth theo đơn (`POST /api/iot/ble/orders/{orderId}/token`, `M/features/locker_ops/presentation/widgets/order_ble_open.dart`); "Tôi đã lấy đồ — hoàn tất" `PUT /api/orders/{id}/complete` | **DONE** | Mở qua Bluetooth chưa thử với tủ thật |
| F1.09 | Ngoại lệ | Khách huỷ tới trước khi KTV cầm kiện `OS/service/OrderService.java:2794-2806`; KTV không lấy được kiện `DronePickupService.java:510-530`; đơn bị chặn (tạm dừng bay, trạm dừng, thời tiết, drone/tủ/bãi đáp có phiếu, quá hạn phóng) `DroneDeliveryBlockService`, quá hạn chặn ⇒ "giao không hoàn tất" `DroneDeliveryFailureService.java:78`; huỷ trước khi phóng (drone lỗi ⇒ `FAULT`) `DroneOrderMaintenanceService.java:313-404`; chuyến bay thất bại `POST …/drone-orders/{id}/fail`; rơi kiện (đặc tả riêng); hoàn tiền qua yêu cầu `REFUND_PENDING` `DroneRefundService`; trả kiện `DroneParcelService`; nhiệm vụ mồ côi `DroneMissionReconciler` | **DONE** | Chưa có `DELAYED`; chưa tự phát hiện chuyến bay hỏng từ telemetry |
| F1.10 | Tủ xác thực PIN và mở khoá vật lý | `backend/iot-service/…/IotService.java` → MQTT `cabinet/{lockerId}/command/open` → Pi `iot/services/locker_service.py`; tủ thật `CAB-TU01` mở được cả 7 ô ([hồ sơ tủ](../03-hardware/tu01-so-do-tong-quan.md)) | **DONE** | Broker riêng chưa bật (SEC-04) |

**Điểm:** DONE 8 × 1 + PARTIAL 2 × 0,5 = 9 / 10 = **90 %**. Lần chấm trước (70 %, 2026-09-25) tính trên code cũ; lý do đổi từng mục ở [CHANGELOG](../CHANGELOG.md) ngày 2026-11-10.

## 3. Luồng đang chạy hôm nay

Rà soát code ngày 2026-11-10. Giá trị trong ngoặc là mặc định; admin sửa được ở **Cấu hình nghiệp vụ** (`OS/settings/OrderSettingsCatalog.java`).

### 3.1 Đặt đơn và thanh toán

1. **Khách** (app → "Gửi hàng bằng drone", `drone_booking_page.dart`) chọn **điểm lấy hàng**: vị trí hiện tại hoặc ghim trên bản đồ (`pickup_location_picker_page.dart`), kèm địa chỉ và ghi chú. Chọn **tủ nhận** có bãi đáp và còn ô DRONE trống. Khai báo kiện: loại hàng, mức khối lượng, kích thước (tuỳ chọn, phải lọt khoang 30 × 25 × 20 cm), giá trị khai báo (≤ 2.000.000 đ), dễ vỡ, cam kết không hàng cấm. Nhập tên, SĐT Việt Nam, email của **cả người gửi lẫn người nhận** (bắt buộc).
2. App gọi `POST /api/orders/drone-deliveries/quote`: hệ thống **tự chọn tủ gửi** = tủ có bãi đáp gần điểm lấy hàng nhất mà còn phục vụ được (`DroneSourceLockerSelector`). Điều kiện: tủ hoạt động, bãi đáp OK, còn drone dùng được, trạm không bị dừng bay, điểm lấy hàng cách tủ ≤ `drone-max-pickup-meters` (5.000 m), quãng bay tới tủ nhận trong khoảng 200–5.000 m. App hiện tủ gửi, quãng đường, phí và thời tiết tuyến bay.
3. **Khách** bấm tạo đơn: `POST /api/orders/drone-deliveries` (Idempotency-Key). Hệ thống chặn khi:
   - đang tạm dừng bay toàn hệ thống hoặc trạm đang dừng;
   - thời tiết tuyến bay xấu (trừ khi admin tắt kiểm tra thời tiết);
   - khách đã có 3 đơn drone đang mở;
   - tủ nhận hết ô DRONE.

   Hợp lệ thì giữ một ô DRONE ở **tủ nhận** (tủ gửi không cần ô: KTV nạp kiện thẳng lên drone). Đơn ở `AWAITING_DISPATCH`, chặng `AWAITING_DISPATCH`, `UNPAID`; phí theo khối lượng khai báo, trừ mã giảm giá (xét theo tủ gửi) và điểm thưởng. Người nhận có tài khoản (khớp email, rồi SĐT) được liên kết và nhận thông báo.
4. App mở ngay bảng thanh toán **SePay VietQR**. Webhook SePay ⇒ `PAID`. Đơn 0đ ghi đã trả luôn. Chưa trả sau `drone-unpaid-cancel-minutes` (30 phút) ⇒ tự huỷ, nhả ô.

### 3.2 Lấy hàng tận nhà

5. **Hệ thống** — đơn `PAID` ⇒ mở lượt lấy hàng (`drone_pickups`, trạng thái `SEARCHING`) và sinh **mã lấy hàng 6 số** hiện trong đơn của người gửi. Mời KTV drone thoả cả 5 điều kiện:
   - đang **vào ca**;
   - có **bật nhận việc lấy hàng** trên app;
   - vị trí GPS cập nhật trong `drone-technician-location-max-age-minutes` (10 phút);
   - trong bán kính `drone-max-pickup-meters`;
   - **rảnh**: không đang được mời hay đang đi lấy kiện khác, không cầm kiện chưa tạo nhiệm vụ, không có nhiệm vụ chờ nạp / chờ phóng / đang bay.

   Người **gần điểm lấy hàng nhất** được mời trước (`OFFERED`).
6. **KTV drone** (tab Điều phối, `drone_pickup_queue.dart`) có `drone-pickup-offer-seconds` (180 giây) để **Nhận** hoặc **Từ chối**:
   - không trả lời hoặc từ chối ⇒ mời người kế tiếp; người vừa bỏ qua không bị mời lại cùng đơn trong `drone-pickup-reoffer-cooldown-minutes` (10 phút);
   - sau 2 lượt bỏ qua ⇒ báo mọi ADMIN để gán tay (web `/admin/drone-orders` → gán KTV);
   - job quét mỗi 30 giây (`DroneDispatchSweeper`) mời lại các lượt đang chờ.
7. **KTV** nhận ⇒ chặng `PICKUP_ASSIGNED`, khách được báo "kỹ thuật viên đang tới, đọc mã lấy hàng khi giao kiện". Quá `drone-pickup-timeout-minutes` (60 phút) chưa lấy ⇒ thu hồi việc, mời người khác.
8. **KTV** tới nhà người gửi → nhập mã lấy hàng người gửi đọc, xác nhận kiện đúng khai báo, chụp ảnh (tuỳ chọn). GPS ca trực phải mới và cách điểm lấy hàng ≤ `drone-pickup-confirm-max-distance-meters` (300 m). Hợp lệ ⇒ chặng `PICKED_UP`, ghi `parcelDroppedAt` (kiện đã rời tay người gửi). Không lấy được ⇒ KTV báo lý do: khách vắng, kiện không đúng khai báo, không tìm thấy địa chỉ, khác (bắt buộc ghi chú). Đơn kết thúc "giao không hoàn tất" và tạo yêu cầu hoàn tiền.
9. Đã trả tiền mà không KTV nào nhận lấy hàng sau `drone-dispatch-timeout-minutes` (120 phút) ⇒ đơn đóng "giao không hoàn tất" + hoàn tiền.

### 3.3 Nạp hàng và phóng

10. **KTV đã cầm kiện** mang kiện về tủ gửi và **gán drone**: `POST /api/drone-technician/drone-orders/{id}/accept {droneUnitId}`. Chỉ đúng KTV đã lấy kiện mới gán được. Drone phải đặt tại tủ gửi, `IDLE`, active, pin > 20 % và biết mức pin. Hai tủ phải `ACTIVE` và bãi đáp OK. Drone đổi nguyên tử `IDLE → RESERVED`, mission `AWAITING_LOADING`, chặng `ACCEPTED`. Drone gặp sự cố trước khi phóng ⇒ **đổi drone** (`…/change-drone`), nhiệm vụ quay về chờ nạp.
11. **KTV** "Xác nhận nạp" (`…/loading-confirmation`): cân thực tế, mã niêm phong `NP-yyMMdd-xxxxxx` do hệ thống cấp, 3 mục kiểm tra (đúng kiện, đã cố định, khoang đã khoá) ⇒ mission `READY_TO_LAUNCH`. Cân vượt khai báo quá 50 g ⇒ tính lại phí, đơn về `UNPAID`. **Khách** "Trả thêm phí chênh" hoặc "Không đồng ý" (`…/decline-surcharge`: huỷ, hoàn phần đã trả, trả kiện). Quá `drone-surcharge-timeout-minutes` (60 phút) ⇒ tự huỷ.
12. **KTV** "Phóng" (`…/launch`): kiểm lại hồ sơ nạp, đơn đã trả đủ, không tạm dừng bay, hai trạm không dừng, trong khung giờ bay, drone còn `RESERVED` + đủ pin, bãi đáp tủ nhận OK, thời tiết tuyến an toàn ⇒ drone `RESERVED → IN_FLIGHT`, chặng `LAUNCHING`, gửi email "đơn đã phóng" cho người gửi và người nhận. Đã lấy hàng mà quá `drone-launch-timeout-minutes` (120 phút) chưa phóng ⇒ đơn bị đánh dấu đang gặp sự cố.

### 3.4 Bay và thả hàng

13. **Chặng bay** `LAUNCHING → DEPARTED → EN_ROUTE → APPROACHING → ARRIVED`, chỉ đi tới, không lùi (`assertForwardTransition`). Ba nguồn:
    - **DEMO**: bộ giả lập, mỗi chặng `drone-demo stage-delay` (15 giây); nếu bật Indoor Demo ArUco và drone có Pi đang gửi telemetry thì dừng ở `APPROACHING`/`ARRIVED` chờ camera;
    - **STANDARD có telemetry**: Pi drone gửi MAVLink → MQTT `lockr/drones/{droneId}/telemetry` có chữ ký; order-service đẩy chặng theo khoảng cách ([hợp đồng](../01-overview/drone-telemetry-contract.md));
    - **KTV xác nhận tay**: `…/advance`, kèm chặng đang thấy để không nhảy cóc.
14. **Thả hàng** (kênh `lockr/drone/delivery/events` ↔ `…/commands`, mọi bản tin ký HMAC theo drone — [`iot/drone-iot/README.md`](https://github.com/LockR-Tech/iot/blob/main/drone-iot/README.md)):
    1. Pi drone hỏi mục tiêu (`TARGET_REQUEST`), backend trả mã ArUco của ô nhận.
    2. Camera thấy đúng mã ổn định ⇒ `MARKER_DETECTED`. Backend kiểm drone đang có nhiệm vụ ở `EN_ROUTE`/`APPROACHING`/`ARRIVED`, đúng đơn, đúng tủ, đúng mã ⇒ mở phiên giao, chặng `ARRIVED`, gửi tủ `cabinet/{lockerId}/command/open` với `lid: true` (nắp trượt, có `commandId` và `expiresAt`).
    3. Tủ báo `ACCEPTED` rồi `SUCCESS` có xác nhận phần cứng ⇒ backend gửi drone `LID_OPENED` + `parcelRelease`. Servo nhả kiện ⇒ `DROP_PHASE_COMPLETED`. Backend ra lệnh đóng nắp; tủ đóng xong ⇒ chặng `READY_FOR_PICKUP`.
    4. Tủ không phản hồi: gửi lại đúng lệnh cũ tối đa 5 lần; quá `open-lid-max-wait-seconds` (600 giây) thì huỷ phiên. Servo lỗi ⇒ đóng nắp an toàn, đơn **không** vào ô, KTV xử lý.

    Nhật ký liên lạc drone ↔ tủ: web `/admin/drone-logs`.

### 3.5 Nhận hàng

15. **Hàng vào ô** (chung cho mọi nguồn) ⇒ đơn `STORING`, mission `DEPOSITED`, ô nhận `OCCUPIED`, drone `IN_FLIGHT → IDLE`, cấp PIN 6 số, hạn lấy 24 giờ. Mã được gửi cho người nhận qua app (nếu có tài khoản và khác người đặt), email, SMS (người nhận chưa có tài khoản); nhật ký ghi đã gửi qua kênh nào.
16. **Người nhận** nhập PIN ở kiosk ⇒ ô mở và **đơn tự hoàn tất** `COMPLETED`. Hoặc dùng nút "Mở ô" (Bluetooth) trong app, hoặc bấm "Tôi đã lấy đồ — hoàn tất".
17. Không ai lấy ⇒ job mỗi giờ: quá hạn + `overdue-release-hours` (72 giờ) ⇒ `EXPIRED`, đồ chuyển kho, trao trả tại quầy (`/admin/storage`).

### 3.6 Ai thấy gì

- **Khách / người nhận**: màn theo dõi (`drone_delivery_tracking_page.dart`): timeline có giờ và toạ độ từng mốc, bản đồ trực tiếp, thẻ thanh toán / phụ thu / huỷ / mã lấy hàng / mã mở ô. Người nhận không thấy điểm lấy hàng và vị trí KTV.
- **KTV drone**: app tab Điều phối (lời mời, việc đang lấy, đơn chờ gán drone / nạp / phóng / xác nhận chặng / trả kiện), Đội bay, Sự cố, Việc của tôi, công cụ bay (Mission Planner, Flight Data).
- **Admin**: `/admin/drone-orders` (hành trình, gán KTV, đóng "giao không hoàn tất", bản đồ, đường bay, camera trực tiếp), `/admin/drone-incidents`, `/admin/drone-logs` (kèm chế độ thử nắp theo ArUco), `/admin/flight-control` (thời tiết, dừng trạm, lịch sử chặn bay), `/admin/drones`.

> Các mục "Cập nhật …" dưới đây là **lịch sử thay đổi** theo từng đợt, giữ lại để tra cứu. Mô tả hiện hành là § 1–3 ở trên. Rà soát 2026-11-10: code của **mọi đợt** dưới đây (kể cả các đợt ghi "cục bộ / chưa commit") đã có trên `main` của backend, mobile, frontend, iot; một số chi tiết đã được thay bằng luồng lấy hàng tận nhà (xem mục 2026-11-10 cuối phần lịch sử).

### Cập nhật 2026-10-01 — cục bộ trên nhánh `feat/f1-g07-live-drone-tracking`, chưa merge/deploy

Các thay đổi dưới đây đã có code + unit test nhưng **chưa chạy thử đầu-cuối**, nên verdict ở bảng § 2 giữ nguyên cho tới khi nghiệm thu.

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.01 · F1.07 | Người nhận khác người đặt: đơn nhận `receiverPhone`/`receiverName`; số trùng tài khoản thì người đó xem được hành trình và nhận mã trong app, không trùng thì mã gửi SMS khi hàng vào ô | `OS/service/OrderService.java` (`applyDroneReceiver`), `OS/service/DroneMissionProgressService.java` (`sendPickupCodeQuietly`), `M/features/drone_delivery/presentation/widgets/drone_booking_sheet.dart` |
| F1.02 · F1.09 | Đơn drone đã PAID bị huỷ (khách huỷ lúc chờ điều phối, đội bay huỷ trước khi phóng) được hoàn về ví Lock.R, `paymentStatus → REFUNDED`; hoàn lỗi thì đơn giữ PAID + ghi nhật ký để admin hoàn tay | `OS/service/DroneRefundService.java`, `payment-service/…/PaymentService.java` (`refundOrder`), `POST /internal/payments/orders/{orderId}/refund` |
| F1.05 | Đơn DEMO phát vị trí nội suy mỗi giây lên STOMP `/topic/deliveries/{orderId}/position`; app bật nút "Theo dõi trên bản đồ" cho đơn DEMO | `OS/service/DronePositionBroadcaster.java`, `M/core/config/feature_flags.dart` |
| F1.05 · F1.06 · F1.07 | Đơn STANDARD không còn kẹt ở LAUNCHING: điều phối viên đã nhận xác nhận từng chặng `POST /api/drone-technician/drone-orders/{id}/advance`; chặng cuối đặt ô nhận OCCUPIED, cấp PIN, trả drone IDLE (dùng chung với simulator) | `OS/service/DroneMissionProgressService.java`, `M/features/locker_ops/presentation/pages/maintenance_home_page.dart` |
| F1.01 | Đơn giữ thêm ô DRONE ở tủ gửi (`orders.source_box_id`, `V17`) tới khi nạp hàng/huỷ | `OS/service/OrderService.java` (`resolveAndReserveDroneSourceBox`) |

### Cập nhật 2026-10-03 — cục bộ, chưa merge/deploy

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.05 | Timeline hành trình (app khách/điều phối viên + web admin) hiện giờ đạt **ngay trên từng chặng**, thời gian chuyển từ chặng trước, "đã ở chặng này bao lâu" và mốc phụ (thanh toán, nạp hàng, sẵn sàng phóng, gửi mã, hạn nhận, người nhận lấy hàng); bỏ khối "Mốc thời gian" riêng | `M/…/widgets/drone_delivery_timeline.dart`, `FE/pages/Admin/drone-orders/DroneJourneyTimeline.tsx` |
| F1.05 | Bản đồ theo dõi: app có thẻ bản đồ A → B (vị trí drone ước theo chặng, km tổng/còn lại); web admin có bản đồ Leaflet, nghe vị trí trực tiếp qua STOMP khi có, không thì ước theo chặng; live map của khách thêm ETA thời gian thực (đếm ngược theo tốc độ đo giữa các snapshot), km còn lại, vĩ độ/kinh độ, marker tủ A/B | `M/…/widgets/drone_route_map_card.dart`, `M/…/pages/drone_live_map_page.dart`, `FE/…/drone-orders/DroneTrackingMap.tsx` |
| F1.05 | Gửi lúc (drone rời trạm), hàng vào tủ lúc, gửi mã cho người nhận lúc, người nhận lấy hàng lúc hiện ở khối lộ trình | `drone_delivery_status.dart` (`sentAt`, `depositedAt`, `pickupCodeEvent`) |
| F1.02 | Read model trả `paymentMethod`, `paymentReference`, `paymentTransactionId` của lần thanh toán thành công gần nhất (payment-service thêm 2 field vào `OrderPaymentSummary` nội bộ) | `OS/service/DroneDeliveryQueryService.java`, `payment-service/…/InternalPaymentReportService.java` |
| F1.07 | Hàng vào ô ⇒ gửi **email** mã mở ô cho người nhận (email nhập lúc đặt — field mới `receiverEmail` — hoặc email tài khoản người nhận, kể cả khi người đặt tự nhận), kèm app/SMS như cũ; ghi dòng nhật ký `READY_FOR_PICKUP → READY_FOR_PICKUP` cho biết đã gửi qua kênh nào, lúc nào, hoặc chưa gửi được | `OS/service/DroneMissionProgressService.java` (`sendPickupCodeQuietly`), `CreateDroneDeliveryOrderRequest.java`, `drone_booking_sheet.dart` |

Email chỉ thực sự đi khi notification-service có cấu hình kênh email (`GuestEmailSender`); chưa cấu hình thì nhật ký ghi "Chưa gửi được mã".

### Cập nhật 2026-10-04 — cục bộ, chưa merge/deploy

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.02 | Tạo đơn drone xong app mở bảng thanh toán ngay (cùng bảng với đơn tủ: phương thức admin bật → VietQR/ví/cổng), rồi mới sang màn theo dõi; khách đóng bảng thì đơn vẫn giữ. Thẻ "Đơn chưa thanh toán" ở màn theo dõi có nút **Thanh toán ngay** trả tại chỗ, không còn đẩy sang danh sách đơn (phần "nhắc trả tiền lúc đặt" của F1-G06) | `M/…/widgets/drone_order_payment.dart`, `drone_booking_sheet.dart` (`_payCreatedOrder`), `drone_delivery_detail.dart` (`_UnpaidBanner`), `M/…/pages/drone_delivery_tracking_page.dart` (`_pay`) |
| F1.01 | Sheet đặt đơn tra số ô DRONE còn trống của từng tủ nhận (`GET /api/lockers/{id}/layout`): hiện "còn N ô drone"/"hết ô nhận", tự chọn tủ còn ô, khoá nút tạo đơn và báo rõ khi tủ nhận đầy; nếu khách có đơn drone chưa thanh toán đang giữ ô thì có nút mở đơn đó để trả. `BOX_NOT_AVAILABLE` lúc tạo đơn báo đúng là tủ nhận hết ô thay vì "ô tủ không còn trống" | `drone_booking_sheet.dart` (`_loadFreeCells`, `_DestinationFullNotice`) |
| F1.09 | Màn theo dõi của khách có thẻ **Huỷ đơn** khi đơn còn ở chặng chờ đội bay tiếp nhận (đúng guard `assertDroneCancelable`): hỏi xác nhận, nói rõ đơn đã trả tiền sẽ hoàn về ví Lock.R, gọi `PUT /api/orders/{id}/cancel` rồi báo kết quả theo `paymentStatus` trả về (REFUNDED / PAID chưa hoàn / chưa trả). Danh sách đơn cũng có **Hủy đơn** cho đơn drone ở chặng này, dùng chung hộp xác nhận. Đóng phần "nút huỷ cho khách" của F1-G04 | `M/…/widgets/drone_order_cancel.dart` (`confirmAndCancelDroneOrder`), `drone_delivery_detail.dart` (`_CancelCard`), `drone_delivery_tracking_page.dart` (`_cancel`), `drone_delivery_status.dart` (`canCustomerCancel`), `M/features/locker_ops/…/my_locker_orders_page.dart` (`_cancelDroneOrder`) |
| F1.01 · F1.02 | **Phí theo khối lượng**: khách chọn mức khối lượng khi đặt (`app.order.drone-weight-options-grams`, mặc định 500/750/1000/1500/2000/3000 g, ẩn mức vượt tải tối đa); phí = phí cơ bản (gồm `drone-base-weight-grams` = 500 g) + `drone-weight-step-fee` (3.000 đ) cho mỗi nấc `drone-weight-step-grams` (250 g) vượt, kể cả nấc chưa trọn. Đặt đơn vượt tải tối đa bị từ chối `DRONE_PAYLOAD_TOO_HEAVY` | `OS/settings/OrderRules.java` (`droneDeliveryFee(int)`), `OrderSettingsCatalog.java`, `OS/service/OrderService.java` (`validateDroneParcelWeight`), `M/core/config/business_config.dart` (`droneDeliveryFeeFor`), `drone_booking_sheet.dart` |
| F1.04 · F1.02 | **Cân lệch khi nạp hàng**: cân thực tế vượt khai báo quá `drone-weight-tolerance-grams` (50 g) ⇒ tính lại phí theo cân thực tế, phần chênh cộng vào tổng đơn, đơn về `UNPAID` (giữ `paidAmount`, checkout chỉ thu phần thiếu — cùng cơ chế gia hạn thuê), lưu `drone_missions.weight_surcharge` (`V18`), báo khách; launch bị chặn `DRONE_SURCHARGE_UNPAID` tới khi trả. Nhẹ hơn khai báo không hoàn. Đội bay huỷ đơn đang nợ phụ thu vẫn hoàn phần khách đã trả. App khách có thẻ trả thêm ở màn theo dõi; app đội bay báo trước khoản thu thêm lúc nhập cân và khoá nút Phóng; web admin hiện khoản thu thêm | `OS/service/DroneOrderMaintenanceService.java` (`applyWeightSurcharge`, `launch`), `DroneRefundService.java` (`hasCollectedMoney`), `drone_delivery_detail.dart` (`_UnpaidBanner`), `maintenance_home_page.dart` (`_confirmLoading`), `FE/pages/Admin/drone-orders/index.tsx` |
| F1.04 | **Mã niêm phong do hệ thống cấp** (`NP-<yyMMdd>-<6 ký tự>`): app đội bay sinh và hiển thị mã chỉ đọc; `sealCode` trong request thành tuỳ chọn, bỏ trống thì order-service tự sinh | `ConfirmDroneLoadingRequest.java`, `DroneOrderMaintenanceService.java` (`generateSealCode`), `M/…/entities/drone_labels.dart` (`generateDroneSealCode`) |

### Cập nhật 2026-10-04 (telemetry drone thật) — cục bộ, chưa merge/deploy

Hợp đồng: [drone-telemetry-contract](../01-overview/drone-telemetry-contract.md). Verdict ở bảng § 2 giữ nguyên cho tới khi bay thử có đơn thật.

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.05 | **Pi trên drone** (Pi 5 `lockr-drone-01`, Pixhawk 6C / ArduPilot qua USB) đọc MAVLink và gửi telemetry có chữ ký lên MQTT mỗi giây: vị trí, độ cao, GPS, pin, vận tốc, mode, armed, trạng thái đáp, cảnh báo; phân biệt mất cổng, mất heartbeat và số đo cũ. Đã chạy trên thiết bị thật trên bàn (trong nhà, chưa có GPS, chưa cắm pin): bản tin tới broker, chữ ký đúng | `iot/drone-iot/` (`main.py`, `lockr_drone/mavlink_reader.py`, `state.py`, `telemetry.py`, `mqtt_publisher.py`, `signing.py`) |
| F1.05 · F1.06 | order-service nghe `lockr/drones/+/telemetry` (tắt mặc định), kiểm chữ ký + độ tươi, **tự đẩy chặng** đơn STANDARD theo vị trí: cất cánh → DEPARTED, rời tủ gửi → EN_ROUTE, vào vùng tủ nhận → APPROACHING, autopilot báo đã đáp trong bán kính bãi đáp → ARRIVED. Chặng "hàng vào ô" vẫn do điều phối viên xác nhận. Phát vị trí thật lên STOMP với ETA theo tốc độ đo được | `OS/service/DroneTelemetryMqttListener.java`, `DroneTelemetryService.java`, `DroneTelemetrySigner.java`, `DroneTelemetryRegistry.java`, `OS/dto/DroneTelemetryFrame.java` |
| F1.03 | Pin thật của drone đồng bộ về đội bay (`POST /internal/drones/telemetry`), nên kiểm tra pin trước khi phóng không còn dựa vào số nhập tay | `LS/service/LockerService.java` (`recordDroneTelemetry`), `OS/client/LockerDroneClient.java` |
| F1.05 | Read model trả `liveTracking`; app khách mời "Theo dõi trên bản đồ" cho cả đơn drone thật khi còn tín hiệu; thẻ nhiệm vụ của điều phối viên báo "Drone đang gửi tín hiệu · chặng bay tự cập nhật" (nút xác nhận tay vẫn còn làm dự phòng) | `OS/service/DroneDeliveryQueryService.java`, `M/…/pages/drone_delivery_tracking_page.dart`, `M/features/locker_ops/…/maintenance_home_page.dart` |

### Cập nhật 2026-10-06 (rà soát thanh toán đơn drone) — cục bộ, chưa merge/deploy

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.02 · F1.09 | **Tiền về sau khi đơn đã huỷ** (khách huỷ lúc mã chuyển khoản/cổng còn chờ, rồi tiền mới tới): trước đây đơn `CANCELED` bị lật `PAID` và không ai hoàn. Nay sự kiện thanh toán trên đơn drone đã huỷ tự hoàn khoản đó về ví sau vài giây, kể cả khi đơn đã `REFUNDED` từ trước | `OS/service/OrderPaymentEventListener.java`, `DroneLateRefundScheduler.java`, `DroneRefundService.java` (`refundLatePayment`) |
| F1.02 | Hoàn tiền không còn báo "đã hoàn 0 đ" rồi đóng đơn là `REFUNDED` khi payment-service không hoàn được khoản nào: đơn giữ `PAID` + nhật ký "cần admin kiểm tra" | `DroneRefundService.java` (`refund`) |
| F1.03 · F1.09 | Khách huỷ và sự kiện thanh toán nay **khoá bản ghi đơn** như accept/nạp hàng/phóng, hết cảnh huỷ chạy xen với tiếp nhận làm đơn `CANCELED` mà nhiệm vụ vẫn giữ drone, hoặc sự kiện thanh toán ghi đè lệnh huỷ | `OS/service/OrderService.java` (`cancel`), `OrderPaymentEventListener.java` |
| F1.02 | `nextAction`/`paymentRequired` của đơn drone khớp guard: chưa trả (kể cả đang nợ phụ thu cân lệch) ⇒ `PAY_FOR_DRONE` + `paymentRequired = true`; trước đây báo `WAIT_FOR_DRONE` và "chưa cần trả" (phần này của F1-G06) | `OS/service/OrderNextActions.java`, `OrderNextActionsDroneTest.java` |

**2026-10-07 — hoàn tiền theo yêu cầu chuyển khoản (backend #45):** payment-service không còn hoàn về ví; `POST /internal/payments/orders/{id}/refund` chỉ tạo yêu cầu hoàn `PENDING` để admin chuyển khoản. Đơn drone bị huỷ vì thế sang `paymentStatus = REFUND_PENDING` (không phải `REFUNDED`), nhật ký và thông báo ghi "đã ghi nhận yêu cầu hoàn … — chờ admin chuyển khoản"; admin duyệt ⇒ payment-service đổi đơn sang `REFUNDED`, từ chối ⇒ `PAID`. App khách, thẻ đơn đã huỷ và trang admin đơn drone đổi lời theo; sự kiện thanh toán tới trễ không lật đơn `REFUND_PENDING` về `PAID` và không báo "thanh toán thành công" cho đơn drone đã huỷ. Bằng chứng: `OS/service/DroneRefundService.java`, `OrderPaymentEventListener.java`, `M/features/drone_delivery/…/drone_order_cancel.dart`, `drone_delivery_detail.dart`, `FE/pages/Admin/drone-orders/index.tsx`. Các dòng "hoàn về ví" ở mục 2026-10-01 và bảng trên đọc theo nghĩa này.

Còn hở sau rà soát: `CASH` vẫn tự xác nhận cho đơn drone nếu admin bật phương thức này (payment-service không biết loại đơn — F1-G06); `POST /api/payments/checkout` không kiểm trạng thái đơn; sự kiện `payment.completed` lặp lại (VNPay return + IPN) sau khi đã cộng phụ thu có thể lật đơn về `PAID` khi chưa thu phần chênh (đợt 2026-10-09 bên dưới đã sửa phần này, nay có trên `main`; VNPay bị gỡ hẳn ở backend #65 — xem 2026-10-13); hoàn tiền lỗi không tự thử lại.

Chưa kiểm chứng: backend nhận telemetry từ broker thật (mới có unit test + vector chữ ký kiểm chéo Python/Java); bay thật có GPS; dịch vụ systemd trên Pi; Pi dùng mạng ngoài Wi-Fi trường.

Còn thiếu sau đợt này: khách tự từ chối phụ thu cân lệch trong app (hiện phải nhờ đội bay huỷ); bật telemetry trên production (`APP_DRONE_TELEMETRY_ENABLED`, `DRONE_TELEMETRY_SECRET`) và bay thử; tự xác nhận hàng vào ô; abort/return-to-base, FAILED/DELAYED; người gửi mở ô DRONE ở tủ gửi từ app/kiosk (cần hợp đồng mở khoá của iot-service); người nhận có tài khoản chưa thấy đơn trong danh sách đơn của mình (F2-G06).

### Cập nhật 2026-10-09 (rà soát rule nghiệp vụ) — cục bộ, chưa commit/merge/deploy

Đã có code + unit test, **chưa chạy thử đầu-cuối**; verdict ở bảng § 2 giữ nguyên.

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.09 | **Chuyến bay thất bại sau khi phóng**: điều phối viên đã nhận nhiệm vụ (`POST /api/drone-technician/drone-orders/{id}/fail`) hoặc admin (`POST /api/admin/drone-orders/{id}/fail`) báo lý do (cùng bảng mã với huỷ trước khi bay) khi mission ở `LAUNCHING`…`ARRIVED`. Đơn sang `CANCELED` với chặng `FAILED`, mission `FAILED`, ô nhận được nhả, drone `IN_FLIGHT → FAULT`, báo người gửi + người nhận, rồi tạo yêu cầu hoàn tiền như đơn huỷ. Trước đây đơn kẹt mãi ở chặng bay và không hoàn được tiền | `OS/service/DroneOrderMaintenanceService.java` (`reportFlightFailure`), `OS/controller/OrderController.java`, `M/features/locker_ops/…/maintenance_home_page.dart` (`_canReportFailure`), `FE/pages/Admin/drone-orders/index.tsx` (`FlightFailureForm`) |
| F1.09 | **Giữ hồ sơ nhiệm vụ khi huỷ/thất bại**: mission không còn bị xoá khi đội bay huỷ; lưu `ended_at`, `ended_by_user_id`, `end_reason`, `end_note`, `failed_stage` (`V19`) cùng cân nặng, niêm phong, người nạp | `OS/model/DroneMission.java`, `V19__drone_mission_outcome.sql`, `DroneOrderMaintenanceService.java` (`closeMission`) |
| F1.02 · F1.09 | **Tự huỷ đơn drone chưa thanh toán** sau `app.order.drone-unpaid-cancel-minutes` (mặc định 30 phút, 0 = tắt), quét mỗi 5 phút: nhả ô ở cả tủ gửi lẫn tủ nhận, báo khách. Chỉ đơn chưa thu đồng nào và đội bay chưa tiếp nhận; đơn nợ phụ thu cân lệch không thuộc job này. Job tự huỷ chung chỉ quét `INITIALIZED` nên trước đây hai ô bị giữ vô hạn. Tiền về sau khi tự huỷ vẫn được hoàn nhờ `DroneLateRefundScheduler` | `OS/service/DroneUnpaidOrderSweeper.java`, `OS/settings/OrderSettingsCatalog.java` |

Đợt hai cùng ngày (cũng cục bộ, có unit test, chưa chạy đầu-cuối):

| Mục | Thay đổi | Bằng chứng |
|---|---|---|
| F1.01 | **Khai báo kiện hàng**: loại hàng (`DOCUMENT`/`FOOD`/`CLOTHING`/`ELECTRONICS`/`COSMETICS`/`OTHER`), kích thước tuỳ chọn (phải lọt khoang `drone-max-parcel-*-cm`, mặc định 30 × 25 × 20 cm, kiện xoay được), giá trị khai báo tuỳ chọn (trần `drone-max-declared-value`, mặc định 2.000.000 đ), cờ dễ vỡ, và **bắt buộc** cam kết không gửi hàng cấm bay (`DRONE_PROHIBITED_ITEMS_NOT_DECLARED`). `paymentMethod` trong request không còn bắt buộc (đơn không lưu) | `V20__drone_parcel_declaration_custody.sql`, `CreateDroneDeliveryOrderRequest.java`, `OS/service/OrderService.java` (`validateDroneParcelDeclaration`), `M/…/entities/drone_parcel.dart`, `drone_booking_sheet.dart` (`_parcelFields`, `_readParcel`) |
| F1.01 | **Giới hạn lúc đặt đơn**: tầm bay tối đa giữa hai tủ (`drone-max-route-meters`, 5.000 m, lưu `orders.route_distance_meters`), số đơn drone đang mở mỗi khách (`drone-max-open-orders-per-user`, 3), và công tắc **Tạm dừng bay** (`drone-flights-suspended`) chặn đặt đơn, tiếp nhận và phóng | `OrderService.java` (`assertDroneOrderingOpen`, `validateDroneRoute`), `OS/settings/OrderSettingsCatalog.java` |
| F1.03 | **Người gửi xác nhận đã bỏ kiện** vào ô gửi (`POST /api/orders/{id}/drone-delivery/drop-confirmation`, cần `PAID`) ⇒ `orders.parcel_dropped_at`, ô gửi `OCCUPIED`, báo đội bay. Đội bay **không tiếp nhận được** đơn chưa có mốc này (`DRONE_PARCEL_NOT_DROPPED`). Xác nhận là bấm tay trong app — chưa gắn với việc mở ô vật lý | `OS/service/DroneParcelService.java` (`confirmDrop`), `DroneOrderMaintenanceService.java` (`accept`), `M/…/drone_delivery_detail.dart` (`_DropBanner`), `maintenance_home_page.dart` |
| F1.03 | Pin `null` không còn qua kiểm tra trước bay (`DRONE_BATTERY_UNKNOWN`); khung giờ phóng theo `drone-flight-start-hour`/`end-hour` (mặc định 0–24 = không giới hạn); lưu pin lúc cất cánh, giờ tới tủ nhận, giờ và người xác nhận hàng vào ô | `DroneOrderMaintenanceService.java` (`requireFlightBattery`, `launch`), `DroneMissionProgressService.java`, `OS/model/DroneMission.java` |
| F1.02 · F1.09 | **Thêm hai hạn chờ** (cùng job quét 5 phút, đều huỷ + tạo yêu cầu hoàn tiền): đã trả tiền mà chưa bỏ kiện/chưa được tiếp nhận sau `drone-dispatch-timeout-minutes` (120, tính từ lúc bỏ kiện, chưa bỏ thì từ lúc trả tiền); nợ phụ thu cân lệch sau `drone-surcharge-timeout-minutes` (60, tính từ lúc nạp hàng, nhả drone `RESERVED → IDLE`) | `OS/service/DroneOrderTimeoutSweeper.java`, `DroneOrderExpiryService.java`, `DroneOrderMaintenanceService.java` (`cancelUnpaidSurcharge`) |
| F1.02 | **Khách tự từ chối phụ thu cân lệch** (`POST /api/orders/{id}/drone-delivery/decline-surcharge`): huỷ đơn, hoàn phần đã trả, đội bay trả kiện | `OrderController.java`, `drone_delivery_detail.dart` (`_UnpaidBanner`), `drone_delivery_tracking_page.dart` (`_declineSurcharge`) |
| F1.09 | **Kiện có đường về**: đơn đóng mà kiện đã vào hệ thống thì read model trả `parcelReturnPending` + `parcelHeldAt` (`SOURCE_BOX`/`FLIGHT_TEAM`). Kiện còn trong ô gửi thì **ô đó được giữ** (khách huỷ, đội bay huỷ trước khi nạp, tự huỷ) và job đối soát không nhả. Điều phối viên đã nhận nhiệm vụ (đơn chưa có nhiệm vụ thì điều phối viên bất kỳ) hoặc admin xác nhận đã trả (`POST …/drone-orders/{id}/parcel-return`) ⇒ nhả ô, báo người gửi. Đơn chờ trả kiện hiện trong hàng việc của đội bay và ở tab "Đang thực hiện" của admin | `OS/service/DroneParcelCustody.java`, `DroneParcelService.java` (`confirmReturn`), `OrderService.java` (`cancel`, `reconcileBoxStates`), `DroneDeliveryQueryService.java` (`operations`), `maintenance_home_page.dart` (`_parcelReturnCard`), `FE/pages/Admin/drone-orders/index.tsx` (`ParcelReturnPanel`) |
| F1.02 | Sự kiện thanh toán của đơn drone cộng **đúng số tiền của lần trả** vào `paidAmount`, chống cộng trùng theo `orders.last_payment_id`, và chỉ lật `PAID` khi đủ tổng — sự kiện lặp lại (VNPay return + IPN; từ backend #65 VNPay đã gỡ, chống cộng trùng vẫn áp cho callback lặp của cổng còn lại) sau khi cộng phụ thu không còn lật đơn về `PAID` | `OS/service/OrderPaymentEventListener.java` (`applyDronePayment`) |

Migration `V20` coi các đơn drone đã có nhiệm vụ trước bản này là đã bỏ kiện, để chúng không bị rule mới chặn giữa chừng. Backend và app phải ra cùng lúc: app cũ không gửi cam kết hàng cấm nên không tạo được đơn drone trên backend mới.

Còn hở sau rà soát này: xác nhận bỏ kiện và trả kiện là bấm tay, chưa gắn với mở ô vật lý (cần hợp đồng mở khoá của iot-service); hàng vào ô nhận vẫn do điều phối viên đã nhận nhiệm vụ xác nhận (người đứng ở tủ gửi), chưa có người hay cảm biến ở tủ nhận; phí chưa theo quãng đường; không tự phát hiện chuyến bay hỏng từ telemetry, chưa có `DELAYED`; thời tiết chỉ là công tắc tạm dừng tay; đơn quá hạn nhận (`EXPIRED`) vẫn ghi "đồ chuyển vào kho" mà không có ai chuyển hay luồng trả về người gửi; kích thước khoang và trần giá trị khai báo là số mặc định tạm, cần chỉnh theo drone thật.

### Cập nhật 2026-10-13 (chỉ thanh toán SePay) — PR mở, chưa merge

- **Backend [#65](https://github.com/LockR-Tech/backend/pull/65):** gỡ VNPay, MoMo khỏi payment-service; tạo thanh toán bằng hai phương thức này ⇒ 400 `PAYMENT_METHOD_UNSUPPORTED`, giao dịch cũ vẫn đọc được. `app.payment.enabled-methods` mặc định chỉ `SEPAY`, nên CASH tự xác nhận cho đơn drone (F1-G06) chỉ còn xảy ra nếu admin bật lại `CASH`.
- **Mobile [#62](https://github.com/LockR-Tech/mobile/pull/62):** thanh toán đơn drone đi thẳng SePay VietQR, không còn chọn ví / cổng; mã VietQR tạo đúng một lần mỗi đơn, chỉ "Thử lại" sau lỗi mới tạo mã mới. Người nhận khác người đặt chỉ **xem** đơn chưa trả — không có nút trả tiền, từ chối phụ thu hay xác nhận bỏ kiện (`M/features/drone_delivery/presentation/widgets/drone_delivery_detail.dart`); test này đang đỏ trên `main` và chặn deploy mobile web.
- Không đổi verdict / %.

### Cập nhật 2026-10-28 (điều khiển bay theo thời tiết) — nhánh `feat/f1-g13-dieu-khien-bay-thoi-tiet`, chưa PR

- **Ngưỡng thời tiết lên admin** (trước chỉ đặt được bằng biến môi trường, sửa phải khởi động lại): gió, gió giật, tầm nhìn, lượng mưa tối đa (mới, mặc định 0 = có mưa là không bay), chặn theo mã mưa/dông WMO 51–99, khoảng dự báo (15–120 phút), chặn hay không khi không có dữ liệu thời tiết. Đọc mỗi lần đánh giá; khoá cache có cả ngưỡng nên sửa là có hiệu lực ngay — `OS/settings/OrderSettingsCatalog.java` (nhóm "Thời tiết & điều kiện bay"), `OS/service/DroneWeatherService.java`.
- **Dừng bay từng trạm** (`drone_station_suspensions`, Flyway `V34`): lý do (thời tiết tại trạm, bảo trì bãi đáp, lệnh cấm bay khu vực, vận hành, khác), ghi chú, giờ tự mở lại. Trạm đang dừng: bộ chọn tủ gửi bỏ qua (đơn chưa gán drone đổi sang trạm khác), đặt đơn vào tủ nhận đang dừng bị từ chối `DRONE_STATION_SUSPENDED`, đội bay không nhận đơn / không phóng qua trạm đó, đơn đã trả tiền chưa cất cánh bị chặn lý do `STATION_SUSPENDED` (drone đang bay thì để bay xong) — `OS/service/DroneFlightControl.java`, `DroneSourceLockerSelector.java`, `DroneDeliveryBlockService.java`, `DroneOrderBookingService.java`, `DroneOrderMaintenanceService.java`.
- **Lịch sử chặn bay** (`drone_flight_blocks`): mỗi lần từ chối vì thời tiết xấu, thiếu dự báo, tạm dừng toàn hệ thống hoặc trạm dừng — bước (khách đặt đơn, đội bay nhận đơn, phóng, đơn đang chạy), đơn, tuyến, số đo thời tiết lúc chặn. Ghi bằng giao dịch riêng nên lời gọi đặt đơn / phóng rollback thì bản ghi vẫn còn. Nhật ký ai dừng / mở trạm ở `drone_station_suspension_logs`.
- **Trang admin "Thời tiết & bay"** (`/admin/flight-control`, có mục sidebar): công tắc tạm dừng toàn hệ thống (quy tắc `drone-flights-suspended`), số lần chặn 24 giờ theo nguyên nhân, thẻ từng trạm (thời tiết + dừng / mở lại), tab lịch sử chặn bay (lọc nguyên nhân, bước, mã đơn, ngày), nhật ký dừng trạm, ngưỡng & điều kiện bay — `FE/pages/Admin/flight-control/`, API `/api/admin/drone-flight-control/**` (gateway → order-service).
- **App:** danh sách thời tiết các tủ của KTV hiện trạm đang tạm dừng; câu "Dự báo N phút tới" theo khoảng admin cấu hình — `M/…/widgets/drone_weather_panel.dart`, `drone_booking.dart`.
- Cùng đợt, các ngưỡng drone khác lên admin: pin tối thiểu để ra lệnh quay về khi rơi kiện (`drone-return-min-battery-percent`, 15 %), không mời lại KTV vừa từ chối (`drone-pickup-reoffer-cooldown-minutes`, 10 phút), thời gian chờ / số lần gửi lại lệnh nắp và ngưỡng coi tủ mất kết nối (`app.drone.delivery.*`), bán kính đã rời / tiếp cận / đã tới (`app.drone.telemetry.*`).
- Không đổi verdict / %. Còn hở: chưa tự dừng trạm theo dự báo (admin vẫn bấm tay), lịch sử chặn chưa có báo cáo tổng hợp theo trạm / theo ngày, trang chưa có thời tiết dự báo theo giờ cho cả ngày.

### Cập nhật 2026-10-29 (sửa lỗi test tay trên điện thoại) — nhánh `fix/f1-g11-sua-loi-test-drone-2910`, chưa commit

Theo [handoff 2026-10-29](../handoff/2026-10-29-test-mobile-luong-drone-unhappy-case.md) § 8. Có unit test, chưa thử lại trên máy thật; verdict § 2 giữ nguyên.

- **Tủ nhận sát nơi gửi** (dưới `drone-min-route-meters`, 200 m) ⇒ từ chối đặt đơn `DRONE_ROUTE_TOO_SHORT`; trước đây hệ thống chọn tủ bay xa hơn để quãng bay "đủ" — `OS/service/DroneSourceLockerSelector.java`.
- **Mời KTV lấy hàng** chỉ trong `drone-max-pickup-meters`; không rơi về KTV vị trí cũ khi KTV vị trí mới vừa bỏ lời mời — `OS/service/DronePickupService.java` (`offerNext`). App: đăng xuất KTV tắt ca trên server — `M/features/locker_ops/presentation/utils/technician_session.dart`.
- **Huỷ trước khi bay vì "Drone lỗi"** ⇒ drone `RESERVED → FAULT` (kèm phiếu lỗi) thay vì về IDLE — `OS/service/DroneOrderMaintenanceService.java` (`cancel`).
- **Phiếu hoàn đơn huỷ** nêu lý do (giao không hoàn tất / huỷ trước khi bay + ghi chú) — `OS/service/DroneRefundService.java` (`refundReason`).
- **Sự cố rơi kiện** đóng được ở mọi phương án (chi trả xong qua callback payment, giao lại xong, thoả thuận riêng không còn việc), phương án có nội dung gửi khách (V35), lý do phiếu bồi thường đúng tỷ lệ, hoàn phí giao thật — [drone-parcel-drop-incidents](../01-overview/drone-parcel-drop-incidents.md).
- App: thẻ đầu trang theo ngữ cảnh (đơn đóng sau khi đã bay, chờ thanh toán, sẵn sàng phóng), bỏ "Đặt lại đơn" ở đơn drone, hỏi xác nhận "Tôi đã lấy đồ", KTV tự cập nhật GPS khi xác nhận lấy hàng bị chặn vì vị trí cũ.

### Cập nhật 2026-10-30 (sửa lỗi 4 báo cáo test lại rơi kiện + thư sự cố) — nhánh `fix/f1-g11-sua-loi-retest-roi-kien-2910`, chưa commit

Theo [handoff 2026-10-30](../handoff/2026-10-30-sua-loi-retest-roi-kien.md). Có test, chưa thử lại trên máy thật; verdict § 2 giữ nguyên.

- **Thư sự cố:** sau thư "đơn đang trên đường", mọi sự cố đều có thư — báo rơi kiện, đơn tạm dừng / tiếp tục khi drone đã phóng, gửi phương án, khách đồng ý (giao lại bằng đơn nào / không giao) — `OS/service/DroneDeliveryMailer.java`.
- **Giao lại:** bay từ tủ đang giữ kiện nếu là trạm bay; ô nhận chuyển hẳn sang đơn mới; đơn giao lại không bị job tự đóng — `OrderIncidentRedeliveryGateway`, `DroneDeliveryBlockService`, `DroneOrderTimeoutSweeper`.
- **Drone quay về:** báo rơi không còn đẩy cả sự cố sang "Cần can thiệp"; admin xác nhận drone đã về (`POST /api/admin/drone-incidents/{id}/return-flight/confirm`).
- **Điều phối:** lượt mời lấy hàng thứ 2 không ai nhận ⇒ báo admin; phiếu kiểm tra drone chỉ tự giao cho KTV đang trong ca.
- **API:** thiếu header bắt buộc trả 400 (`common-lib` `GlobalExceptionHandler`); `OrderResponse.dronePickupCode`; SĐT người gửi / người nhận phải là số Việt Nam.
- **Web admin / app:** gỡ dữ liệu mẫu (sự cố, phiếu bảo trì, nhiệm vụ thu hồi), modal phiếu bồi thường, khoá form phương án, nhãn tiếng Việt; app khách / KTV drone / KTV tủ sửa câu chữ và tự làm mới.

### Cập nhật 2026-11-05 (app KTV drone: tách "Vào ca" khỏi "nhận việc lấy hàng", xác nhận nạp không đổi nút) — mobile nhánh `fix/ktv-drone-tach-ca-lay-hang-va-lam-moi-nap`, chưa commit

Chỉ sửa app; backend vốn đã tách hai trạng thái (ca KTV ở locker-service `/api/maintenance/technician/presence`, nhận việc lấy hàng ở order-service `/api/drone-technician/drone-orders/presence`). Có widget test, chưa thử trên máy thật; verdict § 2 giữ nguyên.

- **"Vào ca" (thẻ ca đầu trang) chỉ là trạng thái online làm việc + toạ độ** — không còn bật nhận việc lấy hàng; cập nhật GPS của thẻ ca không còn gửi sang order-service. **"Hết ca"** vẫn tắt luôn nhận việc lấy hàng (offline thì không được mời) — `M/features/locker_ops/presentation/widgets/technician_shift_card.dart`. Phiếu kiểm tra drone vẫn tự giao theo ca KTV (locker-service), không theo công tắc lấy hàng.
- **Công tắc "nhận việc lấy hàng"** (tab Điều phối): chưa vào ca thì không bật được; chưa bật thì **không thấy lời mời** (chỉ báo "Có N lời mời đang chờ — bật nhận việc để xem và trả lời"), việc đã nhận / kiện đang cầm vẫn hiện để làm cho xong — `M/features/drone_delivery/presentation/widgets/drone_pickup_queue.dart`.
- **Xác nhận nạp xong vẫn hiện nút "Xác nhận nạp"** tới khi tải lại trang: (1) poll so danh sách đơn theo `id` (server trả `orderId`) + chặng/trạng thái/`updatedAt` của đơn, bỏ sót `missionStatus` (`AWAITING_LOADING → READY_TO_LAUNCH`) nên coi như không đổi; (2) tải lại sau thao tác dùng chung lượt tải đang chạy, có thể đã đọc dữ liệu từ trước khi server nhận xác nhận. Sửa: so cả nội dung đơn, lượt tải sau thao tác xếp thêm một lượt mới, bỏ phản hồi poll cũ về muộn, ghép phản hồi `loading-confirmation` vào thẻ ngay — `M/features/locker_ops/presentation/pages/maintenance_home_page.dart` (`droneDeliveriesEqual`, `_load`, `_mergeDeliveryResult`).

### Cập nhật 2026-11-10 (rà soát lại tài liệu theo code trên `main`)

Tài liệu trước đây vẫn tả luồng "người gửi tự bỏ kiện vào ô DRONE ở tủ gửi". Code hiện tại khác ở những điểm sau, đã viết lại vào § 1–3:

| Mục | Code hiện tại | Bằng chứng |
|---|---|---|
| F1.01 | **Lấy hàng tận nhà**: khách nhập điểm lấy hàng (toạ độ + địa chỉ + ghi chú) và liên hệ người gửi/nhận; hệ thống **tự chọn tủ gửi** gần điểm lấy hàng nhất; chỉ giữ ô ở tủ nhận; báo giá trước khi đặt (`/quote`) | `OS/service/DroneOrderBookingService.java`, `DroneSourceLockerSelector.java`, `M/…/pages/drone_booking_page.dart`, `pickup_location_picker_page.dart` |
| F1.03 · F1.04 | **Mời KTV lấy hàng** (`drone_pickups`, `drone_pickup_offers`, `drone_technician_presence`): rảnh + trong ca + GPS mới + trong bán kính, gần nhất trước; nhận/từ chối/hết hạn, thu hồi khi quá hạn lấy, báo admin sau 2 lượt, admin gán tay; mã lấy hàng 6 số + kiểm vị trí lúc xác nhận; KTV không lấy được kiện ⇒ "giao không hoàn tất". Chỉ KTV đã cầm kiện mới gán drone (`DRONE_PARCEL_NOT_PICKED_UP`, `DRONE_PICKUP_NOT_ASSIGNED_TO_USER`) | `OS/service/DronePickupService.java`, `DroneDispatchSweeper.java`, `DroneOrderMaintenanceService.java` (`assertParcelInHand`), `M/…/widgets/drone_pickup_queue.dart`, `drone_pickup_sheet.dart`, `FE/pages/Admin/drone-orders/HomePickupPanels.tsx` |
| F1.09 | Khách huỷ được tới **trước khi KTV cầm kiện** (`AWAITING_DISPATCH`, `PICKUP_ASSIGNED`); đơn **bị chặn** khi tài sản có sự cố / tạm dừng bay / quá hạn phóng, thử đổi tủ gửi khác trước khi chặn, quá `drone-blocked-timeout-minutes` (30 phút) thì đóng "giao không hoàn tất" | `OS/service/OrderService.java` (`assertDroneCancelable`), `DroneDeliveryBlockService.java`, `DroneDeliveryFailureService.java` |
| F1.06 | **Thả hàng bằng ArUco + nắp trượt + servo** (thay cho "điều phối viên xác nhận hàng vào ô"): phiên giao `drone_delivery_sessions`, nhật ký `drone_locker_comm_logs`, gửi lại lệnh nắp theo `commandId`, chế độ thử nắp theo ArUco | `OS/service/DroneLockerCommunicationService.java`, `OS/controller/DroneLockerCommLogController.java`, `iot/drone-iot/`, `FE/pages/Admin/drone-logs/` |
| F1.08 | Kiosk mở bằng PIN **tự hoàn tất** đơn drone; mở ô qua Bluetooth theo đơn | `backend/iot-service/…/IotService.java` (`completeIfPickup`), `M/features/locker_ops/presentation/widgets/order_ble_open.dart` |
| F1.05 | Live map bật cho khách; đường bay lưu lại (V39) và xem trên web admin; camera trực tiếp từ Pi drone | `M/core/config/feature_flags.dart`, `DroneFlightTrackRecorder.java`, `FE/pages/Admin/drone-orders/DroneFlightTrackPanel.tsx`, `LiveCameraPanel.tsx` |
| F1-G13 | Tự dừng / mở lại trạm theo dự báo mỗi 5 phút (`app.drone.weather.auto-station-pause`), admin tắt được kiểm tra thời tiết để thử nghiệm (`app.drone.weather.check-enabled`) | `OS/service/DroneStationWeatherGuard.java`, `DroneOrderMaintenanceService.java` (`assertWeatherSafe`) |

Đơn tạo trước khi có lấy hàng tận nhà (không có `pickupLatitude`) vẫn đi đường cũ: người gửi xác nhận đã bỏ kiện (`POST /api/orders/{id}/drone-delivery/drop-confirmation`) rồi đội bay tiếp nhận.

## 4. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F1-G01** | Bay thật: ~~cầu nối drone → backend, tự đẩy chặng, vị trí thật~~ **đã có trên `main`**. Còn: bật `APP_DRONE_TELEMETRY_ENABLED` + `DRONE_TELEMETRY_SECRET` trên VM, cài systemd trên Pi drone, bay thử ngoài trời có GPS với đơn thật; tự phát hiện chuyến bay hỏng từ telemetry | `OS/service/DroneTelemetry*.java`, `iot/drone-iot/` | F1.05 |
| **F1-G02** | **DONE · DEPLOYED 2026-09-20** — an toàn điều phối (khoá đơn, `RESERVED` nguyên tử, kiểm lại trước khi phóng) | `DroneOrderMaintenanceService.java`, `LS/service/LockerService.java` | F1.03 |
| **F1-G03** | Thả hàng vào ô: ~~xác nhận hạ cánh/gửi hàng, ô OCCUPIED, đơn STORING~~ **đã có** (ArUco → nắp → servo → đóng nắp). Còn: chạy trọn với drone bay thật; nối công tắc hành trình nắp ở tủ (`lidConfirmation = LIMIT_SWITCH`) rồi bật `LID_REQUIRE_LIMIT_SWITCH` | `DroneLockerCommunicationService.java`, `iot/drone-iot/lockr_drone/delivery.py`, `iot/services/locker_service.py` | F1.06 |
| **F1-G04** | Ngoại lệ: ~~nút huỷ cho khách, hoàn tiền, thất bại sau khi phóng, chặn khi tài sản lỗi~~ **đã có**. Còn: trạng thái `DELAYED`, abort/return-to-base tự động từ telemetry | `OS/service/`, `DroneDeliveryBlockService.java` | F1.09 |
| **F1-G05** | ~~Hoàn tất đơn khi mở bằng PIN ở kiosk; nút mở tủ trong app~~ **đã có** (kiosk tự hoàn tất, mở qua Bluetooth). Còn: thử Bluetooth với tủ thật | `IotService.java`, `order_ble_open.dart` | F1.08 |
| **F1-G06** | Toàn vẹn thanh toán: ~~`nextAction` khớp guard, nhắc trả tiền lúc đặt~~ đã có. Còn: chặn `CASH` cho đơn drone ở payment-service nếu admin bật lại; `checkout` kiểm trạng thái đơn | `payment-service/…/PaymentService.java` | F1.02 |
| **F1-G07** | ~~Dữ liệu theo dõi, toạ độ từng mốc, live map~~ **đã có** | `DroneDeliveryQueryService.java`, `OrderHistoryLocator.java` | F1.05 |
| **F1-G08** | ~~Bước nạp hàng bắt buộc trước launch~~ **đã có trên `main`** | `DroneOrderMaintenanceService.java` (`confirmLoading`) | F1.04 |
| **F1-G09** | ~~Người nhận khác người đặt; PIN qua app/email/SMS~~ **đã có** | `DroneMissionProgressService.java` (`sendPickupCodeQuietly`) | F1.07 |
| **F1-G10** | ~~Web admin hành trình drone + đổi trạng thái drone~~ **đã có** (`/admin/drone-orders`, `/admin/drones`) | `FE/pages/Admin/drone-orders/`, `FE/pages/Admin/drones/` | F1.03 |
| **F1-G11** | Sự cố rơi kiện: **đã có** ([đặc tả](../01-overview/drone-parcel-drop-incidents.md)). Dọn nợ còn lại: luồng cũ `DroneDeliveryRequest` ở locker-service (`LS/service/DroneDeliveryService.java`, `DroneDeliveryController.java`) | locker-service | — |
| **F1-G13** | Điều khiển bay theo thời tiết: **đã có** (ngưỡng trên admin, dừng trạm tay + tự động, lịch sử chặn bay). Còn: báo cáo chặn bay theo trạm / ngày | `DroneFlightControl.java`, `DroneStationWeatherGuard.java`, `FE/pages/Admin/flight-control/` | F1.01 · F1.03 |
| **F1-G14** | Phí theo quãng đường (hiện chỉ theo khối lượng); giới hạn tải theo model drone | `OS/settings/OrderRules.java` | F1.01 · F1.04 |
