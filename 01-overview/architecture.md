# Kiến trúc hệ thống

> Sơ đồ in A4: [diagrams/pdf/architecture.pdf](../diagrams/pdf/architecture.pdf) · nguồn [`architecture.mmd`](../diagrams/src/architecture.mmd). Rà soát code 2026-09-13; bổ sung 2026-09-21 theo backend #21 (kiosk), #22 (KTV tủ), #23 (`assistant-service`).

## 1. Repo

| Repo | Nội dung | Stack | Deploy khi merge `main` |
|---|---|---|---|
| [backend](https://github.com/LockR-Tech/backend) | 12 service + `common-lib` | Java 21 · Spring Boot 3.5.14 · Spring Cloud 2025.0.2 · Maven | Azure VM (SSH + docker compose) |
| [frontend](https://github.com/LockR-Tech/frontend) | `fe/` admin web · `landingPage/` | React 19 · Vite 7 · TypeScript · Tailwind 4 · RTK Query | Cloudflare Workers (chỉ khi đổi `fe/**`, `landingPage/**`) |
| [mobile](https://github.com/LockR-Tech/mobile) | App Android/iOS + Flutter web | Flutter 3.44 · Riverpod + provider + bloc · go_router · dio | Mobile web lên Cloudflare Worker |
| [iot](https://github.com/LockR-Tech/iot) | Pi controller (khoá, cảm biến, nắp trượt qua GPIO hoặc Arduino RS485 — [ADR-0007](../adr/0007-tu-nam-viet-pi-dieu-khien-gpio-truc-tiep.md)) · sketch Arduino · kiosk UI · giả lập | Python 3.13 (uv) · paho-mqtt · pyserial · gpiod · FastAPI · React 19 | Không có CI/CD — cập nhật tay trên Pi |
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
| locker-service | 8084 | Tủ, ô, ticket (định tuyến cho KTV phụ trách tủ), bảo trì + kiểm tra định kỳ, drone, bãi đáp, ảnh ticket | lockers, locker_boxes, locker_reports, report_attachments, maintenance_schedules, drone_units, repair_logs… | Feign → iot, user · publish `locker.box.*`, `locker.report.*` (claimed/resolved/routed/assigned), `locker.schedule.due` |
| payment-service | 8086 | Thanh toán CASH/WALLET/VNPAY/MOMO, hoàn tiền, ví | payments, refunds, wallets, wallet_transactions | Feign → order · publish `payment.*` |
| notification-service | 8087 | Thông báo in-app, STOMP `/ws`, FCM | notifications, fcm_tokens | consume `notification.events` |
| iot-service | 8088 | Cầu MQTT tới tủ, xác thực PIN/QR, mở khoá, sức khoẻ thiết bị, gán bộ điều khiển (Pi) vào tủ | device_statuses, box_hardware_status, box_access_logs, access_attempts, gateway_devices | MQTT · Feign → locker (`/internal/lockers/{id}/layout`), order |
| store-service | 8089 | Cửa hàng, tìm gần | stores | Feign → order |
| loyalty-service | 8092 | Điểm, tem, phần thưởng | loyalty_accounts, point_transactions | — |
| assistant-service | 8093 | Trợ lý hỏi đáp RAG: kho tri thức, đánh chỉ mục, hỏi đáp có trích nguồn, bộ đánh giá ([L4](../02-flows/flow-4-rag-assistant.md)) | **DB riêng `assistant-db` (pgvector)**: kb_documents, kb_chunks (`vector(1024)`, HNSW cosine), assistant_conversations, assistant_messages, eval_cases | HTTPS → Anthropic (Claude), Voyage AI (embedding) · không dùng RabbitMQ/Feign |

**RabbitMQ** — một topic exchange `laundry.events`, hai hàng đợi có consumer: `order.payment.events` (→ order), `notification.events` (→ notification; bind `order.status.changed`, `payment.*`, `locker.report.claimed/resolved/routed/assigned`, `locker.schedule.due`, `delivery.status.changed`). Không ai tiêu thụ `order.created`, `locker.box.*`, `iot.device.status.changed`, `notification.requested`.

**MQTT (iot-service)** — hợp đồng đầy đủ: [mqtt-contract.md](mqtt-contract.md) ([ADR-0008](../adr/0008-hop-dong-mqtt-backend-tu.md)). Phát `cabinet/{lockerId}/command/open` (`boxId` + `slotIndex = boxNumber − 1`, chờ `/result` theo `app.iot.unlock-wait-seconds`), `cabinet/{lockerId}/command/sync`, `iot/{mac}/command/setup|clear-setup`, `iot/{mac}/discovery/start`; nghe `cabinet/+/command/+/result`, `cabinet/+/heartbeat`, `cabinet/+/locker/+/status`, `iot/+/discovery/result`, `iot/+/setup/progress|result`. Admin gán Pi vào tủ: `GET /api/admin/iot/gateways`, `POST /api/admin/iot/gateways/{id}/assign|unassign|discover`, `DELETE /api/admin/iot/gateways/{id}`. ⚠ Broker mặc định vẫn là `broker.hivemq.com:1883` công khai (SEC-04) cho tới khi bật broker riêng (bảng dưới). Hợp đồng này có từ [backend#33](https://github.com/LockR-Tech/backend/pull/33) + [iot#9](https://github.com/LockR-Tech/iot/pull/9) (merge 2026-09-27).

**Gateway** (`api-gateway/src/main/resources/application.yml`): `/api/auth/**`→auth · `/api/users/**`, `/api/user/**`, `/api/media/**`→user · `/api/orders/**`, `/api/drone-technician/drone-orders/**`, `/api/admin/drone-orders/**` (ADMIN — hành trình drone), `/api/promotions/**`, `/api/admin/dashboard/**`→order · `/api/lockers/**`, `/api/boxes/**`, `/api/maintenance/**`, `/api/locker-technician/**`, `/api/drone-technician/**`, `/api/admin/drones/**`→locker · `/api/payments/**`, `/api/wallet/**`→payment · `/api/notifications/**`, `/ws/**`→notification · `/api/iot/**`, `/api/locker-technician/devices/**`→iot (khai báo trước locker-service để không bị nuốt) · `/api/stores/**`→store · `/api/loyalty/**`→loyalty · `/api/assistant/**` (mọi JWT), `/api/admin/knowledge/**` (ADMIN)→assistant. `/internal/**` luôn 403 từ ngoài.

Đường công khai của kiosk (mã là credential, không JWT): `/api/iot/verify-pin`, `/verify-access`, `/unlock`, `/unlock-with-code`, `/confirm-drop-with-code`, `/end-rental-with-code`. RBAC đáng chú ý: LOCKER_TECHNICIAN chỉ được `GET /api/admin/lockers/reports` (không giao/đóng/gia hạn bản admin); `PUT /api/maintenance/schedules/**` chỉ ADMIN.

## 3. Hạ tầng

| | Local | Production |
|---|---|---|
| Máy | Docker Desktop | Azure VM `85.211.182.170` (Malaysia West, từ 2026-10-04), Ubuntu 24.04, `Standard_B2as_v2` 8 GB, swap 4 GB |
| Lối vào | Gateway `http://localhost:18080` | Nginx :443 (Let's Encrypt) → `127.0.0.1:8080`; NSG chỉ mở 22/80/443 |
| Postgres | `postgres:16-alpine` `127.0.0.1:15432` | cùng image, không mở ra ngoài |
| Postgres vector (trợ lý) | `pgvector/pgvector:pg16` (`assistant-db`) `127.0.0.1:15433`, volume `assistant_db_data` | cùng image, `shared_buffers=64MB`; mật khẩu `ASSISTANT_DB_PASSWORD` (chỉ có tác dụng lần đầu tạo volume) |
| RabbitMQ | `rabbitmq:3-management-alpine` :5672 / :15672 | cùng image |
| MQTT broker | `eclipse-mosquitto:2` (`mosquitto`), profile `mqtt` — chỉ chạy khi `COMPOSE_PROFILES=mqtt` | cùng container khi bật: iot-service vào `tcp://mosquitto:1883`, Pi vào `wss://api.locker-drone.tech/mqtt` (Nginx → `127.0.0.1:9001`); tài khoản Pi ở `/etc/lockr/mosquitto` (`infra/mosquitto/mqtt-device.sh`). **Chưa bật** ⇒ vẫn HiveMQ công khai. Biến: `MQTT_IOT_SERVICE_PASSWORD`, `MQTT_BROKER_URL`, `MQTT_USERNAME`, `MQTT_PASSWORD` (secret) — [mqtt-contract § 6](mqtt-contract.md#6-bật-broker-riêng-trên-vm) |
| Cấu hình | mặc định trong compose | `/opt/laundry-locker-microservices/.env` (giữ qua các lần deploy) |

## 4. Xác thực & phân quyền

- JWT ký HS (jjwt), claim `sub`=userId, `accountId`, `roles`, `tokenUse`. Access 24h, refresh 30 ngày (lưu hash, thu hồi được). Không có `iss`.
- Đăng nhập: email/mật khẩu, OTP email, số điện thoại, **Firebase** (phone/Google/Facebook) đổi ID token lấy JWT, kiosk quick-register. Admin: 2FA qua OTP email.
- Gateway kiểm chữ ký, gắn `X-User-Id`, `X-Account-Id`, `X-User-Roles`, RBAC theo tiền tố path. **Service không tự kiểm tra lại** ⇒ nguồn gốc các lỗ hổng SEC-02/03/05/06.
- ⚠ **SEC-01**: secret JWT production từng hardcode trong `docker-compose.yml`. [backend #10](https://github.com/LockR-Tech/backend/pull/10) chuyển sang đọc `.env` và dừng khởi động khi thiếu, cho cả ba service xác thực JWT (gateway, auth, **notification** — service này trước đó không được truyền biến). Đóng khi đã đặt biến trên VM và merge.

## 5. Tích hợp ngoài

| Tích hợp | Tình trạng |
|---|---|
| VNPay | Sandbox mặc định (`DEMO`); IPN không kiểm số tiền |
| MoMo | Endpoint test, cần khoá thật |
| Ví nội bộ | Thật (sổ cái `wallet_transactions`) |
| Tiền mặt | Hoàn tất ngay khi chọn — chưa có xác nhận của nhân viên. App khách đã bỏ CASH (mobile #19); kiosk giữ CASH demo |
| Email | SMTP dùng cho OTP đăng nhập (auth-service) và gửi mã mở tủ cho người nhận chưa có tài khoản (notification-service). Biến `SPRING_MAIL_*` (secret), `APP_MAIL_FROM` |
| SMS | **Twilio** Messages API trong notification-service, gửi mã mở tủ cho người nhận chưa có tài khoản. Biến `APP_SMS_TWILIO_ACCOUNT_SID` / `AUTH_TOKEN` / `FROM_NUMBER` (secret). Thiếu bất kỳ biến nào ⇒ rơi về bản chỉ ghi log, **không gửi thật**. Hợp đồng: [receiver-pickup-code](receiver-pickup-code.md) |
| FCM push | notification-service đã khởi tạo Firebase ([backend #10](https://github.com/LockR-Tech/backend/pull/10) — trước đó `FcmPushNotificationService` viết đủ nhưng không ai gọi `initializeApp` nên mọi lệnh push bị bỏ qua trong im lặng). Bật thật khi nạp `FIREBASE_CREDENTIALS_JSON`; trống ⇒ push tắt, các kênh khác vẫn chạy |
| Firebase Auth | Thật (phone/Google/Facebook) |
| Cấu hình nghiệp vụ (nội bộ) | Mỗi service bật `app.settings.scope` sở hữu bảng `system_settings` + `system_setting_audits`; admin sửa qua `/api/admin/settings/{scope}`, app đọc `/api/settings/{scope}/public` — [business-settings](business-settings.md) · [ADR-0005](../adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md) |
| Cloudinary (ảnh) | Client upload trực tiếp bằng chữ ký do user-service cấp; user/order/locker/store-service xác minh chữ ký phản hồi. Biến `CLOUDINARY_URL` (secret), `MEDIA_FOLDER_ROOT`. Trống ⇒ API ảnh trả 503. Hợp đồng: [media-storage](media-storage.md) · [ADR-0004](../adr/0004-anh-luu-cloudinary-upload-truc-tiep.md) |
| Bản đồ | OpenStreetMap + OSRM công khai |
| Claude (Anthropic) | assistant-service sinh câu trả lời có Citations qua Anthropic Java SDK. Biến `ANTHROPIC_API_KEY` (secret), `ASSISTANT_CHAT_MODEL` (mặc định `claude-haiku-4-5`). Trống ⇒ API hỏi đáp trả 503 — [ADR-0006](../adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md) |
| Voyage AI (embedding) | assistant-service nhúng tài liệu/câu hỏi, `voyage-4`, 1024 chiều. Biến `EMBEDDING_API_KEY` (secret), `EMBEDDING_MODEL`. Trống ⇒ tài liệu nằm PENDING, hỏi đáp trả 503 |

## 6. Realtime

STOMP tại `/ws` (notification-service): `/user/queue/notifications` (mobile đăng ký), `/topic/deliveries/{orderId}/position` (live map drone — order-service phát vị trí nội suy cho đơn DEMO qua `POST /internal/deliveries/{orderId}/position`; đơn STANDARD chưa có nguồn vị trí). Web admin chỉ dùng WebSocket ở Partner portal cũ.

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
| iot | `uv sync` | `docker compose -f docker-compose.postgres.yml up -d` · `SIMULATION=true LOCKER_ID=<id tủ> uv run python main.py` · `uv run python simulate_demo_cabinet.py` · kiosk `cd ui && npm run dev` | `uv run python -m unittest tests.test_mqtt_contract tests.test_gpio_hardware` (unittest, không cần Pi) |
| docs | `npm ci` | `npm run diagrams` | `npm run diagrams:check` |
