# Lock.R admin reporting API — /admin/orders, /admin/payments, /admin/revenue

Backend branch: `feat/admin-orders-payments-revenue` (LockR-Tech/backend). Nothing here changes an
existing mobile or web endpoint. Every change only adds fields or endpoints.

---

## 0. Conventions (read first)

### 0.1 Base URL, auth
- Call everything through the API gateway, for example `https://<gateway>/api/admin/...`.
- Header: `Authorization: Bearer <access token>` for a user with role **ADMIN**.
  - No or invalid token → `401`. A valid token without ADMIN → `403` (from the gateway, with the error envelope below).
- `/internal/**` is blocked at the gateway (`403`). It is listed in §5 only as a reference.

### 0.2 Envelope
Success (`message` and `errors` are omitted when null):
```json
{ "success": true, "code": "OK", "data": { } }
```
Error:
```json
{ "success": false, "code": "INVALID_PAGE_SIZE", "message": "size must be between 1 and 100" }
```
| HTTP | When |
|---|---|
| 400 | business or validation error (`code` examples below) |
| 404 | `NOT_FOUND` (unknown order or payment id) |
| 503 | `PAYMENT_DATA_UNAVAILABLE`: revenue reports only. payment-service did not answer. **Show an error, not zeros.** |
| 500 | `INTERNAL_ERROR`, for example a non-numeric `page` |

Error codes added by these APIs: `INVALID_PAGE`, `INVALID_PAGE_SIZE`, `INVALID_SORT`, `INVALID_DATE`,
`INVALID_DATE_RANGE`, `INVALID_KIND`, `PAYMENT_DATA_UNAVAILABLE`, `NOT_FOUND`.

### 0.3 Time values — IMPORTANT
- **Every `LocalDateTime` field** (`createdAt`, `paidAt`, `pickupDeadline`, ...) is serialized as a naive ISO
  string **without an offset**, for example `"2026-09-15T01:02:03"` or `"2026-09-15T01:02:03.123456"` (0–6 fraction
  digits). The value is **UTC**, because containers run UTC. Mobile uses the same rule.
  - Web: parse it as UTC (append `Z`, or use `dayjs.utc(value)`), convert it to **Asia/Ho_Chi_Minh** and display it as
    **`HH:mm:ss dd/MM/yyyy`**. Example: `"2026-09-15T17:30:00"` → `00:30:00 16/09/2026`.
- **`LocalDate` fields** (`from`, `to`, `date`, `previousFrom`, ...) are `"yyyy-MM-dd"` and are **already Vietnam
  calendar days**. Do not convert them.
- Query params `from` / `to`:
  - **Order, payment, refund and wallet search** accept any of these:
    - `2026-09-15` = a Vietnam calendar day. `from` = start of that day. `to` = the whole day is included.
    - `2026-09-15T08:00:00+07:00` or `...Z` = that exact instant.
    - `2026-09-15T08:00:00` (naive) = UTC, the same convention as response values.
    - Ranges are half-open: `from <= t < to` (`to` as a date means start of the next day).
  - **Revenue and payment stats** accept only `yyyy-MM-dd` (Vietnam days, both ends inclusive).
    - Default: from the 1st of the current month to today.
    - `to >= from`. At most **366 days**.

### 0.4 Money
`BigDecimal` JSON numbers in VND, for example `15000.00`, `15000`, `-3000.00`. Scale varies (DB values have 2
decimals, computed averages have 0), so parse as a number. Percentages (`sharePct`, `*Pct`) have 2 decimals, and
`null` means there is no baseline (division by 0).

### 0.5 Pagination
Query `page` (0-based, default 0), `size` (1..100, default 20). Response `data`:
```json
{ "content": [ ], "page": 0, "size": 20, "totalElements": 134, "totalPages": 7 }
```
Multi-value filters (`status`, `type`, `method`, ...) accept `status=STORING,EXPIRED` or repeated params
`status=STORING&status=EXPIRED`. Matching is case-insensitive. An unknown value simply matches nothing.

### 0.6 Domain values actually produced
- Order `status`: `INITIALIZED`, `STORING`, `EXPIRED`, `AWAITING_DISPATCH`, `COMPLETED`, `CANCELED` (legacy `RETURNED` may exist)
- Order `type`: `SEND`, `RENTAL`, `DRONE_DELIVERY`, `STORAGE` (legacy)
- Order `paymentStatus`: `UNPAID`, `PAID`, `REFUNDED`
- Drone `deliveryStage`: `AWAITING_DISPATCH`, `ACCEPTED`, `LAUNCHING`, `DEPARTED`, `EN_ROUTE`, `APPROACHING`, `ARRIVED`, `READY_FOR_PICKUP`
- Payment `method`: `CASH`, `WALLET`, `VNPAY`, `MOMO`, `VNPAY_TOPUP` (wallet top-up, `orderId = 0`)
- Payment `status`: `PENDING`, `COMPLETED`, `FAILED`
- Payment `kind` (computed): `ORDER` | `TOPUP` (`TOPUP` = method `VNPAY_TOPUP` or `orderId <= 0`)
- Refund `status`: `COMPLETED` (created as completed today)
- Wallet tx `type`: `CREDIT` | `DEBIT`. `source`: `TOPUP` | `ORDER_PAYMENT` | `REFUND` | `ADJUST`

