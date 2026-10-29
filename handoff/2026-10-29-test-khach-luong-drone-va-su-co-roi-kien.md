# 2026-10-29 — Test vai khách hàng luồng drone: đặt đơn, unhappy case, sự cố rơi kiện và bồi thường

Người làm: binhtntse182370 (cùng Claude Code), vai **khách hàng**. Các vai drone technician, locker technician, admin do thành viên khác thao tác song song. Thời gian test: 29/10/2026 21:45 → 23:05.
Mốc code: mobile `main` @ `b36fc3b`, backend `main` @ `6474b72`.
Môi trường: production `https://api.locker-drone.tech`, chế độ bay DEMO (mô phỏng), app trên emulator Android 1080×2400 điều khiển qua adb. Trạng thái đơn được đọc song song qua API của khách mỗi 15 giây để đối chiếu với màn hình.

Mức độ: 🔴 nghiêm trọng (kẹt đơn, lỗi server, thiếu thông tin bắt buộc) · 🟠 sai logic / hiển thị sai · 🟡 UI. Lỗi đã có trong báo cáo trước và hôm nay **vẫn còn** được đánh dấu *(vẫn còn — [báo cáo](...))*.

Tài khoản khách: `truongnguyenthaibinh1050@gmail.com` (user 14). Người nhận: Nguyen Quoc Bao Huy · 0912345678 · `nqbhuy2004nt@gmail.com`.

## 1. Tóm tắt kết quả

