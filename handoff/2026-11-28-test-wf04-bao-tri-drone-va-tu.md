# Báo cáo test luồng WF-04 Bảo trì drone và tủ trên thiết bị thật (lần 1) — 28/11/2026

> **Tổng quan**: Kiểm thử toàn bộ 44 test case (`WF04-001` .. `WF04-044`) thuộc các tính năng **F-14** (Xử lý sự cố & bảo trì), **F-18** (Quản lý đội bay & lịch bảo trì định kỳ), **F-19** (Thực hiện kiểm tra định kỳ), và 2 kịch bản demo **DS-04a**, **DS-04b** trên điện thoại Android thật qua USB ADB kết nối môi trường production.
>
> **Kết quả lần 1**: **41/44 Passed (93,2%)**, **3/44 Failed (`WF04-026`, `WF04-027`, `WF04-041`)**, **0 Pending/N/A**.  
> Phát hiện **8 lỗi** gồm **2 lỗi nghiêm trọng (`🔴`)**, **5 lỗi sai logic / hiển thị sai (`🟠`)** và **1 nhóm lỗi UI 360dp / trải nghiệm / đa ngôn ngữ (`🟡`)** (kèm lưu ý cấu hình `requireResolutionPhoto`).

---

## 1. Môi trường & phạm vi kiểm thử

| Hạng mục | Thông số thực tế |
|---|---|
| **Ngày test** | `28/11/2026` (lần 1) |
| **Người test** | Trần Kim Nhã |
| **Thiết bị di động** | OPPO CPH2473 (serial USB ADB: `9f12af34`), màn hình `720×1612`, `320 dpi` (~360dp width) |
| **Ứng dụng Mobile** | `com.laundrylocker.mobile` v1.0.0+2 |
| **Backend Production** | `https://api.locker-drone.tech` |
| **Commit các repo lúc test** | `backend`: `3433882`, `frontend`: `47f62a4`, `mobile`: `c306869`, `docs`: `0763c59` |
| **Tài khoản dùng test** | Admin (`userId #11`), KTV Drone chính (`userId #26`), KTV Drone 2 (`userId #25`), KTV Tủ A (`userId #17` — phụ trách `CAB-TU01`), KTV Tủ B (`userId #4`), Khách hàng (`userId #5`) |
| **Phạm vi dữ liệu** | Drone thật `DRONE-S550-07` (`#9`), drone đang bay `LR-DRN-05` (`#800005` — chỉ kiểm tra chặn chuyển trạng thái, không làm hỏng bay), drone test tạm `DRONE-WF04-TEST` (`#10` — đã xóa sạch), tủ thật `CAB-TU01` (`#7`, ô `#3` `boxId=40` — đã khôi phục `AVAILABLE`). |

### Tổng hợp kết quả theo nhóm & kịch bản demo

| Hạng mục | Số TC | Passed | Failed | Tỉ lệ đạt | Ghi chú |
|---|---:|---:|---:|---:|---|
| **WF-04 toàn luồng (`WF04-001`..`044`)** | **44** | **41** | **3** | **93,2%** | 3 TC fail: `WF04-026`, `WF04-027`, `WF04-041` |
| Tính năng `F-18` (Quản lý lịch & đội bay) | 18 | 18 | 0 | 100% | Bao gồm validation, RBAC, cron nhắc hạn, CRUD drone |
| Tính năng `F-19` (Kiểm tra định kỳ) | 13 | 11 | 2 | 84,6% | Fail tại `WF04-026`, `WF04-027` (nhánh Drone FAIL) |
| Tính năng `F-14` (Phiếu sự cố & SLA) | 11 | 10 | 1 | 90,9% | Fail tại `WF04-041` (RBAC KTV Tủ truy cập phiếu Drone) |
| Kịch bản demo **DS-04a** (`001,002,015,016,043`) | 5 | 5 | 0 | 100% | Đạt trọn vẹn luồng chính (`DRONE-S550-07`) |
| Kịch bản demo **DS-04b** (`003,021,023,044`) | 4 | 4 | 0 | 100% | Đạt trọn vẹn luồng ngoại lệ (`CAB-TU01` ô `#3`) |

---

## 2. Danh sách lỗi phát hiện (8 lỗi: 2 🔴 · 5 🟠 · 1 🟡)

### 🔴 Nghiêm trọng (Blocker / Sai nghiệp vụ / Hỏng phân quyền)

#### `BUG-WF04-01` — Lịch bảo trì Drone đánh FAIL không gắn phiếu chờ, tự dời hạn +14 ngày và cho hoàn tất trùng (`WF04-026`, `WF04-027`)