---

## 1. Orders (`/admin/orders`) — served by order-service

### 1.1 `GET /api/admin/orders/search` — paginated search (NEW)
The legacy `GET /api/admin/orders?status&type` (plain list, no paging) is **unchanged**. Use `/search` for the new page.

| Query | Type | Notes |
|---|---|---|
| `page`, `size` | int | §0.5 |
| `status` | multi | order status |
| `type` | multi | `SEND`, `RENTAL`, `DRONE_DELIVERY`, `STORAGE` |
| `paymentStatus` | multi | `UNPAID`, `PAID`, `REFUNDED` |
| `from`, `to` | date/datetime | on `createdAt`, §0.3 |
| `userId` | long | owner (customer who created the order) |
| `lockerId` | long | matches `lockerId` **or** `destinationLockerId` |
| `storeId` | long | order `storeId`, or any locker belonging to the store |
| `q` | string | case-insensitive "contains" on `orderCode`, `receiverPhone`, `receiverName`. A number also matches the order `id` exactly. A phone number (8–15 digits) also matches orders of the customer account with exactly that phone. PIN is never searched. |
| `sort` | string | `field,dir`. Fields: `createdAt` (default), `updatedAt`, `totalPrice`, `paidAt`, `completedAt`, `id`. Dir: `desc` (default) or `asc`. Ties are broken by `id desc`. When sorting desc by a nullable field, PostgreSQL puts nulls first. |

Response `data`: `PageResponse<AdminOrderResponse>`. `timeline` is `null` in the list.

### 1.2 `GET /api/admin/orders/{id}/detail` — full detail (NEW)
Same `AdminOrderResponse`, plus a `timeline` array. `404 NOT_FOUND` if the id is unknown.
(The legacy `GET /api/admin/orders/{id}` still returns the old `OrderResponse`.)

### 1.3 `AdminOrderResponse` — example with ALL fields (detail of a SEND order)
Enriched objects (`customer`, `receiver`, `locker`, `destinationLocker`, `store`, `payment`, `drone`, box numbers)
are `null` when there is no data, or when the source service failed. The list still loads in that case.
```json
{
  "id": 128,
  "orderCode": "ORD-20260915-K3F9QZ",
  "userId": 44,
  "receiverId": 45,
  "lockerId": 7,
  "sendBoxId": 701,
  "receiveBoxId": null,
  "storeId": null,
  "staffId": 44,
  "type": "SEND",
  "serviceCategory": "PARCEL",
  "status": "STORING",
  "deliveryStage": null,
  "pinCode": "482913",
  "qrToken": "LLQR.3k.Zm9vYmFy...",
  "actualWeight": null,
  "weightUnit": "kg",
  "extraFee": 2000.00,
  "discount": 0.00,
  "totalPrice": 17000.00,
  "originalPrice": 15000.00,
  "promotionCode": null,
  "appliedPromotionCodes": null,
  "nextAction": "PICKUP",
  "nextActionMessage": "Pick up items from locker.",
  "paymentRequired": false,
  "paymentStatus": "PAID",
  "overtime": true,
  "pickupDeadline": "2026-09-15T04:00:00",
  "returnedAt": null,
  "completedAt": null,
  "createdAt": "2026-09-13T02:10:44.512331",
  "updatedAt": "2026-09-15T05:00:12.004511",
  "orderDetails": [],

  "receiverUserId": null,
  "receiverPhone": "0907654321",
  "receiverName": "Trần Bình",
  "destinationLockerId": null,
  "reservedBoxId": null,
  "fulfillmentMode": "STANDARD",
  "paidAt": "2026-09-13T02:12:03.100000",
  "parcelWeightGrams": null,
  "reservationFee": 0.00,
  "storagePrice": 0.00,
  "shippingFee": 0.00,
  "pinCodeIssuedAt": "2026-09-13T02:20:00",
  "receiveAt": null,
  "intendedReceiveAt": null,
  "rentalDurationHours": null,
  "lastReminderAt": "2026-09-15T04:05:00",
  "description": null,
  "customerNote": "Hàng dễ vỡ",
  "staffNote": null,
  "cancelReason": null,
  "deliveryAddress": null,

  "customer": { "id": 44, "fullName": "Nguyễn An", "phoneNumber": "0901111111", "email": "an@example.com", "status": "ACTIVE" },
  "receiver": {
    "userId": 45,
    "name": "Trần Bình",
    "phone": "0907654321",
    "accountFullName": "Trần Bình",
    "accountPhoneNumber": "0907654321",
    "accountEmail": "binh@example.com"
  },
  "locker": { "id": 7, "code": "LK-Q1-01", "name": "Tủ Lê Lợi", "address": "1 Lê Lợi, Q1", "storeId": 3, "status": "ACTIVE" },
  "destinationLocker": null,
  "store": { "id": 3, "name": "Chi nhánh Q1", "address": "1 Lê Lợi, Q1", "contactPhone": "02838000000" },
  "sendBoxNumber": 12,
  "receiveBoxNumber": null,
  "reservedBoxNumber": null,
  "fees": {
    "originalPrice": 15000.00,
    "reservationFee": 0.00,
    "storagePrice": 0.00,
    "shippingFee": 0.00,
    "extraFee": 2000.00,
    "overtimeFee": 2000.00,
    "discount": 0.00,
    "basePrice": 15000.00,
    "totalPrice": 17000.00
  },
  "payment": {
    "paymentCount": 1,
    "latestPaymentId": 90,
    "latestMethod": "WALLET",
    "latestStatus": "COMPLETED",
    "latestAmount": 15000.00,
    "latestCreatedAt": "2026-09-13T02:12:03.100000",
    "paidAmount": 15000.00,
    "lastPaidMethod": "WALLET",
    "lastPaidAt": "2026-09-13T02:12:03.100000",
    "refundedAmount": 0,
    "outstandingAmount": 2000.00
  },
  "drone": null,
  "timeline": [
    { "oldStatus": null, "newStatus": "INITIALIZED", "changedByUserId": 44, "changedByName": "Nguyễn An", "note": "Order created", "createdAt": "2026-09-13T02:10:44.600000" },
    { "oldStatus": "INITIALIZED", "newStatus": "STORING", "changedByUserId": 44, "changedByName": "Nguyễn An", "note": "Sender dropped parcel; pickup PIN issued to receiver 0907654321", "createdAt": "2026-09-13T02:20:00" }
  ]
}
```
Field notes:
- The first block matches the legacy `OrderResponse` exactly: same names, same meaning.
- `receiver`: `name`/`phone` are what was typed on the order (SEND recipient or pickup delegate). `userId` is
  `receiverUserId ?? receiverId`. The `account*` fields come from that user account and can be null.
