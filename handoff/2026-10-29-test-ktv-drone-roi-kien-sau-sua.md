# 2026-10-29 (tối) — Test lại luồng rơi kiện sau bản sửa: vai KTV drone (+ KTV tủ)

Báo cáo **giữa chừng** — test còn đang chạy. Người làm: chủ dự án + nhóm (mỗi người một vai), Claude Code điều khiển điện thoại KTV qua `adb`.
Thời gian: 29/10/2026 21:44 → 23:05. Môi trường: production `https://api.locker-drone.tech`, điện thoại vivo V2154 (1080×2400).
Mốc code: mobile `main` @ `365620c` (đã có nhánh `fix/f1-g11-sua-loi-test-drone-2910`), backend `main` @ `692a47c` (đã deploy, có Flyway order V35), frontend `main` @ `ea9b690`.
Báo cáo trước: [2026-10-29-test-mobile-luong-drone-unhappy-case.md](2026-10-29-test-mobile-luong-drone-unhappy-case.md).

Mức độ: 🔴 nghiêm trọng · 🟠 sai logic / hiển thị sai · 🟡 UI, câu chữ · ❓ cần chủ dự án xác nhận là lỗi hay chủ ý.

## 1. Tiến độ

| Case | Đơn / sự cố | Kết quả tới 23:05 |
|---|---|---|
| Rơi kiện — giao lại + bồi thường một phần | ORD-20261029-6SBKYS (#143) → DPI-143-1793288403320 → giao lại ORD-20261029-58RD1J (#144) | Bồi thường 2.400đ ✅ `PAID`; đơn giao lại **chưa tiếp nhận được** vì 17/17 trạm tự dừng bay do dự báo mưa phùn thật (§ 4) |
| Rơi kiện — chỉ bồi thường | — | Chưa chạy |
| Rơi kiện — thỏa thuận riêng | — | Chưa chạy |
| (KTV tủ) xử lý phiếu trễ hạn để gỡ chặn nhận việc | RPT-33 | ✅ RESOLVED — làm trên **bản app cũ `f53d219`** (trước bản sửa) |

Các bước case 1 đã qua: KTV drone nhận lời mời lấy hàng → nhập mã lấy hàng + chụp ảnh → gán LR-DRN-06 → xác nhận nạp (1000 g) → phóng → **admin** báo rơi kiện (trước khi KTV kịp bấm) → hệ thống tự giao thu hồi cho `kiosk1` → KTV tủ tìm thấy, hư hại nhẹ → admin xác minh → bàn giao về Hub → admin gửi phương án v1 (giao lại + 2.400đ) → khách đồng ý → tạo đơn giao lại 0đ `PAID` + phiếu chi → admin duyệt chi → sự cố `compensationStatus = PAID`.

## 2. Bản sửa đã kiểm chứng chạy đúng

| # báo cáo trước | Kết quả |
|---|---|
| § 3 #1 sự cố có bồi thường không đóng | ✅ Admin duyệt phiếu chi ⇒ sự cố tự `PROCESSING → PAID`; sự cố giữ `RESOLUTION_IN_PROGRESS` vì giao lại còn `PREPARING` (đúng `resolveIfSettled`) |
| § 4 KTV drone: bấm chữ không tick được "Kiện đúng khai báo" | ✅ Bấm vào chữ là tick |
| — | ✅ Khách đồng ý "giao lại" ⇒ đơn giao lại **0đ, PAID**, mô tả ghi rõ sự cố + đơn cũ |
| — | ✅ Chặn đúng nghiệp vụ: xác nhận lấy hàng khi cách 1,7 km ⇒ `DRONE_PICKUP_TOO_FAR`; trạm dừng vì thời tiết ⇒ nút "Tiếp nhận" khóa, nêu lý do |

Chưa kiểm được (chưa tới bước): § 3 #5 giao lại tự đóng sự cố, #4 thỏa thuận riêng, #2 hoàn phí giao, #3 nội dung phiếu chi.

## 3. Lỗi phát hiện — KTV drone (app `365620c`)

| # | Mức | Lỗi | Tái hiện / bằng chứng | Vị trí nghi vấn |
|---|---|---|---|---|
| 1 | 🟠 | **Lỗi xác nhận lấy hàng bị che, KTV không thấy.** Server trả `DRONE_PICKUP_TOO_FAR` ("cách 1,7 km, tối đa 300 m") nhưng câu lỗi nằm cuối hộp thoại dưới ô "Ghi chú", khuất sau bàn phím ⇒ bấm "Đã lấy hàng" như không có phản ứng. Chỉ thấy lỗi qua log | #143, 22:30–22:31 | `mobile/…/drone_delivery/presentation/widgets/drone_pickup_queue.dart:471` (`submitProblem` hiện sau ô ghi chú) — nên đặt ngay trên nút hoặc SnackBar |
| 2 | 🟠 | **Hộp "Xác nhận báo rơi kiện" không đóng khi đơn đã được báo rơi** từ admin: vẫn hiện "Chặng bay: Đang bay tới tủ nhận" và nút "Xác nhận" với dữ liệu cũ (cùng kiểu § 4 báo cáo trước với hộp "Báo chuyến bay thất bại") | #143, admin báo lúc 22:40:03 trong khi hộp đang mở | `mobile/…/maintenance/presentation/widgets/drone_journey_camera_panel.dart:264` |
| 3 | 🟠 | **Phiếu kiểm tra an toàn drone giao cho người không làm.** RPT-44 (sự cố DPI-143) tự giao `IN_PROGRESS` cho KTV phụ trách drone LR-DRN-06 — một tài khoản dữ liệu demo — trong khi KTV vừa bay đơn đó đang trong ca. Phiếu sẽ không ai xử lý; chỉ kiểm `activeTechnician`, không xét ca trực | RPT-44 | `locker-service/…/LockerService.createIncidentTickets` (`drone.getAssignedTechnicianId()`) |
| 4 | 🟠 | **Đơn giao lại sinh ra khi mọi trạm đang dừng bay** ⇒ bị chặn ngay từ đầu. Cần kiểm cơ chế tự đóng đơn bị chặn quá hạn (`DroneDeliveryBlockService`) có đóng + "hoàn tiền" đơn 0đ này không — nếu có, phần giao lại của sự cố kẹt `PREPARING` | #144 (tạo 22:56, trạm dừng từ 22:45–22:50) | `DroneParcelIncidentService` (tạo đơn giao lại), `DroneDeliveryBlockService.review` |
| 5 | 🟡 | Thẻ đơn sau khi nạp ghi "Chặng: **Đang nạp hàng lên drone** · Nhiệm vụ: **Sẵn sàng phóng**" — hai trạng thái mâu thuẫn; dòng "Cập nhật 22:38:25" không đổi sau khi xác nhận nạp lúc 22:39 | #143 | `maintenance_home_page.dart:3880` (`_stageTitle` theo `deliveryStage = ACCEPTED`) |
| 6 | 🟡 | `POST …/launch` mất **8,2 s** (trả 202) | #143, 22:39 | backend launch |
| 7 | 🟡 | Sau khi có sự cố, chi tiết đơn ghi "**Đội bay** đã báo kiện rơi" dù người báo là admin | #143 | `mobile/…/drone_delivery/domain/entities/drone_delivery_stage.dart:201` |
| 8 | 🟡 | Thẻ thời tiết tự mâu thuẫn: điều kiện "Nhiều mây" nhưng lý do chặn "có mưa hoặc dông trên tuyến" (thực tế mưa phùn 0,1 mm, mã 51) | 22:56, mọi trạm | thẻ thời tiết KTV drone / thông điệp weather guard |
| 9 | 🟡 | Hộp "Xác nhận đã lấy hàng": một lần Back đóng cả hộp, **mất** mã, dấu tick, ảnh đã chụp | #143 | `drone_pickup_queue.dart` |
| 10 | ❓ | Giá trị khai báo trong sự cố = **8.000đ** (bằng phí giao) ⇒ gợi ý bồi thường 4.800đ, `compensationCap = 0`. Cần xem form đặt đơn có cho khách khai báo giá trị không, và `compensationCap = 0` nghĩa là gì | DPI-143 | order-service chính sách bồi thường |
| 11 | ❓ | Tủ thu hồi của sự cố demo là **tủ thật CAB-TU01** (gần điểm rơi nhất) — có nên loại tủ vật lý khỏi dữ liệu test? | DPI-143 `recoveryLockerId = 7` | `LockerService.selectRecoveryTechnician` |
| 12 | ❓ | Lời mời lấy hàng do điều phối viên giao trực tiếp tới KTV đang hiện "**Chưa vào ca lấy hàng**" | #143 lúc 22:17 | thẻ ca lấy hàng KTV drone |

## 4. Chặn do môi trường (không phải lỗi)

- Điện thoại KTV cách điểm lấy hàng 1,7 km ⇒ admin tạm nới `app.order.drone-pickup-confirm-max-distance-meters`.
- Để kịp báo rơi kiện khi đang bay: admin tạm tăng `app.drone.demo.stage-delay-ms`.
- 22:45–22:50 Open-Meteo dự báo mưa phùn 0,1 mm (gió 2 km/h) ⇒ 17/17 trạm tự dừng (`max-precipitation-mm = 0`, chặn theo mã thời tiết). Muốn chạy tiếp phải tạm đặt `block-precipitation-codes = false`, `max-precipitation-mm = 50` hoặc chờ hết mưa.

## 5. Lỗi phát hiện — KTV tủ (`kiosk1`, **app cũ `f53d219`**, cần kiểm lại trên `365620c`)

| # | Mức | Lỗi |
|---|---|---|
| 1 | 🟡 | "Xác nhận & Hoàn tất sửa chữa" (RPT-33): không thấy thông báo thành công, hộp đứng vài giây rồi mới về trang chính — dễ bấm lặp |
| 2 | 🟡 | Chip ghi chú mẫu ("Đã cân chỉnh then…") bấm vào thêm chữ vào ô ghi chú nhưng chip không đổi trạng thái chọn |
| 3 | 🟠 | Cùng một màn "Việc của tôi": ô tổng quan "Đã hoàn tất **11**" nhưng thẻ SLA "Đã hoàn thành: **12**" |
| 4 | 🟠 | Tủ "Tủ thật TU01 (7 ô)" nhưng thẻ tủ ghi "Tổng ô **8**" |
| 5 | ❓ | KTV giữ ≥ 3 phiếu trễ hạn bị chặn nhận phiếu mới và không được tự giao (đúng luật `technician-claim-block-overdue = 3`); phiếu trễ là dữ liệu test cũ nên chặn cả buổi test cho tới khi xử lý |

## 6. Thay đổi trên production cần trả lại khi test xong

- `app.order.drone-pickup-confirm-max-distance-meters` → **300**.
- `app.drone.demo.stage-delay-ms` → **5000**.
- Nếu đã nới thời tiết: `app.drone.weather.block-precipitation-codes` → **true**, `app.drone.weather.max-precipitation-mm` → **0**.

Dữ liệu tạo/đổi: RPT-33 (KTV tủ) đã RESOLVED; đơn #143 (sự cố DPI-143), đơn giao lại #144 đang chờ trạm mở lại; phiếu chi bồi thường 2.400đ đã duyệt; RPT-44 đang treo ở tài khoản demo (§ 3 #3).
