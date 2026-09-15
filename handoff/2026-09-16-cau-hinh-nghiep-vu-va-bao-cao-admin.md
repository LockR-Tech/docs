# Bàn giao — Cấu hình nghiệp vụ trên admin & báo cáo đơn/thanh toán/doanh thu (2026-09-16)

> Dành cho người hoặc AI agent tiếp tục trên máy khác. Đọc mục 1–3 trước khi làm.
> Quy trình chung: [AGENTS.md](../AGENTS.md), [STATUS.md](../STATUS.md). File này **không chứa secret**.
> Việc trước đó (ảnh Cloudinary): [2026-09-15-luu-anh-cloudinary.md](2026-09-15-luu-anh-cloudinary.md) — việc gấp còn lại bên đó là đặt `CLOUDINARY_URL` trên VM.

## 1. Yêu cầu của chủ dự án

1. **Toàn bộ business rule phải cấu hình trên admin thay vì hardcode.**
2. Trang admin `/admin/revenue`, `/admin/payments`, `/admin/orders` phải **đồng bộ dữ liệu thật với user mobile**; thiếu API thì bổ sung; mỗi thông tin hiển thị đủ trường cụ thể; **thời gian hiển thị có giờ:phút:giây** (chốt định dạng `HH:mm:ss dd/MM/yyyy`, giờ Việt Nam — trùng định dạng app mobile đang dùng).
3. Làm tới đâu commit tới đó; merge kiểu **rebase** để giữ từng commit.

| Tài liệu | Nội dung |
|---|---|
| [ADR-0005](../adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md) | Vì sao mỗi service tự sở hữu bảng `system_settings`; những gì cố ý không đưa lên admin |
| [01-overview/business-settings.md](../01-overview/business-settings.md) | Hợp đồng API cấu hình nghiệp vụ |
| [01-overview/admin-reporting-api.md](../01-overview/admin-reporting-api.md) | Hợp đồng API admin đơn hàng / thanh toán / doanh thu (do agent backend viết) |

## 2. Trạng thái tại thời điểm bàn giao

### 2.1 Cấu hình nghiệp vụ (yêu cầu 1)

