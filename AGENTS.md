# AGENTS.md — Giao thức làm việc cho người & AI agent

Áp dụng cho **mọi** agent (Claude Code, Codex, Cursor, Copilot…) và mọi thành viên khi làm việc trên bất kỳ repo nào của Lock.R. Mục tiêu: ai mở dự án cũng biết ngay **đang ở đâu, làm gì tiếp**, và tài liệu **luôn khớp với code**.

## 0. Bản đồ

```
G:\Lock.R\            (hoặc thư mục cha bất kỳ — giữ các repo cạnh nhau)
├── docs/       ← repo này: tiến độ, luật, sơ đồ, quyết định
├── backend/    ← Spring Boot microservices  (deploy Azure VM khi merge main)
├── frontend/   ← Admin web + landing page    (deploy Cloudflare khi merge main)
├── mobile/     ← Flutter app + mobile web    (deploy Cloudflare khi merge main)
├── iot/        ← Raspberry Pi + Arduino + kiosk
└── legal/      ← Trang chính sách (GitHub Pages)
```

| Cần biết | Đọc |
|---|---|
| Đang tới đâu, làm gì tiếp | [STATUS.md](STATUS.md) |
| Hệ thống là gì, ai dùng | [01-overview/product.md](01-overview/product.md) |
| Kiến trúc, service, port, deploy | [01-overview/architecture.md](01-overview/architecture.md) |
| Chi tiết từng luồng + gap | [02-flows/](02-flows/) |
| Sơ đồ trạng thái (PDF A4) | [diagrams/](diagrams/README.md) |
| Nhánh, PR, merge | [04-engineering/git-workflow.md](04-engineering/git-workflow.md) |
| Commit message | [04-engineering/commit-convention.md](04-engineering/commit-convention.md) |
| Deploy, rollback, migration | [04-engineering/release-deploy.md](04-engineering/release-deploy.md) |
| Khi nào phải sửa tài liệu | [04-engineering/documentation-rules.md](04-engineering/documentation-rules.md) |
| Vì sao làm thế | [adr/](adr/README.md) |

## 1. Bắt đầu phiên

1. **Kéo bản mới nhất** của `docs` và repo bạn sắp sửa: `git pull --ff-only`.
2. **Đọc [STATUS.md](STATUS.md)** — mục 2 (rủi ro), 3 (đang làm), 4 (tiếp theo).
3. **Kiểm tra độ tươi**: so commit đã rà soát (STATUS § 0) với code hiện tại.
   ```bash
   git -C ../backend log --oneline 705c556..origin/main -- . ':!*.md'
   ```
   Có commit code chưa được phản ánh trong STATUS ⇒ **đừng tin mù quáng**: đọc diff phần liên quan tới việc của bạn trước, và ghi nhận khác biệt khi cập nhật STATUS cuối phiên.
4. **Đọc file luồng** chứa gap bạn sắp làm (`02-flows/flow-N-*.md`) và sơ đồ trạng thái liên quan.
5. **Nhận việc**: thêm một dòng vào STATUS § 3 (việc, ID gap, tên, nhánh). Việc đã có người nhận thì chọn việc khác hoặc hỏi.

## 2. Trong khi làm

- **Code là sự thật, tài liệu là bản đồ.** Tài liệu mâu thuẫn code ⇒ tin code, và sửa tài liệu trong cùng đợt.
- Tuân thủ [git-workflow](04-engineering/git-workflow.md) và [commit-convention](04-engineering/commit-convention.md): không push thẳng `main`; `main` = production, **merge là deploy**.
- Ghi ID gap vào tên nhánh và footer commit: `feat/f2-g01-kiosk-pickup`, `Refs: F2-G01`.
- **Không bao giờ** commit secret, token, mật khẩu, khoá SSH, file `.env` thật. Tài liệu chỉ ghi **tên** secret, không ghi giá trị.
- Không thêm trailer `Co-Authored-By` của công cụ AI vào commit.

## 3. Kết thúc phiên — Definition of Done

Một việc **chưa xong** cho tới khi tài liệu phản ánh nó. PR code phải đi kèm PR `docs` (hoặc ghi rõ "không ảnh hưởng tài liệu" và lý do).

| Nếu bạn đã… | Thì cập nhật |
|---|---|
| Làm bất cứ việc gì | **STATUS.md**: bỏ dòng ở § 3; thêm vào § 5 khi đã merge; sửa § 4 nếu thứ tự ưu tiên đổi |
| Hoàn thành / làm dở một hạng mục checklist | **File luồng**: đổi verdict + bằng chứng `repo/path:line` ⇒ tính lại % ⇒ sửa % ở STATUS § 1 |
| Thêm/đổi/xoá trạng thái hoặc chuyển trạng thái | **`diagrams/src/*.mmd`** (sơ đồ + bảng `@row`) ⇒ `npm run diagrams` ⇒ commit cả PDF |
| Thêm service, endpoint công khai, queue, topic, biến môi trường, secret | **01-overview/architecture.md** (+ `architecture.mmd` nếu đổi thành phần) |
| Vá hoặc phát hiện lỗ hổng | **STATUS § 2** (thêm/xoá dòng SEC-xx) |
| Ra quyết định kiến trúc / quy trình khó đảo ngược | **ADR mới** trong `adr/` |
| Mọi thay đổi ở repo docs | **CHANGELOG.md** — 1 dòng |

Sau cùng: cập nhật dòng **Cập nhật lần cuối** và **Mốc code đã rà soát** (STATUS § 0) nếu bạn đã kiểm lại phần code tương ứng.

## 4. Quy tắc chấm tiến độ

- **DONE** — có API **và** client thật sự gọi **và** trạng thái được lưu **và** phân quyền đúng. Thiếu một vế ⇒ PARTIAL.
- **PARTIAL** — thiếu một lớp, có stub/mock/TODO, chỉ chạy ở DEMO/giả lập, hoặc chưa nối vào UI.
- **MISSING** — không có code.
- Mọi verdict phải có bằng chứng `repo/đường/dẫn:dòng`. Không có bằng chứng ⇒ không được chấm DONE.
- Không đổi % mà không đổi checklist. Không thêm/bớt hạng mục checklist mà không ghi lý do vào CHANGELOG.

## 5. Mã định danh

| Mẫu | Ý nghĩa | Ví dụ |
|---|---|---|
| `L1`…`L4` | Luồng nghiệp vụ | L2 = thuê tủ gửi hàng |
| `F2.07` | Hạng mục checklist số 7 của luồng 2 | |
| `F2-G01` | Gap (việc cần làm) số 1 của luồng 2 | dùng trong nhánh, commit, PR |
| `SEC-01` | Rủi ro bảo mật | |
| `O3`, `D2`, `C6`, `T9` | Mã chuyển trạng thái trên sơ đồ đơn hàng / mission / ô tủ / drone | |
| `ADR-0001` | Quyết định kiến trúc | |
