# Sự cố rơi kiện trong hành trình Drone

Trạng thái: triển khai local trên nhánh `feature/drone-parcel-drop-incident`, chưa merge/deploy.

## 1. Phạm vi và nguồn sự thật

`order-service` sở hữu incident vì sự cố gắn với order, mission, quyền sở hữu kiện, phương án giao lại và bồi thường. `locker-service` tiếp tục sở hữu tài sản vật lý, KTV và phiếu bảo trì; incident chỉ lưu `inspection_report_id` để liên kết, không sao chép lịch sử sửa chữa. Ảnh dùng hợp đồng Cloudinary ký sẵn trong [media-storage.md](media-storage.md). Policy dùng `system_settings` và được snapshot vào order lúc đặt đơn.

Không dùng `order_complaints` vì bảng đó không biểu diễn được state machine an toàn bay, custody của kiện, telemetry bất biến, evidence có GPS và proposal có phiên bản. Vì vậy migration V21 chỉ thêm các bảng chuyên biệt và cột snapshot; không đổi/xóa dữ liệu production.

## 2. Luồng chính

1. Admin hoặc KTV Drone đang phụ trách mở Journey Detail. API camera trả HLS thật và telemetry; thiếu gateway thì trả `UNAVAILABLE`, không sinh stream giả.
2. `Report Dropped Parcel` cần `Idempotency-Key`, mission đang bay và đúng actor. Backend khóa order, tạo một incident duy nhất cho order/mission, lưu telemetry/GPS/evidence rồi chuyển mission/order sang `DROP_REPORTED` để không thể đi tiếp tới delivered.
3. Drone chuyển `IN_FLIGHT → FAULT`. RTL chỉ được yêu cầu khi autopilot online, drone airborne, pin ≥ 15% và telemetry còn live. Kết quả gọi adapter không đồng nghĩa drone đã về; callback phần cứng cập nhật lần lượt `COMMAND_ACCEPTED → RETURNING → COMPLETED`.
4. `locker-service` tạo idempotent phiếu `DRONE_INSPECTION`, ưu tiên KTV Drone đang phụ trách. Đồng thời chọn KTV tủ active của kiosk gần GPS rơi nhất, sau đó dùng workload để phá hòa; tọa độ kiosk chỉ là vùng trách nhiệm, không được ghi là vị trí live của KTV.
5. KTV tủ nhận việc, bắt đầu tìm, chụp ảnh thật + GPS + tình trạng và submit. Admin verify. Kiện tìm thấy phải xác nhận về Hub/kho trước khi giao lại.
6. Admin tạo proposal phiên bản mới. Khách accept hoặc request review; lịch sử proposal cũ không bị ghi đè.
7. Payment payout và lệnh RTL chỉ được đánh dấu thành công khi adapter thật xác nhận. Khi chưa có payout API, incident giữ `PAYMENT_PENDING`.

## 3. State transitions

| Máy trạng thái | Chuyển hợp lệ chính | Actor / điều kiện |
|---|---|---|
| Incident | `REPORTED → INVESTIGATING/MANUAL_INTERVENTION_REQUIRED → RECOVERY_IN_PROGRESS → AWAITING_ADMIN_REVIEW → AWAITING_CUSTOMER_RESPONSE → RESOLUTION_IN_PROGRESS/DISPUTED → RESOLVED → CLOSED` | Reporter/Admin; recovery assignee; Admin; customer |
| Recovery | `OPEN/AWAITING_ASSIGNMENT → ASSIGNED → ACCEPTED → SEARCHING → SUBMITTED → VERIFIED → CLOSED` | Admin assign; đúng KTV tủ; Admin verify; found parcel về Hub |
| Return flight | `RETURN_REQUESTED → COMMAND_ACCEPTED → RETURNING → COMPLETED`; mọi chặng có thể sang `FAILED/MANUAL_INTERVENTION_REQUIRED` | Callback adapter/phần cứng, không phải UI tự xác nhận |
| Parcel | `DROP_REPORTED → RECOVERY_PENDING → FOUND/DAMAGED/LOST → RETURNED_TO_HUB → REDELIVERY_PENDING/COMPENSATED` | Evidence + verify + phương án đã chấp nhận |
| Resolution | Proposal `AWAITING_CUSTOMER_ACCEPTANCE → ACCEPTED/DISPUTED`; dispute tạo proposal version mới | Khách của order; policy cho phép dispute |

Sơ đồ: [drone-parcel-incident.mmd](../diagrams/src/drone-parcel-incident.mmd).