- **Mức độ**: 🔴 Nghiêm trọng (sai lệch logic state machine giữa nhánh Tủ và nhánh Drone).
- **Vị trí code xác nhận**:
  - `backend/locker-service/.../LockerService.java:2399, 2406, 2441, 2447, 2949-2964`
  - `backend/locker-service/.../LockerService.java:2873-2885` (`toSchedule()`)
  - `mobile/lib/features/locker_ops/presentation/widgets/complete_inspection_sheet.dart:719` (`_lockerId != null`)
  - `frontend/fe/src/pages/Admin/maintenance/MaintenanceSchedules.tsx:2408` & `DroneMaintenanceHistoryPanel.tsx:580` (cột `phiếu sinh ra`)
- **Các bước tái hiện**:
  1. Tạo lịch bảo trì drone định kỳ `#26` cho `DRONE-WF04-TEST` (`#10`, `intervalDays=14`, gán KTV `#26`).
  2. Trên app KTV Drone (`#26`), mở kiểm tra `#26`, chấm `"Cánh quạt"` = `Không đạt (FAIL)` kèm lý do `"Canh quat lech"`, `"Pin"` = `Đạt (PASS)` → nhấn **Xác nhận hoàn thành**.
  3. Gọi `GET /api/maintenance/schedules?mine=true`, `GET /api/maintenance/schedules/26/logs`, và gửi lại `POST /api/maintenance/schedules/26/complete` khi `RPT-67` đang `OPEN`.
- **Kết quả thực tế**:
  - `DRONE-WF04-TEST (#10)` chuyển sang `FAULT` và mở `RPT-67` (`OPEN`), API dispatch trả `400 DRONE_NOT_AVAILABLE` (**đúng**).
  - **Sai 1**: Dù app hiển thị banner *"Hạn kiểm tra kế tiếp chỉ dời khi phiếu được hoàn tất"* (vì `toSchedule()` copy `drone.getLockerId()` khiến `_lockerId != null` trên mobile), backend ở `LockerService.java:2399` kiểm tra `opensReport = outcome.failed() && schedule.getLockerId() != null` trong entity `schedule` (`schedule.lockerId` là `null` với lịch drone!). Hệ quả:
    - `nextDueAt` của `#26` bị tự động dời ngay `+14 ngày` (`2026-12-12`) khi chấm `FAIL`.
    - `schedule.pendingReportId = null` và `RPT-67.scheduleId = null`.
    - `inspectionLog.createdReportId = null`, làm Web Admin không hiện `"phiếu sinh ra"` (`RPT-67`) trong lịch sử kiểm tra (`WF04-027`).
  - **Sai 2**: Khi `RPT-67` vẫn đang `OPEN`, gửi lại `POST /api/maintenance/schedules/26/complete` vẫn trả **`200 SCHEDULE_COMPLETED`** (`PASSED`) thay vì chặn `409 SCHEDULE_PENDING_REPORT` như nhánh tủ.
- **Kết quả mong đợi**:
  - Lịch drone đánh `FAIL` phải mở phiếu sự cố drone có gắn `scheduleId`, gán `schedule.pendingReportId = report.id` và `inspectionLog.createdReportId = report.id`, giữ nguyên `nextDueAt` tới khi phiếu `RESOLVED`, và từ chối hoàn tất lại bằng `409 SCHEDULE_PENDING_REPORT`.
- **Hướng xử lý gợi ý**:
  - Sửa điều kiện `opensReport` tại `LockerService.java:2399` áp dụng thống nhất cho cả lịch Tủ (`schedule.getLockerId() != null`) và lịch Drone (`schedule.getDroneUnitId() != null`), đồng thời gắn `pendingReportId`, `createdReportId` và `report.scheduleId` cho phiếu drone sinh ra từ kiểm tra định kỳ.

---

#### `BUG-WF04-02` — API KTV Tủ lộ toàn bộ phiếu Drone và cho phép KTV Tủ claim phiếu Drone khi đang trong ca (`WF04-041`)

- **Mức độ**: 🔴 Nghiêm trọng (lỗ hổng phân quyền chéo vai trò KTV Tủ ↔ KTV Drone ở API backend).
- **Vị trí code xác nhận**:
  - `backend/locker-service/.../LockerController.java:214` (`GET /api/locker-technician/reports`) & `:217-237` (`claim`, `getReport`, `resolve` thiếu guard `!isDroneReport`)
  - `backend/locker-service/.../LockerService.java:1513-1515` (`openReports()` query `findByStatusInOrderByCreatedAtDesc` không lọc phiếu Drone)