- `store`: the order's `storeId` when present, otherwise the locker's store.
- Box numbers: `sendBoxNumber`/`receiveBoxNumber`/`reservedBoxNumber`. For `EXPIRED` orders the box ids are
  cleared, so these numbers are null.
- `fees.overtimeFee` = `extraFee`, because the overtime fee is the only thing added to `extraFee`.
  `fees.basePrice` = `totalPrice − extraFee`.
- `payment` comes from payment-service:
  - `null` means payment-service could not be reached. Show "—".
  - `paymentCount: 0` means there are no payment attempts yet.
  - `latest*` = the newest attempt, any status. `paidAmount` = sum of COMPLETED payments.
  - `lastPaid*` = the newest COMPLETED payment. `refundedAmount` = COMPLETED refunds of the order.
  - `outstandingAmount = max(0, totalPrice − paidAmount)`.
  - Use `/api/admin/payments/search?orderId=` for the full payment list of an order.
- `drone` is only non-null when `type = DRONE_DELIVERY`:
```json
"drone": {
  "missionId": 31, "missionStatus": "LAUNCHING", "deliveryStage": "EN_ROUTE",
  "droneUnitId": 2, "droneCode": "DR-01",
  "sourceLockerId": 1,
  "sourceLocker": { "id": 1, "code": "LK-HUB", "name": "Hub", "address": "...", "storeId": 3, "status": "ACTIVE" },
  "destinationLockerId": 9, "assignedByUserId": 77,
  "readyToLaunchAt": "2026-09-15T03:00:00", "launchingAt": "2026-09-15T03:01:10",
  "createdAt": "2026-09-15T02:55:00", "updatedAt": "2026-09-15T03:01:10"
}
```
  When the order has no mission yet, only `deliveryStage` and `destinationLockerId` are set and the other fields are null.
- `cancelReason`: integer code as stored (nullable).

### 1.4 Status update (confirmed: JSON body)
`PUT /api/admin/orders/{id}/status` (existing) and `PATCH /api/admin/orders/{id}/status` (NEW alias). Both do the same thing.
```json
{ "status": "CANCELED", "staffId": 1, "receiveBoxId": null }
```
`status` is required (non-blank). `staffId` is optional: send the admin's user id so the timeline shows who changed it.
`receiveBoxId` is optional. `CANCELED`/`COMPLETED` release the boxes.
Response `data` = legacy `OrderResponse` (code `ORDER_STATUS_UPDATED`). A missing status gives `400 VALIDATION_ERROR`.

---

## 2. Payments (`/admin/payments`) — served by payment-service

### 2.1 `PaymentResponse` (existing endpoints) — 3 fields ADDED
Affects `/api/payments/**`, `/api/admin/payments`, `/api/admin/payments/{id}`, and the status PATCH/PUT.
```json
{
  "id": 90, "orderId": 128, "userId": 44, "amount": 15000.00, "method": "WALLET", "status": "COMPLETED",
  "referenceId": "PAY-128-1789000000000", "referenceTransactionId": null,
  "paymentUrl": null, "qrCodeUrl": null, "deeplink": null,
  "description": "Thanh toán đơn #128",
  "content": "Thanh toan don 128",
  "createdAt": "2026-09-13T02:12:03.100000",
  "updatedAt": "2026-09-13T02:12:03.100000"
}
```
The legacy `GET /api/admin/payments` (unsorted full list) is unchanged.

