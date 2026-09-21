# L3 — Vai trò · quản lý drone · trạng thái theo vai trò · hỏng thì chuyển bảo trì

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **45 %** (4,5 / 10) | 2026-09-21 · phần KTV tủ theo backend [#22](https://github.com/LockR-Tech/backend/pull/22) · frontend [#15](https://github.com/LockR-Tech/frontend/pull/15) · mobile [#20](https://github.com/LockR-Tech/mobile/pull/20) (đã merge 2026-09-21); phần còn lại như rà soát 2026-09-13 | [Trạng thái drone](../diagrams/pdf/drone-status.pdf) · [Trạng thái ô tủ](../diagrams/pdf/locker-cell-status.pdf) · [Kiến trúc](../diagrams/pdf/architecture.pdf) |

Viết tắt: `…` = `src/main/java/com/huynqb/laundrylocker/<service>`, `LS` = `backend/locker-service/…/locker/service/LockerService.java` (nhánh backend #22).

> Phần việc của **KTV tủ** (định tuyến phiếu, khôi phục tài sản, kiểm tra định kỳ) đã làm xong ở các PR trên; % không đổi vì các hạng mục còn thiếu nằm ở drone, IoT tự phát hiện hỏng và phân quyền (SEC-02/03/05/06). Quy trình cho KTV: [`backend/scripts/knowledge/huong-dan-ktv-tu.md`](https://github.com/LockR-Tech/backend/blob/main/scripts/knowledge/huong-dan-ktv-tu.md) (backend #23, nạp vào trợ lý hỏi đáp).

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
| F3.05 | CRUD đội drone + trạng thái | `locker-service/…/LockerController.java:303-319`, `LockerService.java:612-750`; mobile claim/status/pin `maintenance_home_page.dart:932-1195`; web `pages/Admin/drones/index.tsx` | PARTIAL | Không có vị trí/telemetry; **ADMIN web đổi trạng thái/pin luôn lỗi** `DRONE_OWNERSHIP_REQUIRED` |
| F3.06 | Vòng đời trạng thái drone được cưỡng chế | Giá trị hợp lệ, FAULT cần lý do, IN_FLIGHT cần pin > 20 (`LockerService.java:671-690`) | PARTIAL | Mọi → mọi; 3 đường ghi trạng thái với guard khác nhau; endpoint nội bộ không kiểm chủ sở hữu |
| F3.07 | Hỏng → tài sản tự chuyển FAULT + mở ticket | Ô: `reportBoxFault` `LS:295` (nhớ trạng thái trước khi hỏng, gộp báo trùng vào phiếu mở `LS:341`); bãi đáp `LS:438`; báo cáo chặn cả tủ (KTV/ADMIN) ⇒ tủ MAINTENANCE `LS:579-592`; tủ MAINTENANCE/INACTIVE không nhận đặt ô `LS:471,557`; drone FAULT như cũ | PARTIAL | **Chỉ khi người báo**; lỗi phần cứng (FAILED/JAMMED) chỉ ghi log (`iot-service/…/IotService.java:71-74`) — F3-G03 |
| F3.08 | Ticket: giao → xử lý → hoàn tất trả tài sản | Định tuyến cho KTV phụ trách tủ `LS:1948-1960`, gán KTV cho tủ `PUT /api/admin/lockers/{id}/technician` `LS:125`; ADMIN giao phiếu có kiểm vai trò `LS:733`, `LS:2007`; chỉ người được giao hoàn tất, phiếu đã đóng trả 409 `LS:893-898`; đóng phiếu trả ô về trạng thái trước khi hỏng, bãi đáp về OK, tủ do phiếu chặn về ACTIVE, dời hạn lịch chờ phiếu `LS:937`; `clearFault` đi qua phiếu `LS:356`; web chọn KTV phụ trách `frontend/fe/src/pages/Admin/lockers/layout-view.tsx:401`; app "Đã sửa" mở luồng hoàn tất phiếu `mobile/lib/features/locker_ops/presentation/pages/technician_home_page.dart:753-837` | PARTIAL | Phần **drone**: admin đóng phiếu drone không trả drone về hoạt động; DRONE_TECHNICIAN chưa có màn hình phiếu drone (F3-G07) |
| F3.09 | IoT tự đối soát sức khoẻ (offline/hỏng) | Heartbeat chỉ upsert `LockerMqttService.java:94-99` → `IotService.java:50-58` | MISSING | Không `@Scheduled` timeout; sự kiện `iot.device.status.changed` không ai nghe; topic heartbeat dùng tên tủ, không map lockerId |
| F3.10 | Cảnh báo tới người phụ trách + audit | Báo người báo lỗi khi claim/resolve; KTV tủ nhận push/in-app khi có phiếu mới (`locker.report.routed`), khi được admin giao việc (`locker.report.assigned`) và khi lịch kiểm tra tới hạn (`locker.schedule.due`, 07:00 giờ VN) — `LS:1960`, `LS:1309`, `backend/notification-service/…/config/RabbitConfig.java:57,67`; báo DRONE_TECHNICIAN khi có đơn drone `OrderService.java:477` | PARTIAL | Không cảnh báo khi thiết bị offline; ADMIN chưa nhận cảnh báo hỏng; không audit đổi vai trò/trạng thái |

**Điểm:** PARTIAL 9 × 0,5 + MISSING 1 × 0 = 4,5 / 10 = **45 %**.

## 4. Ma trận vai trò × trạng thái (hiện tại)

V = xem · T = kích hoạt chuyển trạng thái. **Chữ đậm = lỗ hổng.**

| Thực thể | CUSTOMER | LOCKER_TECHNICIAN | DRONE_TECHNICIAN | ADMIN |
|---|---|---|---|---|
| Tủ (ACTIVE/MAINTENANCE) | V (GET công khai) | V; T → MAINTENANCE bằng báo cáo chặn tủ | V | T; gán KTV phụ trách |
| Ô tủ | V; **T → FAULT với mọi ô** | T clear-fault (ô FAULT, qua phiếu nếu có) / out-of-service / cleaning / return / force-open | ✗ 403 | T, kể cả chuỗi tuỳ ý (`updateBoxStatus`) |
| Ticket OPEN/IN_PROGRESS/RESOLVED | V của mình; tạo (không được chặn tủ) | T claim; resolve/log **chỉ khi được giao** | ✗ 403 | T giao/thu hồi (kiểm vai trò) + resolve |
| Lịch kiểm tra định kỳ | — | V; T hoàn tất **chỉ lịch được giao** | V; T hoàn tất lịch drone được giao | T tạo/sửa/giao (`PUT /api/maintenance/schedules/**` chỉ ADMIN) |
| Drone | — | ✗ 403 | T sau khi claim | V; T sau claim ⇒ web lỗi |
| Bãi đáp OK/FAULT/MAINTENANCE | V | T | ✗ 403 | T |
| Thiết bị IoT | **T giả trạng thái qua `/api/iot/device-status`** | T override/restart | ✗ | V |
| Đơn drone (stage) | V của mình | — | T accept/launch/cancel | T |
| Vai trò người dùng | **T tự cấp ADMIN qua `PUT /api/users/{id}`** | — | — | T (API, không UI) |

## 5. Trạng thái ticket (`LockerReport.status`)

`∅ → OPEN` (khách báo hỏng ô / báo cáo tủ / bãi đáp ≠ OK / kiểm tra định kỳ không đạt / drone → FAULT; định tuyến cho KTV phụ trách tủ, không có thì mọi KTV tủ) · `∅ → IN_PROGRESS` (KTV tủ tự báo — tự nhận) → `IN_PROGRESS` (KTV claim, hoặc ADMIN giao) → `RESOLVED` (chỉ người được giao hoặc ADMIN; trả tài sản về hoạt động). ADMIN thu hồi ⇒ về `OPEN`. Phiếu đã `RESOLVED` không giao/thu hồi/đóng lại được (409). Báo trùng một ô đang có phiếu mở được gộp vào phiếu đó. Cột mới (Flyway V18): `category` (BOX/DRONE/LANDING_PAD/LOCKER), `routed_to_user_id`, `schedule_id`, `blocks_locker`.

**Kiểm tra định kỳ:** mỗi mục checklist PASS/FAIL/NA, server tự suy kết quả. ĐẠT ⇒ `next_due_at += interval`. KHÔNG ĐẠT (lịch của tủ) ⇒ không dời hạn, mở phiếu gắn lịch giao cho KTV vừa kiểm tra, `pending_report_id`; phiếu đóng ⇒ dời hạn. Lịch drone giữ cách cũ (luôn dời hạn).

## 6. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F3-G01** | **Vá phân quyền**: `/api/users*` chỉ cho chính mình, bỏ `roles/status` khỏi request không phải admin; `PATCH /api/orders/{id}/status` chỉ ADMIN; notification chỉ của mình; service tự kiểm `X-User-Roles` + chủ sở hữu (locker, iot, order) — SEC-02/03/05/06 | `user-service/…/UserController.java`, `order-service/…/OrderController.java:75`, `notification-service/…/NotificationController.java:105`, `JwtGatewayFilter.java` | F3.02 |
| **F3-G02** | **Nhất quán ticket ↔ tài sản**: ~~`clearFault` đi qua phiếu; resolve kiểm người được giao, trả ô (về trạng thái trước khi hỏng)/bãi đáp/tủ; chống trùng báo hỏng ô~~ **đã làm** (backend #22). Còn: trả drone khi đóng phiếu drone; bỏ `updateBoxStatus`; bảng chuyển trạng thái drone | `locker-service/…/LockerService.java` | F3.06, F3.08 |
| **F3-G03** | **IoT tự đối soát**: timeout heartbeat → OFFLINE; tiêu thụ `iot.device.status.changed` + kết quả FAILED/JAMMED → `/internal/boxes/{id}/fault`; map tên tủ → lockerId, slotIndex → boxId | `iot-service/…/IotService.java` + `@Scheduled`, `LockerMqttService.java:94-111`, `iot/services/heartbeat_service.py:120` | F3.07, F3.09 |
| **F3-G04** | Cảnh báo lỗi tới ~~LOCKER_TECHNICIAN~~ (**đã làm**: phiếu mới, giao việc, lịch tới hạn — backend #22) / ADMIN (thiết bị offline) + audit log đổi vai trò / trạng thái / ô | `notification-service/…/config/RabbitConfig.java`, bảng audit mới | F3.10 |
| **F3-G05** | Quản lý vai trò trên web (dùng `useUpdateUserRolesMutation`); khoá tài khoản đồng bộ `auth_accounts` + thu hồi refresh token; rút TTL access token | `frontend/fe/src/pages/Admin/users/detail.tsx`, `auth-service/…/AuthService.java` | F3.03 |
| **F3-G06** | Đội drone: vị trí/lastSeen + telemetry; ADMIN bỏ qua claim; giữ chỗ drone khi accept; gộp 1 mô hình điều phối; guard pin trên mọi đường IN_FLIGHT | `LockerService.java:823`, `pages/Admin/drones/index.tsx`, `DroneDeliveryService.java` vs `DroneOrderMaintenanceService.java` | F3.05, F3.06 |
| **F3-G07** | Ticket: ~~ADMIN giao/giao lại (endpoint + UI)~~ **đã làm** (kiểm vai trò, thông báo KTV). Còn: DRONE_TECHNICIAN có màn hình ticket drone | `maintenance_home_page.dart` | F3.08 |
| **F3-G08** | ~~Tủ ở MAINTENANCE phải chặn đặt ô~~ — **đã làm** (`LS:471`: `reserveBox`, `findAvailableBox`, danh sách ô trống, `availableBoxes = 0`) | — | F3.07 |
| **F3-G09** | Dọn UI chết + role guard mobile: enum vai trò web, Partner portal, `BoxSettingModal` ghi `MAINTENANCE`, `LockerCard.tsx:50`; route legacy `features/maintenance/*` | `frontend/fe/src/…`, `mobile/lib/core/routing/app_router.dart` | F3.01, F3.04 |
| **F3-G10** | Một enum `Role` dùng chung trong `common-lib`, validate ở auth + user-service | `backend/common-lib` | F3.01 |
