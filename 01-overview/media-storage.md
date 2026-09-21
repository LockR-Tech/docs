# Lưu trữ ảnh — Cloudinary

> Quyết định: [ADR-0004](../adr/0004-anh-luu-cloudinary-upload-truc-tiep.md). Tài liệu này là **hợp đồng API** cho backend, admin web và mobile. Đổi hợp đồng ⇒ sửa file này trong cùng đợt.

## 1. Luồng tổng quát

```
Client ──(1) POST /api/media/upload-signatures {purpose,count}──▶ user-service   (ký, không nhận file)
Client ◀─────────────── uploadUrl + fields (api_key, timestamp, public_id, allowed_formats, signature)
Client ──(2) multipart POST uploadUrl  (fields + file)──────────▶ Cloudinary      (KHÔNG gửi JWT)
Client ◀─────────────── {public_id, version, signature, format, bytes, width, height, secure_url}
Client ──(3) API nghiệp vụ, kèm MediaUpload ────────────────────▶ locker/user/store/order-service
                                         service tự xác minh chữ ký phản hồi Cloudinary rồi mới lưu
```

- Byte ảnh **không đi qua** gateway/VM (VM 8 GB, Nginx giới hạn 20 MB).
- Backend chỉ lưu metadata (`public_id`, `secure_url`, kích thước…). URL do **server tự dựng** từ `public_id` + `version`, không tin URL client gửi.
- Xác minh ở bước (3): `signature == sha1("public_id=<id>&version=<v>" + api_secret)` **và** `public_id` bắt đầu bằng `<root>/<folder>/u<X-User-Id>/` (người gắn ảnh phải là người đã xin chữ ký) **và** `format` hợp lệ.
- Chữ ký upload hết hạn sau 1 giờ (giới hạn của Cloudinary).
- Chưa cấu hình Cloudinary ⇒ mọi API nhận ảnh trả `503 MEDIA_STORAGE_DISABLED`; API không có ảnh vẫn chạy bình thường.

## 2. Cấu hình

| Biến môi trường | Service | Ghi chú |
|---|---|---|
| `CLOUDINARY_URL` | user, locker, store, order | Dạng `cloudinary://<api_key>:<api_secret>@<cloud_name>` (Cloudinary Console → API Keys). **Secret** — chỉ đặt trong `.env` trên VM. |
| `MEDIA_FOLDER_ROOT` | user, locker, store, order | Mặc định `lockr`. Nên đặt `lockr-prod` ở production, `lockr-dev` ở máy dev để tách dữ liệu. Phải **giống nhau** ở cả 4 service. |
| `APP_MAINTENANCE_REQUIRE_RESOLUTION_PHOTO` | locker | Mặc định `false`. Bật `true` sau khi app mobile mới đã phát hành ⇒ hoàn tất phiếu bắt buộc có ≥ 1 ảnh nghiệm thu. |

Thư mục trên Cloudinary: `<root>/avatars|reports|stores|promotions/u<userId>/<uuid>`.

## 3. Đối tượng dùng chung

**MediaUpload** — gửi kèm mọi API gắn ảnh, lấy nguyên từ phản hồi Cloudinary:

```json
{ "publicId": "lockr/reports/u42/9f1c…", "version": 1726390012, "signature": "a94a8fe5…",
  "format": "jpg", "bytes": 234567, "width": 1600, "height": 1200 }
```

**ReportAttachmentRequest** = MediaUpload + tuỳ chọn `caption` (≤ 500), `capturedAt` (ISO `yyyy-MM-ddTHH:mm:ss`), `latitude`, `longitude`.

**ReportAttachmentResponse**

```json
{ "id": 7, "reportId": 12, "repairLogId": null, "stage": "INSPECTION",
  "url": "https://res.cloudinary.com/<cloud>/image/upload/v1726390012/lockr/reports/u42/9f1c….jpg",
  "thumbnailUrl": "https://res.cloudinary.com/<cloud>/image/upload/c_fill,w_320,h_320/f_auto,q_auto/v1726390012/…jpg",
  "publicId": "…", "format": "jpg", "bytes": 234567, "width": 1600, "height": 1200,
  "caption": "Bản lề lệch", "latitude": 10.77, "longitude": 106.70, "capturedAt": "2026-09-15T08:10:00",
  "uploadedByUserId": 42, "createdAt": "2026-09-15T08:10:05" }
```

**stage** của ảnh phiếu sự cố:

| stage | Ai chụp | Khi nào |
|---|---|---|
| `REPORT` | Người báo (khách, KTV, admin) | Lúc gửi phiếu hoặc bổ sung khi phiếu chưa RESOLVED |
| `INSPECTION` | KTV được giao | Tới hiện trường, chụp xác nhận hiện trạng |
| `PROGRESS` | KTV được giao | Trong khi sửa — gắn với 1 dòng nhật ký (`repairLogId`) |
| `RESOLUTION` | KTV được giao | Sửa xong, chụp nghiệm thu (trước hoặc cùng lúc bấm Hoàn tất) |

**purpose** khi xin chữ ký:

| purpose | Ai được xin | Dùng cho |
|---|---|---|
| `REPORT_EVIDENCE` | Mọi tài khoản | Ảnh phiếu sự cố (mọi stage) |
| `AVATAR` | Mọi tài khoản | Ảnh đại diện |
| `STORE_IMAGE` | ADMIN | Ảnh cửa hàng |
| `PROMOTION_IMAGE` | ADMIN | Ảnh khuyến mãi |

## 4. API

Mọi phản hồi bọc trong `ApiResponse { success, code, message, data, errors }`.

### 4.1 Chữ ký upload — user-service

`POST /api/media/upload-signatures` — body `{ "purpose": "REPORT_EVIDENCE", "count": 3 }` (`count` 1–10, mặc định 1)

```json
{ "provider": "CLOUDINARY", "cloudName": "<cloud>",
  "uploadUrl": "https://api.cloudinary.com/v1_1/<cloud>/image/upload",
  "maxBytes": 10485760, "allowedFormats": ["jpg","jpeg","png","webp","heic","heif"],
  "expiresAt": "2026-09-15T09:10:00",
  "uploads": [ { "publicId": "lockr/reports/u42/9f1c…",
                 "fields": { "api_key": "…", "timestamp": "1726390000", "public_id": "lockr/reports/u42/9f1c…",
                             "allowed_formats": "jpg,jpeg,png,webp,heic,heif", "signature": "…" } } ] }
```

Client gửi `multipart/form-data` tới `uploadUrl`: **toàn bộ** `fields` (giữ nguyên giá trị) + `file`. Mỗi file dùng một phần tử `uploads` riêng. Lỗi: `400 MEDIA_PURPOSE_INVALID`, `400 MEDIA_COUNT_INVALID`, `403 MEDIA_PURPOSE_FORBIDDEN`, `503 MEDIA_STORAGE_DISABLED`.

### 4.2 Phiếu sự cố — locker-service (và order-service chuyển tiếp)

| Method · Path | Vai trò | Body | Quy tắc |
|---|---|---|---|
| `POST /api/lockers/{lockerId}/report` | Mọi tài khoản | `{userId, title, description, attachments?: ReportAttachmentRequest[≤5]}` | stage `REPORT`. `userId` lấy từ JWT nếu có. |
| `POST /api/boxes/{boxId}/fault` | Mọi tài khoản | `{reason?, attachments?[≤5]}` | Tạo phiếu + stage `REPORT` |
| `POST /api/orders/{orderId}/report-box-fault` | Chủ đơn | `{reason?, attachments?[≤5]}` | order-service chuyển `attachments` sang locker-service |
| `GET /api/lockers/my-reports` | Người báo | — | Mỗi phiếu có `attachments[]` |
| `GET /api/lockers/reports/{id}/attachments` | Người báo | — | Chỉ chủ phiếu |
| `POST /api/lockers/reports/{id}/attachments` | Người báo | `{attachments: [1..5]}` | Chỉ chủ phiếu, phiếu chưa `RESOLVED`, tối đa 10 ảnh `REPORT`/phiếu |
| `GET /api/locker-technician/reports` | TECH/MAINT/ADMIN | — | Mỗi phiếu có `attachments[]` |
| `GET /api/locker-technician/reports/{id}` | TECH/MAINT/ADMIN | — | 1 phiếu, có `attachments[]` |
| `GET /api/locker-technician/reports/{id}/attachments?stage=` | TECH/MAINT/ADMIN | — | Lọc theo stage (tuỳ chọn) |
| `POST /api/locker-technician/reports/{id}/attachments` | Người được giao hoặc ADMIN | `{stage: INSPECTION\|PROGRESS\|RESOLUTION, note?, attachments: [1..10]}` | Phiếu phải `IN_PROGRESS`. Có `note` ⇒ tạo 1 dòng nhật ký và gắn ảnh vào đó. Tối đa 30 ảnh/phiếu. |
| `DELETE /api/locker-technician/reports/{id}/attachments/{attachmentId}` | Người upload (phiếu chưa RESOLVED) hoặc ADMIN | — | Xoá DB + xoá trên Cloudinary (best-effort) |
| `GET /api/locker-technician/reports/{id}/logs` | TECH/MAINT/ADMIN | — | Mỗi dòng có `attachments[]` |
| `POST /api/locker-technician/reports/{id}/logs` | TECH/MAINT/ADMIN | `{note, attachments?[≤10]}` | Ảnh stage `PROGRESS`, cần là người được giao hoặc ADMIN khi có ảnh |
| `PUT /api/locker-technician/reports/{id}/resolve` | TECH/MAINT/ADMIN | tuỳ chọn `{note?, attachments?[≤10]}` | Ảnh stage `RESOLUTION` lưu trước khi đóng phiếu. Bật `APP_MAINTENANCE_REQUIRE_RESOLUTION_PHOTO` ⇒ `400 RESOLUTION_PHOTO_REQUIRED` nếu phiếu chưa có ảnh nghiệm thu |
| `GET /api/admin/lockers/reports/{id}/attachments` | ADMIN | — | |
| `POST /api/admin/lockers/reports/{id}/attachments` | ADMIN | `{stage, note?, attachments}` | Mọi stage, mọi trạng thái |
| `DELETE /api/admin/lockers/reports/{id}/attachments/{attachmentId}` | ADMIN | — | |
| `PUT /api/admin/lockers/reports/{id}/resolve` | ADMIN | tuỳ chọn `{note?, attachments?}` | Như resolve của maintenance |

