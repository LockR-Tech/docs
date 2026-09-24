| 8 | Firebase FCM | Push notification hiện không gửi (code đã sẵn sàng, chỉ thiếu khoá). |# Cấu hình dịch vụ ngoài — runbook

Nơi nạp khoá cho từng dịch vụ ngoài, thứ tự nên làm, và cách kiểm tra đã ăn chưa.
Liên quan: [release-deploy](release-deploy.md), [architecture § 5](../01-overview/architecture.md), [STATUS § 2](../STATUS.md).

> **Không bao giờ** commit giá trị khoá vào repo, dán vào issue/PR, hay gửi qua chat.
> Tài liệu chỉ ghi **tên** biến. Khoá đã lộ thì phải xoay, không phải "chắc không ai thấy".

## 1. Ba nơi chứa cấu hình

| Nơi | Dùng cho | Cách đặt |
|---|---|---|
| **`.env` trên Azure VM** | Mọi khoá backend chạy lúc runtime | SSH vào VM, sửa `/opt/laundry-locker-microservices/.env` |
| **GitHub Actions secrets** | Khoá mà *pipeline* cần (SSH vào VM, deploy Cloudflare) | Repo → Settings → Secrets and variables → Actions |
| **`system_settings` (trang admin)** | Quy tắc nghiệp vụ — **không phải** khoá | `/admin/settings`, xem [ADR-0005](../adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md) |

`.env` **được giữ nguyên qua mỗi lần deploy** (`scripts/deploy-from-artifact.sh` chép lại
trước khi thay thư mục), nên chỉ phải đặt một lần.

### Sửa `.env` trên VM

```bash
ssh <user>@<host>
cd /opt/laundry-locker-microservices
sudo cp .env .env.bak.$(date +%F)     # luôn giữ bản lùi
sudo nano .env                         # thêm/sửa các dòng KEY=value
sudo docker compose up -d              # chỉ dựng lại container có biến đổi
```

Kiểm tra biến đã vào container chưa (đừng in cả giá trị ra màn hình chung):

```bash
sudo docker compose exec order-service printenv | grep -c APP_SMS_TWILIO_ACCOUNT_SID
# 1 = có, 0 = chưa
```

---

## 2. Thứ tự nên làm

Xếp theo **rủi ro** trước, tiện nghi sau. Hai việc đầu là lỗ hổng đang mở, không phải tính năng.

| # | Việc | Vì sao gấp |
|---|---|---|
| 1 | **Xoay JWT secret** (SEC-01) | Secret production đang là chuỗi mặc định **nằm trong repo**. Ai đọc repo cũng giả được token ADMIN. |
| 2 | **Xoay token Cloudflare** (SEC-08) | Token quyền Edit Workers từng bị dán vào lịch sử chat. Ai có lịch sử đó deploy đè được cả 3 trang web. |
| ~~3~~ | ~~**Cloudinary**~~ | ✅ **Xong 16/09/2026** — xem §4. |
| 4 | **Twilio** | Mã mở tủ chưa gửi được qua SMS. |
| 5 | **SMTP thật** | OTP đăng nhập và mã mở tủ qua email. |
| 6 | **Broker MQTT riêng** (SEC-04) | Đang dùng broker công khai không xác thực — ai cũng gửi lệnh mở tủ được. |
| 7 | VNPay / MoMo thật | Chỉ cần khi thu tiền thật. |
| 8 | Firebase FCM | Push notification hiện không gửi. |

---

## 3. JWT secret (SEC-01) — làm trước tiên

> ✅ **Phần code đã vá** — `docker-compose.yml` giờ đọc `${APP_SECURITY_JWT_SECRET:?chua dat}`
> (bắt buộc, không còn default) ở cả 3 service dùng tới. Đoạn dưới mô tả cách sinh và **đặt
> giá trị thật** vào `.env` trên VM — bước còn lại là vận hành, không phải code, nhưng vẫn
> phải làm vì thiếu biến thì `docker compose up` từ chối chạy. Chưa xác nhận được VM production
> đã có giá trị thật hay chưa (không có quyền SSH lúc soát lại 17/09/2026) — kiểm tra trước
> khi coi đây là xong.