### 2.2 `GET /api/admin/payments/search` (NEW)
| Query | Notes |
|---|---|
| `page`, `size` | §0.5 |
| `status` | multi: `PENDING`, `COMPLETED`, `FAILED` |
| `method` | multi: `CASH`, `WALLET`, `VNPAY`, `MOMO`, `VNPAY_TOPUP` |
| `kind` | `ALL` (default) \| `ORDER` \| `TOPUP`. Anything else gives `400 INVALID_KIND` |
| `includeTopups` | boolean, default true. `false` with no `kind` (or `kind=ALL`) means `kind=ORDER`. An explicit `kind` wins. |
| `from`, `to` | on `createdAt`, §0.3 |
| `userId`, `orderId` | long |
| `q` | contains (case-insensitive) on `referenceId`, `referenceTransactionId`, `description`. A number also matches payment `id` or `orderId` exactly |
| `sort` | `createdAt` (default), `updatedAt`, `amount`, `id`; `,asc` / `,desc` |

Response `data`: `PageResponse<AdminPaymentResponse>`:
```json
{
  "id": 90,
  "orderId": 128,
  "userId": 44,
  "amount": 15000.00,
  "method": "WALLET",
  "status": "COMPLETED",
  "kind": "ORDER",
  "referenceId": "PAY-128-1789000000000",
  "referenceTransactionId": null,
  "paymentUrl": null,
  "qrCodeUrl": null,
  "deeplink": null,
  "description": "Thanh toán đơn #128",
  "content": "Thanh toan don 128",
  "createdAt": "2026-09-13T02:12:03.100000",
  "updatedAt": "2026-09-13T02:12:03.100000",
  "paidAt": "2026-09-13T02:12:03.100000",
  "refundedAmount": 0,
  "order": {
    "id": 128, "orderCode": "ORD-20260915-K3F9QZ", "type": "SEND", "serviceCategory": "PARCEL",
    "status": "STORING", "paymentStatus": "PAID", "totalPrice": 17000.00, "lockerId": 7,
    "createdAt": "2026-09-13T02:10:44.512331"
  },
  "customer": { "id": 44, "fullName": "Nguyễn An", "phoneNumber": "0901111111", "email": "an@example.com" }
}
```
- `paidAt` = `updatedAt` when `status = COMPLETED`, otherwise null. The table has no paid_at column. CASH/WALLET
  complete at creation. VNPAY/MOMO complete on the gateway callback.
- `refundedAmount` = sum of COMPLETED refunds of this payment.
- `order` is null for top-ups (`kind = TOPUP`) or when order-service is unreachable.
  `customer` is null when user-service is unreachable.

### 2.3 `GET /api/admin/payments/{id}/detail` (NEW)
```json
{
  "payment": { "...": "AdminPaymentResponse (§2.2)" },
  "refunds": [ { "...": "AdminRefundResponse (§2.4)" } ],
  "walletTransactions": [ { "...": "AdminWalletTransactionResponse (§2.5)" } ],
  "orderPayments": [ { "...": "AdminPaymentResponse of OTHER payments of the same order, newest first" } ]
}
```
- `walletTransactions`: for `VNPAY_TOPUP`, the TOPUP credit (`referenceId` = payment `referenceId`). For `WALLET`,
  the ORDER_PAYMENT debit of that order (`referenceId` = `ORDERPAY-{orderId}`). Otherwise `[]`.
- `orderPayments` is `[]` for top-ups. `404 NOT_FOUND` if the id is unknown.

### 2.4 `GET /api/admin/payments/refunds` (NEW)
Query: `page`, `size`, `status` (multi), `from`/`to` (on `requestedAt`), `orderId`, `paymentId`, `userId` (owner of the
original payment), `sort` = `requestedAt` (default) | `processedAt` | `amount` | `id`.
Response `data`: `PageResponse<AdminRefundResponse>`:
```json
{
  "id": 7,
  "paymentId": 90,
  "orderId": 128,
  "amount": 5000.00,
  "status": "COMPLETED",
  "reason": "Ô bị kẹt",
  "transactionId": "RF-PAY-128-1789000000000-123456",
  "processedByUserId": 1,
  "requestedAt": "2026-09-14T08:00:00",
  "processedAt": "2026-09-14T08:00:00",
  "userId": 44,
  "paymentMethod": "WALLET",
  "paymentAmount": 15000.00,
  "paymentReferenceId": "PAY-128-1789000000000",
  "order": { "id": 128, "orderCode": "ORD-20260915-K3F9QZ", "type": "SEND", "serviceCategory": "PARCEL", "status": "STORING", "paymentStatus": "PAID", "totalPrice": 17000.00, "lockerId": 7, "createdAt": "2026-09-13T02:10:44.512331" },
  "customer": { "id": 44, "fullName": "Nguyễn An", "phoneNumber": "0901111111", "email": "an@example.com" },
  "processedBy": { "id": 1, "fullName": "Admin", "phoneNumber": "0900000001", "email": "admin@lockr.vn" }
}
```
Note: creating a refund today does **not** change the payment's status or the order's `paymentStatus`.

