# Lock.R — Tài liệu dự án

Tủ khoá thông minh + giao hàng bằng drone. Repo này là **nguồn sự thật** về tiến độ, luồng nghiệp vụ, kiến trúc, sơ đồ và luật làm việc cho cả 5 repo code của org [LockR-Tech](https://github.com/LockR-Tech).

## Bắt đầu từ đâu

| Bạn là | Đọc |
|---|---|
| **AI agent** hoặc người mở dự án lần đầu | [AGENTS.md](AGENTS.md) → [STATUS.md](STATUS.md) |
| Muốn biết dự án tới đâu | [STATUS.md](STATUS.md) |
| Sắp viết code | [git-workflow](04-engineering/git-workflow.md) · [commit-convention](04-engineering/commit-convention.md) · file luồng liên quan |
| Sắp merge / deploy | [release-deploy](04-engineering/release-deploy.md) |
| Cần in sơ đồ | [diagrams/](diagrams/README.md) |

## Cấu trúc

```
docs/
├── README.md                 Trang này
├── AGENTS.md · CLAUDE.md     Giao thức làm việc cho agent và người
├── STATUS.md                 ★ Tiến độ · rủi ro · đang làm · việc tiếp theo
├── CHANGELOG.md              Nhật ký thay đổi tài liệu
├── 01-overview/
│   ├── product.md            Sản phẩm, vai trò, 4 luồng, thuật ngữ
│   └── architecture.md       Repo, service, hạ tầng, auth, tích hợp, CI/CD, lệnh dev
├── 02-flows/                 Mỗi luồng: mục tiêu · checklist có bằng chứng · % · luồng hiện tại · gap
├── 04-engineering/
│   ├── git-workflow.md       GitHub Flow, nhánh, PR, merge, hotfix
│   ├── commit-convention.md  Conventional Commits, scope từng repo
│   ├── release-deploy.md     Môi trường, deploy, migration, rollback, secret
│   └── documentation-rules.md Khi nào sửa tài liệu nào, luật sơ đồ A4
├── adr/                      Quyết định kiến trúc
├── diagrams/
│   ├── src/*.mmd             Nguồn Mermaid
│   └── pdf/*.pdf             Bản in, mỗi file đúng 1 trang A4
├── templates/                Mẫu dùng chung cho các repo code
└── scripts/render-a4.mjs     Render Mermaid → PDF A4, kiểm tra số trang
```

## Làm việc với repo này

```bash
git clone https://github.com/LockR-Tech/docs.git   # đặt cạnh các repo code
npm ci && npm run diagrams                          # render sơ đồ (cần Chrome/Edge)
```

Thay đổi tài liệu cũng đi qua nhánh + PR như code. PR template nhắc những gì cần kiểm.
