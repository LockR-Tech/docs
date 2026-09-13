# L3 — Vai trò · quản lý drone · trạng thái theo vai trò · hỏng thì chuyển bảo trì

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **45 %** (4,5 / 10) | 2026-09-13 · backend `705c556` · mobile `5890184` · frontend `e1b9a73` · iot `927b057` | [Trạng thái drone](../diagrams/pdf/drone-status.pdf) · [Trạng thái ô tủ](../diagrams/pdf/locker-cell-status.pdf) · [Kiến trúc](../diagrams/pdf/architecture.pdf) |

Viết tắt: `…` = `src/main/java/com/huynqb/laundrylocker/<service>`.

## 1. Mục tiêu nghiệp vụ

Mỗi người dùng có đúng vai trò, chỉ thấy và chỉ làm được việc của vai trò đó — **được kiểm soát ở server**. ADMIN tạo tài khoản nhân viên và cấp vai trò. MAINTENANCE quản lý đội drone. TECHNICIAN xử lý tủ/ô. Khi một tài sản (drone, tủ, ô, bãi đáp) hỏng — do người báo **hoặc do thiết bị tự phát hiện** — tài sản chuyển sang FAULT/MAINTENANCE, sinh ticket, giao cho kỹ thuật viên, sửa xong trả tài sản về hoạt động; người phụ trách được cảnh báo và mọi thao tác có audit.

## 2. Vai trò hiện có

| Vai trò | Backend | Mobile | Web | Việc chính |
|---|---|---|---|---|
| Khách hàng | `CUSTOMER` (đăng ký luôn là vai trò này, `auth-service/…/AuthService.java:53`); user-service fallback `USER` | `/home` | — | Gửi/thuê, báo hỏng, đánh giá ticket |
| Quản trị | `ADMIN` (bao trùm mọi quyền ở gateway) | chỉ trang "dùng web" | Toàn bộ console, đăng nhập 2FA | Quản trị hệ thống |
| Kỹ thuật viên | `TECHNICIAN` | `/technician-home` (5 tab) | — | Ô tủ, ticket, lịch bảo trì, bãi đáp, thiết bị IoT |
| Đội drone | `MAINTENANCE` | `/maintenance-home` | — | Đội drone, điều phối đơn drone |
| Rác còn sót | — | — | `USER, STAFF, MODERATOR, PARTNER, PARTNER_STAFF, SUPER_ADMIN` (`frontend/fe/src/types/admin/enums.ts:23-29`, `context/auth-context.tsx:358-377`) | Không dùng |

Vai trò là **chuỗi tự do**, không có enum Java; tập hợp lệ `Set.of("CUSTOMER","ADMIN","MAINTENANCE","TECHNICIAN")` ở `AuthService.java:87`. Gateway kiểm tra theo tiền tố đường dẫn (`api-gateway/…/JwtGatewayFilter.java:148-165`); **không service nào tự kiểm tra** (`@PreAuthorize` = 0).

## 3. Checklist

