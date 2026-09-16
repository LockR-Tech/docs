# Bàn giao — 3 trang báo cáo admin (web) & phần mobile còn lại (2026-09-16)

> Dành cho người hoặc AI agent tiếp tục trên máy khác. Đọc mục 1–3 trước khi làm.
> Quy trình chung: [AGENTS.md](../AGENTS.md), [STATUS.md](../STATUS.md). File này **không chứa secret**.
> Việc trước đó: [2026-09-16-cau-hinh-nghiep-vu-va-bao-cao-admin.md](2026-09-16-cau-hinh-nghiep-vu-va-bao-cao-admin.md).

## 1. Đã làm trong phiên này

### 1.1 Frontend — 3 trang báo cáo admin (mục 3 bước 2 của bàn giao trước)

Nhánh `feat/f2-g08-admin-reporting-web` (repo `frontend`), **đã đẩy lên origin, chưa mở PR**. 5 commit:

| Commit | Nội dung |
|---|---|
| `c64f14a` | `feat(fe-report-api)` — kiểu dữ liệu `src/types/admin/reporting.ts`, endpoint trong `api-paths.ts`, RTK Query cho đơn/thanh toán/doanh thu, tiện ích `lib/report-format.ts` + `lib/report-error.ts` |
| `c4de94c` | `feat(fe-report-ui)` — `src/components/shared/reporting/`: nhãn/màu enum, badge, chọn khoảng ngày, thẻ KPI, khối báo lỗi, cặp nhãn–giá trị |
| `2d4b6b2` | `feat(fe-orders)` — dựng lại `/admin/orders` + trang chi tiết |
| `28bae57` | `feat(fe-payments)` — dựng lại `/admin/payments`, thêm tab hoàn tiền và biến động ví |
| `dcb6c4e` | `feat(fe-revenue)` — dựng lại `/admin/revenue` + trang chi tiết khách hàng |

Điểm cần biết khi đọc code:

- **Enum**: bộ backend thực sự sinh ra nằm ở `src/types/admin/reporting.ts`; bộ legacy giặt ủi ở `src/types/admin/enums.ts` **vẫn giữ** vì các màn hình khác dùng. Nhãn hiển thị tập trung ở `src/components/shared/reporting/report-meta.ts`, gặp mã lạ thì hiện nguyên mã thay vì vỡ giao diện.
- **Thời gian**: mọi chỗ dùng `formatDateTime` (`src/lib/datetime.ts`) ⇒ `HH:mm:ss dd/MM/yyyy` giờ Việt Nam. Trường `LocalDate` (`from`, `to`, `date`) dùng `formatDayLabel`, **không** đổi múi giờ.
- **Bộ lọc nằm trên URL** ở cả 3 trang ⇒ chia sẻ được đường dẫn, F5 không mất. Lọc/phân trang/sắp xếp do backend làm, web không tự cắt trang nữa.
- **Đổi trạng thái gửi body JSON** (`updateAdminOrderStatus`, `updateAdminPaymentStatus`). Mutation cũ gửi query param vẫn còn trong `apis/admin/orders.ts` và `payments.ts` nhưng **không màn hình nào dùng** — giữ lại vì endpoint backend cũ chưa bỏ.
- **Lỗi `PAYMENT_DATA_UNAVAILABLE` (503)** hiện khối báo lỗi kèm mã, **không** vẽ số 0. Xem `src/lib/report-error.ts`.
- **Doanh thu**: mọi tab dùng chung một khoảng ngày (`useRevenueRange`) để các con số cộng khớp; khoảng > 366 ngày bị chặn trước khi gọi API.
- **Biểu đồ theo ngày**: 2 chuỗi cùng đơn vị trên **một** trục, có chú giải và nút xem bảng. Màu ở biến CSS `--report-series-1/2` trong `src/index.css`, có bộ riêng cho nền tối; đã kiểm tách được khi mù màu ở cả hai chế độ.
- Đã **xoá** các thành phần dữ liệu giả: `orders/components/CreateOrderModal.tsx`, `revenue/components/{UserRevenueTab,UserRevenueDetailModal,KioskRevenueTab,LocationRevenueTab}.tsx`.

Kiểm tra đã chạy trên nhánh:

```bash
npx tsc -b          # không lỗi
npm run lint        # 0 error, 69 warning (baseline main: 0 error, 70 warning)
npm run build       # xanh
```

15 endpoint mới đều trả **401** trên `https://api.locker-drone.tech` ⇒ route tồn tại, đường dẫn web dùng là đúng. **Chưa thử với token ADMIN thật** — xem mục 3.

### 1.2 Docs

