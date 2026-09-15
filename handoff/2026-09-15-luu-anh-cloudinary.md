# Bàn giao — Lưu ảnh thật trên Cloudinary (2026-09-15)

> Dành cho người hoặc AI agent tiếp tục việc này trên máy khác. Đọc hết mục 1–3 trước khi làm gì.
> Quy trình chung của dự án vẫn theo [AGENTS.md](../AGENTS.md) và [STATUS.md](../STATUS.md).
> File này **không chứa secret**. Mọi giá trị secret phải lấy lại từ Cloudinary Console hoặc `.env` trên VM.

## 1. Việc này là gì

Chủ dự án yêu cầu: mọi chức năng liên quan ảnh phải lưu ảnh thật (trước đó toàn ảnh mẫu hoặc không lưu được), đặc biệt **phiếu xử lý sự cố** trong quản lý trang thiết bị:

1. Khách thấy tủ hỏng → báo sự cố trên app mobile **kèm ảnh hiện trường**.
2. Kỹ thuật viên (KTV) tới nơi → **chụp ảnh xác nhận** hiện trạng.
3. Trong lúc sửa → ảnh quá trình (gắn với nhật ký sửa chữa).
4. Sửa xong → **chụp ảnh nghiệm thu** và báo cáo, rồi hoàn tất phiếu.

Kèm theo: ảnh đại diện, ảnh cửa hàng, ảnh khuyến mãi, với đầy đủ API.

| Tài liệu gốc | Nội dung |
|---|---|
| [ADR-0004](../adr/0004-anh-luu-cloudinary-upload-truc-tiep.md) | Vì sao chọn Cloudinary + signed direct upload |
| [01-overview/media-storage.md](../01-overview/media-storage.md) | **Hợp đồng API** — mọi endpoint, body, mã lỗi, biến môi trường |

## 2. Trạng thái tại thời điểm bàn giao