| # | Hạng mục | Bằng chứng chính | Verdict | Còn thiếu |
|---|---|---|---|---|
| F3.01 | Mô hình vai trò thống nhất | Gateway + auth thống nhất 4 vai trò; mobile `mobile/lib/core/routing/role_routes.dart:7-18` | PARTIAL | Không có enum chung; fallback `USER` không ai hiểu; web còn PARTNER/STAFF |
| F3.02 | Phân quyền thực thi ở server | Chỉ gateway, theo path | PARTIAL | **Lỗ hổng nghiêm trọng**: SEC-02, SEC-03, SEC-05, SEC-06; MAINTENANCE làm được việc TECHNICIAN ở server |
| F3.03 | ADMIN cấp vai trò, tạo tài khoản nhân viên | Tạo `user-service/…/UserController.java:150-176` + web `CreateUserModal.tsx:72-84`; đổi vai trò `UserController.java:197-200` | PARTIAL | Web không có UI đổi vai trò; API không kiểm vai trò hợp lệ; **khoá user không chặn đăng nhập** (`auth_accounts.status` không đổi); vai trò cũ còn trong token 24h |
| F3.04 | Giao diện theo vai trò | TECHNICIAN `technician_home_page.dart:239-243`; MAINTENANCE `maintenance_home_page.dart:57-67` | PARTIAL | Không có role guard trên route mobile (`app_router.dart:108-119`); màn hình chết (`/maintenance/create-report` gọi API không tồn tại, Partner portal web, `LockerCard.tsx:50`) |
| F3.05 | CRUD đội drone + trạng thái | `locker-service/…/LockerController.java:303-319`, `LockerService.java:612-750`; mobile claim/status/pin `maintenance_home_page.dart:932-1195`; web `pages/Admin/drones/index.tsx` | PARTIAL | Không có vị trí/telemetry; **ADMIN web đổi trạng thái/pin luôn lỗi** `DRONE_OWNERSHIP_REQUIRED` |
| F3.06 | Vòng đời trạng thái drone được cưỡng chế | Giá trị hợp lệ, FAULT cần lý do, IN_FLIGHT cần pin > 20 (`LockerService.java:671-690`) | PARTIAL | Mọi → mọi; 3 đường ghi trạng thái với guard khác nhau; endpoint nội bộ không kiểm chủ sở hữu |
| F3.07 | Hỏng → tài sản tự chuyển FAULT + mở ticket | Ô: `markFault` `LockerService.java:218-233`; drone FAULT `:703`; bãi đáp `:318-325` | PARTIAL | **Chỉ khi người báo**; lỗi phần cứng (FAILED/JAMMED) chỉ ghi log (`iot-service/…/IotService.java:71-74`); tủ không bao giờ tự đổi trạng thái |
| F3.08 | Ticket: giao → xử lý → hoàn tất trả tài sản | Claim `LockerService.java:463-477`; log `:505-513`; resolve `:482-501`; app tech `technician_home_page.dart:1834,1843` | PARTIAL | Chỉ tự nhận, ADMIN không giao được; resolve ticket drone/bãi đáp **không** trả tài sản; `clearFault` không đóng ticket ⇒ lệch trạng thái |
| F3.09 | IoT tự đối soát sức khoẻ (offline/hỏng) | Heartbeat chỉ upsert `LockerMqttService.java:94-99` → `IotService.java:50-58` | MISSING | Không `@Scheduled` timeout; sự kiện `iot.device.status.changed` không ai nghe; topic heartbeat dùng tên tủ, không map lockerId |
| F3.10 | Cảnh báo tới người phụ trách + audit | Báo người báo lỗi khi claim/resolve `LockerService.java:1156-1179`; báo MAINTENANCE khi có đơn drone `OrderService.java:409` | PARTIAL | `locker.box.fault` publish nhưng không bind; không cảnh báo TECHNICIAN/ADMIN khi hỏng/offline; không audit đổi vai trò/trạng thái |

**Điểm:** PARTIAL 9 × 0,5 + MISSING 1 × 0 = 4,5 / 10 = **45 %**.

## 4. Ma trận vai trò × trạng thái (hiện tại)

V = xem · T = kích hoạt chuyển trạng thái. **Chữ đậm = lỗ hổng.**

| Thực thể | CUSTOMER | TECHNICIAN | MAINTENANCE | ADMIN |
|---|---|---|---|---|
| Tủ (ACTIVE/MAINTENANCE) | V (GET công khai) | V | V | T |
| Ô tủ | V; **T → FAULT với mọi ô** | T clear-fault / out-of-service / cleaning / return / force-open | **T như TECHNICIAN (server cho phép)** | T, kể cả chuỗi tuỳ ý |
| Ticket OPEN/IN_PROGRESS/RESOLVED | V của mình; tạo với **userId lấy từ body** | T claim/resolve/log | T (server), không có UI | T + resolve admin |
| Drone | — | ✗ 403 | T sau khi claim | V; T sau claim ⇒ web lỗi |
| Bãi đáp OK/FAULT/MAINTENANCE | V | T | T | T |
| Thiết bị IoT | **T giả trạng thái qua `/api/iot/device-status`** | T override/restart | ✗ | V |
| Đơn drone (stage) | V của mình | — | T accept/launch/cancel | T |
| Vai trò người dùng | **T tự cấp ADMIN qua `PUT /api/users/{id}`** | — | — | T (API, không UI) |

