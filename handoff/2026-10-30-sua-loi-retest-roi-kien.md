# 2026-10-30 — Sửa lỗi từ 4 báo cáo test lại luồng rơi kiện (29/10) + thư báo sự cố cho khách

Người làm: Kimnha01 (cùng Claude Code). Nhánh `fix/f1-g11-sua-loi-retest-roi-kien-2910` ở backend, mobile, frontend, docs — **local, chưa commit / PR / deploy**.

Nguồn lỗi (gọi tắt):
- **[A]** [2026-10-29-retest-admin-roi-kien-sau-sua](2026-10-29-retest-admin-roi-kien-sau-sua.md) — vai admin.
- **[K]** [2026-10-29-test-khach-luong-drone-va-su-co-roi-kien](2026-10-29-test-khach-luong-drone-va-su-co-roi-kien.md) — vai khách.
- **[D]** [2026-10-29-test-ktv-drone-roi-kien-sau-sua](2026-10-29-test-ktv-drone-roi-kien-sau-sua.md) — vai KTV drone + KTV tủ.
- **[V]** [2026-10-29-test-lai-roi-kien-sau-sua](2026-10-29-test-lai-roi-kien-sau-sua.md) — admin + KTV kiosk.

Yêu cầu thêm của chủ dự án: drone phóng đã có thư "đơn đang trên đường" ⇒ **mọi sự cố sau đó phải có thư báo lại khách**.

Test: order-service 464 test (gồm test Postgres/Testcontainers, 0 lỗi, 6 bỏ qua), locker-service 175, common-lib (thêm `GlobalExceptionHandlerTest`), mobile `flutter test` 752 (thêm 3), `flutter analyze` không thêm lỗi/cảnh báo, web admin `tsc -b` sạch + ESLint 0 lỗi. **Chưa thử lại trên điện thoại / production.**

## 1. Thư báo sự cố cho khách (yêu cầu mới)

| Sự cố sau khi đã gửi thư "đang trên đường" | Trước | Sau |
|---|---|---|
| Giao không hoàn tất (KTV / admin / hệ thống tự đóng) | Đã có thư (người gửi; người nhận khi drone đã phóng) | Giữ nguyên |
| **Báo rơi kiện** | Không có thư | Thư cho người gửi (mã sự cố, đang thu hồi, sẽ có phương án trong app) và người nhận (đơn bị chậm, mã mở ô cũ không dùng được); không đưa lý do nội bộ của người báo |
| **Đơn bị chặn khi drone đã phóng** (trời xấu giữa chuyến, drone lỗi giữa chuyến, nắp tủ nhận lỗi) | Chỉ thông báo trong app | Thư "đơn đang tạm dừng" cho cả hai; hết sự cố ⇒ thư "tiếp tục được giao" |
| **Gửi phương án xử lý** | Chỉ thông báo trong app | Thư cho người gửi: phương án, tình trạng kiện, số tiền (kèm hoàn phí giao nếu có), nội dung thoả thuận |
| **Khách đồng ý phương án** | Không có | Thư xác nhận cho người gửi; thư cho người nhận: kiện được giao lại bằng đơn nào, hoặc sẽ không được giao |

Mỗi thư ghi vào nhật ký hành trình "Đã gửi email … cho người gửi tr\*\*\*@…, người nhận …" (hoặc "Chưa gửi được …"). Kênh thư hỏng không làm hỏng thao tác. Vị trí: `OS/service/DroneDeliveryMailer.java` (`parcelDropReported`, `deliveryPaused`, `deliveryResumed`, `incidentProposal`, `incidentResolutionAccepted`), `DroneDeliveryEmailTemplate.incident`, gọi từ `DroneParcelIncidentService` (`report`, `propose`, `customerRespond`) và `DroneDeliveryBlockService.review`.

## 2. Đã sửa

