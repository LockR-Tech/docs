# 2026-10-29 — Test đặt đơn drone trên điện thoại thật: Happy case + unhappy case và lỗi phát hiện

Người làm: Kimnha01 (cùng Claude Code). Thời gian test: 29/10/2026 09:49 → 15:20.
Mốc code đã rà: backend `main` @ `ea21d56` lúc bắt đầu, `9297c4d` lúc kết thúc (đã có rule 200 m), mobile `main` @ `b36fc3b` (app `1.0.0+2`), frontend `main` @ `e2f42bb`.
Môi trường: production `https://api.locker-drone.tech`, điện thoại OPPO CPH2473 (Android, 720×1612). Chế độ thử nghiệm ArUco **tắt** (không test).

Báo cáo ghi nhận lỗi; phần đã sửa (local, **chưa commit/deploy**) ở § 8. Mức độ: 🔴 nghiêm trọng (sai tiền, kẹt đơn/sự cố, sai nghiệp vụ) · 🟠 sai logic / hiển thị sai · 🟡 UI.

Tài khoản: khách `minhanh.tran@gmail.com`, KTV drone `ktvdronedemo2@gmail.com` (Long Hoàng), KTV kiosk `kiosk1@gmail.com`, admin `binhtntse182370@fpt.edu.vn`. Khách, KTV drone, KTV kiosk thao tác trên app điện thoại; các bước admin gọi đúng API mà web admin dùng (web admin trên màn điện thoại quá chật để thao tác bảng).

## 1. Tóm tắt kết quả

