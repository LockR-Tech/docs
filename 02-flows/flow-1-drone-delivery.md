# L1 — Giao hàng bằng drone → mã PIN → nhận hàng

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **60 %** (6 / 10) — chỉ trọn vẹn ở chế độ **DEMO** | 2026-09-13 · backend `705c556` · mobile `5890184` · iot `927b057` | [Vòng đời giao hàng](../diagrams/pdf/drone-mission.pdf) · [Trạng thái drone](../diagrams/pdf/drone-status.pdf) · [Trạng thái đơn](../diagrams/pdf/order-status.pdf) |

Viết tắt đường dẫn: `OS` = `backend/order-service/src/main/java/com/huynqb/laundrylocker/order`, `LS` = `backend/locker-service/…/locker`, `M` = `mobile/lib`, `FE` = `frontend/fe/src`.

## 1. Mục tiêu nghiệp vụ

Khách đặt giao hàng tới một tủ có bãi đáp → thanh toán → nhân viên DRONE_TECHNICIAN điều phối drone, nạp hàng, phóng → khách theo dõi hành trình → drone hạ cánh, gửi hàng vào ô DRONE → hệ thống cấp PIN/QR và báo người nhận → người nhận nhập PIN ở tủ, ô mở, đơn hoàn tất. Có nhánh ngoại lệ: huỷ trước khi bay, drone lỗi/quay về, quá hạn không lấy.

## 2. Checklist

| # | Hạng mục | Bằng chứng chính | Verdict | Còn thiếu |
|---|---|---|---|---|
| F1.01 | Khách tạo đơn drone | `POST /api/orders/drone-deliveries` `OS/controller/OrderController.java:41` → `OS/service/OrderService.java:215-253` giữ ô DRONE; app `M/features/drone_delivery/presentation/widgets/drone_booking_sheet.dart:84-101` | **DONE** | Hàng chỉ là mô tả text; cân nặng cứng 1200 g (`:98`); người nhận luôn là người đặt (`OrderService.java:232`) |
| F1.02 | Bắt buộc thanh toán trước khi điều phối | Accept chặn nếu chưa PAID `OS/service/DroneOrderMaintenanceService.java:50-52`; PAID từ `OrderPaymentEventListener.java:44-53` | PARTIAL | CASH tự xác nhận (`payment-service/…/PaymentService.java:152`); API báo "chưa cần trả" lệch guard (`OrderService.java:1774`); huỷ không hoàn tiền |
| F1.03 | Điều phối drone, tạo mission | accept giữ drone `IDLE → RESERVED` bằng compare-and-set có khóa DB `DroneOrderMaintenanceService.java:57-96`, `LockerService.java:1113-1125`; launch kiểm tra lại drone/pin/pad rồi `RESERVED → IN_FLIGHT` `DroneOrderMaintenanceService.java:100-129` | **DONE** (thủ công) | Không tự động gán; bước nạp hàng vẫn thuộc F1.04 |
| F1.04 | Nạp hàng tại điểm đi | Chỉ lưu `sourceLockerId` (`DroneOrderMaintenanceService.java:73`) | MISSING | Không có bước nạp hàng, ô nguồn, người nạp |
| F1.05 | Theo dõi hành trình gần thời gian thực | Chặng do `OS/service/DroneDeliverySimulator.java:37-99` (DEMO, 3 s/chặng); app poll 3 s `M/…/drone_delivery_providers.dart:35-48`; live map tắt `M/core/config/feature_flags.dart:47` | PARTIAL | Không telemetry thật; API trả missionId/droneCode/eta = null (`OrderService.java:1722`); `DroneDeliveryQueryService` không được gọi |
| F1.06 | Hạ cánh + gửi hàng vào ô DRONE | Pad chỉ là cờ preflight (`DroneOrderMaintenanceService.java:225-235`); "gửi hàng" là simulator đặt DEPOSITED (`DroneDeliverySimulator.java:70-76`) | PARTIAL | Chỉ DEMO; không xác nhận hạ cánh; ô vẫn RESERVED, không OCCUPIED |
| F1.07 | Cấp PIN/QR + báo người nhận | PIN 6 số hạn 24h chỉ trong simulator (`DroneDeliverySimulator.java:74-76`); QR `OrderService.java:1683`; app hiện PIN khi PAID `M/…/my_locker_orders_page.dart:1424` | PARTIAL | PIN chỉ có ở DEMO; push không chứa PIN; không SMS; FCM thực tế không gửi |
| F1.08 | Nhập PIN mở ô → nhả ô → hoàn tất | `complete` `OrderService.java:449-463`; kiosk verify + unlock `iot/ui/src/screens/KioskScreen.jsx:1141-1144,1271` | PARTIAL | Mở ô ở kiosk **không** hoàn tất đơn (`iot/ui/src/api.js:71` `pickupOrder` không dùng); app không có nút mở tủ |
| F1.09 | Ngoại lệ: huỷ, drone lỗi/quay về, quá hạn | Khách huỷ khi AWAITING_DISPATCH `OrderService.java:1620`; bảo trì huỷ `DroneOrderMaintenanceService.java:115-184`; quá hạn → EXPIRED `OrderService.java:1131-1175` | PARTIAL | Không abort/return-to-base, FAILED/DELAYED; FAULT giữa chuyến không đụng mission; app không có nút huỷ đơn drone; không hoàn tiền |
| F1.10 | Tủ xác thực PIN và mở khoá vật lý | `backend/iot-service/…/IotService.java:61-83,125-194` → MQTT → Pi `iot/services/locker_service.py:160-191` → RS485 | **DONE** | Pi thật không hiểu payload backend (thiếu `slotIndex`) — chỉ `simulate_demo_cabinet.py` chạy; xem F2-G09 |

