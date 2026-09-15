# Kiến trúc hệ thống

> Sơ đồ in A4: [diagrams/pdf/architecture.pdf](../diagrams/pdf/architecture.pdf) · nguồn [`architecture.mmd`](../diagrams/src/architecture.mmd). Rà soát code 2026-09-13.

## 1. Repo

| Repo | Nội dung | Stack | Deploy khi merge `main` |
|---|---|---|---|
| [backend](https://github.com/LockR-Tech/backend) | 11 service + `common-lib` | Java 21 · Spring Boot 3.5.14 · Spring Cloud 2025.0.2 · Maven | Azure VM (SSH + docker compose) |
| [frontend](https://github.com/LockR-Tech/frontend) | `fe/` admin web · `landingPage/` | React 19 · Vite 7 · TypeScript · Tailwind 4 · RTK Query | Cloudflare Workers (chỉ khi đổi `fe/**`, `landingPage/**`) |
| [mobile](https://github.com/LockR-Tech/mobile) | App Android/iOS + Flutter web | Flutter 3.44 · Riverpod + provider + bloc · go_router · dio | Mobile web lên Cloudflare Worker |
| [iot](https://github.com/LockR-Tech/iot) | Pi controller · sketch Arduino · kiosk UI · giả lập | Python 3.13 (uv) · paho-mqtt · pyserial · FastAPI · React 19 | Không có CI/CD — cập nhật tay trên Pi |
| [legal](https://github.com/LockR-Tech/legal) | `privacy-policy.html`, `data-deletion.html` | HTML tĩnh | GitHub Pages (public) |
| [docs](https://github.com/LockR-Tech/docs) | Tài liệu này | Markdown · Mermaid → PDF A4 | — |

## 2. Service backend

Mỗi service có database Postgres riêng, Flyway, `ddl-auto: validate`.

| Module | Port | Vai trò | Database → bảng chính | Giao tiếp |
|---|---|---|---|---|
| discovery-server | 8761 | Eureka | — | — |
| api-gateway | 8080 | Định tuyến + JWT + RBAC theo path | — | `lb://` tới mọi service |
| auth-service | 8081 | Đăng nhập, đăng ký, OTP, Firebase, 2FA admin, phát token | auth_accounts, email_otps, refresh_tokens, social_identities | Feign → user; SMTP; Firebase Admin |
| user-service | 8082 | Hồ sơ, cột vai trò, quản lý người dùng | user_profiles | Feign → auth, notification |
| order-service | 8083 | Đơn SEND/RENTAL/DRONE, khuyến mãi, đánh giá, scheduler, dashboard, **drone simulator** | orders, order_status_history, promotions, drone_missions… | Feign → locker, user, notification · publish `order.*` · consume `order.payment.events` |
| locker-service | 8084 | Tủ, ô, ticket, bảo trì, drone, bãi đáp, ảnh ticket | lockers, locker_boxes, locker_reports, report_attachments, drone_units, repair_logs… | Feign → iot, user · publish `locker.box.*`, `locker.report.*` |
| payment-service | 8086 | Thanh toán CASH/WALLET/VNPAY/MOMO, hoàn tiền, ví | payments, refunds, wallets, wallet_transactions | Feign → order · publish `payment.*` |
| notification-service | 8087 | Thông báo in-app, STOMP `/ws`, FCM | notifications, fcm_tokens | consume `notification.events` |
| iot-service | 8088 | Cầu MQTT tới tủ, xác thực PIN/QR, mở khoá, sức khoẻ thiết bị | device_statuses, box_hardware_status, box_access_logs, access_attempts | MQTT · Feign → locker, order |
| store-service | 8089 | Cửa hàng, tìm gần | stores | Feign → order |
| loyalty-service | 8092 | Điểm, tem, phần thưởng | loyalty_accounts, point_transactions | — |
| _assistant-service_ | — | **RAG — CHƯA CÓ** ([L4](../02-flows/flow-4-rag-assistant.md)) | — | — |

**RabbitMQ** — một topic exchange `laundry.events`, hai hàng đợi có consumer: `order.payment.events` (→ order), `notification.events` (→ notification). Không ai tiêu thụ `order.created`, `locker.box.*`, `iot.device.status.changed`, `notification.requested`; không ai phát `delivery.status.changed`.

**MQTT (iot-service)** — phát `cabinet/{lockerId}/command/open` (chờ `/result` 20 s), `cabinet/{lockerId}/command/sync`; nghe `cabinet/+/command/+/result`, `cabinet/+/heartbeat`, `cabinet/+/locker/+/status`. ⚠ Broker mặc định là `broker.hivemq.com:1883` công khai (SEC-04). Pi thật dùng **tên** tủ trong topic và cần `slotIndex` ⇒ lệch hợp đồng với backend.

**Gateway** (`api-gateway/src/main/resources/application.yml`): `/api/auth/**`→auth · `/api/users/**`, `/api/user/**`, `/api/media/**`→user · `/api/orders/**`, `/api/maintenance/drone-orders/**`, `/api/promotions/**`, `/api/admin/dashboard/**`→order · `/api/lockers/**`, `/api/boxes/**`, `/api/maintenance/**`, `/api/admin/drones/**`→locker · `/api/payments/**`, `/api/wallet/**`→payment · `/api/notifications/**`, `/ws/**`→notification · `/api/iot/**`, `/api/technician/**`→iot · `/api/stores/**`→store · `/api/loyalty/**`→loyalty. `/internal/**` luôn 403 từ ngoài.

## 3. Hạ tầng

| | Local | Production |
|---|---|---|
| Máy | Docker Desktop | Azure VM `20.24.196.177`, Ubuntu 22.04, `Standard_B2as_v2` 8 GB, swap 4 GB |
| Lối vào | Gateway `http://localhost:18080` | Nginx :443 (Let's Encrypt) → `127.0.0.1:8080`; NSG chỉ mở 22/80/443 |
| Postgres | `postgres:16-alpine` `127.0.0.1:15432` | cùng image, không mở ra ngoài |
| RabbitMQ | `rabbitmq:3-management-alpine` :5672 / :15672 | cùng image |
| MQTT broker | **không có container** | **không có** — dùng broker công khai |
| Cấu hình | mặc định trong compose | `/opt/laundry-locker-microservices/.env` (giữ qua các lần deploy) |

## 4. Xác thực & phân quyền

- JWT ký HS (jjwt), claim `sub`=userId, `accountId`, `roles`, `tokenUse`. Access 24h, refresh 30 ngày (lưu hash, thu hồi được). Không có `iss`.
- Đăng nhập: email/mật khẩu, OTP email, số điện thoại, **Firebase** (phone/Google/Facebook) đổi ID token lấy JWT, kiosk quick-register. Admin: 2FA qua OTP email.
- Gateway kiểm chữ ký, gắn `X-User-Id`, `X-Account-Id`, `X-User-Roles`, RBAC theo tiền tố path. **Service không tự kiểm tra lại** ⇒ nguồn gốc các lỗ hổng SEC-02/03/05/06.
- ⚠ **SEC-01**: secret JWT production hardcode trong `docker-compose.yml:66,120`.

## 5. Tích hợp ngoài

| Tích hợp | Tình trạng |
|---|---|
| VNPay | Sandbox mặc định (`DEMO`); IPN không kiểm số tiền |
| MoMo | Endpoint test, cần khoá thật |
| Ví nội bộ | Thật (sổ cái `wallet_transactions`) |
| Tiền mặt | Hoàn tất ngay khi khách chọn — chưa có xác nhận của nhân viên |
| Email | SMTP chỉ cho OTP |
| SMS | **Không có** |
| FCM push | App đăng ký token, nhưng **server không gửi** (notification-service không khởi tạo Firebase) |
| Firebase Auth | Thật (phone/Google/Facebook) |
| Cloudinary (ảnh) | Client upload trực tiếp bằng chữ ký do user-service cấp; user/order/locker/store-service xác minh chữ ký phản hồi. Biến `CLOUDINARY_URL` (secret), `MEDIA_FOLDER_ROOT`. Trống ⇒ API ảnh trả 503. Hợp đồng: [media-storage](media-storage.md) · [ADR-0004](../adr/0004-anh-luu-cloudinary-upload-truc-tiep.md) |
| Bản đồ | OpenStreetMap + OSRM công khai |

## 6. Realtime

STOMP tại `/ws` (notification-service): `/user/queue/notifications` (mobile đăng ký), `/topic/deliveries/{orderId}/position` (live map drone — không service nào phát, feature flag đang tắt). Web admin chỉ dùng WebSocket ở Partner portal cũ.

## 7. CI/CD

| Repo · workflow | Kích hoạt | Làm gì | Secret |
|---|---|---|---|
| backend `backend-ci.yml` | PR; push `main`, `feat/**`, `fix/**`, `chore/**`, `docs/**` | `mvn test` | — |
| backend `backend-security.yml` | PR; push `main` + nhánh tính năng; cron CN | dependency-review, CodeQL, SBOM, Trivy | — |
| backend `backend-release.yml` | tag `v*` | build, SBOM, attestation, GitHub Release | `github.token` |
| backend `deploy-azure.yml` | push `main` (bỏ qua `**.md`, `docs/**`) · thủ công | `mvn verify` → scp → `deploy-from-artifact.sh` (giữ `.previous` để rollback) → smoke test → ghi `DEPLOY-LOG.md` `[skip ci]` | `AZURE_VM_HOST`, `AZURE_VM_USER`, `AZURE_VM_PORT`, `AZURE_VM_SSH_KEY` |
| frontend `deploy.yml` | push `main` đổi `fe/**`, `landingPage/**` · thủ công | build + `wrangler deploy` 2 Worker | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| mobile `deploy-web.yml` | push `main` (bỏ qua `**.md`, `docs/**`) · thủ công | `flutter test` → build web → `wrangler deploy` | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| docs `diagrams.yml` | PR / push đổi `diagrams/**`, `scripts/**` | Render lại mọi sơ đồ, fail nếu lỗi cú pháp hoặc > 1 trang A4 | — |

Chi tiết deploy, rollback, migration: [release-deploy.md](../04-engineering/release-deploy.md).

## 8. Lệnh phát triển

| Repo | Cài | Chạy | Test |
|---|---|---|---|
| backend | `mvn -B clean package` | `docker compose up -d --build` → gateway :18080, Eureka :8761, RabbitMQ UI :15672 | `mvn -B test` |
| frontend/fe | `npm ci` | `npm run dev` (:3000, proxy `/api` → production) | `npm run lint` · `npm run build` |
| mobile | `flutter pub get` | `flutter run` (emulator + backend local: `API_BASE_URL=http://10.0.2.2:18080` rồi `dart run build_runner build --delete-conflicting-outputs`) | `flutter test` |
| iot | `uv sync` | `docker compose -f docker-compose.postgres.yml up -d` · `SIMULATION=true uv run python main.py` · `uv run python simulate_demo_cabinet.py` · kiosk `cd ui && npm run dev` | chưa có test runner (pytest không nằm trong `pyproject.toml`); script tay trong `tests/` |
| docs | `npm ci` | `npm run diagrams` | `npm run diagrams:check` |
