# 2026-10-28 — Test luồng giao hàng drone trên điện thoại thật và lỗi phát hiện

Người làm: binhtntse182370 (cùng Claude Code). Thời gian test: 27/10/2026 22:16 → 28/10/2026 09:16 (có Pi drone + Pi tủ TU01 từ 08:40).
Mốc code đã rà: backend `main` @ `b9cc092`, mobile `main` @ `5baed0b` (app `1.0.0+2`), frontend `main` @ `58a0886`.
Môi trường: production `https://api.locker-drone.tech`, điện thoại OPPO CPH2473 (Android, màn 720×1612, cỡ chữ hệ thống 1.15).

Báo cáo này chỉ ghi nhận lỗi, **chưa sửa code**. Mức độ: 🔴 nghiêm trọng (sai tiền, bảo mật, kẹt đơn, crash) · 🟠 sai logic / hiển thị sai · 🟡 UI.

## 1. Tóm tắt

| Luồng | Vai trò | Kết quả |
|---|---|---|
| Đặt đơn → thanh toán → lấy hàng → cân lệch → trả phụ thu → phóng → vào tủ → PIN → mở ô → hoàn tất | Khách, KTV drone | ✅ Chạy hết (sau khi tắt chế độ ArUco trong phòng — § 3) |
| Validate form đặt đơn, ngoài tầm bay, tủ offline, từ chối quyền vị trí | Khách | ✅ |
| Chuyển khoản thiếu | Khách | ⚠️ Chạy nhưng không phản hồi — § 4.1 #5 |
| Khách huỷ đơn chưa bay | Khách | ✅ |
| KTV từ chối lời mời lấy hàng | KTV drone | ✅ |
| Rơi kiện: báo rơi → phiếu kiểm tra drone → thu hồi → admin xác minh → bàn giao Hub → khách yêu cầu xem xét → phương án 2 → khách đồng ý → duyệt bồi thường | KTV drone, KTV kiosk, admin, khách | ⚠️ Chạy tới duyệt bồi thường, **app crash** khi KTV kiosk gửi kết quả thu hồi |
| Giao lại miễn phí sau rơi kiện | KTV drone | ❌ Kẹt: đơn giao lại không KTV nào thấy — § 4.1 #2 |
| Thời tiết xấu theo từng trạm (khách đặt, KTV xem thời tiết, KTV phóng, KTV huỷ vì thời tiết) | Khách, KTV drone | ✅ Chặn đúng; còn lỗ hổng thông báo và hiển thị — § 6 |
| Không có KTV nhận đơn trong 120 phút | Hệ thống | ✅ Tự đóng đơn, tạo yêu cầu hoàn tiền |
| Phần cứng thật: khách mở ô TU01, giao hàng ArUco với Pi drone + Pi tủ, báo chuyến bay thất bại | Khách, KTV drone | ⚠️ Mở cửa ô cho khách chạy thật; **nắp trượt không chạy**, đơn kẹt ARRIVED tới khi KTV báo thất bại — § 7 |
| Admin | Admin | Dùng web (đúng thiết kế). Các bước admin trong luồng rơi kiện được gọi qua đúng API mà web dùng, sau khi đăng nhập có OTP |

Tài khoản dùng: khách `minhanh.tran@gmail.com`, KTV drone `ktvdronedemo@gmail.com` và `ktvdronedemo2@gmail.com`, KTV kiosk `kiosk1@gmail.com`, admin `binhtntse182370@fpt.edu.vn`.

## 2. Đơn và dữ liệu đã tạo / thay đổi trên production

