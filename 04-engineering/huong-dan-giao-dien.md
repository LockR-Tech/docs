# Luật: đổi giao diện ⇒ cập nhật hướng dẫn trên màn hình + HDSD

Áp dụng cho **mọi người và mọi AI agent**, ở cả 3 giao diện: web admin (`frontend/fe`), app mobile (`mobile`), kiosk tại tủ (`iot/ui`). Hệ thống hướng dẫn được mô tả ở [ADR-0011](../adr/0011-huong-dan-lan-dau-tren-man-hinh.md) (F3-G13).

## 1. Khi nào phải cập nhật

Phải cập nhật **trong cùng PR / cùng đợt** khi bạn thêm, xoá hoặc sửa bất kỳ thứ gì sau đây:

- màn hình, trang, route;
- nút, tab, hộp thoại, bảng dưới, menu "⋯";
- bộ lọc, ô nhập, cột bảng;
- nhãn chữ mà hướng dẫn đang trích dẫn (vd. "Xem chi tiết", "Bỏ qua vĩnh viễn").

**Không cần cập nhật** nếu thay đổi không làm hướng dẫn sai, ví dụ:

- chỉ đổi màu hoặc khoảng cách;
- sửa lỗi logic bên trong, mà nút, nhãn và vị trí vẫn như cũ;
- đổi thông báo lỗi mà hướng dẫn không nhắc tới.

Trường hợp này phải tick **"Không ảnh hưởng hướng dẫn — lý do: …"** trong PR và ghi rõ lý do.

## 2. Phải làm gì

| # | Việc | Ở đâu |
|---|---|---|
| 1 | Gắn / sửa neo trên phần tử | web `data-tour="<neo>"`, app `TourAnchor('<neo>')`, kiosk `frontend/fe/scripts/hdsd/kiosk-anchors.json` |
| 2 | Khai nhóm / bước: `platforms`, `webRoute` / `mobileRoute`, `via` (mở chi tiết / tab / hộp thoại), `optional`, `manualOnly` | `frontend/fe/public/onboarding/tours.json` |
| 3 | Viết chữ tiếng Việt và tiếng Anh (`groups.<nhóm>.title|summary`, `steps.<bước>.title|body`) | `frontend/fe/public/onboarding/locales/{vi,en}.json` |
| 4 | **Tăng `version`** của nhóm đã sửa, để người đã xem nhận hộp "Có hướng dẫn mới" | `tours.json` |
| 5 | Chụp lại ảnh HDSD: `npm run hdsd:capture -- --groups=<nhóm>` (chỉ chạy trên dev/demo) | repo frontend |
| 6 | App: chép nội dung sang app bằng `bash tool/sync_onboarding.sh` | repo mobile |
| 7 | Test xanh: `npm test` ở `fe/`, `flutter test test/onboarding` ở mobile. Test đỏ khi thiếu neo, thiếu chữ, thiếu ảnh, ảnh lệch bước, hoặc **có route mới mà chưa có hướng dẫn** | CI |

Thêm màn hình mới thì thêm nhóm mới, có `order` đúng khoảng của khu. Chỉ đặt cờ `intro` cho nhóm tổng quan. Màn hình không dẫn được bằng tour (trước khi đăng nhập, cần đơn thật) thì đặt `manualOnly`. Màn hình cần dữ liệu thật mà không chụp được thì đặt `noImage`.

## 3. Ai nhắc, nhắc ở đâu

| Lúc | Cơ chế | Chặn hay chỉ nhắc |
|---|---|---|
| Mở phiên Claude Code trong repo frontend / mobile | Hook `SessionStart` (`.claude/settings.json`) đưa luật vào ngữ cảnh | nhắc |
| AI sửa một file giao diện | Hook `PostToolUse` nhắc cả AI lẫn người dùng | nhắc |
| AI kết thúc lượt trả lời mà giao diện đã đổi, hướng dẫn chưa đổi | Hook `Stop` hiện cảnh báo | nhắc |
| Commit file giao diện mà không kèm hướng dẫn | Git hook `.githooks/pre-commit` | nhắc |
| Mở / sửa PR | Mẫu PR có mục "Hướng dẫn trên màn hình" | phải tick |
| PR đổi giao diện | Check CI **"Hướng dẫn trên màn hình"** (`.github/workflows/huong-dan.yml`) | **chặn merge** cho tới khi có cập nhật hướng dẫn hoặc tick "Không ảnh hưởng" kèm lý do |
| Mọi PR frontend / mobile | `npm test` / `flutter test`: thiếu neo, chữ, ảnh, hoặc route mới chưa có hướng dẫn | **chặn merge** |

### Bật git hook (một lần cho mỗi bản clone)

- **frontend**: `npm install` trong `fe/` tự chạy `git config core.hooksPath .githooks` (script `prepare`).
- **mobile**: `bash tool/setup_hooks.sh`.

### File giao diện được nhận diện

- **frontend**:
  - giao diện: `fe/src/pages/`, `fe/src/components/`, `fe/src/layouts/`, `fe/src/routes/`, `fe/src/constants/sidebar.ts`, `fe/messages/{vi,en}.json`;
  - hướng dẫn: `fe/public/onboarding/`, `fe/scripts/hdsd/`.
- **mobile**:
  - giao diện: `lib/**/presentation/`, `lib/shared/widgets/`, `lib/core/routing/`, `lib/core/presentation/`, `lib/l10n/app_{vi,en}.arb`;
  - hướng dẫn: `assets/onboarding/`, hoặc diff có thêm / bớt `TourAnchor(`. Nội dung nằm ở repo frontend, nên PR mobile có thể tick "Đã cập nhật hướng dẫn" kèm link PR frontend.
- **kiosk** (`iot/ui/src/`): chưa có CI ở repo iot, vì merge iot làm Pi của tủ thật tự cập nhật. Hook Claude Code ở thư mục làm việc vẫn nhắc. Người sửa kiosk tự cập nhật nhóm `kiosk-*` và `kiosk-anchors.json` ở repo frontend.
