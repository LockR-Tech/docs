# Quy ước commit — Conventional Commits 1.0

Commit trên `main` là lịch sử production. Viết để 6 tháng sau người khác đọc `git log` hiểu **đã đổi gì và vì sao**.

## 1. Cú pháp

```
<type>(<scope>)<!>: <mô tả>

[body — vì sao đổi, đổi gì đáng chú ý, ảnh hưởng]

[footer]
```

| Phần | Luật |
|---|---|
| `type` | Bắt buộc, một trong bảng § 2 |
| `scope` | Nên có, lấy từ bảng § 3 |
| `!` | Có thay đổi phá vỡ tương thích (API, schema, hợp đồng MQTT) — kèm footer `BREAKING CHANGE:` |
| mô tả | Tiếng Việt có dấu được phép; viết thường; câu mệnh lệnh ("thêm", "sửa", không "đã thêm"); ≤ 72 ký tự; không dấu chấm cuối |
| body | Cách dòng trống; giải thích **vì sao**; xuống dòng ~72 ký tự |
| footer | `Refs: F2-G01, SEC-03` · `Closes #12` · `BREAKING CHANGE: …` |

## 2. Type

| type | Khi nào | Deploy? |
|---|---|---|
| `feat` | Thêm tính năng cho người dùng | Có |
| `fix` | Sửa lỗi | Có |
| `sec` | Vá bảo mật | Có |
| `perf` | Tăng hiệu năng | Có |
| `refactor` | Đổi cấu trúc, không đổi hành vi | Có |
| `test` | Thêm/sửa test | Có (CI) |
| `docs` | Chỉ tài liệu (`*.md`) | Không (bị bỏ qua bởi trigger) |
| `ci` | Workflow, pipeline | Tuỳ |
| `build` | Maven/Gradle/npm/pubspec, Dockerfile | Có |
| `chore` | Việc lặt vặt không thuộc loại trên | Tuỳ |
| `revert` | Hoàn tác commit trước — body ghi `This reverts commit <sha>` | Có |

## 3. Scope theo repo

| Repo | Scope |
|---|---|
| backend | `gateway` `auth` `user` `order` `locker` `payment` `notification` `iot` `store` `loyalty` `common` `discovery` `infra` `docker` `db` `ci` |
| frontend | `fe` `landing` `ci` — hoặc khu vực: `fe-orders`, `fe-drones`, `fe-users`… |
| mobile | tên feature trong `lib/features/`: `auth` `locker-ops` `drone-delivery` `maintenance` `payment` `notifications`… · `core` `router` `web` `android` `ios` `ci` |
| iot | `pi` `arduino` `kiosk` `mqtt` `simulator` `setup` |
| legal | `privacy` `data-deletion` |
| docs | `status` `flows` `diagrams` `engineering` `adr` `overview` |

## 4. Ví dụ

```text
feat(order): hoàn tất đơn khi nhận bằng mã tại kiosk

Trước đây kiosk chỉ mở cửa, đơn vẫn STORING và PIN dùng lại được
tới khi EXPIRED. Giờ iot-service gọi order-service hoàn tất đơn,
tính phí quá hạn và thu hồi PIN ngay sau khi tủ xác nhận mở.

Refs: F2-G01, F1-G05
```

```text
sec(user)!: chặn tự cấp vai trò qua PUT /api/users/{id}

BREAKING CHANGE: trường roles và status bị bỏ qua với request không
phải ADMIN. Web admin phải dùng PUT /api/admin/users/{id}/roles.

Refs: SEC-02, F3-G01
```

```text
fix(locker-ops): xác nhận bỏ hàng bằng id đơn thay vì id payment

Refs: F2-G11
```

```text
docs(status): cập nhật tiến độ L2 lên 70% sau khi merge F2-G01
```

## 5. Không được

- Commit secret, token, `.env` thật, khoá SSH, dump database. Lỡ commit ⇒ **xoay secret ngay** rồi mới dọn lịch sử.
- Mô tả vô nghĩa: `update`, `fix bug`, `wip`, `.`, `sửa`.
- Gộp nhiều mục đích không liên quan vào một commit/PR.
- Trailer `Co-Authored-By` của công cụ AI.
- Commit file build (`target/`, `build/`, `dist/`, `node_modules/`, `.dart_tool/`).

Trong nhánh tính năng có thể commit nhỏ tuỳ ý; khi squash merge, **tiêu đề PR** là thứ còn lại trên `main` — tiêu đề PR phải đúng quy ước này.