| Case | Đơn | Kết quả |
|---|---|---|
| Happy case: đặt → trả tiền → KTV lấy tận nhà → nạp → phóng → vào ô → mở ô (BLE mô phỏng) → hoàn tất | ORD-20261029-2JPIS5 (#129) | ✅ Hoàn tất, cộng +800 điểm, drone về IDLE |
| Thời tiết xấu: chặn phóng, chặn đặt đơn mới, đơn bị chặn → KTV "Giao không hoàn tất" → trả kiện → hoàn tiền | ORD-20261029-2QL4UF (#130) | ✅ REFUNDED, đồng bộ 3 vai trò |
| Đội bay hủy trước khi phóng (lý do Drone lỗi) → trả kiện → hoàn tiền | ORD-20261029-113V7U (#131) | ✅ REFUNDED — nhưng drone vẫn IDLE (§ 3 #7) |
| Giao không hoàn tất khi đang bay (Báo chuyến bay thất bại) → drone FAULT → trả kiện → hoàn tiền | ORD-20261029-PF1T60 (#133) | ✅ REFUNDED |
| Rơi kiện — Giao lại miễn phí | ORD-20261029-DBEN8B (#134) → giao lại ORD-20261029-8EQXXL (#135) | ✅ Đơn mới **0đ, PAID**, không thu thêm, giao thành công; sự cố RESOLVED **chỉ sau khi admin bấm tay** |
| Rơi kiện — Giao lại + bồi thường một phần (150.000đ, hư hại nhẹ) | ORD-20261029-YTBQYW (#136) → ORD-20261029-9F5DT8 (#137) | ⚠️ Giao lại OK, phiếu chi 150.000đ COMPLETED, **sự cố kẹt** `RESOLUTION_IN_PROGRESS` |
| Rơi kiện — Chỉ bồi thường (360.000đ, thất lạc) | ORD-20261029-IZ86UN (#141) | ⚠️ Phiếu chi 360.000đ COMPLETED, **sự cố kẹt** |
| Rơi kiện — Thỏa thuận riêng (khách "Yêu cầu xem xét" phương án 1 → admin gửi phương án 2 thỏa thuận riêng → khách đồng ý) | ORD-20261029-2AL2OB (#142) | ❌ Không hợp logic, **sự cố kẹt vĩnh viễn** (§ 3 #4) |
| Rule mới: tủ nhận phải cách nơi gửi ≥ 200 m | ORD-20261029-X3R5VF (#140) | ❌ Tủ nhận cách 13 m vẫn đặt được (§ 3 #6). Đơn đã hủy (cũng test luôn nút Hủy của khách khi chưa trả tiền: ✅) |

Đơn phụ: ORD-20261029-1RGEO6 (#132), #138, #139 — định báo sự cố nhưng drone giả lập đã tới tủ trước, khách nhận hàng để đóng đơn (COMPLETED).

Kết luận: trạng thái đơn (`status`, `deliveryStage`, `paymentStatus`, `missionStatus`) đọc qua API của khách, KTV drone và admin **luôn khớp nhau** ở mọi bước. Lỗi tập trung ở trạng thái **sự cố / bồi thường**, nội dung phiếu hoàn tiền, rule 200 m, điều phối KTV và câu chữ UI.

## 2. Các bước đã chạy từng case (tóm tắt)

- **Happy:** form đặt (điểm lấy hàng = vị trí hiện tại, người nhận, ô, 1 kg, Tài liệu, khai báo 500.000đ) → "Giả lập thanh toán (test)" 8.000đ → KTV nhận lời mời → nhập mã lấy hàng + chụp ảnh → gán drone → xác nhận nạp (cấp mã niêm phong) → phóng → giả lập 5 s/chặng → READY_FOR_PICKUP, PIN 6 số, email mã → khách "Mở ô" (BLE mô phỏng RPi) → COMPLETED.
- **Thời tiết:** đơn #130 tới "Sẵn sàng phóng" → admin hạ ngưỡng gió 30 → 1 km/h (gió thật 7 km/h) → KTV bấm Phóng bị chặn "Thời tiết không cho phép bay: gió 7 km/h…", nút Phóng khóa; 16/16 trạm tự dừng; khách thấy thẻ "Đơn đang gặp sự cố… nếu chưa khắc phục trước 11:00 đơn sẽ kết thúc"; form đặt đơn mới bị khóa nút. Kết thúc bằng KTV "Giao không hoàn tất → Thời tiết xấu" (không chờ tự đóng, xem § 5) → trả kiện → admin duyệt hoàn #26.
- **Hủy trước khi phóng:** #131 tới Sẵn sàng phóng → "Hủy trước khi bay" (bỏ trống lý do → báo "Chọn một lý do" ✅) → Drone lỗi → trả kiện → admin duyệt hoàn #27.
- **Giao không hoàn tất khi bay:** #133 phóng → "Báo chuyến bay thất bại" → Drone lỗi → DRONE-03 FAULT → trả kiện → duyệt hoàn #28. (Lần đầu với #132 drone đã tới tủ trước khi xác nhận → backend từ chối đúng "Đơn không còn ở bước cho phép thao tác này".)
- **Rơi kiện (4 case):** KTV drone mở chi tiết hành trình → khung camera (UNAVAILABLE) → "Báo rơi kiện" + mô tả + ảnh → đơn/mission `DROP_REPORTED`, drone FAULT, tạo phiếu kiểm tra `RPT-…` → admin phân công thu hồi cho `kiosk1` → KTV kiosk: Nhận nhiệm vụ → Bắt đầu tìm → xác nhận GPS hiện trường → kết quả + tình trạng + ảnh → Gửi Admin → admin xác minh → KTV kiosk "Bàn giao về Hub" (trừ case thất lạc) → admin gửi phương án → khách Đồng ý / Yêu cầu xem xét trên app → admin duyệt bồi thường → admin duyệt phiếu chi. Để báo kịp lúc drone đang bay, tạm tăng `app.drone.demo.stage-delay-ms` lên 60.000.
- **Validation phương án (admin) đều đúng:** vượt mức gợi ý không có lý do → `COMPENSATION_OVERRIDE_REASON_REQUIRED`; "giao lại + bồi thường một phần" với 0đ → `RESOLUTION_CONTENT_INVALID`; đề xuất giao lại khi kiện thất lạc → `PARCEL_NOT_AT_HUB`.

## 3. Lỗi phát hiện — 🔴 Nghiêm trọng

| # | Lỗi | Tái hiện / bằng chứng | Vị trí nghi vấn |
|---|---|---|---|
| 1 | **Sự cố có bồi thường không bao giờ đóng.** Admin duyệt phiếu chi (refund `COMPLETED`) nhưng sự cố vẫn `compensationStatus = PROCESSING`, `status = RESOLUTION_IN_PROGRESS`. Không có callback payment → order; admin không còn thao tác nào (approve chỉ nhận `AWAITING_APPROVAL/PAYMENT_PENDING/PAYMENT_FAILED`). Khách thấy "Đang thực hiện phương án · Đã gửi yêu cầu chi bồi thường" dù đã nhận tiền | DPI-136-1793250234358 (phiếu #29), DPI-141-1793259680084 (phiếu #30) | `payment-service/.../PaymentService.java` `adminApproveRefund` không báo lại; callback `POST /internal/drone-incidents/{code}/compensation` không ai gọi |
| 2 | **"Hoàn phí giao" không được thực hiện.** Phương án `refundShippingFee = true`, khách thấy "hoàn phí giao", nhưng chỉ tạo phiếu bồi thường, **không có khoản hoàn 8.000đ**. Đơn gốc lại bị đổi `paymentStatus = REFUND_PENDING → REFUNDED` như đã hoàn tiền đơn | #136, #141 | `order-service/.../PaymentIncidentCompensationGateway.java` bỏ qua `refundShippingFee`; `PaymentService.createCompensationRefund` đổi trạng thái thanh toán đơn |
| 3 | **Nội dung phiếu bồi thường sai / thiếu.** `"[Bồi thường sự cố DPI-136…] Hoàn 60%, số tiền: 150,000 đ. Lý do: Bồi thường sự cố rơi kiện"` — 150.000đ chỉ là **30%** giá trị khai báo 500.000đ, "60%" là tỷ lệ chính sách chứ không phải tỷ lệ thực; lý do chung chung, không nêu tình trạng kiện (hư hại nhẹ / thất lạc), giá trị khai báo, phương án; số tiền viết kiểu `150,000 đ`. Phiếu hoàn đơn hủy chỉ ghi `"Đơn drone ORD-… bị huỷ"`, không nêu lý do (thời tiết / drone lỗi / thất bại khi bay); `createdAt` của phiếu trả về `null` | Phiếu #26–#30 | `PaymentService.createCompensationRefund` (dựng `compReason`), `DroneRefundService` |
| 4 | **Thỏa thuận riêng (`MANUAL_RESOLUTION`) không hợp logic.** API không có trường ghi nội dung thỏa thuận; backend không validate nội dung; khách chỉ thấy "Nhân viên liên hệ xử lý riêng" mà vẫn phải bấm Đồng ý. Phương án 0đ + không giao lại: sau khi khách đồng ý, đơn `CANCELED` nhưng **giữ 8.000đ đã trả**, kiện hư hỏng nằm ở Hub không có bước tiếp, sự cố **kẹt vĩnh viễn** — approve → `COMPENSATION_NOT_REQUIRED`, complete redelivery → `REDELIVERY_NOT_IN_PROGRESS`. Phương án 1 bị tranh chấp không còn hiện cho khách | DPI-142-1793261278775 | `DroneParcelIncidentService.propose` (không kiểm `MANUAL_RESOLUTION`), `customerRespond` (không có nhánh đóng khi không còn việc) |
| 5 | **Giao lại không đồng bộ với sự cố.** Đơn giao lại đã vào tủ rồi COMPLETED mà sự cố vẫn `redeliveryStatus = PREPARING`, phải admin gọi `redelivery/complete` bằng tay; `parcelStatus` vẫn `RETURNED_TO_HUB` sau khi đã giao cho khách | DPI-134 (#135), DPI-136 (#137) | `DroneParcelIncidentService.completeRedelivery` chỉ chạy tay |
| 6 | **Rule 200 m áp dụng sai.** Đặt tới "test tu" cách nơi gửi **13 m** vẫn tạo được đơn: rule `app.order.drone-min-route-meters = 200` chỉ đo **tủ bay → tủ nhận**; tủ bay quá gần thì bỏ qua và chọn tủ xa hơn (F-Town 3, 1,6 km) ⇒ KTV mang kiện 1,6 km rồi drone bay ngược 1,6 km về tủ sát người gửi. Chỉ báo `DRONE_ROUTE_TOO_SHORT` khi **mọi** tủ bay đều quá gần. Danh sách chọn tủ không làm mờ/cảnh báo tủ dưới 200 m (test tu 13 m, Locker2309 79 m, TU01 / tủ demo 88 m). Chưa thử được 3 tủ còn lại bằng API báo giá vì lúc đó trạm FPT đang tự dừng do mưa thật | ORD-20261029-X3R5VF (#140) | `order-service/.../DroneSourceLockerSelector.java:104-129` |
| 7 | **Drone báo lỗi vẫn được dùng.** Hủy trước khi bay với lý do "Drone lỗi" nhưng DRONE-03 vẫn `IDLE`, gán đơn tiếp được. Báo thất bại khi bay chọn "Drone lỗi" nhưng lưu `FLIGHT_INCIDENT` (Sự cố trong lúc bay). DRONE-03 thành `FAULT` sau thất bại mà **không có phiếu kiểm tra** ⇒ không có đường đưa về hoạt động (khác rơi kiện có `RPT-…`) | #131, #133 | `DroneOrderMaintenanceService` (cancel / `reportFlightFailure`) |
| 8 | **Mời KTV sai người.** Lời mời lấy hàng #132 gửi cho "KTV Drone" (id 25) có vị trí cũ 2 ngày (`locationFresh = false`), cách **15,9 km** (vượt bán kính 5 km), trong khi Long Hoàng cách 3 m, rảnh, vị trí mới — chỉ đang trong 10 phút chờ sau lượt mời trước hết hạn | `GET /api/admin/drone-orders/132/pickup/candidates` | bộ điều phối lời mời (`DroneDispatchSweeper` / pickup service) |
| 9 | **Đăng xuất KTV không kết thúc ca.** Hộp thoại ghi "kết thúc ca trực và đăng xuất" nhưng `onDuty` vẫn `true` ⇒ KTV đã đăng xuất vẫn được mời, lời mời hết hạn rồi bị khóa mời 10 phút (gây ra #8) | `GET /api/drone-technician/drone-orders/presence` sau đăng xuất | mobile: luồng đăng xuất KTV drone / KTV tủ |
| 10 | **Tủ bay bị đổi âm thầm sau khi KTV đã lấy hàng.** #142: từ tủ demo sang Vinhomes S5.02 (lúc mọi drone ở tủ demo đang FAULT) ⇒ KTV phải mang kiện thêm 2,9 km, quãng bay 1,7 → 4,27 km; **không có dòng nhật ký**, khách không được báo, giá giữ nguyên | `journeyEvents` của #142 | `DroneSourceLockerSelector` / sweeper chọn lại tủ gửi cho đơn chưa gán drone |
| 11 | **Lệch dữ liệu ô.** Đơn cũ ORD-SND-0009 (SEND, READY_FOR_PICKUP) giữ box 12 (Ô 2 tủ Vinhomes S5.02) trong khi locker-service báo `AVAILABLE` ⇒ form cho chọn ô, tạo đơn báo "Ô tủ không còn trống" | Đặt tới S5.02 ô 2 | `DroneOrderBookingService.assertBoxNotHeldByActiveOrder`; layout ô không xét đơn đang giữ |
| 12 | **Đổi lý do chặn không reset mốc.** Đơn cũ chuyển `STATION_SUSPENDED` → `WEATHER_UNSAFE` vẫn giữ `deliveryBlockedAt` cũ ⇒ hạn tự đóng sớm hơn | CZTMEL, 3TG2TW lúc 10:45 | `DroneDeliveryBlockService.review` |

## 4. Lỗi phát hiện — 🟠 / 🟡 UI, hiển thị

### Khách
- 🟠 Đơn rơi kiện đã đóng ghi **"Đơn drone đã huỷ — Đơn đã dừng trước khi drone cất cánh"** trong khi drone đã bay và rơi kiện.
- 🟠 Mốc thời gian chi tiết đơn có "**Kiện đã được bỏ vào tủ gửi**" — luồng mới (KTV lấy tận nhà, nạp thẳng lên drone) không có bước này.
- 🟠 Đơn **chưa trả tiền** nhưng tiêu đề ghi "Hệ thống đang tìm kỹ thuật viên drone rảnh gần bạn nhất".
- 🟠 Đơn bị chặn vì thời tiết: tiêu đề vẫn "Đang nạp hàng lên drone" (đã nạp xong, mission `READY_TO_LAUNCH`), mốc "Từ" nhảy sang giờ bị chặn; thẻ ở trang chủ chỉ ghi "Đã tiếp nhận", không báo sự cố.
- 🟠 Sau khi đồng ý giao lại, trang chủ vẫn hiện đơn cũ đã hủy, không hiện đơn giao lại cho tới khi kéo làm mới.
- 🟠 Phương án ghi lặp "Giao lại miễn phí · giao lại miễn phí"; thẻ trạng thái vẫn "đang thu hồi… Lock.R sẽ gửi phương án" khi phương án đã gửi; "Tình trạng kiện" chỉ ghi "Đã về kho Lock.R", khách không biết kiện hư hại nhẹ/nặng.
- 🟠 Nút **"Đặt lại đơn"** hiện ở đơn drone → báo "Chỉ đặt lại được đơn gửi hàng hoặc thuê tủ" rồi rơi vào trang "Đơn tủ" **không có nút quay lại, không có thanh điều hướng**; Back thoát app, force-stop mở lại vẫn kẹt trang đó.
- 🟠 "Tôi đã lấy đồ — hoàn tất" đóng đơn ngay, **không hỏi xác nhận**.
- 🟡 Chi tiết đơn có 2 giờ thanh toán khác nhau ("Thanh toán lúc 09:56:56" vs "Thời gian thanh toán 09:56:09"); mã thanh toán `PAY-129-1793242569222` khác nội dung chuyển khoản `PAY-129-ORD-20261029-2JPIS5`.
- 🟡 Nút "Chỉ đường tới drone tại tủ bay" hiện cho khách (khách không đi tới tủ bay).
- 🟡 Hộp hủy đơn chưa trả: "ô drone ở hai tủ được nhả" (luồng mới không giữ ô ở tủ gửi).
- 🟡 Badge "Đã hủy" màu xanh lá; đơn hoàn tất vẫn hiện "Hạn lấy".

### Form đặt đơn
- 🟠 Trạm dừng vì thời tiết: danh sách tủ vẫn chọn được bình thường; vào form chỉ báo chung "Các trạm bay gần điểm lấy hàng đang tạm dừng…", không nói lý do; trạm mở lại thì form **không tự cập nhật**, không có nút thử lại (phải chọn lại điểm lấy hàng).
- 🟠 Giới hạn 3 đơn drone đang mở chỉ báo **sau khi** điền xong cả form ("Bạn đang có quá nhiều đơn drone chưa hoàn tất").
- 🟡 Chip khối lượng được chọn (nền xám nhạt, không viền) trông như chưa chọn so với chip khác.
- 🟡 Danh sách tủ sắp xếp lại khi vừa lấy được vị trí (nháy danh sách).

### KTV drone
- 🟠 Bị chặn "Chưa có vị trí GPS mới" khi xác nhận lấy hàng ⇒ đóng hộp, cập nhật GPS, mở lại thì **mất hết** mã lấy hàng, checkbox, ảnh đã chụp. Bấm vào chữ không tick được checkbox "Kiện đúng khai báo".
- 🟠 Thẻ "Chờ trả kiện" ghi "**chuyến bay thất bại**" cho đơn dừng vì thời tiết, chưa cất cánh.
- 🟠 Hộp "Hủy trước khi bay" không nói gì về hoàn tiền / trả kiện (khác hộp "Giao không hoàn tất"); hộp trả kiện ghi "Ô gửi còn giữ cho đơn này sẽ được nhả" (không có ô gửi).
- 🟠 Hộp báo rơi kiện ghi "Hệ thống không tự tạo toạ độ khi telemetry không trực tuyến" nhưng backend lưu toạ độ ước theo tuyến bay (`gpsSource = FLIGHT_PATH`); "Chặng bay" trong hộp là ảnh chụp lúc mở, không cập nhật.
- 🟠 Hộp "Báo chuyến bay thất bại" vẫn mở khi drone đã tới tủ (không đóng theo realtime).
- 🟡 Dùng câu chữ của khách: "Tủ nhận bạn đã chọn", "Lock.R sẽ gửi phương án xử lý cho bạn".
- 🟡 Chập chờn: danh sách rỗng ở bộ lọc "Mọi trạng thái (3)" ngay sau gán drone; "Không tải được hàng đợi đơn drone: Lỗi kết nối máy chủ" (bấm Thử lại thì được).
- 🟡 Dòng trạng thái ca vẫn "rảnh, sẽ được mời…" sau khi admin phân công việc.
- 🟡 Nút "Thử lại" trong khung camera gần như không đọc được (chữ xanh đậm trên nền đen). Thẻ "Đội bay 0" ở đầu trang không đếm đơn đang khởi phóng.
- 🟡 Đơn đã giao, chờ khách nhận vẫn nằm trong bộ lọc "Đang xử lý".

### KTV tủ (thu hồi kiện)
- 🟡 Banner "Có N nhiệm vụ thu hồi kiện rơi" và tab "Thu hồi kiện (N)" đếm cả nhiệm vụ đã đóng.
- 🟡 Màn chi tiết nhiệm vụ không tự cập nhật sau khi admin xác minh (phải đóng/mở lại mới thấy nút "Bàn giao về Hub").
- 🟡 Chỉ cảnh báo "Cách điểm rơi ~823 m / 1.542 m", vẫn cho gửi "Đã tìm thấy" (cần xác nhận đây là chủ ý).

### Phiếu kiểm tra drone
- 🟡 "Ảnh hiện trường (người báo): 0 ảnh" dù lúc báo rơi kiện đã chụp ảnh.
- 🟡 Drone về `IDLE` trễ vài giây sau khi nghiệm thu.

### Admin web
- 🟡 Trên màn hẹp (720 px) sidebar đè lên nội dung, mất chữ đầu dòng; thẻ thời tiết bị bóp dọc. (Web admin vốn cho desktop.)
- 🟠 Thẻ "Đang bay: 1" trong khi không có chuyến nào thật sự đang bay (do dữ liệu kẹt § 6).

## 5. Đồng bộ trạng thái giữa các vai trò

- ✅ Khớp: mọi lần đối chiếu `GET /api/orders/{id}/drone-delivery` (khách), `/api/drone-technician/drone-orders/{id}` (KTV drone), `/api/admin/drone-orders/{id}` (admin) đều cùng `status`, `deliveryStage`, `paymentStatus`, `missionStatus`, drone, mã niêm phong, hạn nhận.
- ✅ Realtime: màn khách tự chuyển khi KTV nhận việc / lấy hàng / phóng; app KTV tự hiện việc khi admin phân công; khách nhận push "Phương án xử lý sự cố drone".
- ❌ Lệch: trạng thái **sự cố** không theo kịp đơn giao lại và phiếu chi (§ 3 #1, #5); đơn gốc `REFUNDED` dù chỉ chi bồi thường (§ 3 #2); trang chủ khách và các màn chi tiết KTV tủ cần làm mới tay (§ 4).

## 6. Thay đổi trên production và dữ liệu còn tồn

Cấu hình (`/api/admin/settings/order`, được chủ dự án cho phép từng lần) — **đã trả về giá trị cũ**:
- `app.drone.weather.max-wind-speed-kmh` 30 → 1 → 30.
- `app.drone.weather.block-precipitation-codes` true → false → true; `app.drone.weather.max-precipitation-mm` 0 → 50 → 0 (tạm tắt vì mưa thật quanh FPT làm dừng 7 trạm).
- `app.drone.demo.stage-delay-ms` 5000 → 60000 → 5000 (để kịp báo sự cố khi drone đang bay).

Tác động phụ khi hạ ngưỡng gió: 16/16 trạm tự dừng 10:30–10:45; 3 đơn cũ (CZTMEL, 3TG2TW, 3MYOVV) bị gắn chặn, sau đó tự gỡ, **không bị đóng**.

Tiền: đã duyệt phiếu hoàn #26, #27, #28 (8.000đ/đơn), phiếu bồi thường #29 (150.000đ), #30 (360.000đ) — đều là tiền test, tài khoản nhận TPBank 0933102278 của khách test.

Còn tồn cần xử lý:
- Sự cố kẹt: DPI-136-1793250234358, DPI-141-1793259680084, DPI-142-1793261278775 (`RESOLUTION_IN_PROGRESS`); kiện hư hỏng của DPI-142 đang "ở Hub".
- Drone `FAULT`: DRONE-03 (thất bại khi bay, **không có phiếu kiểm tra**), DRONE-S550-07 (rơi kiện DPI-136), DRONE-04 (rơi kiện DPI-142). DRONE-TEST đã về IDLE sau nghiệm thu RPT-40, RPT-42.
- Dữ liệu kẹt có từ trước: ORD-20261015-OIY7WX `EN_ROUTE` từ 15/10; ORD-20261015-3MYOVV, 3TG2TW, ORD-20261027-CZTMEL kẹt chờ nạp / sẵn sàng phóng nhiều ngày (không có hạn tự đóng sau khi đã tiếp nhận); DRONE-05, LR-DRN-05 `IN_FLIGHT` không có nhiệm vụ; các đơn `DROP_REPORTED` cũ (8P2CM8, RLC58R, BGFB6L, E2M5XP) vẫn `AWAITING_DISPATCH`; ORD-SND-0009 giữ box 12 (§ 3 #11).

Trên điện thoại:
- ⚠️ Một lần script đăng nhập gõ nhầm vào **ô tìm kiếm TikTok** và đã mở trang kết quả (có thể chứa `kiosk1@gmail.com` / `45678`) — nên xóa lịch sử tìm kiếm TikTok.
- Ảnh test (ảnh đen, ảnh bàn làm việc) có thể còn trong thư viện ảnh.

## 7. Đề xuất ưu tiên sửa

1. Đóng vòng bồi thường: payment duyệt phiếu chi → báo `PAID` cho sự cố (hoặc admin có nút "Xác nhận đã chi"); sự cố tự `RESOLVED` khi không còn việc (§ 3 #1, #4, #5).
2. Thực hiện `refundShippingFee` (tạo khoản hoàn phí giao riêng), không đổi `paymentStatus` đơn khi chỉ chi bồi thường; viết lại lý do phiếu: tỷ lệ thực, giá trị khai báo, tình trạng kiện, phương án, định dạng `150.000đ` (§ 3 #2, #3).
3. Thỏa thuận riêng: bắt buộc nội dung thỏa thuận (hiện cho khách), validate ít nhất một hành động, hoặc cho admin đóng sự cố với ghi chú (§ 3 #4).
4. Rule 200 m: chặn ngay theo khoảng cách nơi gửi → tủ nhận, làm mờ tủ dưới 200 m trên app (§ 3 #6).
5. Điều phối KTV: bỏ KTV vị trí cũ / ngoài bán kính khỏi lời mời; đăng xuất phải tắt ca (§ 3 #8, #9).
6. Drone: hủy/thất bại với lý do "Drone lỗi" ⇒ FAULT + tạo phiếu kiểm tra; ghi nhật ký và báo khách khi đổi tủ bay (§ 3 #7, #10).
7. Sửa câu chữ luồng cũ (ô gửi, "dừng trước khi cất cánh", "bỏ vào tủ gửi") và nút "Đặt lại đơn" cho đơn drone (§ 4).

## 8. Đã sửa — nhánh `fix/f1-g11-sua-loi-test-drone-2910` (backend, mobile, frontend, docs)

Local, **chưa commit / PR / deploy**. Test: order-service 457 test (0 lỗi, 6 bỏ qua; đã chạy cả test Postgres/Testcontainers), payment-service 99, mobile `flutter test` 749 (gồm 4 test mới), `flutter analyze` không thêm cảnh báo ở file đã sửa, web admin `tsc -b` sạch + ESLint 0 lỗi. **Chưa thử lại trên điện thoại / production.**

| # § 3 | Trạng thái | Đã sửa thế nào | Vị trí |
|---|---|---|---|
| 1 | ✅ | Admin duyệt / từ chối phiếu `RF-CMP-…` ⇒ payment-service gọi `POST /internal/drone-incidents/{mã}/compensation` (PAID / PAYMENT_FAILED). Sự cố tự RESOLVED khi không còn giao lại / chi trả dở (hàm chung `resolveIfSettled`), kiện → `COMPENSATED` | `payment-service/…/client/DroneIncidentClient.java`, `PaymentService` (`notifyIncidentCompensation`), `order-service/…/DroneParcelIncidentService.java` |
| 2 | ✅ | `refundShippingFee` ⇒ phí giao hoàn bằng phiếu hoàn đơn thường riêng; phiếu bồi thường không còn đổi `paymentStatus` đơn (bỏ khỏi `orderRefundStatus`, `refundableAmount`, kiểm "đã hoàn" của `refundOrder`) | `PaymentService.createCompensationRefund`, `orderRefundStatus` |
| 3 | ✅ | Lý do do order-service dựng: phương án, tình trạng kiện (hư hại nhẹ/nặng, thất lạc), số tiền + **tỷ lệ thực** trên giá trị khai báo, hoàn phí giao, lý do vượt mức, nội dung thoả thuận; định dạng `150.000đ`. Phiếu hoàn đơn huỷ nêu lý do (giao không hoàn tất: … / huỷ trước khi bay: … + ghi chú) | `PaymentIncidentCompensationGateway.compensationReason`, `DroneRefundService.refundReason` |
| 4 | ✅ | Phương án có `resolutionNote` (Flyway order **V35**), bắt buộc với thỏa thuận riêng (`RESOLUTION_NOTE_REQUIRED`; web admin cũ gửi qua `overrideReason` vẫn dùng được); khách thấy "Nội dung: …"; đồng ý mà không còn việc ⇒ RESOLVED | `DroneParcelIncidentService.propose/customerRespond`, `V35__incident_proposal_note.sql`, app `customer_drone_incident_card.dart`, web `drone-incidents/detail.tsx` |
| 5 | ✅ | Đơn giao lại COMPLETED ⇒ sau commit đóng phần giao lại của sự cố (`onRedeliveryOrderCompleted`, giao dịch riêng), kiện → `REDELIVERED`; nút admin "hoàn tất giao lại" vẫn còn | `OrderService.transition`, `DroneParcelIncidentService` |
| 6 | ✅ | Nơi gửi → tủ nhận dưới `drone-min-route-meters` ⇒ `DRONE_ROUTE_TOO_SHORT` ngay ("Tủ nhận chỉ cách điểm lấy hàng N m…"), không tìm tủ bay xa hơn. App hiện câu này ở mục "Lộ trình và phí". Chưa làm mờ tủ dưới 200 m trong danh sách chọn tủ | `DroneSourceLockerSelector.select` |
| 7 | ✅ một phần | Huỷ trước khi bay lý do "Drone lỗi" ⇒ drone `RESERVED → FAULT` (locker-service tự mở phiếu lỗi); báo thất bại chọn "Drone lỗi" ⇒ lưu `DRONE_FAULT`. Đường thất bại khi bay vốn đã tạo phiếu lỗi tự động — phiếu không hiện ở tab Sự cố của KTV phụ trách: chưa kiểm | `DroneOrderMaintenanceService.cancel`, app `maintenance_home_page.dart` |
| 8 | ✅ | Chỉ mời KTV trong `drone-max-pickup-meters`; KTV vị trí mới vừa bỏ lời mời thì chờ hết thời gian chờ, không rơi về KTV vị trí cũ. KTV ra ca được đặt `onDuty = false` trước khi trả lời mời đang treo, để người vừa ra ca không chặn việc mời dự phòng | `DronePickupService.offerNext` |
| 9 | ✅ | Đăng xuất KTV tủ / KTV drone tắt ca trên server trước (ca KTV + ca nhận việc lấy hàng) | app `technician_session.dart` (`endTechnicianShiftQuietly`), `maintenance_home_page.dart`, `technician_profile_page.dart` |
| 10 | ❌ không phải lỗi | Rà lại: #142 được chọn tủ bay S5.02 **ngay lúc đặt** (tủ demo khi đó không còn drone dùng được); form đặt đơn hiện "Tủ bay do hệ thống chọn". Đổi tủ bay giữa chừng (`reselectSource`) đã có nhật ký + báo KTV | — |
| 11 | chưa sửa | Dữ liệu: ORD-SND-0009 giữ box 12. Cần đối soát dữ liệu, không sửa code | — |
| 12 | chưa sửa | Giữ mốc chặn đầu tiên khi lý do đổi có thể là chủ ý (tính tổng thời gian bị chặn) — cần chủ dự án quyết | `DroneDeliveryBlockService.review` |

UI (§ 4) đã sửa:
- Khách: thẻ đầu trang theo ngữ cảnh — "Đơn drone đã đóng" (đơn đóng sau khi đã bay), "Chờ thanh toán", "Sẵn sàng phóng" (mission `READY_TO_LAUNCH`); câu chặng chờ điều phối thành "Sau khi thanh toán, hệ thống tìm…"; câu chặng rơi kiện không còn "sẽ gửi phương án"; mốc "Kiện đã được bỏ vào tủ gửi" → "Kỹ thuật viên đã nhận kiện tại nơi gửi" (backend `OrderDetailViews`) và "KTV nhận kiện lúc" (app); ẩn "Đặt lại đơn" cho đơn drone; "Tôi đã lấy đồ — hoàn tất" hỏi xác nhận; bỏ lặp "giao lại miễn phí"; "Tình trạng kiện" kèm mức hư hại; nhãn "Thỏa thuận riêng"; ẩn nút "Chỉ đường tới drone tại tủ bay" với khách; hộp huỷ bỏ câu "ô drone ở hai tủ".
- KTV drone: hộp xác nhận lấy hàng tự lấy GPS rồi thử lại khi `DRONE_PICKUP_LOCATION_STALE`, giữ mã/ảnh/dấu kiểm; bấm chữ để tick; hộp "Huỷ trước khi bay" nói rõ hoàn tiền + trả kiện; thẻ trả kiện ghi "giao không hoàn tất" khi chưa cất cánh; hộp trả kiện bỏ câu "Ô gửi còn giữ"; nhãn "Tủ nhận khách đã chọn"; hộp báo rơi kiện nói rõ vị trí ước theo tuyến bay.
- KTV tủ: banner và tab "Thu hồi kiện" đếm theo `recoveryStatus` (bỏ nhiệm vụ đã đóng / đã xác minh không tìm thấy).
- Web admin: "Phiên bản" đọc `version` (trước hiện `undefined`); hiện "Nội dung gửi khách".

Chưa làm: làm mờ tủ dưới 200 m / trạm tạm dừng trong danh sách chọn tủ, form tự tính lại khi trạm mở lại, các mục chập chờn (danh sách KTV rỗng, "Lỗi kết nối máy chủ"), sheet KTV tủ tự làm mới sau admin xác minh, ảnh báo rơi kiện vào phiếu kiểm tra, admin web responsive, dữ liệu kẹt § 6.

**Thứ tự deploy:** backend (order-service có Flyway **V35** + payment-service) trước — app/web cũ vẫn chạy (`resolutionNote` tuỳ chọn, payment còn nhận tham số `percentage`); rồi mobile và web admin. Sau khi deploy: 3 sự cố DPI-136, DPI-141, DPI-142 đang kẹt không tự đóng (callback chỉ chạy cho phiếu duyệt sau deploy) — cần xử lý tay.

**Test lại sau deploy:** xem [2026-10-29-retest-admin-roi-kien-sau-sua](2026-10-29-retest-admin-roi-kien-sau-sua.md) — #1, #2, #3 đã chạy đúng trên production; #4, #5 chưa kiểm xong.