- **Các bước tái hiện**:
  1. Đăng nhập tài khoản **KTV Tủ** (`userId #17`, chỉ có role `LOCKER_TECHNICIAN` & `CUSTOMER`, không có `DRONE_TECHNICIAN`).
  2. Trên app, mở tab **Sự cố** (`p4_02_kiosk_incidents.png`): app lọc phía client nên hiển thị `0`.
  3. Gọi API `GET /api/drone-technician/reports` và `PUT /api/drone-technician/reports/58/claim`: trả `403` (**đúng**).
  4. Bật **Vào ca** (`onDuty=True`) cho KTV Tủ `#17`, gọi `GET /api/locker-technician/reports` rồi `PUT /api/locker-technician/reports/58/claim` (phiếu `RPT-58` là `Drone LR-DRN-01 lỗi`, `category="DRONE"`, `droneUnitId=800001`).
- **Kết quả thực tế**:
  - `GET /api/locker-technician/reports` trả **`200 OK` gồm 7 phiếu toàn bộ thuộc loại `DRONE`** (`[58, 57, 56, 46, 44, 39, 800057]`).
  - Khi KTV Tủ `#17` đang trong ca, `PUT /api/locker-technician/reports/58/claim` trả **`200 REPORT_CLAIMED`**, chuyển `RPT-58` sang `IN_PROGRESS` với `assignedToUserId=17`! *(Đã gọi Admin unassign để khôi phục `RPT-58` về `OPEN` ngay sau khi ghi nhận lỗi.)*
- **Kết quả mong đợi**:
  - `GET /api/locker-technician/reports` không được trả về các phiếu `DRONE` (`droneUnitId != null` hoặc `category == "DRONE"`).
  - Các endpoint `/api/locker-technician/reports/{id}*` (`get`, `claim`, `resolve`, `extend-sla`, `unclaim`, `notes`) phải từ chối `403` / `400` nếu phiếu đích thuộc loại Drone.
- **Hướng xử lý gợi ý**:
  - Lọc bỏ `isDroneReport(report)` khỏi `LockerService.openReports()`, và bổ sung guard kiểm tra `!isDroneReport(report)` ở mọi thao tác xem/nhận/xử lý/gia hạn phiếu trên luồng `/api/locker-technician/reports/*`.

---

### 🟠 Sai logic / hiển thị sai

#### `BUG-WF04-04` — Nhật ký gia hạn SLA ghi mốc giờ UTC thay vì giờ Việt Nam UTC+7 (`WF04-040`)

- **Mức độ**: 🟠 Sai hiển thị dữ liệu / gây nhầm lẫn mốc hạn trực ca.
- **Vị trí code xác nhận**: `backend/locker-service/.../LockerService.java:1877-1886` (`newDue.format(dtf)` dùng trực tiếp `LocalDateTime` server UTC).
- **Biểu hiện thực tế**:
  - Khi gia hạn SLA cho `RPT-68` thêm 2h, phần thông tin thẻ trên app hiển thị `21:45 28/11/2026` (giờ VN), nhưng dòng nhật ký tự động sinh trong chi tiết phiếu lại ghi **`14:45:13 28/11/2026`** (giờ UTC của server Azure).
- **Hướng xử lý gợi ý**: Chuyển đổi `newDue` từ `ZoneOffset.UTC` sang `ZoneId.of("Asia/Ho_Chi_Minh")` trước khi format vào nội dung nhật ký gia hạn SLA (hoặc lưu mốc chuẩn ISO và format ở client).

#### `BUG-WF04-05` — Chuyển trực tiếp `CHARGING → MAINTENANCE` bỏ qua `lastChargedAt` & hiển thị sai nhãn lịch 1 lần (`WF04-031`)

- **Mức độ**: 🟠 Sai logic phụ & hiển thị sai ngữ nghĩa trên mobile.
- **Vị trí code xác nhận**: `backend/locker-service/.../LockerService.java:2936` vs `:3431`; `mobile/.../schedule_detail_modal_sheet.dart`.
- **Biểu hiện thực tế**:
  - Trên app KTV Drone, khi drone `#10` chuyển từ `CHARGING` sang `MAINTENANCE`, app gọi `POST /api/maintenance/schedules` tạo lịch 1 lần (`#25`, `intervalDays=0`) làm drone vào `MAINTENANCE`, nhưng bỏ qua luồng cập nhật `lastChargedAt` khi kết thúc sạc (`CHARGING`).
  - Trong popup chi tiết `#25`, dù là phiếu 1 lần (`intervalDays=0`), app vẫn hiện tiêu đề `"Định kỳ Drone"` và mô tả `"theo chu kỳ do Quản trị viên thiết lập"`.

