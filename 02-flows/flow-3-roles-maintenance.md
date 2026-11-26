# L3 — Vai trò · quản lý drone · trạng thái theo vai trò · hỏng thì chuyển bảo trì

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **45 %** (4,5 / 10) | 2026-09-22 · phần KTV tủ theo backend [#22](https://github.com/LockR-Tech/backend/pull/22), frontend [#15](https://github.com/LockR-Tech/frontend/pull/15), mobile [#20](https://github.com/LockR-Tech/mobile/pull/20); phần ADMIN quản lý drone theo backend [#24](https://github.com/LockR-Tech/backend/pull/24) + frontend [#17](https://github.com/LockR-Tech/frontend/pull/17). Không tính các chỉnh sửa sau 2026-09-21 22:51 mà chủ dự án chưa lấy. | [Trạng thái drone](../diagrams/pdf/drone-status.pdf) · [Trạng thái ô tủ](../diagrams/pdf/locker-cell-status.pdf) · [Kiến trúc](../diagrams/pdf/architecture.pdf) |

Viết tắt: `…` = `src/main/java/com/huynqb/laundrylocker/<service>`, `LS` = `backend/locker-service/…/locker/service/LockerService.java` (nhánh backend #22).

> Phần việc của **KTV tủ** (định tuyến phiếu, khôi phục tài sản, kiểm tra định kỳ) đã làm xong ở các PR trên. Phần **ADMIN quản lý drone** đã sửa lỗi đổi trạng thái/pin qua route admin, giữ phân công KTV và chặn sửa/ngừng drone đang có nhiệm vụ. % chưa đổi vì telemetry/ticket drone, IoT tự phát hiện hỏng và phân quyền service-level vẫn còn thiếu (SEC-02/03/05/06). Quy trình cho KTV: [`backend/scripts/knowledge/huong-dan-ktv-tu.md`](https://github.com/LockR-Tech/backend/blob/main/scripts/knowledge/huong-dan-ktv-tu.md) (backend #23, nạp vào trợ lý hỏi đáp).

## 1. Mục tiêu nghiệp vụ

Mỗi người dùng có đúng vai trò, chỉ thấy và chỉ làm được việc của vai trò đó — **được kiểm soát ở server**. ADMIN tạo tài khoản nhân viên và cấp vai trò. DRONE_TECHNICIAN quản lý đội drone. LOCKER_TECHNICIAN xử lý tủ/ô. Khi một tài sản (drone, tủ, ô, bãi đáp) hỏng — do người báo **hoặc do thiết bị tự phát hiện** — tài sản chuyển sang FAULT/MAINTENANCE, sinh ticket, giao cho kỹ thuật viên, sửa xong trả tài sản về hoạt động; người phụ trách được cảnh báo và mọi thao tác có audit.

## 2. Vai trò hiện có

| Vai trò | Backend | Mobile | Web | Việc chính |
|---|---|---|---|---|
| Khách hàng | `CUSTOMER` (đăng ký luôn là vai trò này, `auth-service/…/AuthService.java:53`); user-service fallback `USER` | `/home` | — | Gửi/thuê, báo hỏng, đánh giá ticket |
| Quản trị | `ADMIN` (bao trùm mọi quyền ở gateway) | chỉ trang "dùng web" | Toàn bộ console, đăng nhập 2FA | Quản trị hệ thống |
| Kỹ thuật viên tủ | `LOCKER_TECHNICIAN` | `/technician-home` (5 tab) | — | Ô tủ, ticket, lịch bảo trì, bãi đáp, thiết bị IoT |
| Kỹ thuật viên drone | `DRONE_TECHNICIAN` | `/maintenance-home` | — | Đội drone, điều phối đơn drone |
| Rác còn sót | — | — | `USER, STAFF, MODERATOR, PARTNER, PARTNER_STAFF, SUPER_ADMIN` (`frontend/fe/src/types/admin/enums.ts:23-29`, `context/auth-context.tsx:358-377`) | Không dùng |

Vai trò là **chuỗi tự do**, không có enum Java; tập hợp lệ `Set.of("CUSTOMER","ADMIN","DRONE_TECHNICIAN","LOCKER_TECHNICIAN")` ở `AuthService.java:90`. Gateway kiểm tra theo tiền tố đường dẫn (`api-gateway/…/JwtGatewayFilter.java:151-171`); **không service nào tự kiểm tra** (`@PreAuthorize` = 0). Tiền tố route khớp tên vai trò: `/api/locker-technician/**` (KTV tủ), `/api/drone-technician/**` (KTV drone), riêng `/api/maintenance/**` chỉ còn lịch bảo trì + inspection-log và cả hai KTV đều vào được.

## 3. Checklist

| # | Hạng mục | Bằng chứng chính | Verdict | Còn thiếu |
|---|---|---|---|---|
| F3.01 | Mô hình vai trò thống nhất | Gateway + auth thống nhất 4 vai trò; mobile `mobile/lib/core/routing/role_routes.dart:7-18` | PARTIAL | Không có enum chung; fallback `USER` không ai hiểu; web còn PARTNER/STAFF |
| F3.02 | Phân quyền thực thi ở server | Chỉ gateway, theo path | PARTIAL | **Lỗ hổng nghiêm trọng**: SEC-02, SEC-03, SEC-05, SEC-06. (Đã vá: DRONE_TECHNICIAN không còn vào được việc của KTV tủ sau khi tách prefix `/api/locker-technician` ↔ `/api/drone-technician`.) |
| F3.03 | ADMIN cấp vai trò, tạo tài khoản nhân viên | Tạo `user-service/…/UserController.java:150-176` + web `CreateUserModal.tsx:72-84`; đổi vai trò `UserController.java:197-200` | PARTIAL | Web không có UI đổi vai trò; API không kiểm vai trò hợp lệ; **khoá user không chặn đăng nhập** (`auth_accounts.status` không đổi); vai trò cũ còn trong token 24h |
| F3.04 | Giao diện theo vai trò | LOCKER_TECHNICIAN `technician_home_page.dart:239-243`; DRONE_TECHNICIAN `maintenance_home_page.dart:57-67` | PARTIAL | Không có role guard trên route mobile (`app_router.dart:108-119`); màn hình chết (`/maintenance/create-report` gọi API không tồn tại, Partner portal web, `LockerCard.tsx:50`) |
| F3.05 | CRUD đội drone + trạng thái | `locker-service/…/LockerController.java:413-469`, `LockerService.java:1569-1764`; admin web `frontend/fe/src/pages/Admin/drones/index.tsx:32-92,252-261,463`; test `LockerServiceDroneFleetTest.java:151-249` | PARTIAL | ADMIN web đã đổi trạng thái/pin qua route admin, không còn lỗi `DRONE_OWNERSHIP_REQUIRED`; còn thiếu vị trí/telemetry và luồng ticket drone cho DRONE_TECHNICIAN |
| F3.06 | Vòng đời trạng thái drone được cưỡng chế | Giá trị hợp lệ, FAULT cần lý do, IN_FLIGHT cần pin > ngưỡng; admin/technician không tự ép `RESERVED`/`IN_FLIGHT`, chỉ được báo `FAULT` khi đang có mission (`LockerService.java:1575-1586`, `LockerServiceDroneFleetTest.java:204-232`) | PARTIAL | Chưa có bảng chuyển trạng thái đầy đủ cho mọi nguồn ghi; endpoint nội bộ vẫn dành cho workflow điều phối; chưa có telemetry/lastSeen |
| F3.07 | Hỏng → tài sản tự chuyển FAULT + mở ticket | Ô: `reportBoxFault` `LS:295` (nhớ trạng thái trước khi hỏng, gộp báo trùng vào phiếu mở `LS:341`); **từ 24/10** khách báo ⇒ ô `PENDING_CHECK` (không cấp đơn mới, chủ đồ vẫn mở bằng mã, phí dừng từ lúc báo), KTV/admin/hệ thống báo ⇒ FAULT (`isConfirmedReporter` `locker-service/…/LockerService.java:680`); KTV từ chối phiếu khi không đúng mô tả ⇒ REJECTED + phản hồi người báo, ô về trạng thái cũ (`rejectReport` `LockerService.java:4733`, app `mobile/…/technician_home_page.dart:4828`); ô chờ kiểm tra quá `app.maintenance.pending-check-hold-hours` tự trở lại hoạt động (`releaseStalePendingChecks` `LockerService.java:4781`); order-service tách dừng phí khỏi khoá mở ô (`box_incident_blocks_access`, `order-service/…/OrderService.java:989`); bãi đáp `LS:438`; báo cáo chặn cả tủ (KTV/ADMIN) ⇒ tủ MAINTENANCE `LS:579-592`; tủ MAINTENANCE/INACTIVE không nhận đặt ô `LS:471,557`; drone FAULT như cũ | PARTIAL | **Chỉ khi người báo**; lỗi phần cứng (FAILED/JAMMED) chỉ ghi log (`iot-service/…/IotService.java:71-74`) — F3-G03 |
| F3.08 | Ticket: giao → xử lý → hoàn tất trả tài sản | Định tuyến cho KTV phụ trách tủ `LS:1948-1960`, gán KTV cho tủ `PUT /api/admin/lockers/{id}/technician` `LS:125`; ADMIN giao phiếu có kiểm vai trò `LS:733`, `LS:2007`; chỉ người được giao hoàn tất, phiếu đã đóng trả 409 `LS:893-898`; đóng phiếu trả ô về trạng thái trước khi hỏng, bãi đáp về OK, tủ do phiếu chặn về ACTIVE, dời hạn lịch chờ phiếu `LS:937`; `clearFault` đi qua phiếu `LS:356`; web chọn KTV phụ trách `frontend/fe/src/pages/Admin/lockers/layout-view.tsx:401`; app "Đã sửa" mở luồng hoàn tất phiếu `mobile/lib/features/locker_ops/presentation/pages/technician_home_page.dart:753-837` | PARTIAL | Phần **drone**: admin đóng phiếu drone không trả drone về hoạt động; DRONE_TECHNICIAN chưa có màn hình phiếu drone (F3-G07) |
| F3.09 | IoT tự đối soát sức khoẻ (offline/hỏng) | Heartbeat chỉ upsert `LockerMqttService.java:94-99` → `IotService.java:50-58` | MISSING | Không `@Scheduled` timeout; sự kiện `iot.device.status.changed` không ai nghe; topic heartbeat dùng tên tủ, không map lockerId |
| F3.10 | Cảnh báo tới người phụ trách + audit | Báo người báo lỗi khi claim/resolve; KTV tủ nhận push/in-app khi có phiếu mới (`locker.report.routed`), khi được admin giao việc (`locker.report.assigned`) và khi lịch kiểm tra tới hạn (`locker.schedule.due`, 07:00 giờ VN) — `LS:1960`, `LS:1309`, `backend/notification-service/…/config/RabbitConfig.java:57,67`; báo DRONE_TECHNICIAN khi có đơn drone `OrderService.java:477` | PARTIAL | Không cảnh báo khi thiết bị offline; ADMIN chưa nhận cảnh báo hỏng; không audit đổi vai trò/trạng thái |

**Điểm:** PARTIAL 9 × 0,5 + MISSING 1 × 0 = 4,5 / 10 = **45 %**.

## 4. Ma trận vai trò × trạng thái (hiện tại)

V = xem · T = kích hoạt chuyển trạng thái. **Chữ đậm = lỗ hổng.**

| Thực thể | CUSTOMER | LOCKER_TECHNICIAN | DRONE_TECHNICIAN | ADMIN |
|---|---|---|---|---|
| Tủ (ACTIVE/MAINTENANCE) | V (GET công khai) | V; T → MAINTENANCE bằng báo cáo chặn tủ | V | T; gán KTV phụ trách |
| Ô tủ | V; T → FAULT ô của đơn mình (`report-box-fault`) | T clear-fault (ô FAULT, qua phiếu nếu có) / out-of-service / cleaning / return / force-open | ✗ 403 | T, kể cả chuỗi tuỳ ý (`updateBoxStatus`) |
| Ticket OPEN/IN_PROGRESS/RESOLVED | V của mình; tạo (không được chặn tủ) | T claim; resolve/log **chỉ khi được giao** | ✗ 403 | T giao/thu hồi (kiểm vai trò) + resolve |
| Lịch kiểm tra định kỳ | — | V; T hoàn tất **chỉ lịch được giao** | V; T hoàn tất lịch drone được giao | T tạo/sửa/giao (`PUT /api/maintenance/schedules/**` chỉ ADMIN) |
| Drone | — | ✗ 403 | T sau khi claim | V; T trạng thái/pin qua route admin, không cần claim; sửa/ngừng bị chặn khi `RESERVED`/`IN_FLIGHT` |
| Bãi đáp OK/FAULT/MAINTENANCE | V | T | ✗ 403 | T |
| Thiết bị IoT | ✗ 403 (`/api/iot/device-status` · `/box-status` chỉ KTV tủ/ADMIN từ 22/10) | T override/restart | ✗ | V |
| Đơn drone (stage) | V của mình | — | T accept/launch/cancel | T |
| Vai trò người dùng | **T tự cấp ADMIN qua `PUT /api/users/{id}`** | — | — | T (API, không UI) |

## 5. Trạng thái ticket (`LockerReport.status`)

`∅ → OPEN` (khách báo hỏng ô / báo cáo tủ / bãi đáp ≠ OK / kiểm tra định kỳ không đạt / drone → FAULT; định tuyến cho KTV phụ trách tủ, không có thì mọi KTV tủ) · `∅ → IN_PROGRESS` (KTV tủ tự báo — tự nhận) → `IN_PROGRESS` (KTV claim, hoặc ADMIN giao) → `RESOLVED` (chỉ người được giao hoặc ADMIN; trả tài sản về hoạt động). ADMIN thu hồi ⇒ về `OPEN`. Phiếu đã `RESOLVED` không giao/thu hồi/đóng lại được (409). Báo trùng một ô đang có phiếu mở được gộp vào phiếu đó. Cột mới (Flyway V18): `category` (BOX/DRONE/LANDING_PAD/LOCKER), `routed_to_user_id`, `schedule_id`, `blocks_locker`.

**Kiểm tra định kỳ:** mỗi mục checklist PASS/FAIL/NA, server tự suy kết quả. ĐẠT ⇒ `next_due_at += interval`. KHÔNG ĐẠT (lịch của tủ) ⇒ không dời hạn, mở phiếu gắn lịch giao cho KTV vừa kiểm tra, `pending_report_id`; phiếu đóng ⇒ dời hạn. Lịch drone giữ cách cũ (luôn dời hạn).

## 6. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F3-G01** | **Vá phân quyền**: `/api/users*` chỉ cho chính mình, bỏ `roles/status` khỏi request không phải admin; `PATCH /api/orders/{id}/status` chỉ ADMIN; notification chỉ của mình; service tự kiểm `X-User-Roles` + chủ sở hữu (locker, iot, order) — SEC-02/03/05/06. **2026-10-22 (nhánh `sec/sec-03-05-06-khoa-api-don-iot`, chưa PR):** gỡ `PATCH /api/orders/{id}/status`, `POST /api/orders/{id}/checkout`, `POST /api/orders`, `GET /api/orders`, `GET /api/orders/{pin,code,access}/…`; đọc đơn kiểm chủ/người nhận/ADMIN; báo hỏng ô + đẩy trạng thái IoT chỉ KTV tủ/ADMIN; WebSocket topic chung chỉ ADMIN. **2026-10-11:** bỏ `roles/status` (backend #54, đã deploy); `/api/users*` chỉ chính chủ hoặc ADMIN ([backend #55](https://github.com/LockR-Tech/backend/pull/55), chưa merge) | `user-service/…/UserController.java`, `order-service/…/OrderController.java:75`, `notification-service/…/NotificationController.java:105`, `JwtGatewayFilter.java` | F3.02 |
| **F3-G02** | **Nhất quán ticket ↔ tài sản**: ~~`clearFault` đi qua phiếu; resolve kiểm người được giao, trả ô (về trạng thái trước khi hỏng)/bãi đáp/tủ; chống trùng báo hỏng ô~~ **đã làm** (backend #22). Còn: trả drone khi đóng phiếu drone; bỏ `updateBoxStatus`; bảng chuyển trạng thái drone | `locker-service/…/LockerService.java` | F3.06, F3.08 |
| **F3-G03** | **IoT tự đối soát**: timeout heartbeat → OFFLINE; tiêu thụ `iot.device.status.changed` + kết quả FAILED/JAMMED → `/internal/boxes/{id}/fault`; map tên tủ → lockerId, slotIndex → boxId | `iot-service/…/IotService.java` + `@Scheduled`, `LockerMqttService.java:94-111`, `iot/services/heartbeat_service.py:120` | F3.07, F3.09 |
| **F3-G04** | Cảnh báo lỗi tới ~~LOCKER_TECHNICIAN~~ (**đã làm**: phiếu mới, giao việc, lịch tới hạn — backend #22) / ADMIN (thiết bị offline) + audit log đổi vai trò / trạng thái / ô | `notification-service/…/config/RabbitConfig.java`, bảng audit mới | F3.10 |
| **F3-G05** | Quản lý vai trò trên web (dùng `useUpdateUserRolesMutation`); khoá tài khoản đồng bộ `auth_accounts` + thu hồi refresh token; rút TTL access token. **2026-10-11:** khoá đồng bộ + thu hồi refresh token đã có (backend #54); thay cho rút TTL, gateway hỏi `GET /internal/auth/accounts/{id}/active` (nhớ 30 s) và trả 401 cho tài khoản không còn ACTIVE ([backend #55](https://github.com/LockR-Tech/backend/pull/55)); xoá người dùng đặt tài khoản đăng nhập `DELETED` và nhả email/SĐT (`DELETE /internal/auth/users/{userId}`, [backend #56](https://github.com/LockR-Tech/backend/pull/56)) | `frontend/fe/src/pages/Admin/users/detail.tsx`, `auth-service/…/AuthService.java` | F3.03 |
| **F3-G06** | Đội drone: ~~ADMIN bỏ qua claim khi đổi trạng thái/pin~~ **đã làm** (backend #24, frontend #17); còn vị trí/lastSeen + telemetry, giữ chỗ drone khi accept, gộp 1 mô hình điều phối, guard pin trên mọi đường IN_FLIGHT | `LockerService.java`, `pages/Admin/drones/index.tsx`, `DroneDeliveryService.java` vs `DroneOrderMaintenanceService.java` | F3.05, F3.06 |
| **F3-G07** | Ticket: ~~ADMIN giao/giao lại (endpoint + UI)~~ **đã làm** (kiểm vai trò, thông báo KTV). Còn: DRONE_TECHNICIAN có màn hình ticket drone | `maintenance_home_page.dart` | F3.08 |
| **F3-G08** | ~~Tủ ở MAINTENANCE phải chặn đặt ô~~ — **đã làm** (`LS:471`: `reserveBox`, `findAvailableBox`, danh sách ô trống, `availableBoxes = 0`) | — | F3.07 |
| **F3-G09** | Dọn UI chết + role guard mobile: enum vai trò web, Partner portal, `BoxSettingModal` ghi `MAINTENANCE`, `LockerCard.tsx:50`; route legacy `features/maintenance/*` | `frontend/fe/src/…`, `mobile/lib/core/routing/app_router.dart` | F3.01, F3.04 |
| **F3-G10** | Một enum `Role` dùng chung trong `common-lib`, validate ở auth + user-service | `backend/common-lib` | F3.01 |
| **F3-G11** | Thử mở ô qua Bluetooth: admin cho từng tài khoản khách thử trên từng tủ (trang chi tiết tủ), app có nút ở Hồ sơ, chọn ô bất kỳ, Pi kiểm mã Ed25519 rồi kích relay — [ble-open-contract](../01-overview/ble-open-contract.md). Công cụ thử phần cứng, không tính vào checklist | `backend/iot-service/…/BleTestService.java`, `iot/services/ble_gatt_service.py`, `mobile/lib/features/locker_ops/presentation/pages/ble_test_page.dart`, `frontend/fe/src/pages/Admin/lockers/components/BluetoothTestPanel.tsx` | — |
| **F3-G12** | **Lắp đặt & nghiệm thu tủ**: admin lập hồ sơ (KTV lắp đặt, lịch, hiện trường, phần cứng) ⇒ tủ `PLANNED → INSTALLING → COMMISSIONING → ACTIVE`, khách chỉ thấy tủ ACTIVE; checklist 8 bước — bước máy kiểm được do hệ thống tự xác nhận, bước làm tay KTV xác nhận kèm ảnh; gán Pi bằng QR kiosk — [§ 8](#8-lắp-đặt--nghiệm-thu-tủ-f3-g12). Tính năng mới, không tính vào checklist. Đợt 1 đã merge ([backend #138](https://github.com/LockR-Tech/backend/pull/138), [frontend #101](https://github.com/LockR-Tech/frontend/pull/101), [mobile #134](https://github.com/LockR-Tech/mobile/pull/134), [iot #48](https://github.com/LockR-Tech/iot/pull/48)); sửa lỗi sau khi chạy thử E2E (11/11) đã merge lên `main`: [backend #142](https://github.com/LockR-Tech/backend/pull/142), [mobile #136](https://github.com/LockR-Tech/mobile/pull/136), [iot #49](https://github.com/LockR-Tech/iot/pull/49) | `backend/locker-service/…/service/LockerInstallationService.java`, `backend/iot-service/…/service/CabinetCommissioningService.java`, `frontend/fe/src/pages/Admin/lockers/components/InstallationPanel.tsx`, `mobile/lib/features/locker_ops/presentation/pages/installation_detail_page.dart`, `iot/ui/src/screens/SetupScreen.jsx` | — |
| **F3-G13** | **Hướng dẫn lần đầu trên màn hình** (onboarding tour) cho web admin và app mobile: hộp "Chào <tên>" (Bỏ qua / Bỏ qua vĩnh viễn / Xem hướng dẫn), lớp khoanh theo nhóm chức năng và vai trò, nhóm có phiên bản ⇒ hộp "Có hướng dẫn mới", mở lại bằng nút "Hướng dẫn", trang HDSD dựng từ cùng nội dung. Trạng thái lưu ở user-service (V9) dùng chung mọi thiết bị — [ADR-0011](../adr/0011-huong-dan-lan-dau-tren-man-hinh.md). Tính năng mới, không tính vào checklist. **Đã lên production 2026-11-21** (backend [#143](https://github.com/LockR-Tech/backend/pull/143), mobile [#137](https://github.com/LockR-Tech/mobile/pull/137) [#138](https://github.com/LockR-Tech/mobile/pull/138) [#139](https://github.com/LockR-Tech/mobile/pull/139), frontend [#107](https://github.com/LockR-Tech/frontend/pull/107)): phủ đủ mọi màn hình và tính năng: 288 nhóm / 1.468 bước — web admin 152 (mọi trang, trang chi tiết, tab, hộp thoại, menu dòng; có trang đăng nhập + 2FA), app 110 (khách, KTV tủ, KTV drone; có màn trước đăng nhập), kiosk tại tủ 26; 15 nhóm tổng quan (`intro`) tự chạy lần đầu, nhóm chi tiết mở từ nút "Hướng dẫn"; trang chi tiết / tab / hộp thoại mở bằng `via`; luồng cần đơn thật và màn trước đăng nhập chỉ có ở HDSD (`manualOnly`). Test bắt buộc: route web / app nào cũng có hướng dẫn hoặc ngoại lệ có lý do. Trang HDSD web `/admin/huong-dan` + màn hình HDSD trong app; ảnh chụp tự động `npm run hdsd:capture` (web: dữ liệu giả, app: tài khoản demo) | `frontend/fe/public/onboarding/tours.json`, `frontend/fe/src/onboarding/`, `frontend/fe/scripts/hdsd/capture.mjs`, `mobile/lib/features/onboarding/`, `backend/user-service/…/service/OnboardingService.java` | — |
| **F3-G14** | **Dọn sạch web admin**: gỡ hẳn ví Lock.R khỏi giao diện admin và backend (nạp ví, rút tiền, điều chỉnh số dư, biến động ví, phương thức `WALLET` khi thanh toán, nhóm cài đặt "Nạp ví"); DB giữ nguyên, giao dịch ví cũ hiện là "Phương thức cũ", app vẫn đọc lịch sử giao dịch (`/api/wallet/transactions`, `/spending-stats`, `/total-by-method`). Trang Cài đặt có tiếng Anh: backend chỉ dịch nhóm/tên/mô tả/đơn vị, giá trị admin nhập giữ nguyên (`@KeepServerText`), lỗi nhập sai viết tiếng Việt kèm bản tiếng Anh. Trang Thông báo lọc + phân trang ở backend (`/api/admin/notifications/search`, `/stats`, `/bulk-delete`) thay vì tải cả bảng, không hiện thông báo ví cũ. Xoá mềm kèm lý do cho phiếu sự cố, lịch kiểm tra, tài liệu trợ lý (locker V35, assistant V2). Mã thô → nhãn, số/tiền theo ngôn ngữ, chữ vi/en ở mọi trang. Cụm "Giả lập & demo" (ẩn tủ/điểm gửi demo, tắt thử Bluetooth, tắt/bật hàng loạt) và bản tiếng Anh cho mọi quy tắc đã lên `main`: backend [#144](https://github.com/LockR-Tech/backend/pull/144) [#145](https://github.com/LockR-Tech/backend/pull/145), frontend [#111](https://github.com/LockR-Tech/frontend/pull/111). Không tính vào checklist. Phần còn lại ở nhánh `fix/f3-g14-don-sach-admin` (backend, frontend), chưa mở PR | `backend/common-lib/…/settings/BusinessSettingsController.java`, `backend/notification-service/…/service/AdminNotificationQueryService.java`, `backend/payment-service/…/service/TransactionHistoryService.java`, `frontend/fe/src/pages/Admin/notifications/hooks/useNotifications.ts` | — |
| **F3-G14** | **Chuẩn bị vận hành chính thức: cụm "Giả lập & demo" + chuẩn song ngữ.** Web admin › Cấu hình nghiệp vụ có thẻ gom 7 cờ giả lập ở 5 service — nút giả lập thanh toán, drone DEMO, tủ demo, điểm gửi demo, thử mở ô qua Bluetooth, mở thử ô bằng QR, thử nắp trượt — với "Tắt toàn bộ (vận hành chính thức)" và "Bật chế độ demo" (bật lại 5 mục demo; 2 công cụ thử tủ điều khiển phần cứng thật nên bật riêng). 3 cờ mới: ẩn tủ demo (800001–800013) và điểm gửi demo (800001–800007) với khách thường — admin và tài khoản `*@demo.lockr.test` vẫn thấy, order-service từ chối đơn gửi/thuê mới vào tủ demo đã ẩn — và tắt thử mở ô qua Bluetooth (quyền đã cấp vẫn giữ). Song ngữ: bảng dịch server có đủ nhãn/nhóm/mô tả/đơn vị của mọi quy tắc nghiệp vụ (trang Cấu hình hiện tiếng Anh khi chọn English), test `i18n-keys` chặn khoá chữ thiếu trên web (sửa 38 mã khoá thô do frontend #110 đặt chữ sai nhánh), app thay chữ tiếng Việt viết cứng; thông báo tiếng Anh không còn tráo số sao/mã phiếu và dịch trọn lý do drone ghép nhiều vế. Tính năng vận hành, không tính vào checklist. PR: backend [#144](https://github.com/LockR-Tech/backend/pull/144), frontend [#111](https://github.com/LockR-Tech/frontend/pull/111), mobile [#141](https://github.com/LockR-Tech/mobile/pull/141); sửa sau rà song ngữ: backend [#145](https://github.com/LockR-Tech/backend/pull/145), mobile [#142](https://github.com/LockR-Tech/mobile/pull/142) | `frontend/fe/src/pages/Admin/settings/SimulationClusterCard.tsx`, `backend/locker-service/…/settings/LockerSettingsCatalog.java`, `backend/store-service/…/settings/StoreSettingsCatalog.java`, `backend/iot-service/…/settings/IotSettingsCatalog.java`, `backend/common-lib/src/main/resources/i18n/server-text-en.json` | — |

## 7. Xoá mềm ở trang admin

Quyết định: [ADR-0009](../adr/0009-xoa-mem-co-ly-do-o-trang-admin.md). Không thêm hạng mục checklist nên % giữ nguyên. Frontend đã merge ([#83](https://github.com/LockR-Tech/frontend/pull/83)), backend còn ở nhánh `feat/admin-xoa-mem-co-ly-do`.

| Đối tượng | Điều kiện từ chối | Bằng chứng |
|---|---|---|
| Tủ, một hoặc nhiều | Có ô đang chứa hàng hoặc giữ chỗ; còn drone đang hoạt động ở trạm; xoá hàng loạt không chọn tủ nào | `backend/locker-service/…/service/LockerService.java:300,340` |
| Ô tủ | Ô đang chứa hàng hoặc giữ chỗ | `LockerService.java:497` |
| Drone (nhả bộ điều khiển, gỡ KTV) | Drone đang giữ chỗ hoặc đang bay | `LockerService.java:3130` · `frontend/fe/src/pages/Admin/drones/index.tsx:284` |
| Người dùng | Tự xoá chính mình | `backend/user-service/…/controller/UserController.java:499` · `frontend/fe/src/pages/Admin/users/index.tsx:40` |

Mọi trường hợp đều trả `DELETE_REASON_REQUIRED` khi thiếu lý do. Hộp nhập lý do dùng chung: `frontend/fe/src/components/shared/data-table/DeleteReasonDialog.tsx:32`.

Phân biệt với ma trận vai trò ở § 4: chỉ ADMIN gọi được các API này (`/api/admin/**`).

## 8. Lắp đặt & nghiệm thu tủ (F3-G12)

Trước đây admin tạo tủ là khách thấy ngay, không có thông tin lắp đặt cho admin hay KTV. Nay tủ mới đi qua một **hồ sơ lắp đặt**. Tính năng mới nên không thêm hạng mục checklist, % giữ nguyên. Đợt 1 đã merge ([backend #138](https://github.com/LockR-Tech/backend/pull/138), [frontend #101](https://github.com/LockR-Tech/frontend/pull/101), [mobile #134](https://github.com/LockR-Tech/mobile/pull/134), [iot #48](https://github.com/LockR-Tech/iot/pull/48)); PR sửa lỗi sau khi chạy thử E2E trên production (11/11): [backend #142](https://github.com/LockR-Tech/backend/pull/142), [mobile #136](https://github.com/LockR-Tech/mobile/pull/136), [iot #49](https://github.com/LockR-Tech/iot/pull/49).

**Vòng đời** (trạng thái tủ đổi theo hồ sơ, admin không đổi tay được khi hồ sơ còn mở — `LOCKER_INSTALLATION_OPEN`):

| Hồ sơ | Tủ | Ai chuyển | Khách |
|---|---|---|---|
| `SCHEDULED` | `PLANNED` | Admin lập hồ sơ (tủ không được có ô giữ hàng / giữ chỗ) | Không thấy, không đặt được |
| `IN_PROGRESS` | `INSTALLING` | KTV bấm Bắt đầu; admin trả lại cũng về đây | Không thấy |
| `SUBMITTED` | `COMMISSIONING` | KTV gửi duyệt khi đủ | Không thấy |
| `APPROVED` | `ACTIVE` | Admin duyệt (server kiểm lại dữ liệu tủ) | Thấy và đặt được |
| `CANCELLED` | trạng thái trước khi lập hồ sơ (hoặc `INACTIVE`) | Admin huỷ kèm lý do | Như trạng thái đó |

Danh sách tủ cho khách / kiosk (`GET /api/lockers`, `/api/iot/lockers`) bỏ tủ đang lắp đặt; đặt ô chỉ nhận tủ `ACTIVE` (trước đây chỉ loại `MAINTENANCE`/`INACTIVE`) — `backend/locker-service/…/service/LockerService.java` `isBookable`, `customerVisible`.

**Checklist** — KTV không chỉ tích ô:

| Bước | Ai xác nhận | Cách |
|---|---|---|
| Lắp khung (`MOUNTING`) | KTV | Chụp ảnh (bắt buộc) rồi xác nhận |
| Mạng (`NETWORK`) | Hệ thống | Bộ điều khiển của tủ online (heartbeat) |
| Gán bộ điều khiển (`CONTROLLER`) | Hệ thống | Pi báo cài sơ đồ ô `COMPLETED` sau khi KTV quét QR |
| Cấu hình phần cứng (`HARDWARE_CONFIG`) | Hệ thống | Admin áp cấu hình từ web, tủ xác nhận (áp vẫn chỉ ADMIN) |
| Mở thử từng ô (`BOX_TEST`) | Hệ thống | Lệnh mở thử mới nhất của **từng ô** từ khi bắt đầu lắp (`cabinet_control_logs`) |
| Nắp (`LID`) | Hệ thống / KTV | Mở + đóng nắp thành công; tủ không có nắp thì KTV đánh dấu không áp dụng kèm lý do |
| Kiosk (`KIOSK`) | KTV | Chụp ảnh (bắt buộc) rồi xác nhận |
| Bluetooth (`BLUETOOTH`) | KTV | Xác nhận hoặc không áp dụng |

Gửi duyệt cần mọi bước đạt / không áp dụng và **ít nhất 2 ảnh hiện trường**. Ảnh dùng purpose `INSTALLATION_PHOTO` ([media-storage](../01-overview/media-storage.md)).

**Gán Pi bằng QR:** Pi chưa phục vụ tủ nào (`/system/state` → `isConfigured = false`) thì kiosk hiện QR `LOCKR-PI:<MAC>` (`iot/ui/src/screens/SetupScreen.jsx`) và báo lại discovery mỗi 60 s (`UnconfiguredAnnouncer` trong `iot/services/discovery_service.py`) để backend luôn thấy Pi online (cửa sổ 150 s). App KTV quét ⇒ `POST /api/locker-technician/cabinet/{lockerId}/controller` ⇒ iot-service kiểm Pi đã tự khai báo, online, không thuộc tủ khác rồi gửi lệnh setup + mở thử từng ô như admin gán trên web. Quét không được thì chọn trong `GET …/controller/candidates`.

**Thông báo:** `locker.installation.assigned` (giao hồ sơ) và `locker.installation.reviewed` (duyệt / trả lại / huỷ) tới KTV, `referenceType = LOCKER_INSTALLATION`; app mở `/technician-installations?id=`.