| Repo | PR | Trạng thái |
|---|---|---|
| docs | [#2](https://github.com/LockR-Tech/docs/pull/2) — ADR-0004 + hợp đồng API | ✅ Đã merge |
| backend | [#4](https://github.com/LockR-Tech/backend/pull/4) — `ci(ci)`: bước attest không chặn deploy | ✅ Đã merge, deploy **thành công** (run `34991389534`), smoke test production đạt |
| backend | [#3](https://github.com/LockR-Tech/backend/pull/3) — tính năng lưu ảnh (7 commit) | ✅ Đã merge (`5180d00`) và **đã lên VM** (run `34992991471`). Workflow báo đỏ chỉ vì smoke test `/api/lockers` trả 503 ngay sau khi service vừa đăng ký Eureka (gateway chưa làm mới danh sách instance); **không rollback** — kiểm lại sau đó `/api/lockers` 200, `POST /api/media/upload-signatures` 401 (route mới đã chạy). Dòng "đã rollback" trong `DEPLOY-LOG.md` của run này là mẫu chữ cố định, không đúng thực tế. |
| frontend | [#4](https://github.com/LockR-Tech/frontend/pull/4) — admin web (5 commit) | ✅ Đã merge (`3920bd5`), deploy Cloudflare thành công (run `34993835093`) |
| mobile | [#4](https://github.com/LockR-Tech/mobile/pull/4) — app (6 commit) | ✅ Đã merge (`eed1724`), deploy mobile web thành công (run `34993842917`). App Android/iOS **chưa build lại**. |

Nhánh tính năng ở cả 4 repo: `feat/media-cloudinary-photos`.

**Quyết định của chủ dự án cho đợt này:**

- Merge kiểu **rebase** (giữ nguyên từng commit đã chia theo chức năng), khác quy ước squash thường lệ.
- Thứ tự: sửa pipeline deploy → docs + backend → xác nhận API chạy trên production → mới merge frontend và mobile.

**Đã kiểm chứng:**

- Backend: `mvn test` 6 module BUILD SUCCESS; CI `test` trên GitHub pass (có chạy test Postgres/Testcontainers cho migration V13).
- Frontend: `npm run lint` 0 error (70 warning có sẵn), `npm run build` pass.
- Mobile: `flutter test` 122 pass, `flutter analyze` không phát sinh issue mới.
- Chạy thật với Cloudinary cloud `bdst6d8u` (thư mục `lockr-dev`): xin chữ ký → upload → xác minh → ảnh gốc và thumbnail HTTP 200 → xoá `{"result":"ok"}`; ảnh của user khác bị từ chối `MEDIA_OWNER_MISMATCH`, chữ ký giả bị từ chối `MEDIA_SIGNATURE_INVALID`.

**Chưa kiểm chứng:** chạy trên thiết bị Android/iOS thật; luồng end-to-end trên production.

## 3. Việc cần làm tiếp — theo thứ tự

> Cập nhật 2026-09-15 tối: bước 1, 3, 4 (phần merge + deploy web) **đã xong**. Chủ dự án chọn merge frontend/mobile không chờ cấu hình VM. **Việc gấp nhất còn lại là bước 2** — thiếu `CLOUDINARY_URL` trên VM thì API ảnh trả 503 và KTV trên mobile web không hoàn tất được phiếu.
> Nên sửa thêm: bước "Nghiệm thu qua domain công khai" trong `deploy-azure.yml` cần thử lại vài lần (race Eureka ⇒ 503 giả) và mẫu tóm tắt/DEPLOY-LOG chỉ ghi "đã rollback" khi bước *Deploy on Azure VM* thật sự thất bại.

1. ~~**Kiểm tra deploy backend `5180d00`**~~ — đã lên production (xem mục 2).
   - Kiểm lại bất cứ lúc nào: `curl -s -o /dev/null -w '%{http_code}' -X POST https://api.locker-drone.tech/api/media/upload-signatures` phải trả **401**.
2. **Cấu hình Cloudinary trên VM** (chủ dự án tự làm, không dán secret vào chat/issue):
   - Tạo API key riêng `LockR-prod` trên Cloudinary Console (cloud `bdst6d8u`), role có quyền upload + xoá ảnh.
   - Thêm vào `/opt/laundry-locker-microservices/.env`:
     ```
     CLOUDINARY_URL=cloudinary://<API_KEY>:<API_SECRET>@bdst6d8u
     MEDIA_FOLDER_ROOT=lockr-prod
     APP_MAINTENANCE_REQUIRE_RESOLUTION_PHOTO=false
     ```
   - `cd /opt/laundry-locker-microservices && docker compose up -d`.
   - Kiểm tra: đăng nhập lấy JWT, `POST /api/media/upload-signatures` body `{"purpose":"REPORT_EVIDENCE"}` phải trả 200 (không phải 503 `MEDIA_STORAGE_DISABLED`).
3. **Merge frontend PR #4** (rebase) → Cloudflare tự deploy ~2 phút → thử trang Bảo trì, chi tiết cửa hàng, người dùng, khuyến mãi.
4. **Merge mobile PR #4** (rebase) → mobile web tự deploy (`flutter test` phải pass).
   - ⚠ Chỉ merge khi bước 2 xong: màn **Hoàn tất** của KTV bắt buộc ≥ 1 ảnh nghiệm thu, thiếu Cloudinary thì KTV không đóng được phiếu.
   - Build lại app Android/iOS (đã thêm quyền CAMERA, `NSCameraUsageDescription`, `NSPhotoLibraryUsageDescription`, `NSLocationWhenInUseUsageDescription`), tăng `version:` trong `pubspec.yaml`.
5. **Thử end-to-end trên production:** khách báo lỗi ô kèm ảnh → KTV nhận việc → "Xác nhận hiện trường" → nhật ký kèm ảnh → Hoàn tất kèm ảnh nghiệm thu → admin web thấy đủ 4 nhóm ảnh → khách thấy ảnh nghiệm thu trong "Báo cáo của tôi".
6. Khi app mobile mới đã tới tay mọi KTV: đổi `APP_MAINTENANCE_REQUIRE_RESOLUTION_PHOTO=true` trên VM để server cũng bắt buộc ảnh nghiệm thu.
7. **Xoay key dev:** API key `LockR` (dùng cho `lockr-dev`) đã bị dán secret vào lịch sử chat ⇒ coi như lộ. Hết giai đoạn dev thì vô hiệu hoá/xoá trên Cloudinary Console, tạo key mới cho máy dev.
8. **Cập nhật tài liệu sau khi merge xong** (Definition of Done trong AGENTS.md):
   - `STATUS.md`: bỏ dòng § 3, thêm § 5 (đã xong); ghi SEC mới nếu cần cho việc lộ key dev.
   - `02-flows/flow-3-roles-maintenance.md`: bổ sung bằng chứng cho F3.08 (ảnh theo giai đoạn, quyền gắn ảnh theo người được giao) — verdict vẫn PARTIAL vì các gap khác của F3.08 chưa làm.
   - ADR-0004: đổi trạng thái `Proposed` → `Accepted` khi chủ dự án xác nhận.
   - `CHANGELOG.md`.

## 4. Kiến trúc đã làm (tóm tắt)

```
App/Web ─POST /api/media/upload-signatures {purpose,count}─▶ user-service (chỉ ký, không nhận file)
App/Web ─multipart (fields + file), KHÔNG JWT─────────────▶ api.cloudinary.com
App/Web ─API nghiệp vụ kèm MediaUpload{publicId,version,signature,…}─▶ locker/user/store/order-service
          service xác minh sha1("public_id=..&version=.." + api_secret) + tiền tố <root>/<purpose>/u<X-User-Id>/
          rồi tự dựng URL https://res.cloudinary.com/<cloud>/image/upload/v<version>/<publicId>.<format>
```

- `public_id` = `<MEDIA_FOLDER_ROOT>/<avatars|reports|stores|promotions>/u<userId>/<uuid>` ⇒ không ai gắn được ảnh của người khác hoặc URL tuỳ ý.
- Ảnh phiếu sự cố: bảng `locker_schema.report_attachments` (migration `V13`), cột `stage` = `REPORT` / `INSPECTION` / `PROGRESS` / `RESOLUTION`.
- Quyền: KTV chỉ gắn ảnh vào phiếu `IN_PROGRESS` mình được giao; người báo chỉ bổ sung khi phiếu chưa `RESOLVED`; người upload xoá được trước khi đóng phiếu; ADMIN làm mọi thứ.
- Không cấu hình `CLOUDINARY_URL` ⇒ API cần ảnh trả `503 MEDIA_STORAGE_DISABLED`, phần còn lại chạy bình thường.
- Tương thích ngược: body cũ (`{imageUrl}` cho avatar/cửa hàng, resolve không body, log `{note}`) vẫn nhận ⇒ app cũ không vỡ.

### File quan trọng

| Repo | Đường dẫn | Vai trò |
|---|---|---|
| backend | `common-lib/…/common/media/CloudinaryMediaStorage.java` | Ký, xác minh, dựng URL, thumbnail, xoá sau commit |
| backend | `common-lib/…/common/media/MediaPurpose.java` | Purpose + vai trò được xin chữ ký |
| backend | `user-service/…/controller/MediaController.java` | `POST /api/media/upload-signatures` |
| backend | `locker-service/…/service/ReportAttachmentService.java` | Quy tắc ảnh phiếu sự cố (quyền, giới hạn, xoá) |
| backend | `locker-service/…/service/LockerService.java` | Báo lỗi/tạo phiếu/nhật ký/hoàn tất kèm ảnh; cờ `require-resolution-photo` |
| backend | `locker-service/src/main/resources/db/migration/V13__report_attachments.sql` | Bảng ảnh phiếu |
| backend | `api-gateway/…/JwtGatewayFilter.java`, `application.yml` | Route `/api/media/**`; khách được POST `/api/lockers/reports/{id}/attachments` |
| backend | `order-service/…/service/PromotionImageService.java`, `store-service/…/StoreService.java`, `user-service/…/UserProfileService.java` | Ảnh khuyến mãi, cửa hàng, avatar |
| frontend | `fe/src/lib/cloudinary-upload.ts`, `fe/src/hooks/useImageUpload.ts`, `fe/src/components/shared/media/` | Lõi upload + PhotoPicker/PhotoGallery |
| frontend | `fe/src/pages/Admin/maintenance/ReportPhotoGroups.tsx`, `ResolveReportDialog.tsx`, `maintenancePhotos.ts` | Ảnh phiếu theo 4 giai đoạn (đã bỏ ảnh mẫu Unsplash) |
| mobile | `lib/core/media/media_upload_service.dart` (+ `widgets/`) | Lõi upload (Dio riêng, không JWT), picker, gallery |
| mobile | `lib/features/locker_ops/presentation/pages/technician_home_page.dart` | "Xác nhận hiện trường", nhật ký kèm ảnh, Hoàn tất bắt buộc ảnh nghiệm thu |
| mobile | `lib/features/locker_ops/presentation/pages/my_locker_orders_page.dart`, `my_reports_page.dart` | Khách báo lỗi kèm ảnh, xem ảnh nghiệm thu |

### Sửa kèm (lỗi có sẵn phát hiện trong lúc làm)

- `UserSummary` không có `imageUrl` ⇒ API hồ sơ không bao giờ trả avatar. Đã thêm.
- `PUT /api/user/profile`, `PUT /api/admin/stores/{id}` không gửi trường ảnh thì **xoá mất ảnh cũ**. Đã sửa: bỏ trống ⇒ giữ ảnh.
- Mobile gửi avatar dạng multipart nhưng backend chỉ nhận JSON ⇒ avatar chưa bao giờ lưu được. Đã sửa.
- `StoreResponse` trả `image`, web đọc `imageUrl`. Đã trả thêm `imageUrl`.
- Pipeline `Deploy to Azure VM` của org **chưa lần nào tới được VM**: `actions/attest` lỗi `Feature not available for the LockR-Tech organization` (artifact attestation không có cho repo private gói Free). Đã đặt `continue-on-error: true` (PR backend #4).

## 5. Chưa làm / hạn chế đã biết

- Ảnh chụp lúc KTV **mở tủ khẩn cấp** (`_forceOpenFlow`) vẫn bị bỏ đi, không lưu.
- Ảnh bìa hồ sơ trên mobile vẫn là giả lập.
- App mobile chưa có nút xoá ảnh phiếu (API `deleteReportAttachment` đã có trong service).
- Admin web chưa có ô nhập caption/thời điểm chụp/vị trí cho ảnh (backend nhận được).
- Trang tạo báo cáo cũ trên mobile vẫn bắt buộc ≥ 1 ảnh ⇒ khi server tắt Cloudinary thì trang đó không gửi được.
- Ảnh mồ côi (client upload rồi bỏ dở) nằm lại trên Cloudinary; dọn tay trên Console nếu tốn dung lượng.
- `container-scan` (Trivy) và `codeql` trong *Backend Security* **đang đỏ sẵn trên `main` từ trước** cho mọi service — không phải do đợt này.

## 6. Ghi chú môi trường & thao tác (quan trọng khi đổi máy)

- **Máy cũ không có** JDK 21, Maven, Node, Flutter, Docker, `gh`. Đợt này dùng bản portable tải vào thư mục tạm (không cài hệ thống). Máy mới nên cài: JDK 21, Maven 3.9, Node 22, Flutter 3.44.x, Docker Desktop, GitHub CLI.
- **`backend/.env` chỉ có trên máy cũ** (gitignore) với `MEDIA_FOLDER_ROOT=lockr-dev`. Máy mới phải tự tạo lại bằng key dev mới (mục 3 bước 7) — không lấy secret từ lịch sử chat.
- PowerShell: tham số Maven có dấu chấm phải đặt trong nháy: `mvn -B test '-Dcyclonedx.skip=true' -pl 'common-lib,locker-service' -am`. Bỏ qua CycloneDX để khỏi tải dependency của mọi module.
- `LockerServicePostgresContainerTest` tự bỏ qua khi không có Docker; CI trên GitHub vẫn chạy nó.
- Deploy backend có `concurrency: cancel-in-progress` ⇒ **không merge 2 PR backend cách nhau dưới ~20 phút**, lượt sau sẽ huỷ lượt đang deploy dở.
- Không có `gh` thì tạo/merge PR qua REST API (`POST /repos/LockR-Tech/<repo>/pulls`, `PUT …/pulls/<n>/merge` với `merge_method: rebase`), lấy token qua `git credential fill`, không in token ra log.
- Chạy thử Cloudinary thật mà không cần khởi động cả hệ thống: viết một file Java single-source gọi `CloudinaryMediaStorage` (classpath `common-lib/target/classes` + `spring-web`, `spring-core`, `spring-jcl`, `slf4j-api` trong `~/.m2`), đọc `CLOUDINARY_URL` từ `backend/.env`.

## 7. Khi mở phiên mới — gợi ý lời nhắn cho AI

> Đọc `docs/AGENTS.md`, `docs/STATUS.md`, rồi `docs/handoff/2026-09-15-luu-anh-cloudinary.md`. Tiếp tục từ mục 3 của file bàn giao: kiểm tra deploy backend `5180d00`, sau đó merge frontend PR #4 và mobile PR #4 theo đúng điều kiện ghi trong đó. Không dán hay ghi secret vào tài liệu.