## 5. Trạng thái ticket (`LockerReport.status`)

`∅ → OPEN` (báo hỏng ô / báo cáo / bãi đáp ≠ OK / drone → FAULT) → `IN_PROGRESS` (claim, chỉ tự nhận, phải đang OPEN) → `RESOLVED` (resolve — **không kiểm tra trạng thái hay người được giao**). Không có: ADMIN giao việc, bỏ nhận, mở lại, huỷ. Ticket ô bị nhân bản mỗi lần báo; ticket drone có chống trùng.

## 6. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F3-G01** | **Vá phân quyền**: `/api/users*` chỉ cho chính mình, bỏ `roles/status` khỏi request không phải admin; `PATCH /api/orders/{id}/status` chỉ ADMIN; notification chỉ của mình; service tự kiểm `X-User-Roles` + chủ sở hữu (locker, iot, order) — SEC-02/03/05/06 | `user-service/…/UserController.java`, `order-service/…/OrderController.java:75`, `notification-service/…/NotificationController.java:105`, `JwtGatewayFilter.java` | F3.02 |
| **F3-G02** | **Nhất quán ticket ↔ tài sản**: bảng chuyển trạng thái cho ô/ticket/drone; `clearFault` đóng ticket và từ chối ô RESERVED/OCCUPIED; resolve kiểm người được giao và trả drone/bãi đáp; bỏ `updateBoxStatus`; chống trùng `markFault` | `locker-service/…/LockerService.java` | F3.06, F3.08 |
| **F3-G03** | **IoT tự đối soát**: timeout heartbeat → OFFLINE; tiêu thụ `iot.device.status.changed` + kết quả FAILED/JAMMED → `/internal/boxes/{id}/fault`; map tên tủ → lockerId, slotIndex → boxId | `iot-service/…/IotService.java` + `@Scheduled`, `LockerMqttService.java:94-111`, `iot/services/heartbeat_service.py:120` | F3.07, F3.09 |
| **F3-G04** | Cảnh báo lỗi tới TECHNICIAN/ADMIN (bind `locker.box.fault`, thiết bị offline) + audit log đổi vai trò / trạng thái / ô | `notification-service/…/config/RabbitConfig.java`, bảng audit mới | F3.10 |
| **F3-G05** | Quản lý vai trò trên web (dùng `useUpdateUserRolesMutation`); khoá tài khoản đồng bộ `auth_accounts` + thu hồi refresh token; rút TTL access token | `frontend/fe/src/pages/Admin/users/detail.tsx`, `auth-service/…/AuthService.java` | F3.03 |
| **F3-G06** | Đội drone: vị trí/lastSeen + telemetry; ADMIN bỏ qua claim; giữ chỗ drone khi accept; gộp 1 mô hình điều phối; guard pin trên mọi đường IN_FLIGHT | `LockerService.java:823`, `pages/Admin/drones/index.tsx`, `DroneDeliveryService.java` vs `DroneOrderMaintenanceService.java` | F3.05, F3.06 |
| **F3-G07** | Ticket: ADMIN giao/giao lại (endpoint + UI); MAINTENANCE có màn hình ticket drone | `LockerController.java`, `pages/Admin/maintenance/index.tsx`, `maintenance_home_page.dart` | F3.08 |
| **F3-G08** | Tủ ở MAINTENANCE phải chặn đặt ô | `LockerService.java:135,330` (`findAvailableBox`/`reserveBox`) | F3.07 |
| **F3-G09** | Dọn UI chết + role guard mobile: enum vai trò web, Partner portal, `BoxSettingModal` ghi `MAINTENANCE`, `LockerCard.tsx:50`; route legacy `features/maintenance/*` | `frontend/fe/src/…`, `mobile/lib/core/routing/app_router.dart` | F3.01, F3.04 |
| **F3-G10** | Một enum `Role` dùng chung trong `common-lib`, validate ở auth + user-service | `backend/common-lib` | F3.01 |