| Case | Đơn | Kết quả |
|---|---|---|
| Happy case: đặt → trả tiền → KTV lấy tận nhà → nạp → phóng → bay | ORD-20261029-6SBKYS (#143) | ✅ Tới chặng "sắp đến" thì admin báo rơi kiện (chủ ý, để test nhánh sự cố) |
| Unhappy case trên form đặt đơn (16 case) | — | ✅ 15/16 — ❌ SĐT `123456789` lọt qua |
| Unhappy case gọi thẳng API tạo đơn (11 case) | — | ✅ 10/11 — ❌ thiếu header `Idempotency-Key` ⇒ HTTP 500 |
| Rơi kiện → thu hồi → về kho → khách **Đồng ý** "Giao lại + bồi thường một phần" | #143 → giao lại ORD-20261029-58RD1J (#144) | ✅ Đơn giao lại 0đ PAID, phiếu bồi thường #33 (2.400đ) đã chuyển tiền, có UNC |
| Đơn giao lại #144 | ORD-20261029-58RD1J | ⚠️ Kẹt `AWAITING_DISPATCH` vì trạm tự dừng do dự báo mưa; vẫn chưa điều phối lúc 23:18 |

Kết luận: các bước phía khách đều chạy, màn **Theo dõi giao drone** tự cập nhật đúng theo từng chặng của vai khác. Lỗi tập trung ở **trang chi tiết đơn** (thiếu mã cho KTV, không tự cập nhật), **nội dung hiển thị khi có sự cố**, và **đơn giao lại khi trạm dừng vì thời tiết**.

## 2. Các bước đã chạy

### 2.1 Happy case — đơn #143

| # | Giờ | Bước | Vai | Kết quả phía khách |
|---|---|---|---|---|
| 1 | 21:54 | Đặt đơn: lấy hàng tại FPT Software F-Town 3, tủ nhận `test tu` ô 1, 1 kg, Quần áo, 20 × 15 × 10 cm | Khách | ✅ Báo giá 8.000đ, thời tiết "Đủ điều kiện", hệ thống chọn tủ bay F-Town 3 (HCM-TD-01), bay 1,6 km |
| 2 | 21:55 | Thanh toán VietQR bằng "Giả lập thanh toán (test)" | Khách | ✅ `PAID`, mở màn theo dõi, hiện mã lấy hàng 576163 |
| 3 | 21:58 – 22:12 | Mời KTV, quá 3 phút không trả lời ⇒ mời người kế tiếp (2 lần) | Hệ thống | ✅ Nhật ký ghi từng lần mời lại |
| 4 | 22:18 | KTV Bảo Huy Nguyễn nhận lấy hàng | KTV drone | ✅ Hiện tên, SĐT, khoảng cách 1,7 km, bản đồ A → B |
| 5 | 22:37 | KTV nhập mã 576163, chụp ảnh, lấy kiện | KTV drone | ✅ Hiện ảnh kiện; nút Hủy đơn biến mất |
| 6 | 22:38 – 22:39 | Nạp lên LR-DRN-06: 1000 g, niêm phong NP-261029-WHCEMC, checklist 3 mục | KTV drone | ✅ Hồ sơ nạp hàng hiện đủ |
| 7 | 22:39 | Phóng, gửi email "đã phóng" cho người gửi và người nhận | KTV drone + hệ thống | ✅ Nhật ký ghi đã gửi tới tr\*\*\*@gmail.com, nq\*\*\*@gmail.com |
| 8 | 22:39 – 22:40 | Giả lập: rời trạm → đang bay → sắp đến | Hệ thống | ✅ Mỗi chặng có giờ và thời gian chuyển |

Trước khi đặt được đơn có hai lần bị chặn đúng: tuyến Q1 → Hutech bị chặn vì dự báo mưa 0,2 mm; điểm lấy hàng tại ĐH FPT chỉ cách tủ `test tu` 87 m (dưới 200 m).

### 2.2 Unhappy case trên form "Gửi hàng bằng drone"

| # | Case | Thông báo | Kết quả |
|---|---|---|---|
| A1 | Chưa chọn điểm lấy hàng | Chọn điểm lấy hàng | ✅ |
| A2 | Bỏ trống tên người nhận | Nhập tên người nhận | ✅ |
| A3 | SĐT người nhận "12345" | Số điện thoại người nhận không hợp lệ | ✅ |
| A4 | SĐT "123456789" | Không báo lỗi | ❌ § 3 #4 |
| A5 | Email "abc@gmail" | Email người nhận không hợp lệ | ✅ |
| A6 | Chưa chọn ô drone nhận | Chọn ô drone nhận còn trống tại tủ nhận | ✅ |
| A7 | Chưa chọn loại hàng | Chọn loại hàng | ✅ |
| A8 | Chỉ nhập chiều dài | Nhập đủ dài, rộng, cao của kiện (cm) hoặc bỏ trống cả ba | ✅ |
| A9 | Kiện 40 × 30 × 25 cm | Kiện không lọt khoang drone (tối đa 30 × 25 × 20 cm) | ✅ |
| A10 | Giá trị khai báo 3.000.000đ | Drone chỉ nhận kiện có giá trị tới 2.000.000đ | ✅ |
| A11 | Không tick cam kết hàng cấm bay | Bạn cần cam kết kiện không chứa hàng cấm bay | ✅ |
| A12 | Dự báo mưa trên tuyến | "Tạm ngưng bay", nút tạo đơn bị khoá | ✅ |
| A13 | Tủ nhận ngoài tầm bay (Q1 → `test tu`, 13,9 km) | Tủ nhận nằm ngoài tầm bay của drone | ✅ |
| A14 | Điểm lấy hàng cách tủ nhận 87 m | "Tủ nhận ở ngay cạnh tủ gửi…" | ✅ chặn đúng, ❌ câu chữ sai (§ 3 #5) |
| A15 | Tủ bảo trì / mất kết nối | Không chọn được trong danh sách | ✅ |
| A16 | Ô đã có đơn khác giữ | Ô số 1 không còn trong danh sách | ✅ |

### 2.3 Gọi thẳng `POST /api/orders/drone-deliveries` (bỏ qua app)

| # | Dữ liệu sai | Server trả | Kết quả |
|---|---|---|---|
| B1 | Email "abc@gmail" | 400 `DRONE_RECEIVER_EMAIL_INVALID` | ✅ |
| B2 | Tên người nhận chỉ có khoảng trắng | 400 `VALIDATION_ERROR` receiverName | ✅ |
| B3 | `prohibitedItemsDeclared: false` | 400 `DRONE_PROHIBITED_ITEMS_NOT_DECLARED` | ✅ |
| B4 | 6000 g | 400 `DRONE_PAYLOAD_TOO_HEAVY` | ✅ |
| B5 | 40 × 30 × 25 cm | 400 `DRONE_PARCEL_TOO_LARGE` | ✅ |
| B6 | Giá trị 3.000.000đ | 400 `DRONE_DECLARED_VALUE_TOO_HIGH` | ✅ |
| B7 | Loại hàng "WEAPON" | 400 `DRONE_PARCEL_CATEGORY_INVALID` | ✅ |
| B8 | Thiếu toạ độ lấy hàng | 400 `VALIDATION_ERROR` | ✅ |
| B9 | Tủ nhận không tồn tại | 400 `DRONE_DESTINATION_NOT_FOUND` | ✅ |
| B10 | SĐT người gửi "abc" | 400 `VALIDATION_ERROR` senderPhone | ✅ |
| B11 | B1–B7, B9 gửi **không** có header `Idempotency-Key` | 500 `INTERNAL_ERROR` | ❌ § 3 #1 |

Không có đơn rác nào được tạo. Server kiểm lại thời tiết khi tạo đơn (`DroneOrderBookingService.java:137`).

### 2.4 Sự cố rơi kiện, giao lại và bồi thường

| # | Giờ | Bước | Vai | Kết quả phía khách |
|---|---|---|---|---|
| 1 | 22:40 | Báo rơi kiện DPI-143-1793288403320, đơn về `DROP_REPORTED` | Admin | ✅ Thẻ "Sự cố rơi kiện đang được xử lý" tự hiện |
| 2 | 22:46 – 22:47 | Thu hồi: tìm thấy, bao bì rách/móp nhẹ; bàn giao về kho | KTV tủ | ✅ "Tình trạng kiện: Đã về kho Lock.R" |
| 3 | 22:50 | Phương án lần 1: giao lại miễn phí + bồi thường 2.400đ | Admin | ✅ Hai nút "Yêu cầu xem xét" / "Đồng ý" |
| 4 | 22:56 | Đồng ý phương án, kèm ghi chú | Khách | ✅ "Đã ghi nhận phương án bạn chọn" |
| 5 | 22:56 | #143 → `CANCELED`; tạo đơn giao lại #144 (0đ, PAID, cùng người nhận và ô) | Hệ thống | ✅ Đơn mới hiện ở trang chủ và danh sách đơn |
| 6 | 22:57 | #144 bị chặn: trạm tự dừng vì dự báo mưa, hạn tự kết thúc 23:27:15 | Hệ thống | ⚠️ § 3 #3 |
| 7 | 22:58 | Tạo phiếu hoàn tiền #33, 2.400đ về MBBank đã lưu | Hệ thống | ✅ Hồ sơ › Hoàn tiền: "Chờ chuyển khoản", lý do ghi mã sự cố |
| 8 | 23:02 | Duyệt và chuyển tiền bồi thường | Admin | ✅ "Đã chuyển tiền", có ảnh UNC |

## 3. Lỗi phát hiện

### 🔴 Nghiêm trọng

| # | Lỗi | Tái hiện / bằng chứng | Vị trí nghi vấn |
|---|---|---|---|
| 1 | Tạo đơn drone thiếu header `Idempotency-Key` trả **500 INTERNAL_ERROR** thay vì 400 | B11: cùng body, thêm header thì nhận đúng 400 theo từng lỗi | order-service, chỗ đọc header `Idempotency-Key` của `POST /api/orders/drone-deliveries` |
| 2 | Trang **chi tiết đơn** (Đơn tủ › Chi tiết) không hiện **mã lấy hàng** đưa cho KTV (576163); khách chỉ thấy mã ở màn Theo dõi | Đơn #143 lúc `PICKUP_ASSIGNED` | `mobile/lib/features/locker_ops/presentation/pages/my_locker_orders_page.dart:4173-4183` (chỉ có mã mở ô sau khi hàng vào ô) |
| 3 | Đơn **giao lại** 0đ bị chặn vì trạm tự dừng do thời tiết, app báo "Nếu chưa khắc phục trước 23:27:15, đơn sẽ kết thúc và bạn được **hoàn tiền**". Đơn 0đ thì không có gì để hoàn; nếu đơn tự kết thúc thì kiện ở kho không còn đơn nào xử lý | #144, nhật ký 22:57:15 | Cron đóng đơn bị chặn (`drone-blocked-timeout-minutes` = 30) áp dụng cả cho đơn giao lại |

### 🟠 Sai logic / hiển thị sai

| # | Lỗi | Tái hiện / bằng chứng | Vị trí nghi vấn |
|---|---|---|---|
| 4 | Regex SĐT chỉ kiểm 9–15 chữ số, nhận cả "123456789" | A4 | `mobile/…/drone_booking_page.dart:111` và `CreateDroneDeliveryOrderRequest.PHONE` |
| 5 | `DRONE_ROUTE_TOO_SHORT`: server ghi "Tủ nhận chỉ cách **điểm lấy hàng** 87 m", app dịch thành "Tủ nhận ở ngay cạnh **tủ gửi** drone" | A14 | `mobile/lib/features/locker_ops/data/locker_ops_service.dart:1756` |
| 6 | Toạ độ tủ F-Town 3 (HCM-TD-01: 10.8509, 106.7979) lệch khoảng 2,1 km so với địa chỉ thật (10.8348, 106.8081) | Màn đặt đơn: "KTV mang kiện 2,1 km" khi điểm lấy hàng chính là F-Town 3 | Dữ liệu tủ 800005 |
| 7 | Chi tiết đơn không hiện KTV (tên, SĐT), địa chỉ lấy hàng và chỉ dẫn | #143 | `my_locker_orders_page.dart` |
| 8 | Chi tiết đơn có 2 giờ thanh toán: 21:55:11 (trả xong) và 21:54:42 (tạo giao dịch) *(vẫn còn — [2026-10-29 unhappy](2026-10-29-test-mobile-luong-drone-unhappy-case.md))* | #143 | |
| 9 | Chi tiết đơn không tự cập nhật; nút **Tải lại** trên thanh tiêu đề không làm mới "Lịch sử trạng thái" (phải bấm nút Tải lại riêng của khối đó) | #143 lúc `PICKED_UP` → `LAUNCHING`: API `/api/orders/143/timeline` đã có 8 dòng, app vẫn dừng ở 22:18 | `mobile/…/widgets/order_status_timeline.dart` |
| 10 | Lý do nội bộ của admin hiện nguyên văn cho khách: "Admin quan sat thay kien roi khoi drone khi dang bay (test E2E …)" | #143 sau 22:40 | Thẻ `customer_drone_incident_card.dart` dùng `reason` |
| 11 | Nhật ký hành trình có dòng tiếng Anh "Reported dropped parcel: DPI-143-…" | #143 | order-service, chỗ ghi log khi báo rơi kiện |
| 12 | Khi kiện đã rơi, khối Thông tin đơn vẫn ghi "Trạng thái đơn: Đang giao bằng drone" | #143 | |
| 13 | Khách không thấy tình trạng kiện (`MINOR_DAMAGE`, "Bao bì rách/móp nhẹ") và ảnh thu hồi trước khi chọn phương án *(vẫn còn — [2026-10-29 unhappy](2026-10-29-test-mobile-luong-drone-unhappy-case.md))* | API `/api/orders/drone-incidents` có đủ, thẻ không hiện | `customer_drone_incident_card.dart` |
| 14 | Đơn rơi kiện đã đóng ghi "Đơn đã dừng trước khi drone cất cánh" *(vẫn còn — [2026-10-28](2026-10-28-test-mobile-luong-drone-va-loi-phat-hien.md), [2026-10-29 unhappy](2026-10-29-test-mobile-luong-drone-unhappy-case.md))* | #143 sau 22:56 | |
| 15 | Đơn giao lại ghi "Hệ thống đang tìm kỹ thuật viên drone rảnh gần bạn nhất" dù kiện đang ở kho Lock.R | #144 | |

### 🟡 UI

| # | Lỗi | Ghi chú |
|---|---|---|
| 16 | Lỗi nhập liệu chỉ hiện snackbar, ô sai không tô đỏ và không cuộn tới | A1–A11 |
| 17 | Khối lượng mặc định là 2 kg (20.000đ) vì cấu hình 1200 g không có trong danh sách 500 g / 1 / 2 / 3 / 4 / 5 kg | `drone_booking_page.dart:197-204` |
| 18 | Thẻ thời tiết ở form không tự làm mới (24 phút sau vẫn "Cập nhật 9:54 PM") và dùng giờ 12h, các màn khác dùng 24h | |
| 19 | Thoát form đã nhập dữ liệu không hỏi xác nhận | |
| 20 | Nút "Báo ô lỗi" hiện khi kiện chưa vào ô *(vẫn còn — [2026-10-28](2026-10-28-test-mobile-luong-drone-va-loi-phat-hien.md))* | `my_locker_orders_page.dart:4455-4466` (chỉ kiểm `boxId != null`) |
| 21 | Có cả "Hủy đơn" và "Yêu cầu hoàn tiền" khi đơn đang chạy | |
| 22 | Khách thấy enum thô "Trạng thái nhiệm vụ: DROP_REPORTED" và chữ nội bộ "Cần nhân viên xử lý trực tiếp", "Thu hồi kiện: Đã đóng" | |
| 23 | Nhãn "Bỏ kiện vào ô gửi lúc 22:37:51" mâu thuẫn với luồng nạp thẳng lên drone (giá trị là giờ KTV lấy hàng) *(vẫn còn — [2026-10-28](2026-10-28-test-mobile-luong-drone-va-loi-phat-hien.md))* | `parcelDroppedAt` |
| 24 | Thẻ trạng thái vẫn ghi "đang thu hồi… Lock.R sẽ gửi phương án" khi phương án đã gửi *(vẫn còn — [2026-10-29 unhappy](2026-10-29-test-mobile-luong-drone-unhappy-case.md))* | |

## 4. Đúng thiết kế (không phải lỗi)

- Nút "Hủy đơn" vẫn hiện khi KTV đang tới lấy hàng: đơn drone huỷ được tới khi KTV cầm kiện (`AWAITING_DISPATCH`, `PICKUP_ASSIGNED`) — `my_locker_orders_page.dart:4467-4480`.
- Ô đã có đơn giữ không còn trong danh sách chọn ô.
- Bồi thường dùng tài khoản ngân hàng khách đã lưu, khách không phải nhập lại.

## 5. Việc còn dở

- [ ] Đơn giao lại ORD-20261029-58RD1J (#144) vẫn `AWAITING_DISPATCH` lúc 23:18 vì trạm tạm dừng do mưa. Cần kiểm tra sau hạn 23:27:15: đơn bị đóng hay được điều phối, kiện ở kho xử lý thế nào (§ 3 #3).
- [ ] Chưa test bước cuối: drone thả kiện vào ô, email mã mở ô tới `nqbhuy2004nt@gmail.com`, người nhận mở ô bằng PIN, đơn hoàn tất.
- [ ] Chưa test nhánh "Yêu cầu xem xét" (khách từ chối phương án lần 1).
- [ ] Câu hỏi: khách chưa lưu tài khoản ngân hàng thì phiếu bồi thường chuyển tiền về đâu?