### 2.5 `GET /api/admin/payments/wallet-transactions` (NEW)
Query: `page`, `size`, `userId`, `type` (multi `CREDIT`/`DEBIT`), `source` (multi `TOPUP`/`ORDER_PAYMENT`/`REFUND`/`ADJUST`),
`from`/`to` (on `createdAt`), `q` (contains on `referenceId`, `description`), `sort` = `createdAt` (default) | `amount` | `id`.
Response `data`: `PageResponse<AdminWalletTransactionResponse>`:
```json
{
  "id": 70,
  "walletId": 5,
  "userId": 44,
  "type": "DEBIT",
  "amount": 15000.00,
  "balanceAfter": 35000.00,
  "source": "ORDER_PAYMENT",
  "referenceId": "ORDERPAY-128",
  "description": "Thanh toán đơn #128",
  "createdAt": "2026-09-13T02:12:03.090000",
  "relatedOrderId": 128,
  "customer": { "id": 44, "fullName": "Nguyễn An", "phoneNumber": "0901111111", "email": "an@example.com" }
}
```
`relatedOrderId` is only set for `source = ORDER_PAYMENT`. The per-user endpoints `/api/admin/wallet/{userId}/...` are unchanged.

### 2.6 `GET /api/admin/payments/stats?from=&to=` (NEW) — real deltas for the overview cards
`from`/`to` = `yyyy-MM-dd` (Vietnam days), default month-to-date. Payments are bucketed by the Vietnam day of
`createdAt`. Refunds (COMPLETED, of real orders) are bucketed by `processedAt` (fallback `requestedAt`).
```json
{
  "from": "2026-09-01", "to": "2026-09-15",
  "previousFrom": "2026-08-17", "previousTo": "2026-08-31",
  "current": {
    "from": "2026-09-01", "to": "2026-09-15",
    "totalCount": 120, "totalAmount": 2350000.00,
    "completedCount": 101, "completedAmount": 2010000.00,
    "pendingCount": 9, "pendingAmount": 180000.00,
    "failedCount": 10, "failedAmount": 160000.00,
    "otherCount": 0, "otherAmount": 0,
    "successRate": 84.17,
    "orderPayments": { "count": 100, "amount": 1650000.00, "completedCount": 86, "completedAmount": 1410000.00 },
    "topups": { "count": 20, "amount": 700000.00, "completedCount": 15, "completedAmount": 600000.00 },
    "refundCount": 2, "refundAmount": 20000.00,
    "netCollectedAmount": 1390000.00,
    "byStatus": [
      { "key": "COMPLETED", "count": 101, "amount": 2010000.00, "completedCount": 101, "completedAmount": 2010000.00 },
      { "key": "PENDING", "count": 9, "amount": 180000.00, "completedCount": 0, "completedAmount": 0 },
      { "key": "FAILED", "count": 10, "amount": 160000.00, "completedCount": 0, "completedAmount": 0 }
    ],
    "byMethod": [
      { "key": "WALLET", "count": 50, "amount": 800000.00, "completedCount": 50, "completedAmount": 800000.00 },
      { "key": "VNPAY_TOPUP", "count": 20, "amount": 700000.00, "completedCount": 15, "completedAmount": 600000.00 },
      { "key": "VNPAY", "count": 30, "amount": 520000.00, "completedCount": 21, "completedAmount": 350000.00 },
      { "key": "CASH", "count": 12, "amount": 190000.00, "completedCount": 12, "completedAmount": 190000.00 },
      { "key": "MOMO", "count": 8, "amount": 140000.00, "completedCount": 3, "completedAmount": 70000.00 }
    ]
  },
  "previous":  { "...": "same shape as current" },
  "today":     { "...": "same shape, from = to = today" },
  "yesterday": { "...": "same shape, from = to = yesterday" },
  "changes": {
    "totalCountPct": 12.50, "totalAmountPct": 8.33, "completedCountPct": 10.00, "completedAmountPct": 9.10,
    "refundAmountPct": null, "netCollectedAmountPct": 7.25, "successRatePoints": -1.20
  },
  "todayChanges": { "...": "same shape, today vs yesterday" }
}
```
- `successRate` = completedCount / totalCount × 100 (2 decimals). It is `null` when there are no payments.
- `netCollectedAmount` = `orderPayments.completedAmount − refundAmount`, so top-ups are excluded.
- `*Pct` = (current − previous) / |previous| × 100. It is `null` when previous = 0.
  `successRatePoints` = difference in percentage points, and is `null` if either side is null.
- `byStatus`/`byMethod` are sorted by `amount` desc and only list keys that occur.

---

## 3. Revenue (`/admin/revenue`) — served by order-service, data from payment-service

