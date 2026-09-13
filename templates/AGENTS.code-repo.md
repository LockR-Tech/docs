# AGENTS.md — <repo>

Repo này thuộc hệ thống **Lock.R** (org [LockR-Tech](https://github.com/LockR-Tech)). File này chỉ là **con trỏ** — tiến độ, luật và sơ đồ nằm ở repo [**docs**](https://github.com/LockR-Tech/docs). Không ghi tiến độ vào đây.

## Trước khi làm bất cứ việc gì

1. Repo docs phải nằm cạnh repo này (`../docs`). Chưa có: `git clone https://github.com/LockR-Tech/docs.git ../docs`. Có rồi: `git -C ../docs pull --ff-only`.
2. Đọc `../docs/AGENTS.md` — giao thức bắt đầu/kết thúc phiên.
3. Đọc `../docs/STATUS.md` — tiến độ, rủi ro bảo mật, việc đang làm, việc tiếp theo.
4. Đọc file luồng liên quan trong `../docs/02-flows/`.

## Luật bắt buộc

- `main` = production. **Merge vào `main` là deploy thật.** Không push thẳng `main` — nhánh + PR + review + squash merge.
- Nhánh `<type>/<gap-id>-<mo-ta>`; commit và tiêu đề PR theo Conventional Commits; footer `Refs: F2-G01`.
- Không commit secret, `.env` thật, file build. Không thêm trailer `Co-Authored-By` của công cụ AI.
- Việc chỉ xong khi tài liệu ở `../docs` đã cập nhật (STATUS, file luồng, sơ đồ nếu đổi trạng thái).

## Riêng repo này

<!-- lệnh build/test/chạy, deploy, lưu ý -->