#### `BUG-WF04-06` — Push notification hoàn tất phiếu Drone vẫn ghi `"Báo cáo lỗi tủ ..."` (`WF04-036`) + ghi chú cài đặt ảnh nghiệm thu

- **Mức độ**: 🟠 Sai nội dung thông báo đẩy + ghi chú vận hành.
- **Bằng chứng thực tế**:
  - Khi nghiệm thu `RPT-69` (phiếu lỗi Drone `DRONE-WF04-TEST`) trên điện thoại (`p3_67_rpt69_resolved.png`), thông báo đẩy hiển thị tiêu đề `"Báo cáo đã được xử lý xong"` với nội dung: **`"Báo cáo lỗi tủ Tủ demo capstone 3x3 + vali của bạn đã được xử lý xong."`** — dùng nhầm chữ `"lỗi tủ"` và tên trạm thay vì mã Drone.
  - Ngoài ra, trên production hiện tại cấu hình `requireResolutionPhoto = false`, nên gọi API `resolve` không kèm ảnh vẫn trả `200 DRONE_REPORT_RESOLVED` (app vẫn có luồng chụp ảnh tùy chọn và upload Cloudinary hoạt động tốt). Nếu demo yêu cầu bắt buộc có ảnh sau sửa ở mức hệ thống, cần bật `requireResolutionPhoto = true`.

#### `BUG-WF04-07` — Tab `Định kỳ` của KTV Drone không tự tải lại khi có lịch mới & sai `type` thông báo (`WF04-015`, `WF04-003`)

- **Mức độ**: 🟠 Trải nghiệm cập nhật realtime chưa đồng bộ.
- **Biểu hiện thực tế**:
  - Khi KTV Drone `#26` đã mở sẵn màn hình `Định kỳ` (`0` lịch) và Admin vừa tạo lịch `#24`, thông báo `#19732` tới ngay nhưng tab `Định kỳ` vẫn hiện `0` (`p3_11`), buộc phải kéo xuống làm mới thủ công (pull-to-refresh) mới thấy `#24` (`p3_12`). (KTV Tủ khi chuyển từ tab khác sang `Định kỳ` thì có tải lại được `#27`.)
  - Thông báo giao lịch mới cho KTV Tủ `#17` (`#19763`) mang `type = 'locker.report.assigned'` thay vì một mã loại lịch định kỳ riêng.

#### `BUG-WF04-08` — Ảnh hiện trường lúc chấm FAIL lịch tủ không đồng bộ sang `attachments` của phiếu sinh ra & đóng phiếu tủ tự dời `nextDueAt` trước khi kiểm lại (`WF04-023`, `WF04-025`)

- **Mức độ**: 🟠 Thiếu liên kết minh chứng & nhãn hiển thị chưa đúng ngữ cảnh.
- **Biểu hiện thực tế**:
  - Khi hoàn tất `#27` đánh `FAIL` `"Khoa o 3"` kèm ảnh camera thật trên ĐT, ảnh được upload lên Cloudinary và lưu vào `inspectionLog #19` (`photoUrls` có 1 ảnh), **nhưng** phiếu `RPT-70` được tạo ra có `attachments: []` nên KTV mở `RPT-70` sẽ không thấy ảnh hiện trường ở mục `"Ảnh hiện trường (người báo)"`.
  - Chi tiết `RPT-70` (`p4_09b_rpt70_scrolled.png`) hiển thị nhãn **`"Nội dung khách phản ánh:"`** cho phiếu sinh tự động từ bảo trì định kỳ của KTV.
  - Lưu ý hành vi hiện tại (`WF04-025`): ngay khi `RPT-70` được nghiệm thu (`RESOLVED`), `Schedule #27` tự chuyển `pendingReportId=null` và tự dời `nextDueAt` sang `2026-12-28` (`due=False`, sang nhóm `Sắp tới`) **trước** khi KTV thực hiện bước kiểm tra lại `4/4 PASS` (sau khi kiểm tra lại, `nextDueAt` được cập nhật lại `+30 ngày` tính từ lần kiểm tra sau).

---

### 🟡 Lỗi UI / Layout màn hình 360dp / Đa ngôn ngữ (`BUG-WF04-03`)

> Mọi ảnh/XML chụp thực tế trên máy `OPPO CPH2473` (`720×1612` = `360×806 dp`).