### 3.1 Revenue rule (authoritative)
- **Revenue (`totalRevenue`)** = sum of payments with `status = COMPLETED` for a real order (`orderId > 0`).
  - Wallet top-ups (`VNPAY_TOPUP`) are **excluded**. They are deposits.
  - Orders paid with the wallet (`WALLET`) **are included** when that order payment completes.
  - Includes CASH, VNPAY, MOMO.
  - Counts regardless of the order's current status. A canceled order that was paid and not refunded is still revenue.
- **Revenue date** = the Vietnam calendar day of the collection time = payment `updatedAt` for COMPLETED payments.
- **Refunds (`refundAmount`)** = refunds with `status = COMPLETED` and `orderId > 0`, dated by `processedAt`
  (fallback `requestedAt`). **`netRevenue = totalRevenue − refundAmount`** can be negative on a single day.
- **Overtime fee (`OVERTIME_FEE`)**: the overtime fee is added into the order's `extraFee` and `totalPrice` at pickup.
  Per order:
  - `base = totalPrice − extraFee`
  - `overtimeCollectedAllTime = clamp(paidAllTime − base, 0, extraFee)`
  - `overtime in period = min(overtimeCollectedAllTime, collected in period)`
  - That amount is reported on the `OVERTIME_FEE` row and removed from the order-type row.
  - Approximation: when one order's payments span periods, the overtime part is attributed to the latest collections.
- **Order counts**:
  - `orderCount` = orders **created** in the period (any status).
  - `paidOrderCount` = distinct orders with ≥ 1 collection in the period.
  - `completedOrderCount` = orders with `completedAt` in the period.
  - `canceledOrderCount` = orders created in the period that are now `CANCELED`.
- **`averageOrderValue`** = `totalRevenue / paidOrderCount`, rounded to 1 VND. It is `null` when `paidOrderCount = 0`.
- **Locker / store attribution**: `lockerId`, falling back to `destinationLockerId`. Store = order `storeId`, falling back to the locker's `storeId`.
- **Customer attribution**: the order owner (`userId`).
- The legacy `/api/admin/orders/revenue` and the `totalRevenue`/`revenueToday` in `/api/admin/dashboard/overview` and
  `/api/admin/orders/statistics` still use the **old** rule (sum of `totalPrice` of COMPLETED orders). They are
  unchanged for existing screens. The `/admin/revenue` page must use the endpoints below.
- If payment-service is unreachable, every endpoint below returns **`503 PAYMENT_DATA_UNAVAILABLE`**.

All endpoints take `from`, `to` (`yyyy-MM-dd`, default month-to-date, ≤ 366 days).

### 3.2 `GET /api/admin/revenue/summary`
```json
{
  "from": "2026-09-01", "to": "2026-09-15",
  "previousFrom": "2026-08-17", "previousTo": "2026-08-31",
  "current": {
    "from": "2026-09-01", "to": "2026-09-15",
    "totalRevenue": 1410000.00, "refundAmount": 20000.00, "netRevenue": 1390000.00,
    "orderCount": 95, "paidOrderCount": 84, "paymentCount": 86,
    "completedOrderCount": 70, "canceledOrderCount": 6,
    "averageOrderValue": 16786
  },
  "previous": { "...": "RevenuePeriod, same shape" },
  "changes": {
    "totalRevenuePct": 9.10, "refundAmountPct": null, "netRevenuePct": 7.80,
    "orderCountPct": 5.56, "paidOrderCountPct": 3.70, "averageOrderValuePct": 5.21
  },
  "today":     { "...": "RevenuePeriod for today (Vietnam)" },
  "thisWeek":  { "...": "RevenuePeriod Monday..today" },
  "thisMonth": { "...": "RevenuePeriod 1st..today" }
}
```

### 3.3 `GET /api/admin/revenue/daily`
Every day in the range is present, with zeros where there is no data.
```json
{
  "from": "2026-09-01", "to": "2026-09-15", "totalRevenue": 1410000.00,
  "days": [
    { "date": "2026-09-01", "revenue": 90000.00, "refundAmount": 0, "netRevenue": 90000.00, "paidOrderCount": 6, "paymentCount": 6, "orderCount": 7 },
    { "date": "2026-09-02", "revenue": 0, "refundAmount": 0, "netRevenue": 0, "paidOrderCount": 0, "paymentCount": 0, "orderCount": 0 }
  ]
}
```
`orderCount` = orders created that day. `revenue`/`paymentCount`/`paidOrderCount` = collections that day.

