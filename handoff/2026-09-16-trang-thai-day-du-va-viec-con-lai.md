# Bàn giao — trạng thái đầy đủ & việc còn lại (2026-09-16)

> Dành cho người hoặc AI agent tiếp tục **trên máy khác**. Đọc hết mục 1–3 trước khi gõ dòng lệnh nào.
> Quy trình chung: [AGENTS.md](../AGENTS.md) · [STATUS.md](../STATUS.md). File này **không chứa secret**.
> Bàn giao trước: [báo cáo admin & mobile](2026-09-16-bao-cao-admin-web-va-mobile-con-lai.md) · [ảnh Cloudinary](2026-09-15-luu-anh-cloudinary.md)

---

## 1. Đọc trước: hai điều dễ hiểu nhầm

### 1.1 `main` đang ĐI TRƯỚC production

Mọi thứ đã merge vào `main`, **nhưng không repo nào deploy được** — quota Actions đã hết.

| | `main` | Đang chạy thật | Chênh |
|---|---|---|---|
| backend | `569d323` | `980f4fd` | 4 commit: SEC-01, SEC-07, Firebase, F2-G03 |
| frontend | `b1686f5` | `a1ca345` | 1 commit: quản lý dịch vụ + bỏ mã số nội bộ |
| mobile | xem git | bản cũ | hiện tên tủ/số ô thật; mobile web chưa build lại |
| docs | xem git | — | — |

Backend production vẫn khoẻ (`/api/lockers` → 200, 4 tủ thật); admin web đã deploy → 200.

**Không có gì hỏng.** Chỉ là code mới nằm chờ.

### 1.2 GitHub Actions đã hết quota — đây là nút thắt duy nhất

Org `LockR-Tech` dùng hết **2.000/2.000 phút**, gói Free, spending limit $0.
**Reset khoảng 1/10/2026** (15 ngày tính từ 16/09).

Triệu chứng: mọi job đỏ sau 2–5 giây, không có step nào, không có log. Annotation ghi rõ:
> *"The job was not started because recent account payments have failed or your spending limit needs to be increased."*

⚠️ **Đừng mất thời gian debug CI đỏ** — không phải code hỏng.

Đã sửa nguyên nhân gốc (commit `999d48f`): `backend-security.yml` trước đây chạy 14 job quét container + CodeQL trên **mọi PR và mọi push nhánh tính năng**, `backend-ci.yml` test **hai lượt** mỗi PR. Riêng repo backend ngốn 97% quota của cả org. Nay security chỉ chạy trên `main` + lịch tuần; CI chỉ chạy `pull_request` + push `main`.

---

## 2. Việc cần làm tiếp — theo thứ tự

### Bước 1 — Gỡ nút thắt Actions (chọn 1 trong 3)

| Cách | Chi phí | Đánh đổi |
|---|---|---|
| **Chờ tới ~1/10** | 0 | SEC-01 còn mở nửa tháng, không deploy được gì |
| **Nâng spending limit $5–10** | vài USD | Gỡ ngay. Sau commit `999d48f` mức tiêu thụ giảm mạnh nên tháng sau nhiều khả năng không vượt 2.000 phút |
| **Self-hosted runner trên VM Azure** | 0 | Miễn phí vĩnh viễn, không giới hạn. ~20 phút cấu hình. VM đã có Docker |

Billing: `https://github.com/organizations/LockR-Tech/settings/billing`

### Bước 2 — Deploy backend

Actions sống lại thì vào **Actions → Deploy to Azure VM → Run workflow** (hoặc push bất kỳ vào `main`). Một lần deploy sẽ đưa cả 4 commit lên.

⚠️ **Lần deploy này làm MỌI NGƯỜI DÙNG BỊ ĐĂNG XUẤT** — token cũ ký bằng secret cũ, deploy này đổi sang secret mới trong `.env`. Chọn giờ vắng.

Điều kiện tiên quyết **đã xong**: `APP_SECURITY_JWT_SECRET` đã có trong `/opt/laundry-locker-microservices/.env` (đặt 16/09 qua Azure Run command). Thiếu biến này thì `docker compose up` dừng ngay và script tự rollback.

Nghiệm thu sau deploy:
```bash
curl -s -o /dev/null -w '%{http_code}\n' https://api.locker-drone.tech/api/lockers   # 200
sudo docker compose logs notification-service | grep -E "SMS channel|Firebase"
```

