# L2 — Thuê tủ gửi hàng → chuyển mã cho người nhận → người nhận lấy

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **65 %** (6,5 / 10) | 2026-09-13 · backend `705c556` · mobile `5890184` · frontend `e1b9a73` · iot `927b057` | [Trạng thái đơn](../diagrams/pdf/order-status.pdf) · [Trạng thái ô tủ](../diagrams/pdf/locker-cell-status.pdf) |

Viết tắt: `OS` = `backend/order-service/src/main/java/com/huynqb/laundrylocker/order`, `LS` = `backend/locker-service/…/locker`, `M` = `mobile/lib`.

## 1. Mục tiêu nghiệp vụ

**Người gửi** chọn tủ và ô trống → giữ ô → thanh toán → mở ô, bỏ hàng → nhập thông tin người nhận. Hệ thống **gửi mã nhận hàng kèm thông tin đơn tới người nhận** (kể cả người chưa có tài khoản). **Người nhận** tới tủ, nhập mã → ô mở → đơn hoàn tất, ô được giải phóng. Có tính thời hạn giữ hàng, phí quá hạn và gia hạn.

Trong code có hai kiểu đơn phục vụ luồng này: **SEND** (gửi cho người khác — kiểu chính) và **RENTAL** (thuê ô theo giờ, có thể uỷ quyền cho người khác lấy).

## 2. Checklist

| # | Hạng mục | Bằng chứng chính | Verdict | Còn thiếu |
|---|---|---|---|---|
| F2.01 | Xem tủ, ô trống, kích cỡ thật | `GET /api/lockers/{id}/layout` `LS/service/LockerService.java:290-301`; app `M/features/locker_ops/presentation/pages/rent_locker_page.dart:114-135`, `M/features/stores/presentation/pages/store_lockers_page.dart:295` | **DONE** | SEND không cho chọn ô cụ thể; kích thước ô hardcode trong app; trang Tủ truyền locker id như store id (`locker_page.dart:81`) |
| F2.02 | Giữ ô, TTL, tự nhả khi hết hạn | `reserveBox` +24h `LockerService.java:135-150`; cron huỷ đơn `OS/service/OrderScheduler.java:37` → `OrderService.java:1097-1118`; quét TTL `LockerService.java:174-183` | **DONE** | Giữ 24h quá dài; huỷ tự động đơn đã PAID không hoàn tiền |
| F2.03 | Thanh toán ví / VNPay / MoMo / tiền mặt | `POST /api/payments/checkout` `payment-service/…/PaymentService.java:110-165`; app có đủ 4 phương thức `my_locker_orders_page.dart:1479-1497` | PARTIAL | Chỉ ví là thật; CASH khách tự xác nhận; VNPay sandbox, IPN không kiểm số tiền; MoMo cần khoá; trang Gửi/Thuê hardcode "mock CASH" (`send_parcel_page.dart:376`, `rent_locker_page.dart:175`) |
| F2.04 | Bỏ hàng: mở ô → ô OCCUPIED | Kiosk DROP_OFF `iot/ui/src/screens/KioskScreen.jsx:921-995` → `PUT /api/orders/{id}/confirm` `OrderService.java:151-174` → `occupyBox` `LockerService.java:186-197` | PARTIAL | App: nút mở tủ không được nối (`my_locker_orders_page.dart:578` vs `:1247-1323`); **bug** trang Gửi hàng xác nhận bằng **id payment** thay vì id đơn (`send_parcel_page.dart:377-382`); RENTAL confirm không kiểm tra thanh toán |
| F2.05 | Thông tin người nhận gắn với đơn | SEND nhận `receiverPhone`, `receiverName` `OS/dto/SendOrderRequest.java`; app `send_parcel_page.dart:112-113` | PARTIAL | Không có email; RENTAL không có người nhận lúc tạo; `OrderResponse` không trả thông tin người nhận |
| F2.06 | Gửi mã + thông tin đơn cho người nhận | `notifyParcelReadyForReceiver` `OrderService.java:377-399` — chỉ push in-app nếu SĐT trùng tài khoản | PARTIAL | **Không SMS/email** — người chưa có tài khoản không nhận được gì (code chỉ ghi log); `delegate` chỉ báo chủ đơn; FCM không gửi thật |
| F2.07 | Người nhận **không cần tài khoản** vẫn lấy được | `/api/iot/unlock-with-code` công khai `api-gateway/…/JwtGatewayFilter.java:230-234`; tìm đơn theo PIN/QR `IotService.java:125-166`; khoá sau 5 lần sai `:196-205` | **DONE** | Mở được cửa nhưng không hoàn tất đơn (F2.08) |
| F2.08 | Nhập mã → mở ô → đơn hoàn tất, nhả ô | `complete` `OrderService.java:449-463` (cần JWT chủ đơn/người nhận) | PARTIAL | **Nhận bằng mã ở kiosk chỉ mở cửa**, đơn vẫn STORING, PIN vẫn dùng lại được, sau đó EXPIRED kèm thông báo sai; người nhận có tài khoản không thấy đơn gửi tới mình (`OrderService.java:752`) |
| F2.09 | Thời hạn: quá hạn, phí, gia hạn | Nhắc mỗi 10' `OrderScheduler.java:15`; phí `OrderService.java:1556-1565`; EXPIRED `:1131-1175`; gia hạn `:292-321` | PARTIAL | Phí quá hạn cộng **sau** khi kiểm tra PAID ⇒ không bao giờ thu; web thiếu EXPIRED |
| F2.10 | Tủ vật lý xác thực mã, mở khoá thật | MQTT `cabinet/{lockerId}/command/open` chờ ack 20 s `iot-service/…/LockerMqttService.java:176-205`; Pi `iot/services/locker_service.py:94,162,213` | PARTIAL | Broker công khai không auth (SEC-04); Pi thật không hiểu payload (thiếu `slotIndex`, topic dùng tên tủ); cảm biến cửa không điều khiển trạng thái đơn/ô |