## 4. API contract

### Journey / reporter

- `GET /api/admin/drone-orders/{orderId}/camera`
- `GET /api/drone-technician/drone-orders/{orderId}/camera`
- `POST /api/admin/drone-orders/{orderId}/drop-incident`
- `POST /api/drone-technician/drone-orders/{orderId}/drop-incident`
- Header bắt buộc khi report: `Idempotency-Key`.
- Body: `reason`, GPS thủ công tùy chọn, `cameraStatus`, `cameraSnapshot` đã ký, `snapshotCapturedAt` ISO-8601 có timezone.

### Admin

- `GET /api/admin/drone-incidents`
- `GET /api/admin/drone-incidents/{id}`
- `POST /api/admin/drone-incidents/{id}/recovery/assign`
- `POST /api/admin/drone-incidents/{id}/recovery/verify`
- `POST /api/admin/drone-incidents/{id}/proposals`
- `POST /api/admin/drone-incidents/{id}/compensation/approve` (cũng dùng để retry an toàn; payout key idempotent theo incident/proposal).

### KTV tủ

- `GET /api/locker-technician/drone-recoveries`
- `GET /api/locker-technician/drone-recoveries/{id}`
- `POST /api/locker-technician/drone-recoveries/{id}/actions` với `ACCEPT` hoặc `START_SEARCHING`.
- `POST /api/locker-technician/drone-recoveries/{id}/submit` với outcome `FOUND/NOT_FOUND/UNSAFE`, condition và ít nhất một evidence.
- `POST /api/locker-technician/drone-recoveries/{id}/hub-handover`.

### Khách hàng và callback nội bộ

- `GET /api/orders/drone-incidents`
- `GET /api/orders/drone-incidents/{id}`
- `POST /api/orders/drone-incidents/{id}/response` với `ACCEPT/REQUEST_REVIEW`.
- `POST /internal/drone-incidents/{incidentCode}/return-flight` dành cho adapter backend/IoT; transition được validate.
- `POST /internal/drone-incidents/{incidentCode}/compensation` dành cho callback payout thật; chỉ nhận `PAID/PAYMENT_FAILED` sau trạng thái `PROCESSING`.

## 5. Cấu hình policy

Các key scope `ORDER`: `app.order.incident-policy-enabled`, `app.order.incident-compensation-rate` (mặc định 60), `app.order.incident-compensation-cap`, `app.order.incident-free-redelivery`, `app.order.incident-refund-shipping-fee`, `app.order.incident-recovery-sla-hours`, `app.order.incident-approval-required`, `app.order.incident-dispute-allowed`. Tỷ lệ 60% là policy sản phẩm, không phải khẳng định pháp lý. `eligibleBase` hiện là `parcel_declared_value`; amount vượt mức gợi ý cần `overrideReason` và audit actor.

## 6. Giới hạn tích hợp hiện tại

- Camera chỉ live khi cấu hình `app.drone.camera.stream-url-template` trỏ tới HLS gateway có quyền truy cập phù hợp. Không có gateway thì web/mobile hiện `UNAVAILABLE`.
- `DroneReturnCommandGateway` có fallback `Unavailable`; callback đã có hợp đồng nhưng cần adapter MAVLink/MQTT triển khai tại môi trường có phần cứng và xác thực service-to-service.
- Payment service hiện có refund order nhưng chưa có beneficiary compensation payout. `IncidentCompensationGateway` và callback đã định nghĩa; fallback ghi `COMPENSATION_INTEGRATION_UNAVAILABLE` và giữ `PAYMENT_PENDING`, không trả success giả.
- Hệ thống hiện chưa có API tạo delivery attempt liên kết. `IncidentRedeliveryGateway` giữ redelivery ở `ACCEPTED` và ghi `REDELIVERY_INTEGRATION_UNAVAILABLE` cho tới khi có adapter thật; không tạo order giả.
- Tọa độ live của KTV chưa có trong user/location service; routing dùng kiosk active gần nhất như vùng trách nhiệm và ghi rõ giới hạn này.

## 7. Chạy local và kiểm thử

Backend: chạy migration bằng Flyway khi start, rồi `mvn -B test`. Web: đặt `VITE_API_BASE_URL` về gateway local, `npm run build`. Mobile: cấu hình API local trong env hiện hành, chạy `flutter analyze` và `flutter test`. Camera có thể để trống template để kiểm tra nhánh `UNAVAILABLE`; không dùng stream mock để đánh dấu hoàn thành tích hợp.