| Repo | PR / nhánh | Trạng thái |
|---|---|---|
| backend | [#6](https://github.com/LockR-Tech/backend/pull/6) — 10 commit: common module, gateway, order, locker, iot, auth, payment, loyalty, store | ✅ Merge `main` (`8f5ca15`). Deploy Azure **tự chạy sau merge** — kiểm tra Actions. CI `test` trước merge: success. |
| frontend | [#6](https://github.com/LockR-Tech/frontend/pull/6) — trang `/admin/settings` (3 commit) | ✅ Merge `main` (`34a793a`), Cloudflare tự deploy |
| mobile | [#5](https://github.com/LockR-Tech/mobile/pull/5) — đọc giá/giờ thuê/mốc nạp/phương thức từ server (3 commit) | ✅ Merge `main` (`133ac20`); `flutter test` 147 pass |
| mobile | nhánh `wip/mobile-business-settings-remaining` (`a7acd4a`) | ⏳ **Dở dang, chưa kiểm tra** — giới hạn ảnh báo lỗi/KTV, phí + khối lượng mặc định drone, bán kính cửa hàng, văn bản phí quá hạn. Agent dừng vì giới hạn phiên. |
| docs | nhánh `docs/adr-0005-business-settings` | ADR-0005, hợp đồng, file này |

Quy tắc đã đưa lên cấu hình: xem bảng mục 4 của [business-settings.md](../01-overview/business-settings.md). Kiểm tra sau deploy:

```bash
curl -s https://api.locker-drone.tech/api/settings/order/public        # 200, có app.order.send-base-fee = 15000
curl -s -o /dev/null -w '%{http_code}' https://api.locker-drone.tech/api/admin/settings/order   # 401
```

**Thay đổi hành vi đáng chú ý:** `POST /api/orders` và `/api/orders/send` **bỏ qua `totalPrice` client gửi** (trước đây khách tự đặt giá được). Mặc định mọi quy tắc = giá trị đang chạy trước đó ⇒ không đổi hành vi nếu admin chưa sửa.

### 2.2 Báo cáo admin (yêu cầu 2)

| Repo | Nhánh | Trạng thái |
|---|---|---|
| backend | `feat/admin-orders-payments-revenue` — 11 commit | Code xong theo hợp đồng; `mvn test` 8 module pass; CI `test` success. **Đã rebase lên `main` có settings, đang chạy lại test** lúc viết — xem mục 3 bước 1. |
| frontend | — | ❌ **Chưa làm**: 3 trang vẫn như cũ (revenue 100% dữ liệu giả; payments thời gian giả, đổi trạng thái lỗi 400; orders crash với STORING/EXPIRED/AWAITING_DISPATCH). |

Các commit backend báo cáo: internal lookup theo lô (user, locker, store), `PaymentResponse` thêm thời gian + API nội bộ số liệu thu tiền, tìm kiếm phân trang + chi tiết đơn đầy đủ, tra cứu giao dịch/hoàn tiền/biến động ví cho admin, thống kê giao dịch có so sánh kỳ trước, báo cáo doanh thu theo tiền thực thu, route gateway, tiện ích mốc thời gian giờ Việt Nam.

## 3. Việc cần làm tiếp — theo thứ tự

1. **Backend báo cáo:** nếu test sau rebase pass và đã push (`git -C <backend> log origin/feat/admin-orders-payments-revenue`) ⇒ mở PR, merge rebase **sau khi deploy của backend #6 xong** (deploy có `cancel-in-progress`, merge dồn sẽ huỷ lượt đang chạy). Nếu chưa push: `git fetch && git switch feat/admin-orders-payments-revenue && git rebase origin/main`, chạy test, `git push --force-with-lease`.
2. **Frontend 3 trang** theo [admin-reporting-api.md](../01-overview/admin-reporting-api.md), dùng `formatDateTime` ở `fe/src/lib/datetime.ts` (đã có, định dạng `HH:mm:ss dd/MM/yyyy`, chuỗi không múi giờ = UTC):
   - `/admin/orders`: dùng API tìm kiếm phân trang + chi tiết mới; enum trạng thái INITIALIZED/STORING/EXPIRED/AWAITING_DISPATCH/COMPLETED/CANCELED, loại SEND/RENTAL/DRONE_DELIVERY; hiển thị khách, người nhận, tủ/ô, phí chi tiết, thanh toán, drone, timeline; sửa đổi trạng thái gửi JSON body; bỏ nút tạo đơn giả.
   - `/admin/payments`: API phân trang + lọc, thời gian thật, thống kê so sánh kỳ trước (bỏ delta cứng), chi tiết kèm hoàn tiền/biến động ví, sửa đổi trạng thái gửi JSON body.
   - `/admin/revenue`: bỏ toàn bộ mảng giả; tổng quan theo khoảng, chuỗi theo ngày, theo loại dịch vụ, phương thức, tủ, cửa hàng, khách hàng (+ trang chi tiết khách).
3. **Mobile phần dở:** checkout nhánh `wip/mobile-business-settings-remaining`, hoàn thiện, `flutter analyze` (không thêm issue so với baseline 259) + `flutter test`, tách commit sạch lên nhánh mới từ `main`, PR, merge.
4. Sau khi merge hết: STATUS § 3 → § 5; ADR-0005 `Proposed` → `Accepted` khi chủ dự án xác nhận; CHANGELOG.
5. Nên làm: ràng buộc chéo `app.locker.reserved-ttl-hours` ≥ `app.order.auto-cancel-hours`; nếu tăng `app.iot.unlock-wait-seconds` > 20 thì tăng `APP_RESILIENCE4J_TL_TIMEOUT` của locker-service.

## 4. Kiến trúc cấu hình (tóm tắt)

```
Admin web /admin/settings ──PUT /api/admin/settings/{scope}──▶ gateway ──▶ service sở hữu scope
                                                                  BusinessSettings (common-lib)
                                                                  kiểm kiểu/min/max cả lô → system_settings + audits
Service đọc: rules.sendBaseFee() → cache 30s → DB → property cùng key → mặc định catalog
Mobile ──GET /api/settings/{scope}/public (không JWT)──▶ giá/giới hạn công khai (lỗi ⇒ dùng mặc định cũ)
```

| Repo | File | Vai trò |
|---|---|---|
| backend | `common-lib/…/common/settings/` | `BusinessSettings`, `SettingsCatalog`, `SettingDefinition`, `JdbcSettingsStore`, `BusinessSettingsController`, `InMemorySettingsStore` (test) |
| backend | `<service>/…/settings/<Service>SettingsCatalog.java`, `<Service>Rules.java` | Khai báo + đọc có kiểu quy tắc của từng service |
| backend | `<service>/src/main/resources/db/migration/V*__system_settings.sql` | order V11, locker V14, payment V4, iot V4, auth V3, loyalty V2, store V3 |
| backend | `api-gateway/…/application.yml` (`settings-*` routes), `JwtGatewayFilter` (`PUBLIC_SETTINGS_PATH`) | Định tuyến + public GET |
| frontend | `fe/src/pages/Admin/settings/`, `fe/src/stores/apis/admin/businessSettings.ts`, `fe/src/lib/datetime.ts` | Trang cấu hình, API, định dạng thời gian |
| mobile | `lib/core/config/business_config*.dart` (xem commit `9f08983`) | Đọc cấu hình công khai + mặc định |

Thêm quy tắc mới: thêm hằng + `SettingDefinition` vào catalog của service, getter vào `<Service>Rules`, dùng getter thay số cứng, test bằng `Test<Service>Rules` / `BusinessSettings.inMemory`. Trang admin tự hiện, không cần sửa web.

## 5. Ghi chú môi trường

- Máy cũ không có JDK 21/Maven/Node/Flutter/Docker/`gh`; đã dùng bản portable trong thư mục tạm. Máy mới nên cài JDK 21, Maven 3.9, Node 22, Flutter 3.44.x, Docker Desktop, GitHub CLI.
- Nhánh báo cáo backend được làm trong git worktree `D:\BaoHuy\LockRR-work\backend-reports` (máy cũ). Trên máy mới chỉ cần `git switch feat/admin-orders-payments-revenue` trong repo backend; xoá worktree cũ bằng `git worktree prune` nếu cần.
- PowerShell: đặt tham số Maven trong nháy: `mvn -B test '-Dcyclonedx.skip=true' -pl 'common-lib,order-service' -am`.
- Không merge 2 PR backend cách nhau dưới ~20 phút (deploy `cancel-in-progress`). Smoke test deploy có thể đỏ giả do race Eureka (503 ngay sau khởi động) — kiểm lại bằng tay trước khi rollback.
- Không có `gh`: tạo/merge PR qua REST API (`POST /repos/LockR-Tech/<repo>/pulls`, `PUT …/pulls/<n>/merge` với `merge_method: rebase`), token từ `git credential fill`, không in token.

## 6. Lời nhắn mẫu cho AI ở phiên mới

> Đọc `docs/AGENTS.md`, `docs/STATUS.md`, rồi `docs/handoff/2026-09-16-cau-hinh-nghiep-vu-va-bao-cao-admin.md`. Tiếp tục mục 3 theo thứ tự. Commit từng bước theo `docs/04-engineering/commit-convention.md`, không thêm trailer Co-Authored-By, merge kiểu rebase.