**Điểm:** DONE 3 × 1 + PARTIAL 6 × 0,5 + MISSING 1 × 0 = 6 / 10 = **60 %**. Ở STANDARD các mục F1.05–F1.08 không đạt được ⇒ tiến độ thực tế thấp hơn.

## 3. Luồng đang chạy hôm nay

1. **Khách** (app → bản đồ cửa hàng → ô DRONE) `POST /api/orders/drone-deliveries` ⇒ order & stage `AWAITING_DISPATCH`, `UNPAID`, ô `RESERVED` 24h, `fulfillmentMode = DEMO` mặc định; push tới nhóm DRONE_TECHNICIAN.
2. **Khách** thanh toán `POST /api/payments/checkout` ⇒ sự kiện `payment.completed` ⇒ `PAID`.
3. **DRONE_TECHNICIAN** `GET /api/drone-technician/drone-orders` → `POST …/{id}/accept {droneUnitId}` ⇒ khóa bản ghi drone và đổi nguyên tử `IDLE → RESERVED`, mission `READY_TO_LAUNCH`, stage `ACCEPTED`.
4. **DRONE_TECHNICIAN** `POST …/{id}/launch` ⇒ kiểm tra lại drone còn `RESERVED`, active, đủ pin và bãi đáp còn OK; đổi nguyên tử `RESERVED → IN_FLIGHT`, stage `LAUNCHING`.
5. **Bộ giả lập** (chỉ DEMO) mỗi 3 giây: `DEPARTED → EN_ROUTE → APPROACHING → ARRIVED` ⇒ mission `DEPOSITED`, order `STORING`, stage `READY_FOR_PICKUP`, cấp PIN, drone `IN_FLIGHT → IDLE` nếu trạng thái chưa bị đổi sang FAULT. **Ở STANDARD không có gì xảy ra sau bước 4.**
6. **Khách** xem timeline (poll 3 s), thấy PIN/QR khi đã PAID.
7. **Khách** nhập PIN ở kiosk ⇒ ô mở **nhưng đơn vẫn STORING**; hoặc bấm "hoàn tất" trong app ⇒ `COMPLETED`, nhả ô.
8. Không ai lấy ⇒ cron mỗi giờ: quá hạn + 24h ⇒ `EXPIRED`, nhả ô.

## 4. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F1-G01** | Tiến trình bay **thật** cho STANDARD: endpoint/consumer sự kiện mission (departed, position, arrived, deposited, failed) + cầu nối drone → backend | `OS/service/` (handler mới), `backend/iot-service` (ingest MAVLink/MQTT) | F1.05–F1.07 |
| **F1-G02** | **ĐÃ CODE, CHỜ MERGE/DEPLOY:** accept chặn mission trùng và giữ drone `RESERVED` nguyên tử; launch tái kiểm tra drone/pin/pad; hủy nhả reservation; simulator chỉ nhả `IN_FLIGHT → IDLE`, không ghi đè FAULT; trạng thái vận hành không cho sửa tay | `DroneOrderMaintenanceService.java:57-129,155`, `DroneDeliverySimulator.java:96`, `LS/service/LockerService.java:1089-1125` | F1.03 |
| **F1-G03** | Xác nhận hạ cánh/gửi hàng: ô → OCCUPIED, order → STORING **qua `transition()`** (có lịch sử + event) | `OrderService.java`, `iot/services/locker_service.py`, `backend/iot-service` | F1.06 |
| **F1-G04** | Nhánh ngoại lệ: abort/return-to-base, FAILED/DELAYED, phản ứng khi drone FAULT giữa chuyến, nút huỷ cho khách, hoàn tiền, không nhả ô của đơn còn chờ | `OS/service/`, `OrderService.java:1198`, `payment-service`, `M/…/my_locker_orders_page.dart:1311` | F1.09 |
| **F1-G05** | = **F2-G01**: hoàn tất đơn khi mở bằng PIN ở kiosk; nút mở tủ trong app | `IotService.java`, `KioskScreen.jsx`, `my_locker_orders_page.dart` | F1.08 |
| **F1-G06** | Toàn vẹn thanh toán: bỏ CASH tự xác nhận cho đơn drone; `paymentRequired`/`nextAction` khớp guard; nhắc trả tiền lúc đặt | `PaymentService.java:152`, `OrderService.java:1740-1780`, `drone_booking_sheet.dart` | F1.02 |
| **F1-G07** | Dữ liệu theo dõi: trả `DroneDeliveryQueryService` ở `/drone-delivery`, ghi `droneCode`, phát vị trí lên STOMP, bật live map | `OrderController.java:152`, `DroneOrderMaintenanceService.java:70-79`, `feature_flags.dart:47` | F1.05 |
| **F1-G08** | Bước nạp hàng tại điểm đi (ô nguồn, người nạp, xác nhận) trước launch | `OS/model/DroneMission.java`, endpoint mới, `maintenance_home_page.dart` | F1.04 |
| **F1-G09** | Người nhận khác người đặt; PIN trong push hoặc SMS | `CreateDroneDeliveryOrderRequest.java`, luồng thay simulator | F1.07 |
| **F1-G10** | Web admin: màn hình đơn drone + mission; sửa đổi trạng thái drone (claim hoặc route admin) | `FE/pages/Admin/drones/`, `FE/types/admin/enums.ts`, `LS/controller/LockerController.java` | F1.03 |
| **F1-G11** | Xoá luồng cũ `DroneDeliveryRequest` và mock `DroneDeliveryStore` / `drone_tracking_page.dart` | `LS/service/DroneDeliveryService.java`, `DroneDeliveryController.java`, `M/features/drone_delivery/data/` | — (dọn nợ) |