`LockerReportResponse` thêm `attachments: ReportAttachmentResponse[]`; `RepairLogResponse` thêm `attachments`.

Lỗi: `400 MEDIA_UPLOAD_INVALID`, `400 MEDIA_SIGNATURE_INVALID`, `400 MEDIA_OWNER_MISMATCH`, `400 MEDIA_FORMAT_INVALID`, `400 ATTACHMENT_LIMIT_EXCEEDED`, `400 ATTACHMENT_STAGE_INVALID`, `400 CAPTURED_AT_INVALID`, `400 REPORT_NOT_IN_PROGRESS`, `400 REPORT_ALREADY_RESOLVED`, `400 RESOLUTION_PHOTO_REQUIRED`, `403 REPORT_NOT_ASSIGNED`, `403 REPORT_NOT_OWNED`, `403 ATTACHMENT_DELETE_FORBIDDEN`, `404 NOT_FOUND`, `409 ATTACHMENT_DUPLICATE` (gắn 1 ảnh 2 lần), `503 MEDIA_STORAGE_DISABLED`.

### 4.3 Ảnh đại diện — user-service

| Method · Path | Vai trò | Body | Trả về |
|---|---|---|---|
| `PUT /api/user/avatar` | Chính mình | MediaUpload (hoặc cũ `{imageUrl}`) | `UserSummary` |
| `DELETE /api/user/avatar` | Chính mình | — | `UserSummary` |
| `PUT /api/admin/users/{id}/avatar` | ADMIN | MediaUpload | `UserSummary` |
| `DELETE /api/admin/users/{id}/avatar` | ADMIN | — | `UserSummary` |

### 4.4 Ảnh cửa hàng — store-service

| Method · Path | Vai trò | Body | Trả về |
|---|---|---|---|
| `PUT /api/admin/stores/{id}/image` | ADMIN | MediaUpload (hoặc cũ `{imageUrl}`) | `StoreResponse` |
| `DELETE /api/admin/stores/{id}/image` | ADMIN | — | `StoreResponse` |

### 4.5 Ảnh khuyến mãi — order-service

| Method · Path | Vai trò | Body | Trả về |
|---|---|---|---|
| `PUT /api/admin/promotions/{id}/image` | ADMIN | MediaUpload | `Promotion` |
| `DELETE /api/admin/promotions/{id}/image` | ADMIN | — | `Promotion` |

Khi thay/xoá ảnh đại diện, cửa hàng, khuyến mãi: ảnh cũ nằm trong thư mục của hệ thống sẽ bị xoá khỏi Cloudinary sau khi transaction commit (best-effort, lỗi chỉ ghi log).

Thay đổi đi kèm: `UserSummary` (mọi API trả hồ sơ) có thêm `imageUrl`; `StoreResponse` có thêm `imageUrl` (= `image`); `PUT /api/user/profile`, `PUT /api/users/{id}`, `PUT /api/admin/stores/{id}` **không còn xoá ảnh** khi body bỏ trống trường ảnh.

## 5. Quy ước phía client

- Nén trước khi upload: cạnh dài ≤ 1920 px, JPEG chất lượng ~80. Từ chối file > `maxBytes`.
- Hiển thị danh sách bằng `thumbnailUrl`, xem lớn bằng `url`.
- Upload lỗi giữa chừng ⇒ ảnh mồ côi trên Cloudinary (không gắn vào phiếu). Chấp nhận được; dọn định kỳ bằng Cloudinary Console nếu cần.
- Tuyệt đối không gửi header `Authorization` tới `api.cloudinary.com`.