| Đơn | Mục đích | Trạng thái cuối | Còn chiếm |
|---|---|---|---|
| ORD-20261027-8BLSUN (#120) | Happy case + cân lệch | Hoàn tất | — |
| ORD-20261027-Z0YD9K (#121) | Thử báo rơi ở chặng "Đã đến tủ" | Chờ nhận hàng | **Ô drone số 2 tủ demo capstone** (tủ này hết ô drone) |
| ORD-20261027-9I4GMY (#122) | Khách huỷ | Đã huỷ, chờ admin duyệt hoàn 2.000đ | — |
| ORD-20261027-WZ5EQQ (#123) | Thử báo rơi lần 2 | Chờ nhận hàng | Ô 1 tủ Vinhomes S1.02 |
| ORD-20261027-RI79MQ (#124) | Rơi kiện | Đã huỷ, sự cố `DPI-124-1793118887300` đang `RESOLUTION_IN_PROGRESS`, bồi thường 2.000đ `PROCESSING` | — |
| ORD-20261027-CZTMEL (#125) | Đơn giao lại tự sinh | Chờ điều phối, **mồ côi** | Một drone `RESERVED` (DRONE-02), ô 2 tủ Vinhomes S1.02 |
| ORD-20261027-DZJPU6 (#126) | Đặt khi trạm vừa tạnh | Tự đóng sau 120 phút không có KTV, chờ admin hoàn 2.000đ | — |
| ORD-20261028-HICI4P (#127) | KTV phóng khi trạm nhận mưa → huỷ trước khi bay | Đã huỷ, chờ admin hoàn 2.000đ, kiện đã trả | — |
| ORD-20261024-367RYV (#116) | Khách mở ô #3 TU01 (tủ thật) | Hoàn tất (cửa ô thật đã mở) | — |
| ORD-20261028-P7NGPK (#128) | Giao ArUco thật tới TU01 ô #3 → báo chuyến bay thất bại | Đã huỷ, chờ admin hoàn 2.000đ, kiện đã trả | — |

Khác:
- Cấu hình `app.drone.demo.indoor-aruco-enabled`: `true` → `false` (để đi tiếp luồng khi chưa có phần cứng) → **`true`** lại khi test với Pi thật (28/10 08:40). Hiện là `true`.
- **DRONE-S550-07 (drone có Pi thật) đang `FAULT`** sau khi báo chuyến bay thất bại; cần admin kiểm tra và đưa về `IDLE` trước khi dùng lại.
- Trên điện thoại: đã bật Bluetooth, cấp lại quyền "Thiết bị ở gần" cho app (trước đó tôi từ chối để test). App đang là bản debug build từ `main` trỏ production.
- Phiếu `RPT-37` (kiểm tra DRONE-TEST sau rơi kiện) đã "Đã xong"; DRONE-TEST còn `returnFlightStatus = MANUAL_INTERVENTION_REQUIRED`.
- Đơn cũ ORD-20261024-367RYV (kẹt "Drone đã đến tủ" từ 24/10) tự nhảy sang "Sẵn sàng nhận hàng" ngay sau khi tắt ArUco.

## 3. Chế độ "Indoor ArUco demo" chặn luồng

Khi `app.drone.demo.indoor-aruco-enabled = true`, drone giả lập dừng ở `APPROACHING` cho tới khi **camera thật** nhận ra mã ArUco của ô đích, rồi chỉ sang `READY_FOR_PICKUP` khi nắp tủ báo đã đóng (`backend/order-service/.../service/DroneDeliverySimulator.java:49-51`). Lúc test camera gateway `UNAVAILABLE` nên đơn đứng mãi ở "Drone sắp đến" (theo dõi 23:01 → 23:08), không có timeout, không báo gì cho khách hay KTV. Tắt cấu hình thì đơn đi tiếp ngay.

## 4. Lỗi phát hiện

### 4.1 🔴 Nghiêm trọng

| # | Lỗi | Tái hiện | Bằng chứng / nghi vấn |
|---|---|---|---|
| 1 | **App crash (màn đỏ)** khi KTV kiosk bấm "Gửi Admin xác minh" kết quả thu hồi kiện. Server vẫn lưu (200) | Tab "Thu hồi kiện" → nhiệm vụ → Ghi nhận kết quả → đủ GPS, ghi chú, ảnh → Gửi | `Failed assertion: '_dependents.isEmpty'`. Nghi do dispose `photos`/`note` ngay khi `showModalBottomSheet` trả về, lúc animation đóng còn chạy: `mobile/lib/features/maintenance/presentation/widgets/drone_recovery_queue.dart:919-920` (chưa có stack trace) |
| 2 | **Đơn giao lại sau rơi kiện bị mồ côi**: tự giữ drone + ô tủ, mission `AWAITING_LOADING` nhưng không gán KTV; mọi KTV drone gọi chi tiết đều nhận `DRONE_MISSION_NOT_ASSIGNED_TO_USER`, đơn không hiện ở danh sách nào | Khách đồng ý phương án có giao lại | `backend/order-service/.../service/OrderIncidentRedeliveryGateway.java` (~dòng 107–150). `mission.setAssignedByUserId(customerUserId)` lại ghi id **khách** |
| 3 | **Admin đăng nhập mobile không cần OTP**: `POST /api/auth/login` vẫn cấp token `ADMIN` hạn 24 h chỉ với mật khẩu; web dùng `/api/admin/auth/login` mới có 2FA | Đăng nhập admin trên app | `backend/auth-service/.../service/AuthService.java:148-158` |
| 4 | **App KTV báo sai tiền phụ thu cân lệch**: hộp nạp hàng ghi "trả thêm 7.000đ", server chốt 3.000đ | Đơn khai 1 kg, dùng 4.000 điểm, cân 1.200 g | App: `phí(cân thật) − tổng đã trả sau điểm` (`mobile/lib/core/config/business_config.dart:750`). Server: `phí(cân thật) − phí(khai báo) − đã thu` (`DroneOrderMaintenanceService.java` `applyWeightSurcharge`) |
| 5 | **Chuyển khoản thiếu không phản hồi**: giả lập chuyển 2.000/4.000đ, sheet vẫn "cần chuyển 4.000đ"; giả lập tiếp báo "giao dịch đang COMPLETED". Phải đóng mở lại mới thấy còn thiếu 2.000đ | Sheet VietQR → Giả lập → nhập số nhỏ hơn | `mobile/lib/features/locker_ops/presentation/widgets/sepay_payment.dart` (`simulate` chỉ gọi `checkNow`, không làm mới số còn thiếu) |
| 6 | **Đơn kẹt không timeout**: ORD-…-367RYV kẹt "Drone đã đến tủ" 3 ngày (tủ TU01 mất kết nối + ArUco), khoá luôn `ktvdronedemo` không được mời việc mới | — | § 3 |
| 7 | **Xác nhận "Đã lấy hàng" không kiểm tra vị trí**: KTV cách điểm lấy 15,9 km vẫn xác nhận được (nhật ký có ghi khoảng cách nhưng không chặn) | — | |
| 8 | **Báo rơi kiện chỉ nhận ở chặng đầu chuyến**: ở "Đã đến tủ" server trả 409 `DRONE_DROP_NOT_REPORTABLE`, app **không hiện lỗi**, bấm Xác nhận như không có gì | Mở chi tiết nhiệm vụ đơn đang ở ARRIVED → Báo rơi kiện | Lỗi nằm trong SnackBar của Scaffold phía sau dialog: `mobile/lib/features/maintenance/presentation/widgets/drone_journey_camera_panel.dart:344-352` |
| 9 | **Việc thu hồi giao cho KTV đang bị "Hạn chế nhận việc"** (kiosk1 có 3 phiếu trễ SLA, app ghi "Tạm ngưng phân công mới") | — | |
| 10 | **Bồi thường không chặn theo trần**: `compensationCap = 0` nhưng `suggestedCompensation = 1.200đ`; admin đề xuất 1.200đ được chấp nhận không cần `overrideReason` | `POST /api/admin/drone-incidents/{id}/proposals` | `DroneParcelIncidentService.java:502-533` |
| 11 | **Hai đơn cùng giữ một ô**: ORD-20261024-RLC58R và ORD-20261015-3TG2TW đều có `reservedBoxId = 800058` | `GET /api/admin/drone-orders` | Chưa tìm nguyên nhân |
| 12 | **Tắt chế độ ArUco làm đơn "giao xong" giả**: ORD-…-367RYV đang chờ ArUco ở TU01 tự nhảy sang "Sẵn sàng nhận hàng", gửi PIN cho người nhận, trong khi kiện chưa từng vào tủ | Tắt `indoor-aruco-enabled` khi có đơn đang chờ ArUco | Bộ giả lập đẩy chặng bất kể phiên giao chưa xong |
| 13 | **Ô bị giữ vô thời hạn**: ORD-20261024-8P2CM8 `DROP_REPORTED` từ 24/10 giữ ô DRONE #2 của TU01; TU01 chỉ có 2 ô DRONE nên tủ thật gần như luôn hết ô | — | |

### 4.2 🟠 Sai logic / hiển thị sai

**Khách hàng**
- Đơn chưa thanh toán: màn theo dõi vẫn ghi "Hệ thống đang tìm KTV" và trạng thái "Đang giao bằng drone"; đóng sheet mà không trả vẫn hiện "Đang chờ xác nhận thanh toán".
- "Phí giao drone" hiển thị số sau khi trừ điểm (4.000đ) thay vì phí gốc (8.000đ).
- Phụ thu: thời điểm thanh toán gốc 22:37 bị ghi đè thành 22:59; lúc chờ trả phụ thu timeline ghi "Thanh toán: Chưa diễn ra"; trang chủ chỉ ghi "Đã tiếp nhận", không báo đang nợ phụ thu.
- Chi tiết đơn tủ: "Thời gian thanh toán" từng lần là giờ **tạo** giao dịch, không phải giờ tiền về.
- Đơn rơi kiện: ghi "Đơn đã dừng **trước khi drone cất cánh**" (sai — rơi lúc bay); chữ đỏ "Chưa ghi nhận được yêu cầu hoàn tiền — vui lòng liên hệ hỗ trợ" dù phương án là giao lại + bồi thường; đơn biến khỏi "Đơn đang xử lý" dù bồi thường chưa xong.
- "Yêu cầu xem xét" với lý do trống: dialog đóng, không báo, không gửi.
- Mở ô:
  - Từ chối quyền Bluetooth thì app hỏi lại ngay; từ chối lần 2 báo "Chưa phát hiện sóng Bluetooth" thay vì "thiếu quyền".
  - Quyền đã bị đánh dấu "không hỏi lại" thì app không hướng dẫn mở Cài đặt — khách kẹt ở "Chưa phát hiện sóng".
  - Bluetooth điện thoại đang **tắt** thì app cũng chỉ báo "Chưa phát hiện sóng", không nhắc bật Bluetooth.
  - Tủ báo "không phản hồi lệnh mở" nhưng khách vẫn bấm "Tôi đã lấy đồ" để hoàn tất được.
  - (Nút "Mô phỏng RPi" chỉ hiện ở bản debug — `kDebugMode`, `mobile/lib/features/locker_ops/presentation/widgets/locker_unlock_modal.dart:606` — không phải lỗi bản phát hành.)
- Danh sách và dropdown chọn tủ nhận **không hiện thời tiết từng trạm**: trạm đang mưa trông như trạm bình thường, khách chỉ biết sau khi chọn và chờ báo giá. Dropdown còn lẫn tủ test ("test tu") và tủ "Chưa có bãi đáp drone".
- Danh sách đơn: đơn tự đóng vì không có KTV hiện nhãn **"FAILED"** tiếng Anh, tô màu xanh lá như đơn thành công.
- Nút "Báo ô lỗi" hiện khi kiện chưa vào ô; khách thấy "Chỉ đường tới drone tại tủ bay" (việc của KTV).
- Tên chặng không thống nhất: trang chủ "Chờ điều phối", màn theo dõi "Chờ kỹ thuật viên nhận lấy hàng"; thẻ ghi "Từ 22:37:33" nhưng timeline tính từ 22:33; nhãn "Bỏ kiện vào ô gửi lúc" mâu thuẫn với luồng nạp thẳng lên drone.

**KTV drone**
- Đăng xuất ghi "kết thúc ca" nhưng đăng nhập lại vẫn "ĐANG TRONG CA"; không cảnh báo khi đang giữ đơn.
- GPS ghi "Hoạt động" dù lần cập nhật cuối là 24/10.
- Công tắc "Chưa vào ca lấy hàng" tắt mà vẫn nhận lời mời; dòng "đang bận một việc nên chưa được mời thêm" nằm ngay trên lời mời mới.
- Header "1 drone đang bay" nhưng ô "Đội bay" = 0.
- Lời mời ghi "Đang gặp sự cố: Bãi đáp drone không sẵn sàng" mà vẫn cho bấm "Nhận lấy hàng".
- Gán drone: mặc định chọn DRONE-02 pin 41 % khi có drone 100 %; LR-DRN-06 vẫn 57 % sau một chuyến.
- Lấy hàng nhập sai mã: dialog tự đóng, mất ảnh và các ô đã tick.
- Phiếu kiểm tra sau rơi kiện (RPT-37): "Nghiệm thu" khi trống kết quả, không ảnh, không ghi chú vẫn thành "Đã xong".
- Khi mở lại app từ nền (và lần đầu sau khi cài mới), header có lúc hiện nút "Quay lại" bấm không tác dụng và mất nút Đăng xuất.
- Sau khi đã cấp quyền vị trí ở hộp thoại hệ thống, bảng giải thích "Quyền truy cập vị trí" vẫn hiện lại, phải bấm "Cho phép" thêm một lần.
- Lời mời lấy hàng hết hạn khi KTV đang đổi tài khoản / mở app muộn ⇒ KTV bị "nghỉ" 10 phút (`REOFFER_COOLDOWN_MINUTES`), app không cho biết vì sao không nhận được lời mời. KTV "trong ca" nhưng tắt app cả đêm vẫn bị mời lặp mỗi 3 phút cho tới khi đơn tự đóng sau 120 phút.
- Hộp "Báo chuyến bay thất bại" và "Hủy trước khi bay": lý do mặc định chọn sẵn là "Thời tiết xấu"; không có lý do "Tủ nhận / nắp trượt không mở".
- Sau "Báo chuyến bay thất bại", drone chuyển `FAULT` ("cho tới khi bạn kiểm tra xong") nhưng **không tạo phiếu kiểm tra** (tab Sự cố = 0) và KTV không phụ trách drone thì không có màn hình nào để kiểm tra / đưa drone về sẵn sàng. `faultReason` trộn Anh–Việt: "Delivery of order … failed: Lý do khác".
- Gán drone: DRONE-S550-07 hiện "100%" trong khi Pi drone báo `batteryPercent = null` (MAVLink chưa kết nối) — số pin tĩnh, trái quy tắc "chưa biết pin thì làm mờ".
- Đăng nhập có lúc trả 503, app hiện nguyên "Service Unavailable" (thử lại thì được).

**KTV kiosk (thu hồi kiện)**
- Cách điểm rơi ~16 km vẫn gửi kết quả được (chỉ cảnh báo); cho chọn ảnh từ thư viện cho "ảnh thật hiện trường"; gửi khi thiếu ảnh không báo gì.
- Bàn giao Hub một chạm, không hộp xác nhận; sau khi admin đã xác minh vẫn ghi "Admin sẽ xác minh…".
- Tab "Thu hồi kiện" là tab thứ 6, khuất ngoài màn, phải cuộn thanh tab mới thấy.
- Màn KTV kiosk thấy TU01 "7 ô" nhưng chỉ đếm STANDARD 5 + XL 1.

**Nhật ký**
- Đơn 367RYV có dòng "Chưa gửi được email báo đơn đã phóng cho người gửi và người nhận."

### 4.3 🟡 UI

- Tràn layout (debug): màn chọn điểm lấy hàng khi mở bàn phím + có gợi ý "BOTTOM OVERFLOWED BY 29 PIXELS" (`mobile/lib/features/drone_delivery/presentation/pages/pickup_location_picker_page.dart`); nhãn "Kiện nặng hơn khai báo · chờ khách trả thêm phí" "RIGHT OVERFLOWED BY 13 PIXELS" (`mobile/lib/features/locker_ops/presentation/pages/maintenance_home_page.dart:3818`).
- Chữ bị bóp ở cỡ chữ 1.15 / 360 dp: mã đơn vỡ 3 dòng ở thẻ "Đơn đang xử lý"; màn KTV mã đơn ngắt giữa chữ, header cố định chiếm ~45 % màn, tên/SLA bị cắt, nút "Nhận lấy hàng" xuống 2 dòng; ô PIN thứ 6 bị cắt nửa; tên KTV kiosk thành "ky thua…".
- Lỗi "Cần chụp ảnh kiện" gắn dưới ô Mã lấy hàng, bị cắt và không tự mất sau khi đã chụp.
- Nút "Thử lại" ở khung camera chữ xanh đậm trên nền đen; sheet thanh toán tràn lên thanh trạng thái; chip đã chọn (khối lượng, loại hàng) nhạt hơn chip chưa chọn; nút "Xác nhận nạp" thụt lệch so với "Hủy trước khi bay".
- Lộ chuỗi tiếng Anh / mã thô: "Service Unavailable", "FAILED", lý do huỷ "Weather" trong nhật ký đơn, "Invalid credentials", "UNAVAILABLE", "COMPLETED", "DEPARTED → EN_ROUTE", "Customer completed pickup", "Redelivery requested", `PICKUP_ASSIGNED`, `PICKED_UP`, `ASSIGNED / ACCEPTED / SEARCHING / SUBMITTED / VERIFIED / FOUND / CLOSED / RETURNED TO HUB`, `FLIGHT_PATH`, "sai số không rõ m", mã chính sách "INCIDENT-b6c4fa9a", giờ "10:27 PM".
- Định dạng không đồng nhất: "1.200 ₫" và "1.200đ"; "26600 điểm" thiếu dấu phân cách; "1.7 km" và "1,7 km".
- Form đặt đơn báo lỗi bằng SnackBar từng lỗi một, không cuộn tới ô lỗi.
- Tủ mất kết nối vẫn ghi màu xanh "Còn 2 ô drone nhận trống".

### 4.4 ⚙️ Hiệu năng

- Màn đặt đơn gọi `GET /api/lockers/{id}/layout` **131 lần trong ~5 phút**: tải lại layout mọi tủ mỗi 20 s kể cả khi socket vẫn sống (`mobile/lib/features/drone_delivery/presentation/pages/drone_booking_page.dart:71`, `:220`).
- Mỗi lần mở sheet thanh toán gọi `POST /api/payments/checkout` 2 lần; API báo giá cũng gọi 2 lần.

## 5. Chạy đúng

- Đặt đơn: chặn tủ offline và tủ ngoài tầm 5 km (thông báo rõ, khoá nút); validate SĐT, email, kích thước khoang 30×25×20, giá trị ≤ 2.000.000đ, ô cam kết hàng cấm; phí đổi theo khối lượng; điểm thưởng tối đa 50 %; voucher không đủ điều kiện bị làm mờ; từ chối quyền vị trí vẫn nhập tay / tìm địa chỉ được.
- Thanh toán giả lập, cộng dồn nhiều lần đúng tổng; lịch sử từng lần ghi rõ "Chuyển thiếu: nhận 2000 đ / cần 4000 đ".
- KTV: server chặn mã lấy hàng sai; checklist nạp bắt buộc; nút Phóng khoá tới khi khách trả phụ thu; drone đang bay / bảo trì bị làm mờ khi gán.
- Rơi kiện: tự tạo phiếu kiểm tra drone, tự giao việc thu hồi, khách thấy trạng thái sự cố và phương án, yêu cầu xem xét / đồng ý đều chạy, có hộp xác nhận rõ.
- Khách huỷ đơn chưa bay: hộp xác nhận nêu rõ số tiền hoàn và điều kiện.

## 6. Thời tiết xấu (unhappy case)

### 6.1 Thiết kế hiện tại (đọc code)

| Điểm | Hành vi | Bằng chứng |
|---|---|---|
| Ngưỡng "không an toàn" | Có mưa (> 0 mm hoặc mã WMO mưa/dông), gió > 30 km/h, giật > 40 km/h, tầm nhìn < 1.500 m trong 30 phút tới, lấy mẫu dọc tuyến nơi gửi → tủ bay → tủ nhận | `backend/order-service/.../service/DroneWeatherService.java:72-74`, `:344-348` |
| Nguồn | Open-Meteo, dự phòng MET Norway; cả hai lỗi ⇒ `UNAVAILABLE` (cũng chặn) | `DroneWeatherService.java:37` |
| Báo giá | Trả kèm đánh giá, **không** chặn | `DroneOrderBookingService.java:77-91` |
| App đặt đơn | Khung "Thời tiết tuyến bay: Tạm ngưng bay" + lý do; **khoá nút "Tạo đơn"** khi `weatherSafe == false` | `mobile/.../drone_booking_page.dart:1055`, `:1408-1495` |
| Tạo đơn | Server kiểm lại, ném `DRONE_WEATHER_UNSAFE` / `DRONE_WEATHER_UNAVAILABLE` trước khi giữ ô | `DroneOrderBookingService.java:121-128` |
| Phóng | Kiểm lại tuyến tủ bay → tủ nhận, chặn bằng mã trên | `DroneOrderMaintenanceService.java:224`, `:250-279` |
| Admin "Tạm dừng bay" | Chặn báo giá + tạo đơn; đơn đang chờ bị gắn sự cố lý do `WEATHER`, quá 30 phút (`drone-blocked-timeout-minutes`) thì tự đóng | `DroneDeliveryBlockService.java:194-197`, `:168-172` |

**Trả lời câu hỏi "thời tiết xấu có đặt đơn được không":** không. App khoá nút ngay từ báo giá, và nếu thời tiết đổi trong lúc khách đang điền form thì server vẫn từ chối khi tạo đơn.

### 6.2 Cách giả lập "thời tiết xấu theo từng trạm"

Lúc test cả 10 tủ đều trời quang và ngưỡng là cấu hình khởi động (`@Value`), không đổi được lúc chạy. Không dùng "Tạm dừng bay" vì cờ này dừng **toàn hệ thống**, trong khi yêu cầu là thời tiết theo **từng trạm**.

Cách làm: một proxy chạy trên máy test (không deploy, không commit) đứng giữa app và production. Proxy chuyển nguyên mọi request, chỉ sửa phần `weather` của các tủ trong danh sách "đang mưa" thành `UNSAFE` (mưa 2,4 mm, giật 38 km/h, đúng câu thông báo server sinh ra). Với tạo đơn và phóng tới tủ đang mưa, proxy trả đúng lỗi server (`409 DRONE_WEATHER_UNSAFE`). App debug được build tạm trỏ vào proxy qua `adb reverse`, test xong đã build lại bản trỏ production; `env_config.g.dart` đã hoàn nguyên.

Trạm "mưa" dùng: Tủ Nhà Văn hóa Sinh viên ĐHQG (800007), sau đó thêm/bớt Vinhomes S1.02 (800006). Các trạm còn lại giữ thời tiết thật.

### 6.3 Kết quả trên điện thoại

| # | Tình huống | Kết quả |
|---|---|---|
| 1 | Khách chọn tủ nhận đang mưa (ĐHQG) | ✅ Khung "Thời tiết tuyến bay: Tạm ngưng bay", nêu lý do, nút "Tạo đơn" **bị khoá** |
| 2 | Đổi sang tủ trời tốt (S1.02) | ✅ "Đủ điều kiện", nút mở |
| 3 | Đang điền form thì S1.02 chuyển mưa, bấm Tạo đơn | ✅ Server từ chối, SnackBar "Không thể đặt chuyến bay: có mưa hoặc dông…" ; bấm làm mới thời tiết thì khung đỏ và khoá nút |
| 4 | Trời tạnh, làm mới | ✅ Mở lại nút, tạo đơn được |
| 5 | Đơn đã trả tiền, tủ nhận chuyển mưa — màn theo dõi của khách | ✅ Khung "Không an toàn để bay" — nhưng thẻ trạng thái vẫn "Chờ kỹ thuật viên nhận lấy hàng", không nói đơn sẽ bị trễ / xử lý ra sao |
| 6 | KTV xem "Thời tiết tại các tủ drone" | ✅ Đúng từng trạm ("2/10 tủ đang không bay được", ĐHQG đỏ, các trạm khác xanh) — nhưng xếp theo tên, trạm xấu không lên đầu |
| 7 | KTV nạp hàng xong, tủ nhận đang mưa, bấm **Phóng** | ✅ Bị chặn, SnackBar "Không thể **đặt** chuyến bay…" (câu dành cho khách đặt đơn, sai ngữ cảnh phóng). Thẻ đơn không cảnh báo trước, nút Phóng vẫn xanh |
| 8 | KTV **Hủy trước khi bay** lý do "Thời tiết xấu" | ✅ Đơn huỷ, tạo yêu cầu hoàn 2.000đ, drone về `IDLE`, KTV có việc "Xác nhận đã trả kiện" — nhưng nhật ký đơn ghi lý do thô **"Weather"** |
| 9 | Admin xem thời tiết từng trạm | ✅ Web có panel "Thời tiết tại các tủ drone" theo từng trạm, tự làm mới (`frontend/fe/src/pages/Admin/drone-orders/WeatherPanels.tsx:105`). Chỉ đọc code, chưa mở web |

### 6.4 Test tự động (chạy 28/10 00:05)

- Backend `order-service`: `DroneWeatherServiceTest` 6, `DroneWeatherServiceContextTest` 1, `DroneOrderMaintenanceServiceTest` 24 (có ca phóng bị chặn `DRONE_WEATHER_UNSAFE`), `DroneOrderBookingBenefitsTest` 5 — **36 pass, 0 lỗi**. Không chạy test Postgres (cần Docker).
- Mobile: `drone_weather_panel_test`, `drone_booking_page_test` (có "tạm dừng bay: báo rõ và không cho tạo đơn"), `maintenance_home_page_test` — **31 pass**.

### 6.5 Lỗ hổng thiết kế

| # | Mức | Vấn đề |
|---|---|---|
| W0 | 🟠 | **Admin không dừng bay được theo từng trạm**: chỉ có công tắc "Tạm dừng bay" toàn hệ thống (`app.order.drone-flights-suspended`). Một trạm mưa thì hoặc dừng tất cả, hoặc trông vào kiểm tra tự động. |
| W1 | 🟠 | Thời tiết xấu **tự nhiên** không làm đơn đã thanh toán bị gắn sự cố: `DroneDeliveryBlockService.detect` chỉ xét cờ tạm dừng của admin. **Đã tái hiện (§ 6.3 #7):** lần phóng bị từ chối không được ghi vào nhật ký đơn, đơn không bị gắn sự cố, khách không được báo; đơn không có hạn tự đóng / hoàn tiền vì lý do thời tiết. |
| W6 | 🟡 | Danh sách / dropdown chọn tủ nhận của khách không hiện thời tiết từng trạm (§ 4.2). |
| W2 | 🟠 | Không kiểm lại thời tiết khi drone **đang bay**; chỉ đánh giá dự báo 30 phút lúc phóng. |
| W3 | 🟡 | Lý do chặn của "Tạm dừng bay" luôn là `WEATHER` ("Tạm dừng bay do thời tiết hoặc lệnh điều hành") kể cả khi admin dừng vì lý do khác. |
| W4 | 🟡 | Mobile chưa có test "báo giá trả `weatherSafe = false` ⇒ nút Tạo đơn bị khoá" (chỉ có test cho "Tạm dừng bay"). |
| W5 | 🟡 | Đơn giao lại sau rơi kiện được tạo không kiểm thời tiết (chỉ chặn lúc phóng) — chấp nhận được, nhưng cộng với lỗi § 4.1 #2 thì đơn này hiện không ai xử lý. |

## 7. Test với phần cứng thật (Pi drone + Pi tủ TU01), 28/10 08:40–09:16

### 7.1 Thiết bị

| Thiết bị | Định danh | Trạng thái lúc test |
|---|---|---|
| Pi tủ | gateway `2C:CF:67:DB:C5:C3`, tủ **TU01** (id 7), firmware `v1.0.0` | Online. Log tủ cho thấy rớt rồi kết nối lại lúc 02:02 UTC (09:02) |
| Pi drone | gateway `88:A2:9E:D9:FD:67` = **DRONE-S550-07** (id 9), `LockR-OS v1.2 (Bookworm)`, `http://10.3.78.45:8080` | Online, camera LIVE, MAVLink `disconnected` (không cắm autopilot) |
| TU01 | ô DRONE #2 (ArUco 0), #3 (ArUco 1), từ điển `DICT_4X4_50` | Bật lại `indoor-aruco-enabled = true` (Chế độ B) |

Trước khi test, TU01 **không còn ô DRONE trống**: #2 bị đơn kẹt 8P2CM8 giữ (§ 4.1 #13), #3 bị 367RYV giữ (§ 4.1 #12).

### 7.2 Diễn biến

| Giờ (VN) | Bước | Kết quả |
|---|---|---|
| 08:56 | Khách mở ô #3 cho đơn 367RYV trên app (bản debug: bỏ qua bước Bluetooth, lệnh vẫn đi qua server `/api/iot/unlock` → MQTT → Pi tủ) | ✅ Server trả 200 sau 9,3 s; **cửa trước ô #3 bật mở thật** (người dùng xác nhận). Đơn → Hoàn tất, ô #3 trống. ⚠️ Log tủ ghi lần mở cho khách là "Nắp trượt ô tủ đã mở thành công đón kiện hàng từ Drone" và `credentialType = PIN_OR_QR` — sai nội dung |
| 08:55 | Mở ô bằng Bluetooth thật | ❌ Không tìm thấy sóng tủ (điện thoại đã bật BT, đã cấp quyền). Chưa xác định Pi tủ có phát BLE không |
| 09:02 | Đặt đơn P7NGPK tới TU01 → giữ đúng ô #3 (ArUco 1) | ✅ |
| 09:05 | Lời mời lấy hàng hết hạn lúc đổi tài khoản; admin gán KTV2 qua `pickup/assign` | ✅ |
| 09:06 | KTV2 lấy hàng, gán **DRONE-S550-07**, nạp, phóng | ✅ Giả lập chặng tới "Drone sắp đến" rồi **dừng chờ ArUco** — đúng Chế độ B |
| 09:08 | Camera thấy mã **#17** (không phải mã ô đích) | ✅ Backend không làm gì — đúng quy tắc chỉ xét mã của ô đích |
| 09:09:16 | Đưa mã **#1** vào camera | ✅ `MARKER_DETECTED` hợp lệ → chặng `ARRIVED` → backend gửi `cabinet/7/command/open` (nắp trượt, hạn 120 s). Pi drone: `VALIDATED – Opening lid…` |
| 09:09:17 | Pi tủ trả "đã mở" **không có `lidConfirmation`** | ⚠️ Backend bỏ qua (`LID_UNVERIFIED`). **Nắp trượt không chuyển động** (người dùng xác nhận) — Pi tủ đang chạy kiểu giả lập/bypass hoặc motor chưa nối, nhưng vẫn báo thành công |
| 09:09:49 | Pi drone gửi lại `MARKER_DETECTED` | ✅ Bỏ qua vì trùng phiên |
| 09:11:17 | Hết 120 s | ⚠️ `LID_OPEN_FAILED` lý do "Tủ không phản hồi lệnh mở nắp… (mất kết nối)" — **sai**, tủ có phản hồi. Log IoT của tủ cùng lúc lại ghi "mở thành công". Đơn **kẹt ở ARRIVED**, không lệnh đóng nắp, không báo KTV/khách |
| 09:14 | KTV "Báo chuyến bay thất bại" (lý do Khác) | ✅ Đơn huỷ/FAILED, hoàn 2.000đ chờ duyệt, email hai bên, việc "Xác nhận đã trả kiện", nhả ô #3. ⚠️ DRONE-S550-07 thành `FAULT`, không có phiếu kiểm tra, KTV không có cách đưa về sẵn sàng |

### 7.3 Lỗi phần cứng / tích hợp

| # | Mức | Lỗi |
|---|---|---|
| H1 | 🔴 | **Firmware Pi tủ chưa khớp hợp đồng**: trả `LID_OPEN_RESULT` thành công mà không có `lidConfirmation`, trong khi nắp không chạy. Giao hàng ArUco **không thể hoàn tất** với TU01 hiện tại. Cần kiểm `LID_BYPASS_PHYSICAL_MOTION` trên Pi tủ, nối motor/công tắc hành trình, cập nhật firmware gửi `lidConfirmation` (`STEP_COUNT`/`LIMIT_SWITCH`) |
| H2 | 🔴 | **Lệnh mở nắp thất bại thì đơn kẹt ARRIVED vô thời hạn**: không thử lại, không đóng nắp, không báo KTV/khách; thẻ KTV vẫn ghi "Drone đã đến tủ" |
| H3 | 🟠 | Thông báo `LID_OPEN_FAILED` ghi "không phản hồi / mất kết nối" khi thực tế tủ có phản hồi nhưng không xác nhận được — dẫn KTV đi sai hướng. Log IoT tủ ghi "mở thành công" cùng thời điểm |
| H4 | 🟠 | **Firmware Pi drone cũ**: không gửi `TARGET_REQUEST`, `/api/status` không có `arucoVision.delivery`, luôn `SCANNING` kể cả khi không có nhiệm vụ (README mô tả `NO_TARGET`); log cũ có `distanceM = -0.101` (âm) vẫn được nhận |
| H5 | 🟠 | Chế độ ArUco bật toàn hệ thống: **mọi** đơn DEMO tới tủ không có camera (S1.02, ĐHQG…) sẽ dừng ở "Drone sắp đến" mãi vì chỉ DRONE-S550-07 có camera |
| H6 | 🟠 | Chế độ trong nhà cho phép "drone cầm tay": khi chỉ có một đơn DEMO đang chờ, đưa đúng mã vào camera là backend tự tạo nhiệm vụ — **bỏ qua toàn bộ bước KTV lấy hàng / nạp / phóng** (`DroneLockerCommunicationService.indoorDemoMission`) |
| H7 | 🟡 | Danh sách drone admin (`GET /api/admin/drones`) không trả thiết bị gắn kèm (`device = null` cho mọi drone) dù `GET /api/admin/drones/9/device` có; log IoT drone viết không dấu ("Bo xu ly Raspberry Pi cam nguon truc tuyen") |
| H8 | 🟡 | `GET /api/admin/iot/devices` trả 500 `INTERNAL_ERROR` |

## 8. Việc nên làm tiếp (đề xuất thứ tự)

1. § 7.3 H1–H2: cho Pi tủ chạy nắp thật + gửi `lidConfirmation`; xử lý đơn kẹt khi mở nắp thất bại. Đưa DRONE-S550-07 khỏi `FAULT`.
2. § 4.1 #2 đơn giao lại mồ côi và #1 crash thu hồi kiện — chặn luồng rơi kiện.
3. § 4.1 #3 admin đăng nhập mobile không OTP (bảo mật).
4. § 4.1 #4 tính phụ thu sai, #5 chuyển thiếu không phản hồi (tiền).
5. § 4.1 #6–#13, W0, W1 (kẹt đơn, ô bị giữ, kiểm vị trí, trần bồi thường, dừng bay theo trạm, đơn đã trả gặp trời xấu).
6. Dọn dữ liệu test ở § 2 (ô Vinhomes S1.02, ô demo capstone, DRONE-02 `RESERVED`, ô #2 TU01 do 8P2CM8 giữ).
7. Gom các chuỗi tiếng Anh / mã thô (§ 4.3) và polling layout (§ 4.4).

## 9. Chưa làm

- Giao hàng ArUco **trọn vẹn** trên tủ thật (chặn bởi H1): nắp mở → giả lập nhả hàng 30 s → đóng nắp → PIN → khách mở ô.
- Mở ô bằng Bluetooth thật (điện thoại không thấy sóng TU01).
- Thời tiết xấu thật trên server (chỉ giả lập phía app bằng proxy); kiểm thời tiết khi drone đang bay.
- Hết hạn 24 h lấy hàng / phí quá giờ, phụ thu bị khách từ chối, KTV "Không lấy được" / "Giao không hoàn tất".
- Luồng trên web admin (chỉ gọi API tương ứng).