**Điểm:** DONE 3 × 1 + PARTIAL 7 × 0,5 = 6,5 / 10 = **65 %**.

## 3. Luồng đang chạy hôm nay (SEND)

1. **Người gửi** (app) `GET /api/lockers` → `GET /api/lockers/{id}/layout`.
2. `POST /api/orders/send {lockerId, receiverPhone, receiverName, size}` ⇒ server tự chọn ô STANDARD ⇒ đơn `INITIALIZED / UNPAID`, ô `RESERVED` (+24h), phát PIN gửi hàng cho người gửi.
3. Thanh toán (trang Gửi hàng hardcode CASH ⇒ hoàn tất ngay) ⇒ `PAID`. Không bỏ hàng trong 24h ⇒ `CANCELED`, nhả ô, **không hoàn tiền**.
4. Mở ô: kiosk DROP_OFF (`POST /api/iot/unlock`) — app chưa có nút.
5. "Tôi đã bỏ hàng" `PUT /api/orders/{id}/confirm` ⇒ `STORING`, ô `OCCUPIED`, đổi sang PIN nhận hàng, hạn 48h. _(Trên app, bug id payment có thể làm bước này thất bại.)_
6. SĐT người nhận trùng tài khoản ⇒ push in-app có PIN. Không trùng ⇒ **không gửi gì**, người gửi tự copy PIN chuyển cho người nhận.
7. **Người nhận** nhập PIN/QR ở kiosk `POST /api/iot/unlock-with-code` ⇒ cửa mở, **đơn vẫn `STORING`**.
8. Đơn chỉ `COMPLETED` khi chủ đơn/người nhận có tài khoản bấm hoàn tất trong app, hoặc staff checkout.
9. Không ai hoàn tất ⇒ nhắc, cộng phí (không thu được) ⇒ quá hạn + 24h ⇒ `EXPIRED`, nhả ô.