1. **Header KTV Tủ (`p4_01_kiosk_home.png`) vỡ bố cục nghiêm trọng do chèn 5 nút icon**:
   - Dòng `'🌅 Chào buổi chiều'` bị ép chiều rộng còn **16px (`[140..156]`) nên biến mất hoàn toàn chữ**!
   - Tên KTV bị cắt cụt `'ky thuat...'` và dòng `'SLA: Bình t...'` bị cắt cụt ngay bên dưới.
   - Tên trạm tủ lặp 2 lần `'Locker2309 · Locker2309'`.
2. **Header KTV Drone (`p3_07`..`p3_57`) cắt chữ & chiếm diện tích lớn**:
   - Dòng chào `'🌤️ Chào buổi ...'`, `'SLA: Bình thường · Chưa c...'`, `'GPS: Hoạt động (±16m) · Vừa x...'` bị ellipsis; header cố định chiếm ~34% chiều cao màn hình.
3. **Các `ModalBottomSheet` thiếu `SafeArea` phía trên (`p3_22`, `p3_66`, `p4_05d`, `p4_11b`)**:
   - `CompleteInspectionSheet` và `_DroneResolveSheet` khi cuộn sát đỉnh để nội dung đè lên thanh trạng thái Android (trùng đồng hồ/biểu tượng hệ thống ở vùng `y=0..65`).
4. **Cắt chữ ở cạnh phải TabBar & bộ lọc sắp xếp**:
   - Tab `'Định kỳ (3...'` bị cắt ở mép phải trên màn hình KTV Tủ (`p4_01_kiosk_home.png`).
   - Chip sắp xếp `'Hạn gần nhất'` trên tab `Việc của tôi` KTV Drone bị đẩy sát mép phải, chỉ nhìn thấy mỗi icon menu (`[662..699]`, `p3_57`).
5. **Từ ngữ thô / tiếng Anh / sai icon**:
   - Nhãn thô tiếng Anh: badge `'DRONE'`, `'KIOSK'`, status chip `'ACTIVE'`, `'STANDARD 0'`, `'XL 0'`, chuỗi giờ `'01:29 PM (13:29)'` trên `ScheduleDetailModalSheet`.
   - Từ kỹ thuật cho người dùng cuối: banner `'...sau khi Backend xác nhận'`, SnackBar `'...theo phản hồi Backend.'`.
   - SnackBar báo thiếu lý do ở `WF04-032` hiển thị mã trạng thái thô `'FAULT'` (`"Cần nhập lý do khi chuyển sang FAULT"`) sau khi dialog chọn trạng thái đã tự đóng.
   - `ScheduleDetailModalSheet` của Drone (`#24`) vẫn hiển thị icon chiếc hộp/tủ thay vì icon Drone, đồng thời cắt tiêu đề `'WF04 DS-04a Bao tri...'`.

---

## 3. Kết quả kiểm tra máy trạng thái (State-Machine Invariants)

Đã kiểm tra cả chuyển trạng thái hợp lệ và các bước nhảy cóc bất hợp pháp qua API + App:

| Thực thể | Chuyển đổi / Hành động kiểm tra | Kết quả thực tế | Đánh giá |
|---|---|---|---|
| **Drone** | `IDLE → MAINTENANCE` (khi tạo lịch `#24`) | Tự chuyển `MAINTENANCE`, chặn điều phối `400 DRONE_NOT_AVAILABLE` | ✅ Đúng |
| **Drone** | `IDLE → RESERVED` / `IN_FLIGHT` (thủ công) | Từ chối `400 DRONE_STATUS_WORKFLOW_MANAGED` | ✅ Đúng |
| **Drone** | `IN_FLIGHT (#800005) → FAULT` (thủ công) | Từ chối `409 DRONE_IN_FLIGHT_USE_FAIL`, drone giữ `IN_FLIGHT` | ✅ Đúng |
| **Drone** | `IN_FLIGHT (#800005)` xóa drone | Từ chối `400 DRONE_ACTIVE_MISSION` | ✅ Đúng |
| **Drone** | `FAULT (#10)` chuyển `IDLE` / `CHARGING` khi phiếu mở | Khóa chip trên app; API trả `409 DRONE_HAS_OPEN_REPORT` | ✅ Đúng |
| **Drone** | `FAULT (#10) → IDLE` sau `RPT-69` `RESOLVED` | Tự động chuyển `IDLE` ngay khi nghiệm thu xong | ✅ Đúng |
| **Ô tủ (`CAB-TU01 #40`)** | `AVAILABLE → FAULT` khi lịch tủ `#27` FAIL gắn ô `#3` | Chuyển `FAULT`, tạo `RPT-70`; tủ vẫn `ACTIVE` | ✅ Đúng |
| **Ô tủ (`#40`)** | `FAULT → out-of-service` / `cleaning` / `return-to-service` | Từ chối `409 BOX_IN_FAULT` / `400 BOX_IN_FAULT` | ✅ Đúng |
| **Ô tủ (`#40`)** | `FAULT → AVAILABLE` sau `RPT-70` `RESOLVED` | Tự phục hồi `AVAILABLE` | ✅ Đúng |
| **Phiếu sự cố** | `OPEN → resolve` / `extend-sla` / `release` (chưa nhận) | Từ chối `409 REPORT_NOT_IN_PROGRESS` / `403 REPORT_NOT_ASSIGNED` | ✅ Đúng |
| **Phiếu sự cố** | `OPEN` khi KTV off-duty → `claim` | Từ chối `409 TECHNICIAN_OFF_DUTY` | ✅ Đúng |
| **Phiếu sự cố** | `OPEN` khi KTV có 3 phiếu quá hạn → `claim` | Từ chối `400 TECHNICIAN_SLA_RESTRICTED` | ✅ Đúng |
| **Phiếu sự cố** | `RESOLVED` → re-`resolve` / `extend-sla` / `unassign` / `claim` | Từ chối `409 REPORT_ALREADY_RESOLVED` / `400 REPORT_NOT_CLAIMABLE` | ✅ Đúng |
| **Lịch bảo trì (Tủ)** | `FAIL` khi còn `pendingReportId` → gửi lại `complete` | Từ chối `409 SCHEDULE_PENDING_REPORT` | ✅ Đúng |
| **Lịch bảo trì (Tủ)** | `inactive (#23)` → `complete` / `PUT` | Từ chối `409 SCHEDULE_INACTIVE` | ✅ Đúng |
| **Lịch bảo trì (Drone)** | `FAIL (#26)` khi `RPT-67` đang `OPEN` → gửi lại `complete` | Trả `200 SCHEDULE_COMPLETED`, dời hạn sai | ❌ Lỗi (`BUG-WF04-01`) |
| **Phiếu Drone ↔ KTV Tủ** | `LOCKER_TECHNICIAN (#17)` liệt kê & `claim` `RPT-58` | `GET /locker-technician/reports` lộ 7 phiếu Drone; `claim` trả `200` | ❌ Lỗi (`BUG-WF04-02`) |

---

## 4. Bảng chi tiết 44 test case (`WF04-001` .. `WF04-044`)

