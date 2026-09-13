# ADR-0003: Chuyển sang org `LockR-Tech` bằng snapshot sạch

| | |
|---|---|
| **Trạng thái** | Accepted |
| **Ngày** | 2026-09-13 |
| **Người quyết định** | BaoHuy-Dev (chủ dự án) |
| **Liên quan** | [release-deploy](../04-engineering/release-deploy.md), [ADR-0001](0001-github-flow-main-la-production.md) |

## Bối cảnh

Code nằm ở ba tài khoản cá nhân khác nhau:

| Repo cũ | Repo mới |
|---|---|
| `BaoHuy-Dev/laundry-locker-microservices` (nhánh `develop`) | `LockR-Tech/backend` |
| `LeThiYenVi/laundry-locker-frontend` (`main`) | `LockR-Tech/frontend` |
| `BaoHuy-Dev/smart-laundry-locker-mobile` (`develop`) | `LockR-Tech/mobile` |
| `TruongNguyenThaiBinh77/smart-locker-iot` (`chore/cleanup-unused-assets-and-deps`) | `LockR-Tech/iot` |
| `BaoHuy-Dev/lockerly-legal` (`main`) | `LockR-Tech/legal` |

Repo cũ có hàng trăm nhánh cũ và nhiều tài liệu lỗi thời.

## Quyết định

- Mỗi repo mới là **một commit snapshot** trên `main`, không mang lịch sử cũ.
- Chỉ giữ **mã nguồn + cấu hình build + `.github/`**. Bỏ mọi `*.md` và thư mục `docs/`, ngoại trừ `mobile/assets/markdown/*.md` (asset khai báo trong `pubspec.yaml`).
- 4 repo code **private**; `legal` **public** vì GitHub Pages không chạy trên repo private ở gói Free.
- Repo cá nhân cũ **giữ nguyên làm lưu trữ**, không archive, không xoá. Workflow deploy trong đó **đã tắt** (`disabled_manually`); CI/security vẫn chạy.
- **Nguồn deploy duy nhất là `LockR-Tech`.** Secret đã nạp lại: Azure (4) cho backend, Cloudflare (2) cho frontend và mobile.

## Hệ quả

- Tích cực: repo gọn; một nguồn deploy; quyền tập trung ở org.
- Đánh đổi: `git blame` và lịch sử PR cũ chỉ còn xem được ở repo cá nhân. Hai bên có lịch sử không liên quan ⇒ **không push chéo** giữa repo cũ và mới.
- File bị gitignore (`fe/.env`, `landingPage/.env`, `mobile/.env`, `iot/ui/.env`) không nằm trong git — clone mới phải tự tạo lại. Build CI của frontend/mobile không cần chúng (có giá trị mặc định trỏ `https://api.locker-drone.tech`).
- Token Cloudflare đã bị dán vào lịch sử một phiên chat khi nạp secret ⇒ nên xoay token.