### 3.4 `GET /api/admin/revenue/by-service`
The rows `SEND`, `RENTAL`, `DRONE_DELIVERY` and `OVERTIME_FEE` are **always present**. `STORAGE`, `OTHER` and
`UNKNOWN` (the order was not found) appear only when non-zero. The sum of `revenue` over all rows = `totalRevenue`.
```json
{
  "from": "2026-09-01", "to": "2026-09-15", "totalRevenue": 1410000.00,
  "items": [
    { "serviceType": "SEND", "revenue": 700000.00, "refundAmount": 10000.00, "netRevenue": 690000.00, "sharePct": 49.65, "orderCount": 50, "paidOrderCount": 46, "paymentCount": 47 },
    { "serviceType": "RENTAL", "revenue": 500000.00, "refundAmount": 10000.00, "netRevenue": 490000.00, "sharePct": 35.46, "orderCount": 35, "paidOrderCount": 30, "paymentCount": 31 },
    { "serviceType": "DRONE_DELIVERY", "revenue": 150000.00, "refundAmount": 0, "netRevenue": 150000.00, "sharePct": 10.64, "orderCount": 10, "paidOrderCount": 8, "paymentCount": 8 },
    { "serviceType": "OVERTIME_FEE", "revenue": 60000.00, "refundAmount": 0, "netRevenue": 60000.00, "sharePct": 4.26, "orderCount": 0, "paidOrderCount": 12, "paymentCount": 0 }
  ]
}
```
For `OVERTIME_FEE`: `paidOrderCount` = orders with a collected overtime part. `orderCount`/`paymentCount` are always 0.
Refunds are attributed to the order type, never to `OVERTIME_FEE`.

### 3.5 `GET /api/admin/revenue/by-method`
Sorted by `revenue` desc. Refunds are attributed to the method of the refunded payment.
```json
{
  "from": "2026-09-01", "to": "2026-09-15", "totalRevenue": 1410000.00,
  "items": [
    { "method": "WALLET", "revenue": 800000.00, "refundAmount": 10000.00, "netRevenue": 790000.00, "sharePct": 56.74, "paymentCount": 50, "paidOrderCount": 49 },
    { "method": "VNPAY", "revenue": 350000.00, "refundAmount": 10000.00, "netRevenue": 340000.00, "sharePct": 24.82, "paymentCount": 21, "paidOrderCount": 21 },
    { "method": "CASH", "revenue": 190000.00, "refundAmount": 0, "netRevenue": 190000.00, "sharePct": 13.48, "paymentCount": 12, "paidOrderCount": 12 },
    { "method": "MOMO", "revenue": 70000.00, "refundAmount": 0, "netRevenue": 70000.00, "sharePct": 4.96, "paymentCount": 3, "paidOrderCount": 3 }
  ]
}
```

### 3.6 `GET /api/admin/revenue/by-locker?storeId=`
Includes **every locker**, even those with zero revenue. It adds one row with `lockerId: null` for orders without a
locker, but only when that row is non-zero and `storeId` is not given. Sorted by `revenue` desc, then `orderCount` desc.
`storeId` (optional) keeps only lockers of that store.
```json
{
  "from": "2026-09-01", "to": "2026-09-15", "totalRevenue": 1410000.00, "lookupAvailable": true,
  "items": [
    {
      "lockerId": 7, "code": "LK-Q1-01", "name": "Tủ Lê Lợi", "address": "1 Lê Lợi, Q1", "status": "ACTIVE",
      "storeId": 3, "storeName": "Chi nhánh Q1",
      "boxCount": 24, "orderCount": 40, "paidOrderCount": 37,
      "revenue": 610000.00, "refundAmount": 10000.00, "netRevenue": 600000.00,
      "revenuePerBox": 25417, "sharePct": 43.26
    }
  ]
}
```
- `boxCount` = all boxes of the locker, including inactive ones. `revenuePerBox` = `revenue / boxCount`, rounded, and `null` when `boxCount = 0`.
- `lookupAvailable = false` means locker-service or store-service failed: names are null and lockers without revenue may be missing.

### 3.7 `GET /api/admin/revenue/by-store`
Includes **every store**, plus a `storeId: null` row ("chưa gán cửa hàng") when that row is non-zero.
```json
{
  "from": "2026-09-01", "to": "2026-09-15", "totalRevenue": 1410000.00, "lookupAvailable": true,
  "items": [
    {
      "storeId": 3, "name": "Chi nhánh Q1", "address": "1 Lê Lợi, Q1", "contactPhone": "02838000000",
      "lockerCount": 2, "boxCount": 36, "orderCount": 60, "paidOrderCount": 55,
      "revenue": 900000.00, "refundAmount": 10000.00, "netRevenue": 890000.00, "sharePct": 63.83
    },
    {
      "storeId": null, "name": null, "address": null, "contactPhone": null,
      "lockerCount": 1, "boxCount": 4, "orderCount": 5, "paidOrderCount": 5,
      "revenue": 150000.00, "refundAmount": 0, "netRevenue": 150000.00, "sharePct": 10.64
    }
  ]
}
```

### 3.8 `GET /api/admin/revenue/by-customer`
Query: `from`, `to`, `page`, `size` (≤ 100), `sort` and `q`.
- `sort` = `field,dir`. Fields: `totalSpent` (default), `netSpent`, `orderCount`, `paidOrderCount`,
  `averageOrderValue`, `lastOrderAt`, `lastPaidAt`. Dir defaults to `desc`.
- `q` = contains on full name or email (case-insensitive), contains on phone, or an exact user id.