```bash
# Sinh secret mới, tối thiểu 32 ký tự
openssl rand -base64 48
```

Thêm vào `.env`:

```
APP_SECURITY_JWT_SECRET=<chuỗi vừa sinh>
```

> ⚠️ Xoay secret làm **mọi người dùng bị đăng xuất** vì token cũ hết hiệu lực. Chọn giờ vắng.

---

## 4. Cloudinary (ảnh) ✅ đã cấu hình 16/09/2026

Hợp đồng: [media-storage](../01-overview/media-storage.md) · [ADR-0004](../adr/0004-anh-luu-cloudinary-upload-truc-tiep.md)

> **Đã xong.** `CLOUDINARY_URL` và `MEDIA_FOLDER_ROOT` đã nằm trong `.env` trên VM;
> `user`, `order`, `locker`, `store-service` đều ghi `Cloudinary media storage enabled`
> lúc khởi động. Phần dưới giữ lại để tra cứu khi đổi tài khoản hoặc dựng môi trường mới.

1. Đăng ký tài khoản miễn phí ở <https://cloudinary.com> (gói free đủ cho demo).
2. Dashboard → **API Environment variable**, copy chuỗi dạng
   `cloudinary://<api_key>:<api_secret>@<cloud_name>`.
3. Thêm vào `.env`:

```
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
MEDIA_FOLDER_ROOT=lockr
```

4. `sudo docker compose up -d user-service order-service locker-service store-service`

**Kiểm tra:** gọi `POST /api/media/upload-signatures` bằng token bất kỳ.
Chưa cấu hình ⇒ **503 `MEDIA_STORAGE_DISABLED`**. Cấu hình rồi ⇒ 200 kèm chữ ký.

Không có token thì đọc log — cách này không cần đăng nhập:

```bash
cd /opt/laundry-locker-microservices
for s in user-service order-service locker-service store-service; do
  line=$(sudo docker compose logs --tail=800 "$s" | grep -i "Cloudinary media storage" | tail -1)
  echo "$s => ${line:-KHONG THAY}"
done
```

Ba điều dễ hiểu nhầm, đã kiểm chứng ngày 16/09:

- **Không phải deploy lại web hay mobile.** Client nhận `cloudName` và `uploadUrl` trong
  chữ ký backend trả về ([`UploadSignatureResponse`](../../backend/common-lib/src/main/java/com/huynqb/laundrylocker/common/media/UploadSignatureResponse.java)),
  không nhúng cloud name lúc build. Đổi tài khoản Cloudinary chỉ cần sửa `.env` rồi restart.
- **Ảnh cũ không tự đổi.** Các bản ghi seed vẫn trỏ `picsum.photos` cho tới khi có người
  upload đè.
- **`/api/lockers` và `/api/stores` trả 503 khoảng 1 phút sau restart** là bình thường —
  service chưa đăng ký lại vào Eureka, không phải lỗi cấu hình.

---

## 5. Twilio (SMS mã mở tủ)

Hợp đồng: [receiver-pickup-code](../01-overview/receiver-pickup-code.md)

1. Đăng ký ở <https://www.twilio.com/try-twilio> — bản dùng thử có sẵn credit.
2. Console → **Account Info**: copy `Account SID` và `Auth Token`.
3. Console → **Phone Numbers → Manage → Buy a number**, lấy một số (trial dùng credit sẵn có).
4. **Quan trọng với bản trial:** Console → **Verified Caller IDs** → thêm số điện thoại
   sẽ nhận tin. Bản trial **chỉ gửi được tới số đã xác minh**.
5. Thêm vào `.env`:

```
APP_SMS_TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
APP_SMS_TWILIO_AUTH_TOKEN=<auth token>
APP_SMS_TWILIO_FROM_NUMBER=+1xxxxxxxxxx
```

6. `sudo docker compose up -d notification-service`

**Kiểm tra:** xem log lúc khởi động.

```bash
sudo docker compose logs notification-service | grep "SMS channel"
```

- `SMS channel: Twilio (from +1…)` ⇒ đã ăn.
- `SMS channel not configured` ⇒ thiếu **ít nhất một** trong ba biến.