Nhánh `docs/f2-g08-admin-reporting-web`: STATUS § 3, flow-2 (F2.09 và F2-G08), CHANGELOG, file này.

## 2. Việc cần làm tiếp — theo thứ tự

1. **Mở PR frontend** cho `feat/f2-g08-admin-reporting-web` → `main`, review, merge **rebase**. Máy làm phiên này không có `gh` và không đọc được token nên chỉ đẩy được nhánh.
   Đường dẫn tạo PR: `https://github.com/LockR-Tech/frontend/pull/new/feat/f2-g08-admin-reporting-web`
2. **Thử với token ADMIN thật** sau khi Cloudflare deploy: mở `/admin/orders`, `/admin/payments`, `/admin/revenue`, đối chiếu vài đơn với app khách. Cần soát kỹ:
   - đơn `EXPIRED` (số ô trống — backend đã nhả ô) và đơn `DRONE_DELIVERY` (khối chuyến bay);
   - giao dịch `VNPAY_TOPUP` (không gắn đơn, không tính vào doanh thu);
   - khoảng ngày không có dữ liệu (phải ra 0 chứ không phải lỗi) so với khi payment-service chết (phải ra lỗi).
3. **Mobile phần dở dang** — xem mục 3.
4. Sau khi merge hết: STATUS § 3 → § 5; ADR-0005 `Proposed` → `Accepted` khi chủ dự án xác nhận.
5. Nên làm (giữ từ bàn giao trước): ràng buộc chéo `app.locker.reserved-ttl-hours` ≥ `app.order.auto-cancel-hours`; tăng `APP_RESILIENCE4J_TL_TIMEOUT` của locker-service nếu `app.iot.unlock-wait-seconds` > 20.

## 3. Mobile — phần dở dang

Nhánh gốc: `origin/wip/mobile-business-settings-remaining`, commit `a7acd4a` (agent trước dừng vì hết phiên, **chưa chạy `flutter analyze`/`flutter test`**).

Đã soát tĩnh trong phiên này: **mọi ký hiệu commit đó dùng đều tồn tại trên `main`** —
`BusinessConfig.{droneDeliveryFee, droneDefaultParcelWeightGrams, dronePickupHoursLimit, reportPhotosPerRequestReporter, reportPhotosPerRequestStaff, tierSilverPoints, tierGoldPoints, tierPlatinumPoints, nearbyDefaultRadiusKm}`,
`BusinessConfigStateMixin`, `dronePickupPolicyText`, `StoreService.getStores(radiusKm:)`, `PhotoPickerController.maxPhotos`, `useBusinessConfig` (test helper). Nên khả năng biên dịch được là cao, nhưng **vẫn phải chạy kiểm tra trước khi merge**.

Các bước:

```bash
git -C mobile switch -c feat/adr-0005-mobile-remaining main
git -C mobile cherry-pick a7acd4a          # hoặc chép thủ công từng file
flutter pub get
flutter analyze                             # không được thêm issue so với baseline 259
flutter test                                # baseline main: 147 pass
```

Ba test mới trong commit đó cần đúng: phí drone/hạn lấy hàng/khối lượng kiện theo cấu hình, giới hạn ảnh báo lỗi theo cấu hình, và `nextLoyaltyTierText`. Xong thì tách commit sạch, mở PR, merge **rebase**.

## 4. Ghi chú môi trường (máy phiên này)

- Máy **không có** Node, JDK, Maven, Flutter, `gh`; Docker Desktop có cài nhưng daemon không chạy. Đã dùng bản portable trong thư mục tạm của phiên: Node 24.21.0 và Flutter 3.44.9. Máy mới nên cài sẵn Node 22, Flutter 3.44.x, JDK 21, Maven 3.9, GitHub CLI.
- `npm ci` lần đầu **đỏ** vì `EBUSY` khi hậu cài đặt `esbuild` ghi `esbuild.exe` (phần mềm diệt virus giữ file). Xoá `node_modules` rồi chạy lại là xong.
- Git trên máy này chưa cấu hình `user.name`/`user.email`; đã đặt trùng lịch sử commit sẵn có.
- `git push` chạy được nhờ Git Credential Manager, nhưng **không đọc được token** để gọi REST API tạo PR.

## 5. Lời nhắn mẫu cho AI ở phiên mới

> Đọc `docs/AGENTS.md`, `docs/STATUS.md`, rồi `docs/handoff/2026-09-16-bao-cao-admin-web-va-mobile-con-lai.md`. Tiếp tục mục 2 theo thứ tự. Commit từng bước theo `docs/04-engineering/commit-convention.md`, không thêm trailer Co-Authored-By, merge kiểu rebase.