| Nguồn | Mức | Lỗi | Đã sửa thế nào | Vị trí |
|---|---|---|---|---|
| [K] 3 #1 | 🔴 | Thiếu `Idempotency-Key` ⇒ 500 | Handler chung trả 400 `HEADER_REQUIRED` (và 400 cho thiếu tham số, sai kiểu, body hỏng) — áp cho mọi service | `common-lib/…/GlobalExceptionHandler.java` |
| [K] 3 #2 | 🔴 | Chi tiết đơn không có mã lấy hàng | `OrderResponse.dronePickupCode` (chỉ khi KTV chưa cầm kiện); app hiện ô "Mã lấy hàng — đọc cho kỹ thuật viên" | `OS/service/OrderService.dronePickupCode`, `M/…/my_locker_orders_page.dart` |
| [K] 3 #3 · [D] 3 #4 | 🔴 | Đơn giao lại 0đ bị job tự đóng khi trạm dừng vì thời tiết / quá hạn điều phối ⇒ "hoàn tiền" 0đ, sự cố kẹt | Đơn giao lại không bị tự đóng (chặn quá hạn, chưa có KTV quá hạn); thông báo "kiện vẫn giữ an toàn tại kho" | `DroneDeliveryBlockService.review/announce`, `DroneOrderTimeoutSweeper.expire` |
| [V] 3 #1 | 🔴 | Đơn giao lại bay từ tủ gửi cũ, kiện lại ở kho khác | Tủ cất cánh = tủ KTV bàn giao kiện (`recoveryLockerId`) nếu có bãi đáp; không thì giữ tủ cũ + ghi chú nhân viên "mang kiện từ kho tủ #… tới trạm bay tủ #…" | `OrderIncidentRedeliveryGateway`, `DroneSourceLockerSelector.isDroneStation` |
| [V] 3 #2 | 🔴 | Đơn giao lại dùng chung ô với đơn cũ | Ô chuyển hẳn sang đơn giao lại; đơn cũ bỏ `reservedBoxId` | `OrderIncidentRedeliveryGateway` |
| [V] 3 #3 · [A] 4 #11 | 🔴 | `returnFlightStatus = MANUAL_INTERVENTION_REQUIRED` là ngõ cụt; sự cố nào ở DEMO cũng mang nhãn đỏ "Cần can thiệp thủ công" | Báo rơi luôn để sự cố `INVESTIGATING`; API admin `POST /api/admin/drone-incidents/{id}/return-flight/confirm` + nút "Xác nhận drone đã về trạm" trên web; callback cho `FAILED/MANUAL → COMPLETED` | `DroneParcelIncidentService.report/confirmDroneReturned/updateReturnFlight`, `FE/…/drone-incidents/detail.tsx` |
| [V] 3 #4 | 🔴 | Lời mời lấy hàng xoay vòng, admin không biết | Lượt mời thứ 2 hết hạn / bị từ chối mà chưa ai nhận ⇒ báo mọi admin một lần + ghi nhật ký đơn | `DronePickupService.escalateIfNobodyTakesIt` |
| [A] 4 #2 | 🔴 | Admin đóng được phần giao lại khi đơn giao lại chưa xong | Backend từ chối `REDELIVERY_ORDER_NOT_COMPLETED`; web đổi nút thành "Đóng phần giao lại (đơn giao lại đã hoàn tất)" + giải thích sự cố tự đóng | `DroneParcelIncidentService.completeRedelivery`, `detail.tsx` |
| [K] 3 #4 | 🟠 | SĐT "123456789" lọt qua | Regex số Việt Nam `^(?:0\|\+?84)[1-9][0-9]{8}$` ở cả app và server | `CreateDroneDeliveryOrderRequest.PHONE`, `M/…/drone_booking_page.dart` |
| [K] 3 #5 | 🟠 | `DRONE_ROUTE_TOO_SHORT` dịch sai "tủ gửi" | App dùng câu của server (có số mét); câu dự phòng sửa "điểm lấy hàng" | `M/…/locker_ops_service.dart` |
| [K] 3 #9 | 🟠 | "Tải lại" không làm mới "Lịch sử trạng thái" | Khối lịch sử tải lại khi đơn được tải lại | `M/…/order_status_timeline.dart` |
| [K] 3 #10 | 🟠 | Khách đọc lý do nội bộ của admin | Thẻ sự cố khách bỏ `reason`, hiện "Ghi chú hiện trường" của KTV + ảnh thu hồi | `M/…/customer_drone_incident_card.dart` |
| [K] 3 #11 | 🟠 | Nhật ký tiếng Anh "Reported dropped parcel" | "Báo sự cố rơi kiện DPI-…"; timeline "Proposal version N" ⇒ "Gửi phương án lần N" | `DroneParcelIncidentService` |
| [K] 3 #12 | 🟠 | "Trạng thái đơn: Đang giao bằng drone" sau khi rơi | "Tạm dừng do sự cố rơi kiện" | `M/…/drone_delivery_detail.dart` |
| [K] 3 #13 | 🟠 | Khách không thấy tình trạng kiện / ảnh thu hồi | Như [K] #10 | — |
| [K] 3 #15 | 🟠 | Đơn giao lại ghi "đang tìm KTV gần bạn" | "Chờ đội bay tiếp nhận — kiện đã sẵn sàng tại trạm" cho đơn không lấy hàng tận nhà | `drone_delivery_detail.dart` `_headerText` |
| [K] 3 #20 | 🟡 | "Báo ô lỗi" hiện khi kiện chưa vào ô | Đơn drone chỉ báo ô lỗi khi `STORING` | `my_locker_orders_page.dart` |
| [K] 3 #22 | 🟡 | "Trạng thái nhiệm vụ: DROP_REPORTED", "Cần nhân viên xử lý trực tiếp", "Thu hồi kiện: Đã đóng" | Nhãn "Dừng do sự cố rơi kiện", "Nhân viên đang xử lý trực tiếp", "Đã bàn giao kiện về kho" | `drone_labels.dart`, `drone_incident_labels.dart` |
| [D] 3 #1 | 🟠 | Lỗi xác nhận lấy hàng bị bàn phím che | Lỗi lên đầu hộp thoại + hạ bàn phím | `M/…/drone_pickup_queue.dart` |
| [D] 3 #2 | 🟠 | Hộp báo rơi kiện không đóng khi admin đã báo | Hỏi lại chặng mỗi 5 giây; đơn không còn bay / server trả `DRONE_DROP_INCIDENT_EXISTS` ⇒ đóng hộp, báo "đã được báo từ nơi khác" | `M/…/drone_journey_camera_panel.dart` |
| [D] 3 #3 | 🟠 | Phiếu kiểm tra drone giao cho người không trực | Chỉ tự giao khi KTV phụ trách đang trong ca; không thì `OPEN` + báo đội drone | `LS/service/LockerService.createIncidentTickets` |
| [D] 3 #5 | 🟡 | "Đang nạp hàng lên drone · Nhiệm vụ: Sẵn sàng phóng" | Mission `READY_TO_LAUNCH` ⇒ chặng "Sẵn sàng phóng", bỏ nhãn trùng | `M/…/maintenance_home_page.dart` |
| [D] 3 #7 | 🟡 | "Đội bay đã báo kiện rơi" khi admin báo | "Kiện được báo rơi khỏi drone…", nhật ký "Ghi nhận kiện rơi khỏi drone" | `drone_delivery_stage.dart`, `drone_incident_labels.dart` |
| [V] 4 | 🟠 | Dữ liệu mẫu trộn vào web admin (sự cố INC-2026-DROP-001/002, phiếu DRN-DROP-2026-001) và app KTV kiosk (nhiệm vụ INC-2026-DROP-001) | Gỡ hết: chỉ dữ liệu thật, API lỗi thì báo lỗi | `FE/stores/apis/admin/droneIncidents.ts`, `drone-incidents/index.tsx`, `detail.tsx`, `maintenance/index.tsx`, `M/…/locker_ops_service.dart` |
| [V] 4 · [A] 4 #1 | 🟠 | Tỷ lệ "6000%" | `formatCompensationRate` | `detail.tsx` |
| [V] 4 | 🟡 | Sheet thu hồi chữ trắng trên nền trắng; thẻ ghi "Bị hư hỏng" khi KTV chọn hư hại nhẹ | Màu chữ đặt rõ; nhãn theo `parcelCondition` ("Hư hại nhẹ") | `M/…/drone_recovery_queue.dart`, `drone_parcel_incident_card.dart` |
| [V] 2 | 🟡 | Sheet KTV kiosk không tự cập nhật sau admin xác minh | Đang chờ admin (`SUBMITTED`) ⇒ tự tải lại mỗi 10 giây | `drone_recovery_queue.dart` |
| [V] 4 | 🟡 | Chi tiết đơn lấy hàng tận nhà ghi "Người gửi chưa bỏ kiện" | Ẩn dòng "Bỏ kiện vào ô gửi" khi có lấy hàng tận nhà | `FE/…/drone-orders/index.tsx` |
| [A] 4 #3 | 🟠 | "Hoàn phí giao hàng" tick sẵn với phương án giao lại | Chọn phương án có giao lại ⇒ bỏ tick | `detail.tsx` |
| [A] 4 #4 | 🟠 | Modal duyệt phiếu bồi thường ghi "ĐÃ HOÀN TIỀN", nội dung CK "HOANTIEN ORD-…" | Câu riêng cho phiếu bồi thường (không đổi trạng thái hoàn tiền của đơn); nội dung CK / VietQR `BOITHUONG DPI-…` | `FE/…/refunds/components/RefundTable.tsx` |
| [A] 4 #5 | 🟡 | Danh sách Hoàn tiền không phân biệt phiếu bồi thường | Nhãn "Bồi thường sự cố" ở cột số tiền | `RefundTable.tsx` |
| [A] 4 #6, #7 | 🟡 | Chip "Chờ Admin xác minh" sau khi đã xác minh; badge KTV lùi trạng thái | "Chờ lập phương án"; badge "Đã bàn giao về Hub" | `detail.tsx` |
| [A] 4 #8 | 🟡 | Timeline chưa dịch | Thêm nhãn cho mã backend thật (`RECOVERY_ACCEPT`, `RECOVERY_START_SEARCHING`, `RESOLUTION_PROPOSED`, `CUSTOMER_*`, `REDELIVERY_REQUESTED`, `COMPENSATION_*`, `RETURN_FLIGHT_CONFIRMED`, `INCIDENT_RESOLVED`); "Quay về" theo nhãn tiếng Việt | `detail.tsx` |
| [A] 4 #10 | 🟡 | Form phương án vẫn mở khi đang chờ / khách đã đồng ý | Khoá form, hiện câu giải thích | `detail.tsx` |
| [A] 4 #13 | 🟡 | "Gán KTV" khi KTV đã nhận | "Đổi KTV" + câu "chỉ đổi khi KTV hiện tại không đi được" | `FE/…/drone-orders/HomePickupPanels.tsx`, `messages/*.json` |
| — | 🟡 | Nhãn phương án "Giao lại miễn phí" rơi về "Bồi thường" trong lý do / thư | Thêm nhãn `FREE_REDELIVERY` | `PaymentIncidentCompensationGateway.resolutionLabel` |