Thử end-to-end: tạo một đơn gửi hàng với số người nhận **đã xác minh ở bước 4**, bấm
"Tôi đã bỏ hàng", số đó phải nhận được tin có mã mở tủ.

> Thiếu khoá thì service **vẫn chạy bình thường**, chỉ ghi log thay vì gửi — không gây sự cố,
> nhưng người nhận sẽ không nhận được gì.

---

## 6. SMTP (email OTP + mã mở tủ)

Dùng chung cho `auth-service` và `notification-service`. Ba lựa chọn:

| Nhà cung cấp | Ghi chú |
|---|---|
| **Brevo** (cũ: Sendinblue) | 300 email/ngày miễn phí. Bắt `APP_MAIL_FROM` phải là **sender đã verify**, khác tài khoản SMTP. |
| **Gmail** | Cần bật 2FA rồi tạo **App Password** (không dùng mật khẩu tài khoản). Giới hạn thấp. |
| **Amazon SES** | Rẻ nhất khi chạy thật, nhưng phải xin thoát sandbox. |

```
SPRING_MAIL_HOST=smtp-relay.brevo.com
SPRING_MAIL_PORT=587
SPRING_MAIL_USERNAME=<smtp login>
SPRING_MAIL_PASSWORD=<smtp key>
SPRING_MAIL_SMTP_AUTH=true
SPRING_MAIL_SMTP_STARTTLS=true
APP_MAIL_FROM=no-reply@<domain đã verify>
```

Cả hai service đọc cùng bộ biến này. `notification-service` mặc định **trống**: chưa đặt thì
kênh email tắt hẳn và `emailChannelAvailable` trả `false` — đúng tình trạng thật. `auth-service`
giữ mặc định `localhost:1025` vì `SmtpEmailService` nhận thẳng `JavaMailSender`, không có bean
thì service không khởi động được.

**Kiểm tra:** đăng nhập bằng email OTP — hộp thư phải nhận được mã. Với kênh mã mở tủ, gửi thử
một đơn SEND có nhập email người nhận rồi soi log `notification-service`: chưa cấu hình thì thấy
`Email channel not configured`.

> ✅ **SEC-07 đã vá** — `EmailOtpService` giờ chỉ log email đã che (`OTP generated for
> {maskedEmail}...`), OTP được hash (`passwordEncoder.encode`) trước khi lưu DB, không còn
> log ra dạng rõ. Xem `CHANGELOG.md`: "SEC-01 và SEC-07 ghi rõ đã merge". Cảnh báo cũ ở đây
> mô tả tình trạng trước khi vá — sửa lại 17/09/2026 sau khi đọc lại code xác nhận.

---

## 7. Azure VM (deploy backend)

Pipeline `deploy-azure.yml` SSH vào VM. Bốn secret đặt ở **GitHub repo `backend`**
(Settings → Secrets and variables → Actions):

| Secret | Giá trị |
|---|---|
| `AZURE_VM_HOST` | IP hoặc hostname của VM |
| `AZURE_VM_USER` | user SSH (thường `azureuser`) |
| `AZURE_VM_SSH_KEY` | **private key** dạng OpenSSH, dán trọn kể cả dòng `-----BEGIN…` |
| `AZURE_VM_PORT` | cổng SSH, bỏ trống thì mặc định 22 |

Tạo cặp khoá riêng cho CI, đừng dùng khoá cá nhân:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/lockr_deploy
ssh-copy-id -i ~/.ssh/lockr_deploy.pub <user>@<host>   # đẩy public key lên VM
cat ~/.ssh/lockr_deploy                                 # private key → dán vào secret
```

**Kiểm tra:** Actions → *Deploy to Azure VM* → *Run workflow*. Pipeline tự nghiệm thu
qua `https://api.locker-drone.tech` sau khi deploy.

---

## 8. Cloudflare (3 trang web)

Secret đặt ở **cả hai** repo `frontend` và `mobile`:

| Secret | Lấy ở đâu |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | Dashboard → Workers & Pages → cột phải |
| `CLOUDFLARE_API_TOKEN` | My Profile → API Tokens → Create Token → template **Edit Cloudflare Workers** |