### Bước 3 — Nạp khoá còn thiếu

Chạy khối này ở **Azure Portal → VM → Run command → RunShellScript** để biết còn thiếu gì (chỉ in tên biến, không in giá trị):

```bash
cd /opt/laundry-locker-microservices
for k in APP_SECURITY_JWT_SECRET CLOUDINARY_URL MEDIA_FOLDER_ROOT \
         SPRING_MAIL_HOST SPRING_MAIL_USERNAME APP_MAIL_FROM \
         APP_SMS_TWILIO_ACCOUNT_SID APP_SMS_TWILIO_AUTH_TOKEN APP_SMS_TWILIO_FROM_NUMBER \
         FIREBASE_CREDENTIALS_JSON; do
  grep -q "^$k=." .env 2>/dev/null && echo "CO    $k" || echo "THIEU $k"
done
```

Cách lấy từng khoá: [cau-hinh-dich-vu-ngoai.md](../04-engineering/cau-hinh-dich-vu-ngoai.md).

Trạng thái đã biết tính tới 16/09:

| Khoá | Trạng thái | Thiếu thì sao |
|---|---|---|
| `APP_SECURITY_JWT_SECRET` | ✅ đã đặt | — |
| `CLOUDINARY_URL` | ✅ đã nạp 16/09, 4 service xác nhận qua log | API ảnh trả 503 `MEDIA_STORAGE_DISABLED` |
| `APP_SMS_TWILIO_*` | ⏳ có SID + Auth Token, **thiếu số gửi** | SMS chỉ ghi log, không gửi |
| `SPRING_MAIL_*` | ❓ | Không gửi được OTP và mã mở tủ qua email |
| `FIREBASE_CREDENTIALS_JSON` | ❓ | Push tắt |

### Bước 4 — Hoàn tất Twilio

Chủ dự án đã tạo tài khoản trial, có Account SID + Auth Token. **Còn thiếu:**

1. **Số gửi**: Phone Numbers → Manage → Buy a number (lọc SMS) → giá trị `APP_SMS_TWILIO_FROM_NUMBER`
2. **Verified Caller IDs**: thêm số sẽ nhận tin — bản trial **chỉ gửi được tới số đã xác minh**
3. **Geo Permissions**: Messaging → Settings → Geo Permissions → bật **Vietnam**, nếu không Twilio trả lỗi `21408`

> ⚠️ **Kỳ vọng thực tế**: SMS tới số Việt Nam qua Twilio **khả năng cao vẫn không tới nơi** — VN yêu cầu brandname đăng ký trước với nhà mạng, tin từ số nước ngoài thường bị chặn ở đầu cuối (Twilio báo `sent` nhưng máy không nhận được). Kênh **email** mới là kênh đáng tin. Code đã tính tới: gửi cả ba kênh, không kênh nào tới nơi thì báo người gửi tự chuyển mã. Muốn SMS thật ở VN thì chuyển sang eSMS.vn / FPT SMS — chỉ cần thêm một lớp `SmsSender`, không sửa nghiệp vụ.

### Bước 5 — Thử với token ADMIN thật

3 trang báo cáo admin đã deploy nhưng **chưa ai mở bằng tài khoản ADMIN thật**. Cần soát:

- đơn `EXPIRED` (số ô trống — backend đã nhả ô) và đơn `DRONE_DELIVERY` (khối chuyến bay)
- giao dịch `VNPAY_TOPUP` (không gắn đơn, không tính vào doanh thu)
- khoảng ngày không có dữ liệu (phải ra 0) so với khi payment-service chết (phải ra **lỗi**, không phải 0)

### Bước 6 — Dọn nốt

- `SEC-08`: xoay token Cloudflare — tạo mới → `gh secret set CLOUDFLARE_API_TOKEN --repo LockR-Tech/frontend` (và `mobile`) → **xoá token cũ**
- ADR-0005 `Proposed` → `Accepted` khi chủ dự án xác nhận
- Ràng buộc chéo `app.locker.reserved-ttl-hours` ≥ `app.order.auto-cancel-hours`

---

## 3. Đã làm trong phiên 15–16/09

### 3.1 Đã deploy và đang chạy

