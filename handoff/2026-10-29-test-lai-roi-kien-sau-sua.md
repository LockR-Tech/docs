# 2026-10-29 — Test lại luồng rơi kiện sau bản sửa F1-G11 và lỗi phát hiện

Người làm: Vi (cùng Claude Code). Thời gian test: 29/10/2026 21:45 → 23:05.
Mốc code đã rà: backend `main` @ `692a47c` (đã có bản sửa `fix/f1-g11-sua-loi-test-drone-2910`), mobile `main` @ `365620c` (app cài lúc 22:22), frontend `main` @ `ea9b690`.
Môi trường: production `https://api.locker-drone.tech`, điện thoại OPPO CPH1937 (Android, 720×1600) cho KTV kiosk; web admin chạy local (`frontend/fe`, Vite cổng 3000, gọi API production) và `https://admin.locker-drone.tech`.

Đây là lượt test lại các lỗi của handoff [2026-10-29-test-mobile-luong-drone-unhappy-case](2026-10-29-test-mobile-luong-drone-unhappy-case.md) (gọi tắt là **handoff gốc**), § 8 "Đã sửa" ghi "chưa thử lại trên điện thoại / production". Mức độ: 🔴 nghiêm trọng (sai tiền, kẹt đơn/sự cố, sai nghiệp vụ) · 🟠 sai logic / hiển thị sai · 🟡 UI.