> ⚠️ **SEC-08**: token hiện tại từng bị dán vào lịch sử chat. Phải **tạo token mới → nạp lại
> vào cả hai repo → xoá token cũ**, không phải chỉ tạo thêm.

**Kiểm tra:** push một commit nhỏ vào `main`, xem `DEPLOY-LOG.md` có dòng `success` mới.

---

## 9. Broker MQTT (SEC-04)

`iot-service/application.yml:81` đang trỏ `tcp://broker.hivemq.com:1883` — broker **công khai,
không xác thực, không TLS**. Ai cũng publish được lệnh mở tủ vào `cabinet/{id}/command/open`.

Cần dựng broker riêng (Mosquitto trong `docker-compose.yml`) có user/password + TLS, rồi:

```
MQTT_BROKER_URL=ssl://<host>:8883
MQTT_USERNAME=<user>
MQTT_PASSWORD=<password>
```

Phải cấu hình **đồng thời** ở `iot-service` và ở Raspberry Pi (repo `iot`), nếu không tủ mất kết nối.
Đây là thay đổi code + hạ tầng, không chỉ nạp biến — xem gap **F2-G09**.

---

## 10. VNPay / MoMo

Đang dùng endpoint sandbox. Chuyển sang thật cần hợp đồng với nhà cung cấp.

```
VNPAY_TMN_CODE=...
VNPAY_HASH_SECRET=...
VNPAY_PAY_URL=...
VNPAY_RETURN_URL=https://api.locker-drone.tech/api/payments/vnpay/return

MOMO_PARTNER_CODE=...
MOMO_ACCESS_KEY=...
MOMO_SECRET_KEY=...
MOMO_ENDPOINT=...
MOMO_IPN_URL=https://api.locker-drone.tech/api/payments/momo/ipn
MOMO_REDIRECT_URL=...
```

> ⚠️ Trước khi thu tiền thật phải vá **F2-G04**: IPN VNPay hiện **không kiểm số tiền**, và
> CASH do khách tự bấm xác nhận đã trả.

---

## 11. Firebase FCM (push notification)

App đã đăng ký device token nhưng **server không gửi** — `notification-service` chưa khởi tạo Firebase.

1. Firebase Console → Project settings → Service accounts → **Generate new private key** (file JSON).
2. Nén JSON về một dòng rồi đặt:

```
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"...",...}
```