| ID | Tính năng | Mô tả ngắn | KQ L1 | Bằng chứng / Ghi chú |
|---|---|---|---|---|
| `WF04-001` | F-18 | Tạo lịch drone, giao KTV drone | **Passed** | Tạo `#24` (`DRONE-S550-07 #9`, 30d, `#26`): `#9 IDLE→MAINTENANCE`, TB `#19732` |
| `WF04-002` | F-18 | Drone MAINTENANCE không nhận đơn | **Passed** | App chặn chọn; API dispatch trả `400 DRONE_NOT_AVAILABLE` |
| `WF04-003` | F-18 | Tạo lịch tủ, giao KTV tủ | **Passed** | Tạo `#27` (`CAB-TU01 #7`, `#17`): tủ vẫn `ACTIVE`, nhận TB `#19763` |
| `WF04-004` | F-18 | Lịch chọn cả tủ và drone | **Passed** | `POST /api/admin/lockers/schedules` → `400 SCHEDULE_TARGET_INVALID` |
| `WF04-005` | F-18 | Lịch không chọn đối tượng | **Passed** | `400 SCHEDULE_TARGET_INVALID` |
| `WF04-006` | F-18 | Lịch tủ giao cho KTV drone | **Passed** | `400 TECHNICIAN_ROLE_REQUIRED` |
| `WF04-007` | F-18 | Lịch drone giao cho KTV tủ | **Passed** | `400 TECHNICIAN_ROLE_REQUIRED`; `#9` giữ `IDLE` |
| `WF04-008` | F-18 | Giao cho KTV bị khoá | **Passed** | User tạm INACTIVE `#40` → `400 TECHNICIAN_INACTIVE` (đã xóa `#40`) |
| `WF04-009` | F-18 | Không nhập ngày đầu tiên | **Passed** | `#23` chu kỳ 7 ngày, `firstDueDate=null` → `nextDueAt` +7 ngày (`2026-12-05`) |
| `WF04-010` | F-18 | Đổi KTV được giao | **Passed** | Đổi `#23` `#17→#4`: mất ở `#17`, hiện ở `#4`, TB `#19731` |
| `WF04-011` | F-18 | Ngưng lịch rồi hoàn tất | **Passed** | Gửi/sửa `#23` khi ngưng → `409 SCHEDULE_INACTIVE` |
| `WF04-012` | F-18 | Xoá lịch | **Passed** | Thiếu lý do `400 DELETE_REASON_REQUIRED`; có lý do `200`, mất khỏi DS |
| `WF04-013` | F-18 | Khách / KTV gọi API tạo lịch | **Passed** | `#5`, `#17`, `#26` gọi API admin → `403` |
| `WF04-014` | F-18 | Nhắc lịch tới hạn | **Passed** | Lịch tủ `#900008` nhận 1 TB `locker.schedule.due` (`#19582`); drone `#13088`, `#6140` |
| `WF04-015` | F-19 | KTV drone thấy lịch được giao | **Passed** | Thấy `#24` đủ checklist, hạn, ưu tiên (`BUG-WF04-07`: cần kéo refresh) |
| `WF04-016` | F-19 | Mọi mục Pass kèm ảnh | **Passed** | Hoàn tất `#24` trên ĐT + ảnh Cloudinary → `#9` về `IDLE`, hạn +30d (`BUG-WF04-03`) |
| `WF04-017` | F-19 | Có mục NA, còn lại Pass | **Passed** | `#27` 1 `NA` + 3 `PASS` trên ĐT → `PASSED`, log `#21`, hạn `2026-12-28` |
| `WF04-018` | F-19 | Bỏ sót mục checklist | **Passed** | ĐT disable nút hoàn tất (`Còn 1/4...`); API → `400 CHECKLIST_INCOMPLETE` |
| `WF04-019` | F-19 | Kết quả mục không hợp lệ | **Passed** | API gửi `'OK'` → `400 INSPECTION_ITEM_RESULT_INVALID` |
| `WF04-020` | F-19 | Mục không có trong checklist / trùng | **Passed** | `(1) 400 CHECKLIST_ITEM_UNKNOWN`; `(2) 400 CHECKLIST_ITEM_DUPLICATE` |
| `WF04-021` | F-19 | KTV B hoàn tất lịch giao KTV A | **Passed** | KTV B `#4` làm lịch `#27` của `#17` → `403 SCHEDULE_NOT_ASSIGNED` |
| `WF04-022` | F-19 | KTV drone làm lịch tủ | **Passed** | `#26` gọi complete & logs `#27` → `403 SCHEDULE_TARGET_FORBIDDEN` |
| `WF04-023` | F-19 | Lịch tủ: một mục Fail trên ô | **Passed** | ĐT FAIL `'Khoa o 3'` Ô `#3` + ảnh → `RPT-70`, Ô `#3 FAULT`, hạn giữ nguyên (`BUG-WF04-08`) |
| `WF04-024` | F-19 | Hoàn tất lại khi phiếu cũ còn mở | **Passed** | App thay nút bằng `Xử lý phiếu RPT-70`; API → `409 SCHEDULE_PENDING_REPORT` |
| `WF04-025` | F-19 | Đóng phiếu rồi kiểm tra lại | **Passed** | Nghiệm thu `RPT-70` → Ô `#3 AVAILABLE`; kiểm lại 4 PASS → hạn +30d (`BUG-WF04-08`) |
| `WF04-026` | F-19 | Lịch drone: một mục Fail | **Failed** | `BUG-WF04-01`: Mở `RPT-67` & `#10 FAULT`, nhưng dời hạn +14d, `pendingReportId=null`, không chặn gửi lại |
| `WF04-027` | F-19 | Admin xem lịch sử kiểm tra | **Failed** | `BUG-WF04-01`: Lịch sử `#26` thiếu `createdReportId` của `RPT-67` (`null`) |
| `WF04-028` | F-18 | Admin thêm drone | **Passed** | Tạo `DRONE-WF04-TEST #10` (`IDLE`, `CAB-DEMO-01`, `#26`) → hiện tab `Đội bay` |
| `WF04-029` | F-18 | Thêm drone trùng mã | **Passed** | Trùng `DRONE-S550-07` → `400 DRONE_CODE_DUPLICATE` |
| `WF04-030` | F-18 | KTV nhận xử lý drone | **Passed** | Bấm `Nhận xử lý` trên ĐT → gán `#10` cho `#26`, mở khóa điều khiển |
| `WF04-031` | F-14 | Đổi trạng thái Đang sạc / Bảo trì | **Passed** | ĐT đổi `IDLE→CHARGING→MAINTENANCE` (tạo `#25`, ghi chú `BUG-WF04-05`) |
| `WF04-032` | F-14 | Báo Lỗi không có lý do | **Passed** | ĐT hiện SnackBar `'Cần nhập lý do khi chuyển sang FAULT'`; API `400 DRONE_FAULT_REASON_REQUIRED` |
| `WF04-033` | F-14 | Báo Lỗi có lý do | **Passed** | ĐT nhập `'Canh quat nut'` → `#10 FAULT`, mở `RPT-68`, chặn điều phối đơn |
| `WF04-034` | F-14 | Về Sẵn sàng khi còn phiếu mở | **Passed** | ĐT khóa chip `Sẵn sàng`/`Đang sạc`; API → `409 DRONE_HAS_OPEN_REPORT` |
| `WF04-035` | F-18 | Đặt Lỗi cho drone đang bay | **Passed** | `LR-DRN-05 #800005` (`IN_FLIGHT`) → `409 DRONE_IN_FLIGHT_USE_FAIL` |
| `WF04-036` | F-14 | Xử lý phiếu drone tới phục vụ | **Passed** | ĐT xử lý `RPT-69` + nhật ký + ảnh Cloudinary → `RESOLVED`, `#10 IDLE` (`BUG-WF04-06`) |
| `WF04-037` | F-18 | Admin xoá drone | **Passed** | Xóa `#800005 IN_FLIGHT` `400 DRONE_ACTIVE_MISSION`; xóa `#10` không lý do `400`; có lý do `200 DRONE_DECOMMISSIONED` |
| `WF04-038` | F-14 | KTV drone nhận phiếu drone | **Passed** | Nhận `RPT-68` trên ĐT → `IN_PROGRESS`, `slaDueAt = +4h` |
| `WF04-039` | F-14 | KTV drone giữ 3 phiếu trễ hạn | **Passed** | Gán `39,57,58` → app hiện `Hạn chế nhận việc`, nhận `RPT-68` bị chặn `400 TECHNICIAN_SLA_RESTRICTED` |
| `WF04-040` | F-14 | Gia hạn SLA phiếu drone | **Passed** | 2 lần OK (`2/2`), lần 3 `409 SLA_EXTENSION_LIMIT_REACHED` (`BUG-WF04-04`: log ghi giờ UTC) |
| `WF04-041` | F-14 | KTV tủ nhận phiếu drone | **Failed** | `BUG-WF04-02`: `GET /api/locker-technician/reports` lộ 7 phiếu Drone; `PUT .../58/claim` trả `200 REPORT_CLAIMED` |
| `WF04-042` | F-18 | KTV vào ca / hết ca | **Passed** | App cập nhật `onDuty` + GPS; off-duty claim → `409 TECHNICIAN_OFF_DUTY`; đăng xuất tự kết thúc ca |
| `WF04-043` | F-18,F-19 | Kịch bản DS-04a trọn vẹn | **Passed** | `#9 DRONE-S550-07` + lịch `#24`: tạo → `MAINTENANCE` → TB `#19732` → 4 PASS + ảnh trên ĐT → `IDLE` +30d |
| `WF04-044` | F-18,F-19 | Kịch bản DS-04b trọn vẹn | **Passed** | `#7 CAB-TU01` + lịch `#27`: KTV B bị chặn `403` → KTV A FAIL Ô `#3` + ảnh → `RPT-70`, Ô `#3 FAULT`, hạn giữ nguyên |

---

## 5. Xác nhận dọn dẹp dữ liệu production sau test

- `DRONE-S550-07` (`#9`): `IDLE`, `batteryPercent=100`, `lockerId=1`, `assignedTechnicianId=6`.
- `DRONE-WF04-TEST` (`#10`): Đã `DECOMMISSIONED` và ẩn khỏi danh sách Admin & KTV.
- `LR-DRN-05` (`#800005`): Nguyên vẹn `IN_FLIGHT`, `batteryPercent=60`.
- `CAB-TU01` (`#7`): `ACTIVE`, `acceptingOrders=True`, `assignedTechnicianId=17`, các ô `#1, #2, #3, #6, #7 = AVAILABLE`, `#4, #5 = OCCUPIED`.
- `RPT-39`, `RPT-57`, `RPT-58`: Nguyên trạng `OPEN`, `assignedToUserId=null`.
- Tất cả lịch & phiếu test (`#23`..`#27`, user `#40`, `RPT-67`..`RPT-70`): Đã xóa hoặc `RESOLVED`.
- Tài khoản test `#17` và `#26`: Đều đã kết thúc ca (`onDuty=False`).