Tài khoản: admin `binhtntse182370@fpt.edu.vn`, KTV kiosk `kiosk1@gmail.com` (user #17, "ky thuat vien Kiosk"). Khách và KTV drone do thành viên khác thao tác trên máy của họ; báo cáo này ghi những gì quan sát được từ vai trò admin và KTV kiosk.

## 1. Tóm tắt kết quả

| Case | Đơn / sự cố | Kết quả |
|---|---|---|
| Rơi kiện — Giao lại + bồi thường một phần (hư hại nhẹ, 2.400đ) | ORD-20261029-6SBKYS (#143) → giao lại ORD-20261029-58RD1J (#144), DPI-143-1793288403320 (incident #10) | ⏳ Đang chạy. Thu hồi, xác minh, bàn giao Hub, đề xuất, khách đồng ý, phiếu chi #33 đều đúng; sự cố còn `RESOLUTION_IN_PROGRESS` chờ đơn giao lại #144 bay xong. Lỗi mới về tủ xuất phát của đơn giao lại (§ 3 #1) |
| Rơi kiện — Chỉ bồi thường | — | Chưa test |
| Rơi kiện — Thỏa thuận riêng | — | Chưa test |

Phần đã xác nhận sửa đúng trên production ở § 2. Lỗi mới ở § 3 và § 4.

## 2. Kiểm lại các mục "Đã sửa" của handoff gốc

| # handoff gốc | Kết quả test lại | Bằng chứng |
|---|---|---|
| § 3 #1 — sự cố có bồi thường không đóng | ✅ Admin duyệt phiếu chi ⇒ sự cố nhận callback, `compensationStatus` `PROCESSING → PAID` ngay | DPI-143: timeline `COMPENSATION_PAID` 23:02:03 "Admin đã chuyển khoản hoàn 2400 đ"; phiếu #33 `COMPLETED` |
| § 3 #2 — phiếu bồi thường đổi `paymentStatus` đơn | ✅ Đơn gốc #143 giữ `PAID` sau khi chi bồi thường (không còn bị đổi `REFUNDED`). Chưa test được "hoàn phí giao" vì phương án lần này `refundShippingFee = false` | `GET /api/admin/drone-orders/143` |
| § 3 #3 — lý do phiếu bồi thường | ✅ Lý do nêu phương án, tình trạng kiện, số tiền định dạng mới: "Giao lại kèm bồi thường một phần sau sự cố rơi kiện (đơn ORD-20261029-6SBKYS) — kiện hư hại nhẹ. Bồi thường 2.400đ." Đơn không khai báo giá trị nên không có tỷ lệ thực — cần xác nhận như vậy là đúng | Phiếu #33 |
| § 3 #4 — thỏa thuận riêng kẹt vĩnh viễn | Chưa test lại (case 3). DPI-142 tạo trước bản sửa vẫn kẹt (handoff gốc § 8 đã ghi phải xử lý tay) | — |
| § 3 #5 — giao lại không đồng bộ với sự cố | ⏳ Chờ đơn #144 COMPLETED để xem sự cố có tự đóng phần giao lại | — |
| § 4 KTV tủ — tab "Thu hồi kiện" đếm cả nhiệm vụ đã đóng | ✅ Tab ghi "Thu hồi kiện (0)" khi chỉ còn nhiệm vụ đã đóng, "(1)" khi có DPI-143 | App KTV kiosk |
| § 4 KTV tủ — màn chi tiết không tự cập nhật sau admin xác minh | ❌ Vẫn còn: phải đóng sheet, kéo làm mới, mở lại mới thấy nút "Xác nhận bàn giao kiện về Hub / kho" | App KTV kiosk, 22:46 |

## 3. Lỗi phát hiện — 🔴 Nghiêm trọng

| # | Lỗi | Tái hiện / bằng chứng | Vị trí nghi vấn |
|---|---|---|---|
| 1 | **Đơn giao lại xuất phát từ tủ gửi cũ, không phải nơi giữ kiện.** KTV kiosk bàn giao kiện về Hub gắn tủ CAB-TU01 (`recoveryLockerId = 7`), nhưng đơn giao lại #144 lấy `sourceLockerId` của đơn cũ ⇒ tủ bay HCM-TD-01 (F-Town 3). Comment trong code ghi "xuất phát từ Hub" nhưng gán `oldOrder.getSourceLockerId()`. Không có bước nào đưa kiện từ Hub sang HCM-TD-01 ⇒ KTV drone ra tủ bay sẽ không có kiện để nạp | DPI-143 → #144 (`src HCM-TD-01`) | `order-service/.../OrderIncidentRedeliveryGateway.java:61` |
| 2 | **Đơn giao lại dùng lại ô nhận của đơn cũ.** #143 (đã `CANCELED`) và #144 cùng `reservedBoxId = 61`. Nếu luồng huỷ đơn cũ hoặc job đối soát nhả ô 61 thì đơn giao lại mất ô | `GET /api/admin/drone-orders/143`, `/144` | `OrderIncidentRedeliveryGateway.java:64-65` |
| 3 | **Bước "drone quay về" là trạng thái cụt.** Mọi sự cố (13/13, kể cả DPI-134 đã RESOLVED) có `returnFlightStatus = MANUAL_INTERVENTION_REQUIRED`: ở DEMO telemetry luôn cũ nên lệnh RTL không gửi; từ trạng thái này không có chuyển tiếp nào và admin không có API xác nhận "đã đưa drone về bằng tay" | Tất cả incident, gồm DPI-143 | `DroneParcelIncidentService.java:203-205`, `:526-531` |
| 4 | **Lời mời lấy hàng xoay vòng không báo admin.** Không KTV nào nhận ⇒ đơn lặp SEARCHING → OFFERED → hết hạn → chờ 10 phút → mời lại cùng người mãi. Không có thông báo, không có ngưỡng "quá N lần mời / quá X phút" để đẩy lên admin giao tay; admin chỉ biết khi tự mở trang đơn | #143 lúc 21:55 → 22:25 (mời Long Hoàng 2 lần) | `DronePickupService.java:243-300` (`offerPending`, `sweep`) |

## 4. Lỗi phát hiện — 🟠 / 🟡 UI, hiển thị

### Web admin
- 🟠 **Dữ liệu giả trộn vào danh sách thật.** Trang "Sự cố rơi kiện" hiện 14 sự cố trong khi API trả 12 — thêm `INC-2026-DROP-001/002` (ORD-2026-8801/8802, DRN-HCMC-09/14) từ hằng `SAMPLE_DRONE_INCIDENTS`; trang bảo trì tab "Drone Incidents" ghim phiếu giả `DRN-DROP-2026-001` lên đầu với đồng hồ SLA đếm ngược. Admin có thể thao tác lên sự cố không tồn tại — `frontend/fe/src/stores/apis/admin/droneIncidents.ts:200`, `pages/Admin/drone-incidents/index.tsx:274`, `detail.tsx:251`, `pages/Admin/maintenance/index.tsx:208`.
- 🟠 **Tỷ lệ bồi thường hiện "6000%"** ở thẻ "Mức bồi thường" của chi tiết sự cố: API trả `compensationRate = 60` (đơn vị %) nhưng thẻ này nhân thêm 100; các chỗ khác dùng `formatCompensationRate` thì đúng "60%" — `frontend/fe/src/pages/Admin/drone-incidents/detail.tsx:655`.
- 🟡 Chi tiết đơn lấy hàng tận nhà ghi "Dropped in sending box at: Sender has not dropped off the parcel" — luồng này KTV lấy tại nhà, khách không bỏ kiện vào tủ.
- 🟡 Danh sách giao tay KTV lấy hàng: 4/5 KTV gắn "Stale location", khoảng cách hiển thị theo vị trí cũ.

### App KTV kiosk (thu hồi kiện)
- 🟠 **App hiện nhiệm vụ thu hồi giả khi API lỗi hoặc rỗng.** `droneRecoveries()` nuốt lỗi và trả `_sampleDroneRecovery`; các thao tác nhận / tìm / nộp trên id mẫu sửa dữ liệu trong bộ nhớ ⇒ API hỏng trông như chạy, KTV có thể làm việc trên nhiệm vụ không tồn tại — `mobile/lib/features/locker_ops/data/locker_ops_service.dart:1345-1351`, `:1360`, `:1378`, `:1416`.
- 🟠 **Lần bấm "Nhận nhiệm vụ" đầu tiên không có tác dụng**: sheet đóng, thẻ vẫn "Đã phân công", server vẫn `recoveryStatus = ASSIGNED`, không báo lỗi; bấm lần hai mới `POST …/drone-recoveries/10/actions` 200. Chưa rõ lần đầu có gửi request không (log đã bị xoá trước lần bấm hai) — cần tái hiện.
- 🟡 **Sheet chi tiết nhiệm vụ không đọc được**: mã sự cố ở tiêu đề chữ trắng trên nền trắng; ô "Tình huống" và "Độ chính xác dữ liệu" có nội dung (trình đọc màn hình đọc được) nhưng chữ trùng màu nền nên trông trống.
- 🟡 Thẻ nhiệm vụ ghi "**Bị hư hỏng**" khi KTV chọn "Hư hại nhẹ" — nhãn lấy theo `parcelStatus = DAMAGED` chứ không theo `parcelCondition = MINOR_DAMAGE`.
- 🟡 (Đã có ở handoff gốc, vẫn còn) GPS KTV cách điểm rơi ~4.008 m vẫn gửi được "Đã tìm thấy", chỉ cảnh báo.

## 5. Đồng bộ trạng thái

- ✅ Mỗi thao tác của KTV kiosk trên app đổi đúng trạng thái sự cố trên API admin trong vòng 15 giây: `ASSIGNED → ACCEPTED → SEARCHING → SUBMITTED` (sự cố `RECOVERY_IN_PROGRESS → AWAITING_ADMIN_REVIEW`) → admin `VERIFIED` → bàn giao `CLOSED`, kiện `RETURNED_TO_HUB`.
- ✅ Khách đồng ý ⇒ cùng lúc: đơn gốc `CANCELED / DROP_REPORTED`, đơn giao lại #144 `PAID` 0đ, sự cố `redeliveryStatus = PREPARING`, `compensationStatus = AWAITING_APPROVAL`.
- Ghi chú (không phải lỗi): đơn drone giữ `status = AWAITING_DISPATCH` suốt lúc bay, tiến độ nằm ở `deliveryStage` / mission; chỉ đổi `STORING` khi vào ô (`DroneMissionProgressService.java:141`).

## 6. Thay đổi trên production và dữ liệu còn tồn

- Không đổi cấu hình nào.
- Tiền: admin (thành viên khác) đã duyệt phiếu bồi thường #33 — 2.400đ, tiền test.
- Còn tồn: DPI-143 `RESOLUTION_IN_PROGRESS` chờ #144; đơn #144 sẽ gặp § 3 #1 khi KTV drone ra tủ HCM-TD-01 nạp hàng. Báo cáo kiểm tra drone RPT-43 (DPI-142) vẫn `OPEN` chưa phân công, quá SLA.
- Trên điện thoại OPPO CPH1937: tài khoản khách đang đăng nhập đã bị đăng xuất để vào `kiosk1`; app Máy ảnh được cấp quyền vị trí **một lần**; có 1 ảnh test (màn hình bàn làm việc) trong thư viện ảnh. KTV kiosk vẫn đang **trong ca** — cần "Hết ca" khi test xong.

## 7. Đề xuất ưu tiên sửa

1. Đơn giao lại: chọn tủ bay theo nơi đang giữ kiện (`recoveryLockerId` / Hub), hoặc thêm bước KTV mang kiện về tủ bay; giữ ô nhận cho đơn mới bằng thao tác giữ ô riêng thay vì dùng lại `reservedBoxId` (§ 3 #1, #2). **Cần chủ dự án chốt nghiệp vụ.**
2. Gỡ dữ liệu mẫu khỏi web admin (sự cố, phiếu bảo trì) và app KTV kiosk (nhiệm vụ thu hồi): lỗi API phải hiện lỗi, rỗng phải hiện rỗng (§ 4).
3. Cho admin đóng bước "drone quay về" (đã thu hồi bằng tay / drone đã về), hoặc ở DEMO không đặt `MANUAL_INTERVENTION_REQUIRED` (§ 3 #3).
4. Cảnh báo admin khi đơn lấy hàng tận nhà quá N lượt mời hoặc quá X phút chưa có KTV nhận (§ 3 #4).
5. Sửa `detail.tsx:655` dùng `formatCompensationRate`; sửa màu chữ sheet nhiệm vụ thu hồi; nhãn thẻ theo `parcelCondition`; sheet tự làm mới sau admin xác minh (§ 4).
6. Chạy nốt case "Chỉ bồi thường" và "Thỏa thuận riêng", kiểm lại "hoàn phí giao" (`refundShippingFee = true`).

**Đã sửa (30/10):** xem [2026-10-30-sua-loi-retest-roi-kien](2026-10-30-sua-loi-retest-roi-kien.md) — bảng đối chiếu từng mục, local chưa deploy.