## 3. Chưa sửa (cần quyết định hoặc để đợt sau)

| Nguồn | Việc | Lý do |
|---|---|---|
| [A] 4 #9 · [D] 3 #10 · [V] 2 | Không khai giá trị thì bồi thường theo gì (hiện lấy cước làm gốc) | ❓ Chủ dự án chốt chính sách |
| [D] 3 #11 | Loại tủ thật CAB-TU01 khỏi chọn tủ thu hồi khi test | ❓ Dữ liệu / cấu hình |
| [D] 3 #6 · [A] | `POST …/launch` mất ~8 s | Thư "đã phóng" gửi đồng bộ trong request (2 lần SMTP + tra tủ/ô). Nên gửi sau commit ở luồng nền; chưa làm vì test Postgres đang kiểm thư ngay trong luồng |
| [A] 4 #12 · [V] 4 | GPS KTV lệch 4 km vẫn duyệt / gửi bình thường | Nên bắt ghi chú khi lệch > ngưỡng — cần chốt ngưỡng |
| [A] 4 #14, #15 | Bảng web phải cuộn ngang mới thấy nút; `GET /api/admin/drone-orders` bỏ qua `size` | Admin web responsive / phân trang thật — đợt riêng |
| [K] 3 #6 | Toạ độ tủ F-Town 3 lệch 2,1 km | Dữ liệu tủ 800005 |
| [K] 3 #7, #8, #14, #16–19, #21, #23, #24 | Còn lại trên app khách (KTV/địa chỉ ở chi tiết đơn, hai giờ thanh toán, form …) | Một phần đã đúng ở bản app `365620c` (báo cáo [K] chạy bản `b36fc3b`); phần còn lại để đợt sau |
| [D] 3 #8, #9, #12 · [D] 5 | Thẻ thời tiết tự mâu thuẫn, Back mất dữ liệu hộp lấy hàng, nhãn "chưa vào ca" khi được giao trực tiếp; app KTV tủ bản cũ | Cần kiểm lại trên bản app mới |
| [V] 4 | Lần bấm "Nhận nhiệm vụ" đầu không có tác dụng | Chưa tái hiện được; có thể liên quan dữ liệu mẫu đã gỡ |

## 4. Deploy

Không có migration mới. Backend: common-lib + order-service + locker-service (thêm trường `dronePickupCode` vào `OrderResponse` — client cũ bỏ qua). Mobile và web admin deploy sau backend (web gọi API mới `…/return-flight/confirm`). Sự cố cũ đang `MANUAL_INTERVENTION_REQUIRED` (vd. DPI-113, DPI-111) đóng được bằng nút "Xác nhận drone đã về trạm".
