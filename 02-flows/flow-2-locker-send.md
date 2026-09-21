# L2 — Thuê tủ gửi hàng → chuyển mã cho người nhận → người nhận lấy

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **70 %** (7 / 10) | 2026-09-21 · backend [#20](https://github.com/LockR-Tech/backend/pull/20) + [#21](https://github.com/LockR-Tech/backend/pull/21) · mobile [#19](https://github.com/LockR-Tech/mobile/pull/19) · iot [#5](https://github.com/LockR-Tech/iot/pull/5) (bằng chứng theo các nhánh này, chờ merge) | [Trạng thái đơn](../diagrams/pdf/order-status.pdf) · [Trạng thái ô tủ](../diagrams/pdf/locker-cell-status.pdf) |

Viết tắt: `OS` = `backend/order-service/src/main/java/com/huynqb/laundrylocker/order`, `IS` = `backend/iot-service/…/iot`, `LS` = `backend/locker-service/…/locker`, `M` = `mobile/lib`, `K` = `iot/ui/src/screens/KioskScreen.jsx`.

## 1. Mục tiêu nghiệp vụ

**Người gửi** chọn tủ và ô trống → giữ ô → thanh toán → mở ô, bỏ hàng → nhập thông tin người nhận. Hệ thống **gửi mã nhận hàng kèm thông tin đơn tới người nhận** (kể cả người chưa có tài khoản). **Người nhận** tới tủ, nhập mã → ô mở → đơn hoàn tất, ô được giải phóng. Có tính thời hạn giữ hàng, phí quá hạn và gia hạn.

Trong code có hai kiểu đơn phục vụ luồng này: **SEND** (gửi cho người khác — kiểu chính) và **RENTAL** (thuê ô theo giờ, có thể uỷ quyền cho người khác lấy).

## 2. Checklist

| # | Hạng mục | Bằng chứng chính | Verdict | Còn thiếu |
|---|---|---|---|---|
| F2.01 | Xem tủ, ô trống, kích cỡ thật | `GET /api/lockers/{id}/layout` `LS/service/LockerService.java:290-301`; app `M/features/locker_ops/presentation/pages/rent_locker_page.dart:114-135`, `M/features/stores/presentation/pages/store_lockers_page.dart:295` | **DONE** | SEND không cho chọn ô cụ thể; kích thước ô hardcode trong app; trang Tủ truyền locker id như store id (`locker_page.dart:81`) |
| F2.02 | Giữ ô, TTL, tự nhả khi hết hạn | `reserveBox` +24h `LockerService.java:135-150`; cron huỷ đơn `OS/service/OrderScheduler.java:37` → `OrderService.java:1097-1118`; quét TTL `LockerService.java:174-183` | **DONE** | Giữ 24h quá dài; huỷ tự động đơn đã PAID không hoàn tiền |
| F2.03 | Thanh toán ví / VNPay / MoMo / tiền mặt | `POST /api/payments/checkout` `payment-service/…/PaymentService.java:110-165`; app chỉ còn Ví/VNPay/MoMo và **chờ đơn PAID** trước khi cho mở ô `M/features/locker_ops/presentation/widgets/order_payment_sheet.dart:24,85`, poll `GET /api/orders/{id}/status` `M/features/locker_ops/data/locker_ops_service.dart:204`; `isPaid` = PAID hoặc đơn 0đ `OS/service/OrderService.java:751-766`; kiosk poll PAID trước khi mở `K:990-1016` | PARTIAL | VNPay sandbox, IPN không kiểm số tiền; MoMo cần khoá; `PATCH /api/payments/{id}/status` vẫn mở cho mọi JWT (SEC-03) nên bỏ CASH ở app mới là UX, chưa phải ranh giới bảo mật; kiosk giữ CASH demo |
| F2.04 | Bỏ hàng: mở ô → ô OCCUPIED | Mở ô đơn INITIALIZED ghi `drop_opened_at` `IS/service/IotService.java:276` → `POST /internal/orders/{id}/drop-opened` `OS/controller/OrderController.java:82`, `OS/service/OrderService.java:155`; confirm SEND bắt buộc đã mở ô (`ORDER_DROP_NOT_OPENED`) và mọi loại đơn đều kiểm thanh toán trước (`OrderService.java:121-135`); app "Mở ô để bỏ hàng" → "Tôi đã bỏ hàng vào ô" `M/…/pages/send_parcel_page.dart:165,192,605-613`; kiosk "Đã bỏ hàng xong" `POST /api/iot/confirm-drop-with-code` `IS/controller/IotController.java:91`, `IotService.java:201-217`, `K:1172-1193` | **DONE** | — |
| F2.05 | Thông tin người nhận gắn với đơn | SEND nhận `receiverPhone`, `receiverName` `OS/dto/SendOrderRequest.java`; app `send_parcel_page.dart:112-113` | PARTIAL | Không có email; RENTAL không có người nhận lúc tạo; `OrderResponse` không trả thông tin người nhận |
| F2.06 | Gửi mã + thông tin đơn cho người nhận | `notifyParcelReadyForReceiver` `OrderService.java` gọi cả ba kênh; SMS/email ở `notification-service/…/channel/`, hợp đồng [receiver-pickup-code.md](../01-overview/receiver-pickup-code.md); app nhập email người nhận `send_parcel_page.dart` | PARTIAL | Có đủ SMS + email, nhưng **SMS chưa gửi được cho tới khi nạp khoá Twilio trên VM** (trial còn chỉ gửi tới số đã xác minh); `delegate` vẫn chỉ báo chủ đơn; `OrderResponse` chưa trả thông tin người nhận; FCM không gửi thật |
| F2.07 | Người nhận **không cần tài khoản** vẫn lấy được | `/api/iot/unlock-with-code` công khai `api-gateway/…/JwtGatewayFilter.java:230-234`; tìm đơn theo PIN/QR `IotService.java:125-166`; khoá sau 5 lần sai `:196-205` | **DONE** | Mở được cửa nhưng không hoàn tất đơn (F2.08) |
| F2.08 | Nhập mã → mở ô → đơn hoàn tất, nhả ô | Mở bằng mã nhận ở kiosk hoàn tất đơn SEND `completeIfPickup` `IS/service/IotService.java:282,376`; **đơn RENTAL không bị kết thúc khi mở lại** (vá lỗi production, backend #20); mã của đơn chưa trả tiền / thuê quá hạn bị từ chối mà không tính nhập sai `IotService.java:184-187` theo `OS/service/OrderAccessPolicy.java:21-35`; kết thúc thuê bằng mã `POST /api/iot/end-rental-with-code` `IotService.java:224-240`, `K:647` | PARTIAL | Người nhận có tài khoản không thấy đơn gửi tới mình (F2-G06) |
| F2.09 | Thời hạn: quá hạn, phí, gia hạn | Nhắc mỗi 10' `OrderScheduler.java:15`; phí `OrderService.java:1556-1565`; EXPIRED `:1131-1175`; gia hạn `OrderService.java:284`, app trả tiền phần gia hạn `M/…/pages/rent_locker_page.dart:216`; thuê quá hạn thì mã bị từ chối (`RENTAL_EXPIRED`) tới khi gia hạn | PARTIAL | Phí quá hạn cộng **sau** khi kiểm tra PAID ⇒ không bao giờ thu (F2-G05); chặn mở ô khi phần gia hạn chưa trả nằm sau cài đặt `app.order.block-unpaid-rental-access` (mặc định tắt) |
| F2.10 | Tủ vật lý xác thực mã, mở khoá thật | MQTT `cabinet/{lockerId}/command/open` chờ ack 20 s `iot-service/…/LockerMqttService.java:176-205`; Pi `iot/services/locker_service.py:94,162,213` | PARTIAL | Broker công khai không auth (SEC-04); Pi thật không hiểu payload (thiếu `slotIndex`, topic dùng tên tủ); cảm biến cửa không điều khiển trạng thái đơn/ô |

**Điểm:** DONE 4 × 1 + PARTIAL 6 × 0,5 = 7 / 10 = **70 %**.

## 3. Luồng chạy sau backend #20/#21, mobile #19, iot #5

**SEND**

1. **Người gửi** (app) `GET /api/lockers` → `GET /api/lockers/{id}/layout`.
2. `POST /api/orders/send {lockerId, receiverPhone, receiverName, receiverEmail?, size}` ⇒ server tự chọn ô STANDARD ⇒ đơn `INITIALIZED / UNPAID`, ô `RESERVED` (+24h), phát PIN gửi hàng cho người gửi.
3. Thanh toán Ví/VNPay/MoMo; app chờ `PAID` (sự kiện `payment.completed` cập nhật bất đồng bộ). Mã gửi của đơn chưa trả tiền bị kiosk từ chối (`ORDER_UNPAID`), không khoá ô. Không bỏ hàng trong 24h ⇒ `CANCELED`, nhả ô, **không hoàn tiền**.
4. Mở ô: nút "Mở ô để bỏ hàng" trong app, hoặc nhập mã gửi ở kiosk. Lần mở thành công đầu tiên ghi `drop_opened_at`.
5. Xác nhận bỏ hàng: "Tôi đã bỏ hàng vào ô" (app) hoặc "Đã bỏ hàng xong" (kiosk, chỉ trong `app.iot.kiosk-confirm-window-minutes` phút sau lần mở) ⇒ `STORING`, ô `OCCUPIED`, đổi sang PIN nhận hàng, hạn 48h. Chưa mở ô thì confirm bị từ chối `ORDER_DROP_NOT_OPENED` (tắt được bằng `app.order.send-confirm-requires-open`).
6. Gửi mã cho người nhận qua **cả ba** đường: push in-app nếu SĐT trùng tài khoản, SMS tới SĐT đã nhập, và email nếu người gửi có nhập. Xem [receiver-pickup-code.md](../01-overview/receiver-pickup-code.md).
7. **Người nhận** nhập PIN/QR ở kiosk `POST /api/iot/unlock-with-code` ⇒ cửa mở ⇒ đơn `COMPLETED`, nhả ô.
8. Không ai lấy ⇒ nhắc, cộng phí (chưa thu được) ⇒ quá hạn + 24h ⇒ `EXPIRED`, nhả ô.

**RENTAL**

1. `POST /api/orders/rental {lockerId, cellType, hours}` → thanh toán (bắt buộc trước khi confirm) → mở ô → confirm ⇒ `STORING`, hạn thuê tính từ lúc confirm.
2. Trong hạn, mở lại ô bằng cùng mã bao nhiêu lần cũng được; kiosk hỏi "Đóng cửa, tiếp tục thuê" hay "Lấy hết đồ & kết thúc thuê". Mở lại **không** kết thúc lượt thuê.
3. Kết thúc: `POST /api/iot/end-rental-with-code` (kiosk) hoặc `pickup-storage` (app) ⇒ `COMPLETED`.
4. Quá hạn ⇒ mã bị từ chối `RENTAL_EXPIRED` ⇒ gia hạn trong app (`extend-rental`, thanh toán phần gia hạn) để mở lại.

## 4. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F2-G01** | ~~Hoàn tất đơn phía server khi mở bằng mã ở kiosk~~ — **đã làm** (`IS/service/IotService.java:376`), kèm vá đơn thuê bị kết thúc khi mở lại (backend #20) và kết thúc thuê bằng mã (backend #21, iot #5). Còn lại: tính phí quá hạn khi lấy hàng (F2-G05) | `IS/service/IotService.java` | F2.08 |
| **F2-G02** | Khoá API đổi trạng thái đơn/thanh toán + kiểm tra chủ sở hữu — xem **SEC-03, SEC-05** | `OrderController.java:75,115,147,212`, `PaymentController.java:39-53`, `JwtGatewayFilter.java:148-165` | F2.03, F2.08 |
| **F2-G03** | ~~Kênh gửi mã cho người nhận: SMS (+ email) trong notification-service; thêm `receiverEmail`~~ — **đã làm** ([hợp đồng](../01-overview/receiver-pickup-code.md)). Còn lại: nạp khoá Twilio trên VM; trả thông tin người nhận trong `OrderResponse`; `delegate` dùng chung kênh; gửi lại mã khi người nhận báo không nhận được | `OrderService.notifyReceiverOutOfBand`, `notification-service/…/channel/`, `OS/dto/SendOrderRequest.java` | F2.05, F2.06 |
| **F2-G04** | Thanh toán thật: ~~bỏ mock CASH ở app, app chờ PAID~~ **đã làm** (mobile #19). Còn lại: CASH ở kiosk chờ nhân viên xác nhận; VNPay IPN kiểm số tiền + idempotent; hoàn tiền khi huỷ đơn đã PAID (REFUNDED) | `PaymentService.java:152,181-200`, `PaymentController.java:75-79`, `OrderService.java:466,1097` | F2.03 |
| **F2-G05** | Thu phí quá hạn: cộng phí trước khi kiểm tra PAID, chuyển UNPAID, chặn lấy hàng tới khi trả | `OrderService.java:449-463,527-553` | F2.09 |
| **F2-G06** | Người nhận có tài khoản thấy đơn gửi tới mình: `findByReceiverId`, tab "Hàng chờ nhận" | `LockerOrderRepository.java`, `OrderService.java:752`, `my_locker_orders_page.dart` | F2.08 |
| **F2-G07** | RENTAL → người nhận: cho nhập `receiverPhone` khi tạo. ~~Áp guard thanh toán khi confirm~~ **đã làm** (`OrderService.java:125`) | `OS/dto/RentalOrderRequest.java` | F2.05 |
| **F2-G08** | Dọn state machine: enum Java + CHECK constraint; xoá RETURNED/READY/WAITING/RESERVED; simulator đi qua `transition()`. _Phía web đã xong_: 3 màn hình báo cáo admin dùng đúng bộ enum backend sinh ra (`frontend/fe/src/types/admin/reporting.ts`); còn lại là bộ legacy giặt ủi ở `frontend/fe/src/schemas/admin.schemas.ts:54-64` và `src/types/admin/enums.ts` mà các màn hình khác vẫn dùng | `LockerOrder.java:66` + Flyway, `frontend/fe/src/schemas/admin.schemas.ts:54-64` | — (nợ kỹ thuật) |
| **F2-G09** | IoT production: broker riêng có auth/TLS (SEC-04); thống nhất payload lệnh mở (`slotIndex`, topic theo lockerId) giữa backend và Pi; sự kiện cửa điều khiển vòng đời; kiosk DROP_OFF tự confirm | `LockerMqttService.java:30,183`, `iot/services/locker_service.py:170-181`, `IotService.java:246-260` | F2.10 |
| **F2-G10** | PIN duy nhất trong các đơn đang hoạt động (partial unique index + sinh lại); rút TTL giữ ô | `OrderService.java:1839` + migration, `app.locker.reserved-ttl-hours` | F2.02, F2.08 |
| **F2-G11** | **Bug mobile**: ~~(a) confirm sai id payment; (b) nút mở ô ở trang Gửi/Thuê~~ **đã làm** (mobile #19, `send_parcel_page.dart:192`, `rent_locker_page.dart:243`). Còn: (c) trang Tủ/Home truyền locker id làm `Store.id` | `M/features/locker/presentation/pages/locker_page.dart:81`, `M/features/home/presentation/pages/home_page.dart:514` | F2.01 |