| Việc | PR | Commit |
|---|---|---|
| 3 trang báo cáo admin dùng dữ liệu thật (F2-G08 phần web) | [frontend #7](https://github.com/LockR-Tech/frontend/pull/7) | `43e5d00` |

Bỏ toàn bộ dữ liệu giả ở `/admin/revenue`, mốc thời gian giả ở `/admin/payments`, sửa crash ở `/admin/orders` với trạng thái `STORING`/`EXPIRED`/`AWAITING_DISPATCH`, sửa lỗi 400 khi đổi trạng thái, thêm tab hoàn tiền + biến động ví, thêm trang chi tiết doanh thu khách hàng. Thời gian hiển thị `HH:mm:ss dd/MM/yyyy` giờ Việt Nam ở mọi chỗ.

### 3.2 Đã merge, CHỜ DEPLOY

| Việc | PR | Commit trên `main` |
|---|---|---|
| SEC-01 JWT secret ra `.env` · SEC-07 ngừng ghi OTP ra log | [backend #10](https://github.com/LockR-Tech/backend/pull/10) | `093d422` |
| Khởi tạo Firebase để push thật sự gửi | [backend #10](https://github.com/LockR-Tech/backend/pull/10) | `f0c36cb` |
| Giảm tiêu thụ Actions | [backend #11](https://github.com/LockR-Tech/backend/pull/11) | `999d48f` |
| Gửi mã mở tủ cho người nhận chưa có tài khoản (F2-G03) | [backend #9](https://github.com/LockR-Tech/backend/pull/9) | `569d323` |
| Cấu hình admin còn lại + theo dõi trạng thái/địa điểm + email người nhận | [mobile #6](https://github.com/LockR-Tech/mobile/pull/6) | `b0152a4` |
| Quản lý dịch vụ trên admin + bỏ mã số nội bộ khỏi giao diện | [frontend #8](https://github.com/LockR-Tech/frontend/pull/8) | `b1686f5` |
| Hiện tên tủ và số ô thật trong app | [mobile #7](https://github.com/LockR-Tech/mobile/pull/7) | xem git |

Toàn bộ đã kiểm tra trên `main` của mobile sau khi cài được Flutter 3.44.9:
`flutter analyze` **259 issue — đúng bằng baseline**, `flutter test` **154 pass**,
`gradlew :app:assembleDebug` **BUILD SUCCESSFUL**.

Ba phát hiện đáng lưu ý khi làm:

- **`notification-service` chưa bao giờ được truyền JWT secret.** Ba service trùng secret chỉ vì cùng rơi về giá trị mặc định. Nếu chỉ sửa hai chỗ hardcode rồi đặt secret mới thì realtime STOMP đứt mà không rõ lý do. Đã vá cùng lúc.
- **FCM không phải thiếu khoá mà thiếu code.** `FcmPushNotificationService` viết đủ từ lâu nhưng không ai gọi `FirebaseApp.initializeApp` trong service đó (`getApps()` là trạng thái theo tiến trình, auth-service khởi tạo thì notification-service không thấy), nên server im lặng bỏ qua mọi lệnh push.
- **Repo mobile trước đây không kiểm tra gì trước khi merge** — `deploy-web.yml` chỉ chạy `flutter test` **sau** khi push vào `main`, nên test hỏng chỉ chặn deploy chứ code lỗi đã nằm trên `main`. Đã thêm `.github/workflows/pr-check.yml`.

### 3.3 Kết quả kiểm tra

| Nơi | Kết quả |
|---|---|
| backend `mvn test` (local, sau khi gỡ xung đột rebase) | order-service 51 pass · notification-service 17 pass · auth-service 6 pass · common-lib 34 pass — **BUILD SUCCESS** |
| mobile CI (trước khi hết quota) | `flutter analyze` **259 issue = đúng baseline** · **154 test pass** (baseline 147) |
| frontend | `tsc` sạch · lint 0 error / 69 warning (baseline 70) · `npm run build` xanh |
| `docker compose config` | thiếu `APP_SECURITY_JWT_SECRET` ⇒ dừng đúng ở cả 3 service; có ⇒ hợp lệ |
| Production 16/09 sau khi merge hết | `api.locker-drone.tech/api/lockers` **200** (4 tủ thật) · `admin.locker-drone.tech` **200** |

### 3.4 Tài liệu mới

| File | Nội dung |
|---|---|
| [`01-overview/admin-reporting-api.md`](../01-overview/admin-reporting-api.md) | Hợp đồng API báo cáo admin (có từ phiên trước) |
| [`01-overview/receiver-pickup-code.md`](../01-overview/receiver-pickup-code.md) | Kênh gửi mã mở tủ: endpoint, hai nhà cung cấp, bảo mật log, biến môi trường |
| [`04-engineering/cau-hinh-dich-vu-ngoai.md`](../04-engineering/cau-hinh-dich-vu-ngoai.md) | Runbook nạp khoá từng dịch vụ + cách kiểm tra + xử lý khi khoá lộ |

---

## 4. Việc dở dang / nợ kỹ thuật

- **2 PR cũ chưa xử lý, không thuộc phiên này**: [backend #1](https://github.com/LockR-Tech/backend/pull/1), [docs #1](https://github.com/LockR-Tech/docs/pull/1) (nhắc tới một mã `SEC-09` chưa có trong STATUS). Cần người hiểu bối cảnh xem lại.
- **`OrderResponse` chưa trả thông tin người nhận** — phần còn lại của F2-G03.
- **`delegate` (uỷ quyền lấy hộ) vẫn chỉ báo chủ đơn**, chưa dùng kênh SMS/email mới.
- **Bộ enum legacy giặt ủi** vẫn còn ở `frontend/fe/src/types/admin/enums.ts` và `schemas/admin.schemas.ts` cho các màn hình khác — phần còn nợ của F2-G08.
- **Mutation cũ gửi trạng thái qua query param** vẫn nằm trong `apis/admin/orders.ts` và `payments.ts` nhưng không màn hình nào dùng.
- **`dependency-review` và `codeql` đỏ ở mọi PR** vì org chưa bật Dependency graph + Advanced Security. Không phải lỗi code.

---

## 5. Ghi chú môi trường

Máy làm phiên này (Windows 11) **không có sẵn** Node, JDK, Maven, Flutter, `gh`; Docker Desktop cài rồi nhưng daemon không chạy. Đã dùng bản portable trong thư mục tạm.

| Thứ | Ghi chú |
|---|---|
| Node | 24.21.0 portable. `npm ci` lần đầu đỏ vì `EBUSY` khi esbuild ghi `esbuild.exe` (antivirus giữ file) — xoá `node_modules` rồi chạy lại là xong |
| JDK / Maven | Temurin 21.0.12.1 + Maven 3.9.9 portable. `dlcdn.apache.org` 404 với 3.9.9, phải lấy từ `archive.apache.org` |
| Flutter | 3.44.9 ở `C:\src\flutter`. Đã thêm workflow kiểm tra PR cho repo mobile để runner GitHub chạy `analyze` + `test` — giữ lại vì hữu ích kể cả khi máy dev có Flutter |
| **Java cho build Android** | ⚠️ Máy có **Java 25**, mà Android Gradle Plugin chưa hỗ trợ ⇒ `flutter run` chết với thông báo cụt lủn `* What went wrong: 25.0.2` (chính là số hiệu Java, không phải NDK hay build-tools như ta tưởng lúc đầu). Cài JDK 21 ở `C:\src\jdk-21` và trỏ Flutter vào đó bằng `flutter config --jdk-dir=C:\src\jdk-21` là hết. `flutter doctor` **không** phát hiện được lỗi này |
| `gh` | Cài bằng `winget install GitHub.cli`, đăng nhập bằng luồng trình duyệt (`gh auth login`). **Phải chạy ở terminal của người dùng** vì cần tương tác |
| SSH vào VM | Máy này **không có** private key; pipeline giữ khoá duy nhất trong GitHub secret (không đọc lại được). Đường vòng: **Azure Portal → VM → Run command → RunShellScript**, chạy được lệnh shell với quyền root mà không cần SSH |

Máy mới nên cài sẵn: Node 22, JDK 21, Maven 3.9, Flutter 3.44.x, GitHub CLI, Docker Desktop.

---

## 6. Lời nhắn mẫu cho AI ở phiên mới

> Đọc `docs/AGENTS.md`, `docs/STATUS.md`, rồi `docs/handoff/2026-09-16-trang-thai-day-du-va-viec-con-lai.md`.
> **Lưu ý trước khi bắt đầu**: GitHub Actions của org đang hết quota (reset ~1/10) nên mọi CI đỏ sau vài giây — đó không phải lỗi code. `main` của backend đang đi trước production 4 commit.
> Tiếp tục mục 2 theo thứ tự. Commit từng bước theo `docs/04-engineering/commit-convention.md`, không thêm trailer Co-Authored-By, merge kiểu rebase.
