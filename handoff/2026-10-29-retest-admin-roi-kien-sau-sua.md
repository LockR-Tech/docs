# 2026-10-29 — Test lại luồng rơi kiện sau khi sửa (vai admin, nhiều người cùng test)

Người làm: Kimnha01 (cùng Claude Code). Thời gian test: 29/10/2026 22:18 → 23:08.
Mốc code: backend `origin/main` @ `692a47c` (đã có merge `6854ba0` của `fix/f1-g11-sua-loi-test-drone-2910` — các bản sửa ở [handoff 2026-10-29 § 8](2026-10-29-test-mobile-luong-drone-unhappy-case.md#8-đã-sửa--nhánh-fixf1-g11-sua-loi-test-drone-2910-backend-mobile-frontend-docs) đã chạy trên production). Web admin chạy **local** (`npm run dev`, nhánh `fix/f1-g11-sua-loi-test-drone-2910`, proxy `/api` → production).
Môi trường: production `https://api.locker-drone.tech`. Web admin mở bằng Chrome trên điện thoại OPPO CPH2473 (chế độ "Trang cho máy tính", `adb reverse` vào máy chạy Vite).

Mỗi người một vai: **admin** (Claude điều khiển web admin trên điện thoại), **khách** "thai binh truong nguyen" (userId 14), **KTV drone lấy hàng** Bảo Huy Nguyễn, **KTV kiosk thu hồi** "ky thuat vien Kiosk" (userId 17) — khách và KTV do người khác thao tác trên app thật. Admin chỉ phản ứng theo request của các vai khác; riêng việc **báo rơi kiện khi drone đang bay** do admin làm.

Mức độ: 🔴 nghiêm trọng (sai tiền, đóng sai sự cố) · 🟠 sai logic / hiển thị sai · 🟡 UI, câu chữ.

## 1. Tóm tắt kết quả

| Case | Đơn / sự cố | Kết quả |
|---|---|---|
| Rơi kiện — Giao lại + bồi thường một phần (2.400đ = 30 %, hư hại nhẹ, không hoàn phí giao) | ORD-20261029-6SBKYS (#143) → giao lại ORD-20261029-58RD1J (#144) · DPI-143-1793288403320 (id 10) | ✅ phần bồi thường: phiếu #33 duyệt xong ⇒ sự cố tự nhận `PAID`. ⏳ phần giao lại: đơn #144 còn `AWAITING_DISPATCH` lúc viết báo cáo (23:08) — chưa kiểm được sự cố tự `RESOLVED` |
| Rơi kiện — Chỉ bồi thường | — | ⏳ chưa test (chờ đơn mới) |
| Rơi kiện — Thỏa thuận riêng | — | ⏳ chưa test (chờ đơn mới) |

Kết luận: các bản sửa 🔴 #1, #2, #3 của handoff 2026-10-29 **chạy đúng trên production** (callback payment → order, phiếu bồi thường không đổi trạng thái hoàn tiền của đơn, lý do phiếu đúng phương án). Lỗi mới chủ yếu ở **web admin** (hiển thị, câu chữ) và một lỗ hổng 🔴: admin đóng được phần giao lại khi đơn giao lại chưa xong.

## 2. Diễn biến (giờ VN)

| Giờ | Vai | Việc | Kết quả hệ thống |
|---|---|---|---|
| 21:54 | Khách | Đặt đơn #143 (F-Town 3 → tủ "test tu", 1 kg quần áo, cước 8.000đ, **không khai giá trị**), trả tiền | `AWAITING_DISPATCH` |
| 22:18 | KTV drone | Nhận lời mời lấy hàng tận nhà | `PICKUP_ASSIGNED` |
| ~22:37 | KTV drone | Lấy hàng | `PICKED_UP` |
| 22:39 | — | Nạp + phóng (LR-DRN-06) | đang bay |
| 22:39:53 | Admin | `POST /api/admin/drone-orders/143/drop-incident` (camera UNAVAILABLE) | DPI-143 `MANUAL_INTERVENTION_REQUIRED`, tự gán thu hồi cho KTV kiosk, phiếu kiểm tra drone #44, gợi ý bồi thường 4.800đ (60 %), đơn `DROP_REPORTED` |
| 22:41 → 22:44 | KTV kiosk | Nhận nhiệm vụ → Bắt đầu tìm → gửi kết quả FOUND, `MINOR_DAMAGE`, "Bao bì rách/móp nhẹ do va đập" + 1 ảnh + GPS | `AWAITING_ADMIN_REVIEW`, kiện `DAMAGED` |
| 22:46 | Admin | Web: Duyệt xác minh kết quả tìm hàng | thu hồi `VERIFIED` |
| 22:47 | KTV kiosk | Bàn giao kiện về Hub | thu hồi `CLOSED`, kiện `RETURNED_TO_HUB` |
| 22:50 | Admin | Web: gửi phương án v1 "Giao lại kiện + Bồi thường một phần", 2.400đ, bỏ tick "Hoàn phí giao hàng" | `AWAITING_CUSTOMER_RESPONSE` |
| 22:56 | Khách | Đồng ý ("Dong y giao lai va bo thuong") | tạo đơn giao lại #144 (0đ, `PAID`), đơn #143 `CANCELED`, bồi thường `AWAITING_APPROVAL` |
| 22:58 | Admin | Web: Phê duyệt phiếu hoàn tiền bồi thường | phiếu `RF-CMP-DPI-143-1793288403320-1793289526443` (#33) `PENDING`, sự cố `PROCESSING` |
| 23:01 | Admin | Web "Hoàn tiền": Duyệt & CK phiếu #33, tải ảnh biên lai test | phiếu `COMPLETED` ⇒ sự cố tự `PAID` (timeline `COMPENSATION_PAID`), vẫn `RESOLUTION_IN_PROGRESS` vì còn giao lại — **đúng** |

## 3. Kiểm lại các bản sửa của handoff 2026-10-29

| # gốc | Nội dung sửa | Kết quả trên production |
|---|---|---|
| 1 | Duyệt phiếu `RF-CMP-…` ⇒ payment báo order, sự cố tự cập nhật | ✅ `compensationStatus` `PROCESSING → PAID` ngay khi duyệt phiếu #33 |
| 2 | Phiếu bồi thường không đổi trạng thái hoàn tiền của đơn; hoàn phí giao bằng phiếu riêng | ✅ đơn #143 `refundStatus` vẫn `null` sau khi chi bồi thường; bỏ tick hoàn phí ⇒ chỉ có 1 phiếu (#33), không sinh phiếu phí |
| 3 | Lý do phiếu bồi thường theo phương án + tình trạng kiện | ✅ "[Bồi thường sự cố DPI-143-1793288403320] Giao lại kèm bồi thường một phần sau sự cố rơi kiện (đơn ORD-20261029-6SBKYS) — kiện hư hại nhẹ. Bồi thường 2.400đ." — thiếu phần tỷ lệ khi đơn không khai giá trị (§ 4 #9) |
| 4 | Thỏa thuận riêng có `resolutionNote`, tự đóng | ⏳ chưa test |
| 5 | Đơn giao lại COMPLETED ⇒ sự cố tự đóng phần giao lại | ⏳ đơn #144 chưa giao |
| UI web | "Phiên bản" hiện đúng số | ✅ "Phiên bản 1" |

## 4. Lỗi mới phát hiện

| # | Mức | Lỗi | Tái hiện / bằng chứng | Vị trí nghi vấn |
|---|---|---|---|---|
| 1 | 🟠 ✅ đã sửa | Badge "Mức bồi thường" hiện **6000%** | Backend trả `compensationRate: 60.00` (đơn vị %), web nhân thêm 100 | `fe/…/drone-incidents/detail.tsx` (badge) — đổi sang `formatCompensationRate` như các chỗ khác; local, chưa commit |
| 2 | 🔴 | Admin đóng được phần giao lại khi **đơn giao lại chưa xong** | Nút "Xác nhận đã giao lại thành công & hoàn tất sự cố" hiện ngay khi `redeliveryStatus = PREPARING`; backend chỉ kiểm trạng thái sự cố, không kiểm đơn #144 đã `COMPLETED` | `DroneParcelIncidentService.completeRedelivery`; web `detail.tsx` khối "Tiến trình giao lại". Đề xuất: ẩn nút (giờ đã tự đóng khi đơn giao lại xong) hoặc bắt buộc lý do + chỉ cho khi đơn giao lại lỗi |
| 3 | 🟠 | "Hoàn phí giao hàng khi bồi thường" **tick sẵn** cả với phương án có giao lại miễn phí | Chọn "Giao lại kiện + Bồi thường một phần" ⇒ ô vẫn tick; bấm gửi luôn là khách vừa được giao lại 0đ vừa được hoàn cước | web `detail.tsx` form phương án — mặc định bỏ tick khi `redeliveryOffered` |
| 4 | 🟠 | Modal "Duyệt & Xác nhận chuyển khoản" cho phiếu bồi thường ghi sai | Cảnh báo "Hành động này sẽ cập nhật đơn hàng thành **ĐÃ HOÀN TIỀN**" (sai — phiếu bồi thường không đổi đơn); nội dung CK `HOANTIEN ORD-…` thay vì theo mã sự cố | web `refunds/components/RefundTable.tsx` — nhận biết `RF-CMP-` / lý do "[Bồi thường sự cố" |
| 5 | 🟡 | Danh sách "Hoàn tiền" không phân biệt phiếu bồi thường với phiếu hoàn cước | Dòng #33 trông như phiếu hoàn đơn thường (chỉ modal "Chi tiết" mới có nhãn "Bồi thường sự cố rơi") | `RefundTable.tsx` |
| 6 | 🟠 | Chip trạng thái sự cố vẫn "Chờ Admin xác minh" sau khi admin đã xác minh và kiện đã về Hub | `status` giữ `AWAITING_ADMIN_REVIEW` tới khi có phương án; chỉ chip "Thu hồi" đổi | nhãn `status` ở web (`detail.tsx`) — gợi ý "Chờ lập phương án" khi `recoveryStatus ∈ {VERIFIED, CLOSED}` |
| 7 | 🟡 | Badge thẻ "Kỹ thuật viên phụ trách thu hồi kiện" lùi về "KTV đã tiếp nhận nhiệm vụ" sau khi bàn giao Hub (`recoveryStatus = CLOSED`) | Trước đó là "Đã xác minh thu hồi" | `detail.tsx` |
| 8 | 🟡 | Còn mã kỹ thuật chưa dịch | Timeline: "RECOVERY ACCEPT", "RECOVERY START SEARCHING", "RESOLUTION PROPOSED", "REDELIVERY REQUESTED", "CUSTOMER ACCEPT", "COMPENSATION SUBMITTED"; lịch sử đề xuất "REDELIVERY PARTIAL COMPENSATION"; thẻ kiện "Quay về: MANUAL_INTERVENTION_REQUIRED", thẻ bồi thường "Trạng thái: NOT_REQUIRED"; ghi chú timeline "Admin đã chuyển khoản hoàn 2400 đ" (không định dạng) | `detail.tsx`, câu ghi chú ở `PaymentService` / `DroneParcelIncidentService` |
| 9 | 🟠 | Gốc tính bồi thường không thống nhất khi đơn **không khai giá trị** | Web/gợi ý lấy cước 8.000đ làm "giá trị khai báo" (60 % = 4.800đ), "Kiện hàng & Trọng lượng" lại ghi "Giá trị khai báo: —"; lý do phiếu bỏ hẳn phần "= x % giá trị khai báo" | `DroneParcelIncidentService.toResponse` (fallback `totalPrice`), `PaymentIncidentCompensationGateway.compensationReason` — cần chốt: không khai giá trị thì bồi thường theo gì |
| 10 | 🟡 | Form phương án không reset / không khoá sau khi gửi, vẫn hiện sau khi khách đã đồng ý | Dễ gửi nhầm phiên bản 2 khi khách đã chấp nhận phiên bản 1 | `detail.tsx` |
| 11 | 🟠 | Trạng thái tổng "Cần can thiệp thủ công" ngay khi báo rơi ở chế độ DEMO | Không có telemetry ⇒ `telemetryStale` ⇒ RTL `MANUAL_INTERVENTION_REQUIRED` và cả sự cố cùng nhãn đỏ — admin tưởng có việc khẩn | `DroneParcelIncidentService.report` — tách trạng thái quay về của drone khỏi trạng thái sự cố |
| 12 | 🟡 | Toạ độ KTV xác nhận lệch **4.004 m** so với điểm rơi vẫn duyệt bình thường | Web có cảnh báo vàng "Độ lệch so với điểm rơi: 4004 mét" nhưng nút duyệt không hỏi lý do (điểm rơi DEMO là ước theo tuyến bay) | `detail.tsx` hộp duyệt xác minh — gợi ý bắt buộc ghi chú khi lệch > ngưỡng |
| 13 | 🟡 | Hành trình drone (#143): khi KTV đã nhận việc vẫn hiện "6 KTV đang trong ca · gán tay trước khi lấy hàng" + nút "Gán KTV" | Dễ gán đè | web trang hành trình drone |
| 14 | 🟡 | Bảng "Sự cố rơi kiện" và "Hoàn tiền": nút "Chi tiết" / "Duyệt & CK" nằm ở cột cuối, phải cuộn ngang mới thấy; chạm vào dòng không mở chi tiết | Màn hẹp | `drone-incidents/index.tsx`, `RefundTable.tsx` |
| 15 | 🟡 | `GET /api/admin/drone-orders?size=5` bỏ qua `size`, trả ~200 đơn | Trang hành trình sẽ chậm khi dữ liệu tăng | admin drone order controller |

Lỗi đã biết, vẫn còn: sự cố mẫu giả `INC-2026-DROP-001/002` (ORD-2026-8801/8802) vẫn trộn vào danh sách sự cố (`drone-incidents/index.tsx`, `SAMPLE_DRONE_INCIDENTS`); đơn cũ kẹt `AWAITING_DISPATCH` (800522 `EN_ROUTE` từ 15/10; 113, 111, 800531, 800530 `DROP_REPORTED`).

## 5. Đồng bộ giữa các vai trò

- Web admin tự làm mới danh sách sự cố khi KTV kiosk gửi kết quả (không phải bấm "Làm mới") ✅; trang chi tiết cần bấm nút làm mới để thấy bàn giao Hub.
- Trạng thái sự cố đọc qua API admin khớp với thao tác của KTV kiosk và khách ở mọi bước (nhận nhiệm vụ, bắt đầu tìm, gửi kết quả, bàn giao Hub, đồng ý phương án).
- Duyệt phiếu ở trang "Hoàn tiền" (payment-service) ⇒ trang sự cố (order-service) thấy `PAID` ngay ✅ — trước bản sửa bước này kẹt vĩnh viễn.

## 6. Thay đổi trên production và dữ liệu còn tồn

- Phiếu #33 (2.400đ) được đánh dấu **đã chuyển khoản** với ảnh biên lai test (ảnh nền đỏ trơn) — không có giao dịch thật. Nếu cần sổ sách sạch, ghi chú lại phiếu này.
- Sự cố DPI-143 còn `RESOLUTION_IN_PROGRESS` chờ đơn giao lại #144; phiếu kiểm tra drone #44 (LR-DRN-06) còn `INSPECTING`.
- Không đổi cấu hình production trong đợt này.

## 7. Việc tiếp theo

1. Theo dõi đơn #144 tới `COMPLETED` ⇒ kiểm sự cố DPI-143 tự `RESOLVED`, kiện `REDELIVERED` (bản sửa § 8 #5).
2. Test 2 case còn lại: "Chỉ bồi thường" (có tick hoàn phí giao — kiểm phiếu phí riêng) và "Thỏa thuận riêng" (kiểm `resolutionNote` hiện cho khách, tự `RESOLVED`).
3. Sửa § 4 #2 (🔴) trước, rồi #3, #4, #9, #11.