notification-service đã khởi tạo Firebase (backend #10), nên **chỉ cần nạp biến này là push chạy**.
Trước đó `FcmPushNotificationService` viết đủ nhưng không ai gọi `initializeApp`, nên server bỏ
qua mọi lệnh push trong im lặng.

**Kiểm tra:** `sudo docker compose logs notification-service | grep Firebase` —
`Firebase initialised — FCM push enabled` là đã ăn.

---

## 11b. Trợ lý hỏi đáp: Anthropic (Claude) + Voyage AI (embedding)

`assistant-service` ([ADR-0006](../adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md)) cần hai khoá.
Thiếu khoá thì service **vẫn chạy**; API hỏi đáp trả 503 "chưa cấu hình", tài liệu nạp vào nằm
PENDING cho tới khi có `EMBEDDING_API_KEY` (có khoá là tự đánh chỉ mục tiếp, không phải nạp lại).

1. **Anthropic**: console.anthropic.com → API keys → tạo khoá cho workspace production. Đặt giới hạn
   chi tiêu (spend limit) ở console.
2. **Voyage AI**: dashboard.voyageai.com → API keys → tạo khoá.
3. Thêm vào `.env` VM:

```
ANTHROPIC_API_KEY=...
ASSISTANT_CHAT_MODEL=claude-haiku-4-5
EMBEDDING_API_KEY=...
EMBEDDING_MODEL=voyage-4
ASSISTANT_DB_PASSWORD=<chuỗi ngẫu nhiên>
```

`ASSISTANT_DB_PASSWORD` chỉ có tác dụng **lần đầu** container `assistant-db` tạo volume — đặt trước lần
deploy đầu tiên có `assistant-service`. `EMBEDDING_MODEL` chỉ đổi sang model **1024 chiều**; khác số
chiều phải có migration đổi cột `kb_chunks.embedding` rồi đánh chỉ mục lại mọi tài liệu.
`ASSISTANT_CHAT_MODEL` mặc định là `claude-haiku-4-5` — rẻ nhất và đủ cho hỏi đáp bám tài liệu.
Đổi sang model khác thì kiểm tra model đó có nhận `output_config.effort` không: Opus 4.5+, Sonnet 4.6+
và Fable thì có, Haiku và Sonnet 4.5 trở xuống trả 400. Danh sách nằm ở `ClaudeAnswerGenerator.supportsEffort`;
model lạ không có trong danh sách thì service tự bỏ `effort` đi nên vẫn chạy, chỉ là ở mức mặc định.

4. `sudo docker compose up -d assistant-service`.
5. Nạp bộ tài liệu mặc định từ máy có đủ các repo cạnh nhau:
   `API_BASE_URL=https://<api> ADMIN_TOKEN=<access token ADMIN> backend/scripts/seed-knowledge.sh`.
6. Chạy đánh giá truy xuất (chỉ tốn phí nhúng): `POST /api/admin/knowledge/eval`. `?generate=true` gọi
   Claude cho từng câu — tốn phí, chỉ chạy khi cần.

**Kiểm tra:** `GET /api/assistant/status` trả `{"enabled":true,"configured":true}`; danh sách
`GET /api/admin/knowledge/documents` chuyển sang READY sau vài phút.

---

## 12. Bảng tra nhanh

| Dịch vụ | Biến | Đặt ở | Thiếu thì sao |
|---|---|---|---|
| JWT | `APP_SECURITY_JWT_SECRET` | `.env` VM | Dùng secret mặc định trong repo — **lỗ hổng** |
| Cloudinary ✅ | `CLOUDINARY_URL`, `MEDIA_FOLDER_ROOT` | `.env` VM | API ảnh trả 503 |
| Twilio | `APP_SMS_TWILIO_ACCOUNT_SID` · `AUTH_TOKEN` · `FROM_NUMBER` | `.env` VM | SMS chỉ ghi log, không gửi |
| SMTP | `SPRING_MAIL_*`, `APP_MAIL_FROM` | `.env` VM | Không gửi được OTP và mã mở tủ |
| Azure | `AZURE_VM_HOST` · `USER` · `SSH_KEY` · `PORT` | GitHub secrets (`backend`) | Không deploy được backend |
| Cloudflare | `CLOUDFLARE_ACCOUNT_ID` · `API_TOKEN` | GitHub secrets (`frontend`, `mobile`) | Không deploy được web |
| MQTT | `MQTT_BROKER_URL` · `USERNAME` · `PASSWORD` | `.env` VM | Dùng broker công khai — **lỗ hổng** |
| VNPay | `VNPAY_*` | `.env` VM | Chỉ chạy sandbox |
| MoMo | `MOMO_*` | `.env` VM | Chỉ chạy endpoint test |
| Firebase | `FIREBASE_CREDENTIALS_JSON` | `.env` VM | Không push notification |
| Anthropic | `ANTHROPIC_API_KEY`, `ASSISTANT_CHAT_MODEL` | `.env` VM | Trợ lý hỏi đáp trả 503 |
| Voyage AI | `EMBEDDING_API_KEY`, `EMBEDDING_MODEL` | `.env` VM | Tài liệu không được đánh chỉ mục, trợ lý trả 503 |
| DB trợ lý | `ASSISTANT_DB_PASSWORD` | `.env` VM (trước lần deploy đầu) | Dùng mật khẩu mặc định trong compose |

## 13. Khi khoá bị lộ

1. **Thu hồi ngay** ở console nhà cung cấp — đừng chỉ tạo khoá mới rồi để khoá cũ sống.
2. Tạo khoá mới, nạp lại vào `.env` hoặc GitHub secrets.
3. `sudo docker compose up -d` để container nhận giá trị mới.
4. Nếu khoá từng nằm trong commit: xoay khoá là **bắt buộc**, xoá commit không đủ —
   ai clone rồi vẫn còn.
5. Ghi một dòng vào [STATUS § 2](../STATUS.md) nếu đây là lỗ hổng mới.
