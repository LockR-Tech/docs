# Git workflow — GitHub Flow, `main` là production

Quyết định: [ADR-0001](../adr/0001-github-flow-main-la-production.md). Áp dụng cho cả 6 repo.

## 1. Nguyên tắc

1. **`main` luôn deploy được và chính là production.** Merge vào `main` của `backend`, `frontend`, `mobile` **tự động deploy thật** (xem [release-deploy](release-deploy.md)).
2. **Không push thẳng `main`.** Mọi thay đổi đi qua nhánh ngắn hạn → Pull Request → review → **squash merge**.
3. Không có nhánh `develop`, không có nhánh dài hạn. Chưa có môi trường staging.
4. Một PR = một mục đích. Code và tài liệu đi cùng nhau ([documentation-rules](documentation-rules.md)).

## 2. Đặt tên nhánh

```
<type>/<gap-id>-<mô-tả-ngắn-kebab>      khi làm một gap đã có mã
<type>/<mô-tả-ngắn-kebab>               việc nhỏ không có mã
```

| type | Dùng khi |
|---|---|
| `feat` | Tính năng mới |
| `fix` | Sửa lỗi |
| `sec` | Vá bảo mật (SEC-xx) — ưu tiên review |
| `refactor` | Đổi cấu trúc, không đổi hành vi |
| `perf` | Hiệu năng |
| `test` | Chỉ thêm/sửa test |
| `docs` | Chỉ tài liệu |
| `ci` | Workflow, pipeline |
| `chore` | Dọn dẹp, dependency, cấu hình |
| `hotfix` | Sửa gấp production — xem § 6 |

Ví dụ: `feat/f2-g01-kiosk-pickup-complete` · `sec/sec-02-user-roles-escalation` · `fix/f2-g11-send-parcel-order-id` · `docs/status-2026-09-20`.

Chữ thường, không dấu tiếng Việt, tối đa ~50 ký tự.

## 3. Vòng đời một thay đổi

```bash
git switch main && git pull --ff-only
git switch -c feat/f2-g01-kiosk-pickup-complete
# … code + test + cập nhật docs …
git commit -m "feat(order): hoàn tất đơn khi nhận bằng mã tại kiosk"   # xem commit-convention
git fetch origin && git rebase origin/main                             # giữ nhánh thẳng, không merge main vào nhánh
git push -u origin HEAD
gh pr create --fill                                                     # điền PR template
```

- **Nhánh sống ≤ 3 ngày làm việc.** Việc lớn ⇒ chia nhiều PR nhỏ; tính năng dở dang giấu sau feature flag.
- Đẩy lên sớm, mở **Draft PR** khi còn làm để người khác thấy.
- Cập nhật từ `main` bằng `rebase`. Đã có người review thì dùng `git push --force-with-lease`, không bao giờ `--force`.

## 4. Pull Request

**Tiêu đề PR** = một Conventional Commit, vì squash merge lấy tiêu đề PR làm commit trên `main`:
`feat(order): hoàn tất đơn khi nhận bằng mã tại kiosk`

**Mô tả** theo PR template (có sẵn trong mọi repo): mục đích, gap/SEC liên quan, cách test, ảnh hưởng deploy/migration, **link PR docs**.

**Điều kiện merge**

| # | Điều kiện |
|---|---|
| 1 | ≥ 1 người review **approve** (không tự approve PR của mình) |
| 2 | CI xanh (`backend-ci`, `backend-security`, `flutter test`, `diagrams`) |
| 3 | Đã rebase trên `main` mới nhất, không conflict |
| 4 | Tài liệu đã cập nhật hoặc PR ghi rõ "không ảnh hưởng tài liệu" |
| 5 | Có migration DB ⇒ tương thích ngược ([release-deploy § 4](release-deploy.md#4-migration-cơ-sở-dữ-liệu)) |
| 6 | Người merge sẵn sàng theo dõi deploy tới khi smoke test xanh |

**Merge:** chỉ **Squash and merge**, xoá nhánh sau khi merge. Không merge vào tối thứ Sáu / trước ngày nghỉ nếu không có người trực.

**Review:** phản hồi trong 1 ngày làm việc. Người review kiểm: đúng mục đích, test, phân quyền (ai gọi được endpoint này?), migration, secret, tài liệu.

## 5. `[skip ci]`

Commit trên `main` chứa `[skip ci]` sẽ **không chạy workflow nào**, kể cả deploy. Chỉ dùng cho thay đổi **không đụng tới code chạy** (ví dụ `AGENTS.md`, PR template, chỉnh trigger workflow) và phải ghi lý do trong PR. Không bao giờ dùng để né CI khi sửa code.

## 6. Hotfix production

1. `git switch -c hotfix/<mô-tả> origin/main`
2. Sửa tối thiểu + test tái hiện lỗi.
3. PR tiêu đề `fix(...)`, gắn nhãn `hotfix`, gọi reviewer trực tiếp — vẫn cần 1 approve.
4. Merge ⇒ theo dõi deploy ⇒ nếu hỏng thì **rollback trước, điều tra sau** ([release-deploy § 5](release-deploy.md#5-rollback)).
5. Ghi sự cố vào STATUS § 5 và CHANGELOG.

## 7. Giới hạn hiện tại

Org `LockR-Tech` đang dùng gói **GitHub Free** với repo private ⇒ **không bật được branch protection hay rulesets**. GitHub sẽ không chặn push thẳng `main` hay merge khi chưa review — luật này đang được giữ bằng **quy ước + PR template + review chéo**. Nâng gói Team để GitHub cưỡng chế: cần quyết định ở [STATUS Q1](../STATUS.md#6-blocker--câu-hỏi-mở). Khi nâng, bật ruleset cho `main`: require PR, 1 approval, dismiss stale approvals, require status checks, block force push, require linear history.