A customer is listed if they created an order in the range or had a collection in the range.
Response `data`: `PageResponse<CustomerRevenue>`:
```json
{
  "content": [
    {
      "userId": 44, "fullName": "Nguyễn An", "phoneNumber": "0901111111", "email": "an@example.com",
      "orderCount": 5, "paidOrderCount": 5,
      "totalSpent": 95000.00, "refundAmount": 0, "netSpent": 95000.00, "averageOrderValue": 19000,
      "lastOrderAt": "2026-09-14T09:00:00", "lastPaidAt": "2026-09-14T09:01:30"
    }
  ],
  "page": 0, "size": 20, "totalElements": 61, "totalPages": 4
}
```
`lastOrderAt` = latest order created in the range. `lastPaidAt` = latest collection in the range. Names are null if user-service is down.

### 3.9 `GET /api/admin/revenue/customers/{userId}`
Customer info, totals for the range, and their orders. The orders are those created in the range plus orders with a
collection in the range, newest first.
```json
{
  "from": "2026-09-01", "to": "2026-09-15",
  "userId": 44, "fullName": "Nguyễn An", "phoneNumber": "0901111111", "email": "an@example.com", "status": "ACTIVE",
  "orderCount": 5, "paidOrderCount": 5,
  "totalSpent": 95000.00, "refundAmount": 0, "netSpent": 95000.00, "averageOrderValue": 19000,
  "firstOrderAt": "2026-08-20T02:00:00", "lastOrderAt": "2026-09-14T09:00:00",
  "orders": [
    {
      "orderId": 128, "orderCode": "ORD-20260915-K3F9QZ", "type": "SEND", "status": "COMPLETED", "paymentStatus": "PAID",
      "lockerId": 7, "lockerCode": "LK-Q1-01", "lockerName": "Tủ Lê Lợi",
      "totalPrice": 17000.00, "extraFee": 2000.00, "discount": 0.00,
      "paidInRange": 17000.00, "refundedInRange": 0, "paidAllTime": 17000.00,
      "paymentMethods": ["WALLET", "CASH"], "lastPaymentMethod": "CASH", "lastPaidAt": "2026-09-14T09:01:30",
      "createdAt": "2026-09-13T02:10:44.512331", "paidAt": "2026-09-13T02:12:03.100000", "completedAt": "2026-09-14T09:02:00"
    }
  ]
}
```
- Only payments **made by this user** count here. Totals follow §3.1.
- `paymentMethods` = distinct methods of the collections in the range.
- `paidAllTime`, `lastPaymentMethod` and `lastPaidAt` come from payment-service across all time. They are null when
  that lookup failed; `paidAllTime` is 0 when there is no payment.
- An unknown `userId` returns 200 with zero totals, `orders: []` and null name fields.

---

## 4. Suggested web usage
- **/admin/orders**:
  - The table uses `GET /api/admin/orders/search`. Useful columns: `orderCode`, `customer.fullName/phoneNumber`,
    `type`, `status`, `paymentStatus` + `payment.lastPaidMethod`, `locker.code` + `sendBoxNumber`, `totalPrice`, `createdAt`.
  - The drawer uses `/detail`.
  - The status change uses `PUT` (or `PATCH`) with a JSON body.
- **/admin/payments**:
  - Cards use `/stats` (`current` vs `previous` with `changes`, or `today` vs `yesterday` with `todayChanges`).
  - The table uses `/search`, the row drawer uses `/{id}/detail`, and the tabs use `/refunds` and `/wallet-transactions`.
- **/admin/revenue**: `/summary` (KPI + deltas), `/daily` (chart), `/by-service`, `/by-method`, `/by-locker`,
  `/by-store`, `/by-customer` (table) and `/customers/{userId}` (drill-down). Use the same `from`/`to` for all calls.

---

## 5. Internal endpoints added (gateway-blocked; for backend reference only)
| Service | Endpoint | Returns |
|---|---|---|
| user-service | `GET /internal/users/batch?ids=` (≤ 500) | `UserSummary[]` |
| locker-service | `GET /internal/lockers/batch?ids=` (omit ids → all) | `LockerResponse[]` |
| locker-service | `GET /internal/boxes/batch?ids=` | `{id, lockerId, boxNumber, size, cellType, status, active}[]` |
| store-service | `GET /internal/stores/batch?ids=` (omit ids → all) | `StoreResponse[]` |
| order-service | `GET /internal/orders/batch?ids=` (≤ 500) | `OrderBriefResponse[]` |
| payment-service | `GET /internal/payments/order-summaries?orderIds=` (≤ 500) | `OrderPaymentSummary[]` |
| payment-service | `GET /internal/payments/collected?from=&to=&userId=` (ISO local date-time, storage zone, `[from,to)`) | `{payments[], refunds[], orderPaidTotals[]}` |

Gateway: new route `order-service-admin-revenue` for `/api/admin/revenue`, `/api/admin/revenue/**` → order-service.
The other new public paths are under prefixes that were already routed (`/api/admin/orders/**` and `/api/admin/payments/**`).