**RENTAL:** `POST /api/orders/rental {cellType, hours}` → confirm (không kiểm tra thanh toán) → `delegate {phone}` cấp PIN mới cho người khác (chỉ báo chủ đơn) → `extend-rental` → `pickup-storage` ⇒ `COMPLETED`.

## 4. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F2-G01** | **Hoàn tất đơn phía server khi mở bằng mã ở kiosk** (hoặc khi cửa đóng sau lấy hàng): tính phí quá hạn, bắt thanh toán nếu cần, nhả ô, thu hồi PIN | `backend/iot-service/…/IotService.java:125-166` → endpoint nội bộ mới ở `OrderService`; `iot/ui/src/screens/KioskScreen.jsx:1271` | F2.08 |
| **F2-G02** | Khoá API đổi trạng thái đơn/thanh toán + kiểm tra chủ sở hữu — xem **SEC-03, SEC-05** | `OrderController.java:75,115,147,212`, `PaymentController.java:39-53`, `JwtGatewayFilter.java:148-165` | F2.03, F2.08 |
| **F2-G03** | **Kênh gửi mã cho người nhận**: SMS (+ email) trong notification-service; thêm `receiverEmail`; trả thông tin người nhận trong `OrderResponse` | `OrderService.java:377-399,490-523`, `OS/dto/SendOrderRequest.java`, `notification-service` | F2.05, F2.06 |
| **F2-G04** | Thanh toán thật: CASH chờ nhân viên/kiosk xác nhận; VNPay IPN kiểm số tiền + idempotent; bỏ mock CASH ở app; hoàn tiền khi huỷ đơn đã PAID (REFUNDED) | `PaymentService.java:152,181-200`, `PaymentController.java:75-79`, `send_parcel_page.dart:376`, `rent_locker_page.dart:175`, `OrderService.java:466,1097` | F2.03 |
| **F2-G05** | Thu phí quá hạn: cộng phí trước khi kiểm tra PAID, chuyển UNPAID, chặn lấy hàng tới khi trả | `OrderService.java:449-463,527-553` | F2.09 |
| **F2-G06** | Người nhận có tài khoản thấy đơn gửi tới mình: `findByReceiverId`, tab "Hàng chờ nhận" | `LockerOrderRepository.java`, `OrderService.java:752`, `my_locker_orders_page.dart` | F2.08 |
| **F2-G07** | RENTAL → người nhận: cho nhập `receiverPhone` khi tạo; áp guard thanh toán khi confirm | `OS/dto/RentalOrderRequest.java`, `OrderService.java:156,192-212` | F2.04, F2.05 |
| **F2-G08** | Dọn state machine: enum Java + CHECK constraint; xoá RETURNED/READY/WAITING/RESERVED; simulator đi qua `transition()`; đồng bộ enum web | `LockerOrder.java:66` + Flyway, `frontend/fe/src/schemas/admin.schemas.ts:54-64`, `OrderStatusUpdateModal.tsx` | — (nợ kỹ thuật) |
| **F2-G09** | IoT production: broker riêng có auth/TLS (SEC-04); thống nhất payload lệnh mở (`slotIndex`, topic theo lockerId) giữa backend và Pi; sự kiện cửa điều khiển vòng đời; kiosk DROP_OFF tự confirm | `LockerMqttService.java:30,183`, `iot/services/locker_service.py:170-181`, `IotService.java:246-260` | F2.10 |
| **F2-G10** | PIN duy nhất trong các đơn đang hoạt động (partial unique index + sinh lại); rút TTL giữ ô | `OrderService.java:1839` + migration, `app.locker.reserved-ttl-hours` | F2.02, F2.08 |
| **F2-G11** | **Bug mobile**: (a) `send_parcel_page.dart:377-382` ghi đè `_order` bằng payment rồi confirm sai id; (b) nối nút mở tủ `onOpenLocker` vào `_DetailSheet`; (c) trang Tủ/Home truyền locker id làm `Store.id` | `M/features/locker_ops/…`, `M/features/locker/presentation/pages/locker_page.dart:81`, `M/features/home/presentation/pages/home_page.dart:514` | F2.01, F2.04 |
