# ADR-0001: GitHub Flow — `main` là production

| | |
|---|---|
| **Trạng thái** | Accepted |
| **Ngày** | 2026-09-13 |
| **Người quyết định** | BaoHuy-Dev (chủ dự án) |
| **Liên quan** | [git-workflow](../04-engineering/git-workflow.md), [ADR-0003](0003-snapshot-sach-khi-chuyen-org.md) |

## Bối cảnh

- Nhóm nhỏ, chỉ có **một môi trường production**, không có staging.
- Trước đây workflow deploy của `backend` và `mobile` chạy khi push **cả `main` lẫn `develop`**, cùng một concurrency group có `cancel-in-progress` ⇒ push `develop` cũng thay production, và `develop` có thể huỷ ngang một lần deploy từ `main`.
- Repo cũ tích tụ ~100 nhánh tính năng không dọn.
- Sau khi chuyển org, cả 5 repo chỉ còn nhánh `main`.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| **GitHub Flow**: `main` + nhánh ngắn hạn + PR + squash | Đơn giản, khớp hiện trạng chỉ có `main`, lịch sử thẳng | Mọi merge là deploy thật ⇒ cần review kỹ và rollback tốt |
| Git Flow rút gọn: `main` + `develop` | Có vùng tích hợp trước production | Không có staging nên `develop` không có nơi để chạy; phải sửa workflow; thêm bước merge |
| Trunk-based commit thẳng `main` | Nhanh nhất | Không review, rủi ro cao với production thật |

## Quyết định

Dùng **GitHub Flow**. `main` là production. Không nhánh `develop`. Mọi thay đổi qua PR, ≥ 1 approve, squash merge. Bỏ trigger `develop` khỏi mọi workflow.

## Hệ quả

- Tích cực: một đường duy nhất lên production; không còn deploy chồng chéo từ hai nhánh.
- Đánh đổi: không có vùng thử ngoài local ⇒ bắt buộc test ở local + review + theo dõi sau merge; tính năng dở phải giấu sau feature flag.
- Org gói Free + repo private ⇒ **GitHub không cưỡng chế** được PR/review (không có branch protection). Luật dựa trên quy ước cho tới khi nâng gói ([STATUS Q1](../STATUS.md#6-blocker--câu-hỏi-mở)).
- Việc theo sau: khi có staging, xem lại ADR này.
