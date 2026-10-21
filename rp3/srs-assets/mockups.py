"""Wireframe mock-ups for the SRS (rendered to PNG with headless Chrome)."""
import os, subprocess, html

OUT = os.path.join(os.path.dirname(__file__), "mockups")
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
E = html.escape

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,Helvetica,sans-serif;background:#ECEFF1;font-size:13px;color:#263238}
.phone{width:360px;height:740px;margin:20px;border:10px solid #263238;border-radius:34px;background:#fff;overflow:hidden;position:relative}
.status{height:22px;background:#fff;font-size:10px;color:#607D8B;padding:4px 16px;display:flex;justify-content:space-between}
.appbar{height:48px;background:#D84315;color:#fff;display:flex;align-items:center;padding:0 14px;font-weight:bold;font-size:15px;gap:10px}
.appbar .back{font-size:18px}
.body{padding:12px 14px;height:calc(100% - 70px);overflow:hidden}
.body.nav{height:calc(100% - 126px)}
.lbl{font-size:11px;color:#607D8B;margin:8px 0 3px}
.in{border:1px solid #B0BEC5;border-radius:8px;padding:8px 10px;color:#90A4AE;background:#FAFAFA}
.in.v{color:#263238}
.sel:after{content:" \\25BE";float:right}
.btn{background:#D84315;color:#fff;border-radius:10px;padding:10px;text-align:center;font-weight:bold;margin-top:10px}
.btn2{border:1.5px solid #D84315;color:#D84315;border-radius:10px;padding:9px;text-align:center;font-weight:bold;margin-top:8px}
.btn3{background:#ECEFF1;color:#455A64;border-radius:10px;padding:9px;text-align:center;margin-top:8px}
.card{border:1px solid #CFD8DC;border-radius:10px;padding:9px 10px;margin:8px 0;background:#fff}
.card b{display:block;margin-bottom:3px}
.muted{color:#78909C;font-size:11px}
.row{display:flex;gap:8px;align-items:center}
.row>*{flex:1}
.chip{display:inline-block;border:1px solid #B0BEC5;border-radius:14px;padding:4px 10px;margin:3px 4px 3px 0;font-size:11px}
.chip.on{background:#FBE9E7;border-color:#D84315;color:#D84315;font-weight:bold}
.tabs{display:flex;border-bottom:1px solid #CFD8DC;margin:-12px -14px 8px}
.tabs div{flex:1;text-align:center;padding:9px 2px;font-size:11px;color:#607D8B}
.tabs .on{color:#D84315;border-bottom:3px solid #D84315;font-weight:bold}
.grid{display:grid;gap:5px;margin:6px 0}
.cell{border:1px solid #90A4AE;border-radius:5px;height:34px;display:flex;align-items:center;justify-content:center;font-size:11px}
.free{background:#E8F5E9}.res{background:#FFF8E1}.occ{background:#ECEFF1;color:#90A4AE}.fault{background:#FFEBEE}.sel2{background:#D84315;color:#fff;border-color:#D84315}
.bnav{position:absolute;bottom:0;left:0;right:0;height:56px;border-top:1px solid #CFD8DC;display:flex;background:#fff}
.bnav div{flex:1;text-align:center;font-size:10px;color:#78909C;padding-top:8px}
.bnav .on{color:#D84315;font-weight:bold}
.ico{display:block;width:20px;height:20px;border-radius:5px;background:#CFD8DC;margin:0 auto 3px}
.bnav .on .ico{background:#D84315}
.qr{width:150px;height:150px;margin:8px auto;background:repeating-linear-gradient(45deg,#263238 0 6px,#fff 6px 12px),#fff;border:6px solid #fff;outline:1px solid #B0BEC5}
.sheet{position:absolute;left:0;right:0;bottom:0;background:#fff;border-radius:18px 18px 0 0;box-shadow:0 -4px 18px rgba(0,0,0,.25);padding:14px}
.dim{position:absolute;inset:70px 0 0 0;background:rgba(0,0,0,.35)}
.handle{width:40px;height:4px;background:#CFD8DC;border-radius:2px;margin:0 auto 10px}
.tl{border-left:2px solid #CFD8DC;margin-left:6px;padding-left:12px}
.tl div{position:relative;margin:7px 0}
.tl div:before{content:"";position:absolute;left:-18px;top:2px;width:10px;height:10px;border-radius:50%;background:#CFD8DC}
.tl .done:before{background:#2E7D32}.tl .now:before{background:#D84315}
.map{height:120px;border-radius:10px;background:linear-gradient(135deg,#E3F2FD,#E8F5E9);position:relative;border:1px solid #CFD8DC}
.badge{display:inline-block;border-radius:10px;padding:1px 8px;font-size:10px;font-weight:bold}
.b-o{background:#FFF3E0;color:#E65100}.b-g{background:#E8F5E9;color:#2E7D32}.b-r{background:#FFEBEE;color:#C62828}.b-b{background:#E3F2FD;color:#1565C0}
.stat{border-radius:10px;background:#FBE9E7;padding:8px;text-align:center}
.stat b{font-size:18px;color:#D84315;display:block}
.bubble{border-radius:12px;padding:8px 10px;margin:6px 0;max-width:85%}
.me{background:#D84315;color:#fff;margin-left:auto}
.bot{background:#ECEFF1}
.cite{font-size:10px;color:#1565C0;margin-top:4px}
/* browser */
.browser{width:1180px;height:700px;margin:20px;border:1px solid #90A4AE;border-radius:8px;background:#fff;overflow:hidden}
.bbar{height:30px;background:#CFD8DC;display:flex;align-items:center;padding:0 10px;gap:6px}
.bbar i{width:10px;height:10px;border-radius:50%;background:#fff;display:inline-block}
.bbar .url{flex:1;background:#fff;border-radius:4px;height:18px;font-size:11px;color:#607D8B;padding:2px 8px;margin-left:10px}
.wrap{display:flex;height:670px}
.side{width:210px;background:#263238;color:#B0BEC5;padding:12px 0;font-size:12px}
.side .logo{color:#fff;font-weight:bold;font-size:16px;padding:0 16px 12px}
.side div.it{padding:7px 16px}
.side .on{background:#D84315;color:#fff}
.main{flex:1;padding:16px 20px;overflow:hidden}
.main h2{font-size:18px;margin-bottom:10px}
table{border-collapse:collapse;width:100%;font-size:12px;margin-top:8px}
th{background:#FBE9E7;text-align:left;padding:7px;border:1px solid #E0E0E0}
td{padding:6px 7px;border:1px solid #E0E0E0}
.toolbar{display:flex;gap:8px;align-items:center}
.toolbar .in{flex:none;width:220px}
.kiosk{width:1024px;height:600px;margin:20px;border:14px solid #212121;border-radius:12px;background:#FFF8F5;overflow:hidden;position:relative}
.key{border:1px solid #B0BEC5;border-radius:8px;background:#fff;height:56px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold}
"""


def page(inner, w, h):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body style='width:{w}px;height:{h}px'>{inner}</body></html>"


def phone(title, body, nav=None, overlay="", back=True):
    nv = ""
    if nav is not None:
        items = ["Trang chủ", "Tủ", "Đơn hàng", "Trợ lý AI", "Hồ sơ"]
        nv = "<div class='bnav'>" + "".join(
            f"<div class='{'on' if i == nav else ''}'><span class='ico'></span>{x}</div>" for i, x in enumerate(items)) + "</div>"
    bar = f"<div class='appbar'>{'<span class=back>&#8592;</span>' if back else ''}{E(title)}</div>" if title else ""
    return (f"<div class='phone'><div class='status'><span>9:41</span><span>LTE 100%</span></div>{bar}"
            f"<div class='body {'nav' if nav is not None else ''}'>{body}</div>{nv}{overlay}</div>"), 400, 780


def browser(url, menu_on, body):
    menu = ["Dashboard", "Users", "Stores", "Lockers", "Drones", "Drone Orders", "Drone Incidents", "Orders",
            "Payments", "Refunds", "Revenue", "Promotions", "Maintenance", "Feedback", "Notifications",
            "Business Settings", "Knowledge Base"]
    side = "<div class='side'><div class='logo'>Lock.R Admin</div>" + "".join(
        f"<div class='it {'on' if m == menu_on else ''}'>{m}</div>" for m in menu) + "</div>"
    return (f"<div class='browser'><div class='bbar'><i></i><i></i><i></i><div class='url'>https://admin.locker-drone.tech{url}</div></div>"
            f"<div class='wrap'>{side}<div class='main'>{body}</div></div></div>"), 1220, 740


def field(label, value="", ph="", sel=False):
    cls = "in" + (" v" if value else "") + (" sel" if sel else "")
    return f"<div class='lbl'>{E(label)}</div><div class='{cls}'>{E(value or ph)}</div>"


def boxgrid(cols, cells):
    return f"<div class='grid' style='grid-template-columns:repeat({cols},1fr)'>" + "".join(
        f"<div class='cell {c}'>{n}</div>" for n, c in cells) + "</div>"


SCREENS = {}

# 1 Login / Register sheet
SCREENS["m01-login"] = phone("", "<div style='text-align:center;margin-top:40px'><div style='font-size:26px;font-weight:bold;color:#D84315'>LOCK.R</div><div class='muted'>Tủ thông minh &amp; giao hàng drone</div></div>",
    overlay="<div class='dim' style='top:22px'></div><div class='sheet' style='height:560px'><div class='handle'></div>"
    "<div class='tabs' style='margin:0 0 8px'><div class='on'>Đăng nhập</div><div>Đăng ký</div></div>"
    "<div class='row'><div class='chip on' style='text-align:center'>Email</div><div class='chip' style='text-align:center'>SĐT</div></div>"
    + field("Email", ph="name@example.com") + field("Mật khẩu", ph="Nhập mật khẩu") +
    "<div class='muted' style='text-align:right;margin-top:6px;color:#D84315'>Quên mật khẩu?</div>"
    "<div class='btn'>Đăng nhập</div><div class='muted' style='text-align:center;margin:12px 0 4px'>Hoặc tiếp tục với</div>"
    "<div class='btn3'>Google</div><div class='btn3'>Số điện thoại (OTP)</div></div>", back=False)

# 2 Home
SCREENS["m02-home"] = phone("", "<div class='row' style='margin-bottom:8px'><div><div class='muted'>Xin chào,</div><b style='font-size:16px'>Nguyễn Văn A</b></div><div style='text-align:right'><span class='badge b-o'>Ví: 120.000 đ</span></div></div>"
    "<div class='grid' style='grid-template-columns:repeat(4,1fr)'>" + "".join(
        f"<div style='text-align:center;font-size:11px'><div class='stat' style='height:48px'></div>{x}</div>" for x in ["Gửi hàng", "Thuê tủ", "Drone", "Quét QR"]) + "</div>"
    "<div class='lbl' style='font-size:13px;color:#263238;font-weight:bold'>Đơn đang hoạt động</div>"
    "<div class='card'><b>ORD-20261021-0042 <span class='badge b-b'>STORING</span></b><span class='muted'>Gửi hàng · Tủ CAB-TU01 · Ô 3</span><div class='muted'>PIN lấy hàng: ••••••</div></div>"
    "<div class='card'><b>ORD-20261021-0051 <span class='badge b-o'>EN_ROUTE</span></b><span class='muted'>Drone · CAB-01 → CAB-TU01</span></div>"
    "<div class='lbl' style='font-size:13px;color:#263238;font-weight:bold'>Điểm gửi gần bạn</div>"
    "<div class='card'><b>Lock.R FPT University</b><span class='muted'>0,6 km · còn 4 ô trống · Trực tuyến</span></div>", nav=0)

# 3 Send parcel
SCREENS["m03-send-parcel"] = phone("Gửi hàng qua tủ", field("Chọn tủ", "Lock.R FPT University (CAB-TU01)", sel=True) +
    "<div class='lbl'>Kích thước hàng</div><span class='chip'>Nhỏ</span><span class='chip on'>Vừa</span><span class='chip'>Lớn</span>"
    "<div class='lbl'>Hoặc chạm ô trống trên sơ đồ tủ</div>" +
    boxgrid(4, [("1", "occ"), ("2", "free"), ("3", "sel2"), ("4", "res"), ("5", "free"), ("6", "fault"), ("7", "free"), ("D", "occ")]) +
    field("Số điện thoại người nhận", "0901 234 567") + field("Tên người nhận (tùy chọn)", ph="Nguyễn Văn B") +
    field("Email người nhận (tùy chọn)", ph="email@example.com") +
    "<div class='row' style='margin-top:8px'><div class='chip'>Mã giảm giá</div><div class='chip'>Điểm thưởng</div></div>"
    "<div class='row' style='margin-top:6px'><b>Phí gửi</b><b style='text-align:right;color:#D84315'>15.000 đ</b></div>"
    "<div class='btn'>Tạo đơn &amp; lấy PIN bỏ hàng</div>")

# 4 VietQR payment
SCREENS["m04-vietqr"] = phone("Gửi hàng qua tủ", "<div class='card'><b>ORD-20261021-0042</b><span class='muted'>Đơn đã tạo — ô đang được giữ</span></div>",
    overlay="<div class='dim'></div><div class='sheet' style='height:580px'><div class='handle'></div>"
    "<div class='muted' style='text-align:center'>LOCK.R • THANH TOÁN</div><div style='text-align:center;font-size:22px;font-weight:bold;color:#D84315;margin:6px 0'>15.000 đ</div>"
    "<div class='qr'></div>"
    "<div class='card'><div class='row'><span class='muted'>Ngân hàng</span><b style='text-align:right'>MB Bank</b></div>"
    "<div class='row'><span class='muted'>Số tài khoản</span><b style='text-align:right'>0123456789</b></div>"
    "<div class='row'><span class='muted'>Nội dung</span><b style='text-align:right'>ORD20261021 0042</b></div></div>"
    "<div class='muted' style='text-align:center'>Đang chờ xác nhận chuyển khoản…</div>"
    "<div class='btn'>Thanh toán bằng app ngân hàng</div><div class='btn3'>Ở lại thanh toán sau</div></div>")

# 5 Rent locker
SCREENS["m05-rent-locker"] = phone("Thuê tủ giữ đồ", field("Chọn tủ", "Lock.R FPT University (CAB-TU01)", sel=True) +
    "<div class='lbl'>Loại ô</div><span class='chip on'>Ô thường · 5.000 đ/giờ</span><span class='chip'>Ô vali (XL) · 10.000 đ/giờ</span>"
    "<div class='lbl'>Thời gian thuê</div><span class='chip'>2 giờ</span><span class='chip on'>4 giờ</span><span class='chip'>8 giờ</span><span class='chip'>24 giờ</span><span class='chip'>Tùy chọn...</span>" +
    boxgrid(4, [("1", "occ"), ("2", "free"), ("3", "free"), ("4", "res"), ("5", "sel2"), ("6", "free"), ("7", "free"), ("D", "occ")]) +
    field("Ghi chú", ph="Ví dụ: vali màu xanh") +
    "<div class='row' style='margin-top:8px'><div class='chip'>Mã giảm giá</div><div class='chip'>Điểm thưởng</div></div>"
    "<div class='row' style='margin-top:8px'><b>Tạm tính</b><b style='text-align:right;color:#D84315'>20.000 đ</b></div>"
    "<div class='muted'>PIN dùng nhiều lần trong kỳ thuê</div><div class='btn'>Thuê ngay</div>")

# 6 Order detail
SCREENS["m06-order-detail"] = phone("Chi tiết đơn", "<div class='card' style='text-align:center'><span class='badge b-b'>STORING</span><div class='muted' style='margin-top:6px'>Mã lấy hàng</div><div style='font-size:28px;font-weight:bold;letter-spacing:6px;color:#D84315'>482 915</div><div class='muted'>Hạn lấy: 23/10/2026 18:00</div></div>"
    "<div class='btn'>Chia sẻ mã cho người nhận</div><div class='row'><div class='btn2'>Đổi mã PIN</div><div class='btn2'>Ủy quyền lấy hộ</div></div>"
    "<div class='card'><b>Thông tin đơn</b><div class='muted'>ORD-20261021-0042 · Gửi hàng</div><div class='muted'>Tủ CAB-TU01 · Ô 3 (Vừa)</div><div class='muted'>Người nhận: Nguyễn Văn B · 0901 234 567</div><div class='muted'>Thanh toán: SePay · 15.000 đ · GD 9F2K…</div></div>"
    "<div class='card'><b>Lịch sử trạng thái</b><div class='tl'><div class='done'>INITIALIZED · 10:02</div><div class='done'>PAID · 10:04</div><div class='now'>STORING · 10:15</div></div></div>"
    "<div class='btn3'>Báo ô lỗi</div>")

# 7 Drone booking
SCREENS["m07-drone-booking"] = phone("Gửi hàng bằng Drone", "<div class='card'><b>Tủ gửi: CAB-01 · Ô DRONE D1</b><span class='muted'>Kiện sẽ được bỏ vào ô drone tại tủ gửi</span></div>" +
    field("Chọn tủ nhận", "Lock.R FPT University · 3,2 km · còn 2 ô drone", sel=True) +
    field("Chọn loại hàng", "Tài liệu (DOCUMENT)", sel=True) +
    "<div class='lbl'>Khối lượng</div><span class='chip'>500 g</span><span class='chip on'>750 g</span><span class='chip'>1 kg</span><span class='chip'>1,5 kg</span><span class='chip'>2 kg</span>" +
    "<div class='row'>" + field("Giá trị khai báo", "300.000 đ").replace("<div class='lbl'>", "<div><div class='lbl'>", 1) + "</div><div><div class='lbl'>Dễ vỡ</div><div class='in v'>Không</div></div></div>" +
    field("Số điện thoại người nhận", "0901 234 567") +
    "<div class='card' style='font-size:11px'>&#9745; Tôi cam kết kiện không chứa hàng cấm bay</div>"
    "<div class='row'><b>Phí giao</b><b style='text-align:right;color:#D84315'>18.000 đ</b></div>"
    "<div class='btn'>Tạo đơn và thanh toán</div>")

# 8 Drone tracking
SCREENS["m08-drone-tracking"] = phone("Theo dõi đơn drone", "<div class='map'><div style='position:absolute;left:20px;top:80px' class='badge b-b'>A · CAB-01</div><div style='position:absolute;right:16px;top:16px' class='badge b-g'>B · CAB-TU01</div><div style='position:absolute;left:150px;top:50px;font-size:20px'>&#9992;</div></div>"
    "<div class='row' style='margin:6px 0'><span class='muted'>Tổng 3,2 km · còn 1,4 km</span><span class='badge b-o' style='text-align:center'>EN_ROUTE</span></div>"
    "<div class='card'><b>Hành trình</b><div class='tl'><div class='done'>Đã thanh toán · 09:58</div><div class='done'>Đội bay tiếp nhận · 10:03 (drone DR-02)</div><div class='done'>Đã nạp hàng · 10:07 · 742 g · NP-261021-K7Q2</div><div class='done'>Đã rời trạm · 10:10</div><div class='now'>Đang bay · 6 phút</div><div>Sắp tới</div><div>Đã đến tủ nhận</div><div>Sẵn sàng lấy hàng</div></div></div>"
    "<div class='btn2'>Theo dõi trên bản đồ</div>")

# 9 Create report
SCREENS["m09-create-report"] = phone("Báo sự cố", field("Tủ", "Lock.R FPT University (CAB-TU01)", sel=True) + field("Ô", "Ô 6", sel=True) +
    field("Tiêu đề", "Cửa ô không mở") + "<div class='lbl'>Mô tả</div><div class='in v' style='height:70px'>Nhập đúng PIN nhưng cửa ô không bật ra…</div>"
    "<div class='lbl'>Ảnh hiện trường (tối đa 5)</div><div class='row'><div class='stat' style='height:60px'></div><div class='stat' style='height:60px'></div><div class='in' style='height:60px;text-align:center;padding-top:20px'>+</div></div>"
    "<div class='btn'>Gửi báo cáo</div>")

# 10 Technician home
SCREENS["m10-technician-home"] = phone("KTV tủ", "<div class='tabs'><div class='on'>Sự cố (3)</div><div>Việc của tôi (1)</div><div>Kiểm tra tủ</div><div>Định kỳ (2)</div><div>Thiết bị IoT</div></div>"
    "<div class='grid' style='grid-template-columns:repeat(3,1fr)'><div class='stat'><b>3</b>Chờ xử lý</div><div class='stat'><b>1</b>Đang làm</div><div class='stat'><b>0</b>Trễ hạn SLA</div></div>"
    "<div class='card'><b>RPT-1042 · Cửa ô không mở <span class='badge b-r'>OPEN</span></b><span class='muted'>CAB-TU01 · Ô 6 · Hỏng khóa · SLA còn 3 giờ</span><div class='btn' style='padding:6px'>Nhận việc</div></div>"
    "<div class='card'><b>RPT-1040 · Màn hình kiosk đơ <span class='badge b-r'>OPEN</span></b><span class='muted'>CAB-01 · Ngưng cả tủ · SLA còn 1 giờ</span><div class='btn' style='padding:6px'>Nhận việc</div></div>"
    "<div class='card'><b>RPT-1037 · Ô bẩn <span class='badge b-o'>IN_PROGRESS</span></b><span class='muted'>CAB-TU01 · Ô 2 · Phụ trách: bạn</span></div>")

# 11 Resolve ticket sheet
SCREENS["m11-resolve-ticket"] = phone("RPT-1042", "<div class='card'><b>Cửa ô không mở</b><span class='muted'>CAB-TU01 · Ô 6 · Đơn ORD-…0042 còn hàng</span></div>",
    overlay="<div class='dim'></div><div class='sheet' style='height:560px'><div class='handle'></div><b>Nghiệm thu &amp; Hoàn tất</b>"
    "<div class='lbl'>Ô còn hàng của khách — chọn cách xử lý</div>"
    "<div class='card' style='border-color:#D84315'>&#9673; Điều chuyển sang ô trống mới<div class='muted'>Khách nhận PIN ô mới</div></div>"
    "<div class='card'>&#9675; Bàn giao trực tiếp (nhập PIN/QR của khách)</div><div class='card'>&#9675; Niêm phong đưa về Hub</div>"
    "<div class='card'>&#9675; Sửa tại chỗ</div><div class='card'>&#9675; Khoá ô bảo trì</div>"
    "<div class='lbl'>Ảnh sau sửa</div><div class='row'><div class='stat' style='height:50px'></div><div class='in' style='height:50px;text-align:center;padding-top:14px'>+</div></div>"
    "<div class='btn'>Hoàn tất phiếu</div></div>")

# 12 Drone technician loading
SCREENS["m12-loading"] = phone("Điều phối drone", "<div class='tabs'><div class='on'>Điều phối (2)</div><div>Việc của tôi</div><div>Đội bay</div><div>Sự cố</div></div>"
    "<div class='card'><b>ORD-…0051 · CAB-01 → CAB-TU01</b><span class='muted'>750 g · Tài liệu · đã bỏ kiện</span></div>",
    overlay="<div class='dim'></div><div class='sheet' style='height:540px'><div class='handle'></div><b>Xác nhận nạp hàng · Drone DR-02</b>"
    + field("Khối lượng cân thực tế (g)", "742") + field("Mã niêm phong (hệ thống cấp)", "NP-261021-K7Q2") +
    "<div class='lbl'>Kiểm tra</div><div class='card'>&#9745; Kiện khớp đơn</div><div class='card'>&#9745; Kiện đã cố định chắc chắn</div><div class='card'>&#9745; Khoang hàng đã khoá</div>"
    + field("Ghi chú", ph="Tùy chọn") + "<div class='btn'>Xác nhận nạp</div></div>")

# 13 AI assistant
SCREENS["m13-assistant"] = phone("Trợ lý AI", "<div class='bubble me'>Đơn ORD-…0042 của tôi khi nào hết hạn lấy?</div>"
    "<div class='bubble bot'>Đơn ORD-20261021-0042 đang ở trạng thái STORING tại tủ CAB-TU01, ô 3. Hạn lấy hàng là 18:00 ngày 23/10/2026. Sau hạn, người nhận phải trả phí quá giờ trước khi mở ô.<div class='cite'>[1] Đơn hàng của bạn · [2] Quy định gửi hàng</div></div>"
    "<div class='bubble me'>Phí quá giờ tính thế nào?</div>"
    "<div class='bubble bot'>Phí quá hạn là 500 đ mỗi giờ, tối đa 50.000 đ và không vượt 50 % giá đơn.<div class='cite'>[1] Quy định gửi hàng</div></div>"
    "<div style='position:absolute;bottom:66px;left:14px;right:14px' class='row'><div class='in' style='flex:5'>Nhập câu hỏi…</div><div class='btn' style='margin:0;flex:1'>Gửi</div></div>", nav=3, back=False)

# 14 Wallet withdraw
SCREENS["m14-withdraw"] = phone("Rút tiền", "<div class='card' style='text-align:center'><span class='muted'>Số dư ví</span><div style='font-size:24px;font-weight:bold;color:#D84315'>120.000 đ</div></div>" +
    field("Ngân hàng", "MB Bank", sel=True) + field("Số tài khoản", "0123456789") + field("Tên chủ tài khoản", "NGUYEN VAN A") + field("Số tiền", "50.000") +
    "<div class='muted' style='margin-top:6px'>Số tiền rút tối thiểu là 10.000 đ. Ví bị trừ ngay, yêu cầu chờ admin duyệt.</div>"
    "<div class='btn'>Gửi yêu cầu rút tiền</div><div class='btn3'>Yêu cầu rút tiền</div>")

# K1 Kiosk
SCREENS["k01-kiosk-pin"] = ("<div class='kiosk'><div style='display:flex;height:100%'>"
    "<div style='flex:1;padding:30px'><div style='font-size:26px;font-weight:bold;color:#D84315'>LOCK.R</div><div class='muted'>CAB-TU01 · Lock.R FPT University</div>"
    "<div style='font-size:22px;font-weight:bold;margin:30px 0 10px'>Mở tủ / Nhận đồ</div><div class='muted'>Nhập mã PIN 6 số hoặc đưa mã QR vào camera</div>"
    "<div style='display:flex;gap:10px;margin:20px 0'>" + "".join("<div class='key' style='width:56px'>" + c + "</div>" for c in "482•••") + "</div>"
    "<div class='card' style='background:#FFEBEE;border-color:#EF9A9A;color:#C62828'>Mã PIN không hợp lệ (còn 3 lần thử)</div>"
    "<div class='btn3' style='width:200px'>&#8592; Quay lại</div></div>"
    "<div style='width:380px;padding:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:10px;align-content:center'>" +
    "".join(f"<div class='key'>{k}</div>" for k in "123456789") + "<div class='key'>Xoá</div><div class='key'>0</div><div class='key' style='background:#D84315;color:#fff;font-size:16px'>Mở ô</div></div>"
    "</div></div>", 1064, 640)

# A1 Admin locker layout
SCREENS["a01-locker-layout"] = browser("/admin/lockers/7", "Lockers",
    "<h2>CAB-TU01 · Lock.R FPT University <span class='badge b-g'>ACTIVE</span></h2>"
    "<div class='toolbar'><div class='btn2' style='margin:0'>+ Add boxes</div><div class='btn2' style='margin:0'>Batch delete</div><div class='btn2' style='margin:0'>GPS location</div><div class='btn2' style='margin:0'>Print box QR</div></div>"
    "<div style='display:flex;gap:20px;margin-top:12px'><div style='flex:1'><b>Box map</b>" +
    boxgrid(4, [("1 STD", "occ"), ("2 STD", "free"), ("3 STD", "occ"), ("4 XL", "res"), ("5 STD", "free"), ("6 STD", "fault"), ("7 XL", "free"), ("D1 DRONE", "free")]).replace("height:34px", "height:60px") +
    "<div class='muted'>Free · Reserved · Occupied · Fault</div>"
    "<table><tr><th>Box</th><th>Size</th><th>Status</th><th>Order</th><th>Action</th></tr>"
    "<tr><td>6</td><td>STANDARD</td><td><span class='badge b-r'>FAULT</span></td><td>—</td><td>View ticket</td></tr>"
    "<tr><td>4</td><td>XL</td><td><span class='badge b-o'>RESERVED</span></td><td>ORD-…0060</td><td>—</td></tr></table></div>"
    "<div style='width:330px'><div class='card'><b>Responsible technician</b>nhatkse182290 <span class='muted'>(Locker Technician)</span><div class='btn2'>Change</div></div>"
    "<div class='card'><b>Locker controller (Pi)</b>MAC d8:3a:dd:…:21 · firmware f76eaaa<div class='muted'>Online · last seen 12 s ago</div><div class='btn2'>Test open box…</div><div class='btn3'>Unassign</div></div>"
    "<div class='card'><b>Connection log</b><div class='muted'>10:31 ONLINE · 09:58 OFFLINE · 09:40 ONLINE</div></div></div></div>")

# A2 Admin refunds
SCREENS["a02-refunds"] = browser("/admin/refunds", "Refunds",
    "<h2>Refunds &amp; Withdrawals</h2><div class='toolbar'><span class='chip on'>Pending (4)</span><span class='chip'>Approved</span><span class='chip'>Rejected</span><span class='chip'>Withdrawals</span><div class='in' style='margin-left:auto'>Search order / phone…</div></div>"
    "<div style='display:flex;gap:20px'><div style='flex:1'><table><tr><th>Order</th><th>Customer</th><th>Amount</th><th>Reason</th><th>Requested</th><th>Status</th></tr>"
    "<tr style='background:#FFF8F5'><td>ORD-…0033</td><td>0901 234 567</td><td>18.000 đ</td><td>Drone flight failed</td><td>21/10 10:40</td><td><span class='badge b-o'>PENDING</span></td></tr>"
    "<tr><td>ORD-…0029</td><td>0912 000 111</td><td>15.000 đ</td><td>Tủ lỗi không mở được</td><td>21/10 09:12</td><td><span class='badge b-o'>PENDING</span></td></tr>"
    "<tr><td>ORD-…0024</td><td>0987 654 321</td><td>20.000 đ</td><td>Cancelled after payment</td><td>20/10 17:30</td><td><span class='badge b-o'>PENDING</span></td></tr></table></div>"
    "<div style='width:340px' class='card'><b>Refund ORD-…0033</b><div class='muted'>Bank: MB Bank · 0123456789 · NGUYEN VAN A</div><div class='muted'>Customer evidence: 1 photo</div>"
    + field("Bank transfer reference", ph="Optional") + "<div class='lbl'>Transfer receipt</div><div class='in' style='height:60px;text-align:center;padding-top:20px'>Upload image</div>"
    "<div class='btn'>Approve &amp; transferred</div><div class='btn2'>Reject with reason</div></div></div>")

# A3 Business settings
SCREENS["a03-business-settings"] = browser("/admin/business-settings", "Business Settings",
    "<h2>Business Settings</h2><div class='toolbar'><span class='chip on'>Order</span><span class='chip'>Locker</span><span class='chip'>Payment</span><span class='chip'>IoT</span><span class='chip'>Auth</span><span class='chip'>Loyalty</span><span class='chip'>Assistant</span></div>"
    "<table><tr><th>Group</th><th>Rule</th><th>Value</th><th>Default</th><th>Last change</th><th></th></tr>"
    "<tr><td>Pricing</td><td>Send parcel fee</td><td><div class='in v' style='width:110px'>15000 VND</div></td><td>15000</td><td>—</td><td>Reset</td></tr>"
    "<tr><td>Pricing</td><td>Standard box rental rate</td><td><div class='in v' style='width:110px'>5000 VND/h</div></td><td>5000</td><td>—</td><td>Reset</td></tr>"
    "<tr><td>Deadlines</td><td>Send pickup deadline</td><td><div class='in v' style='width:110px'>48 h</div></td><td>48</td><td>—</td><td>Reset</td></tr>"
    "<tr><td>Deadlines</td><td>Auto-cancel unpaid order after</td><td><div class='in v' style='width:110px'>15 min</div></td><td>15</td><td>19/10 huynqbse180211</td><td>Reset</td></tr>"
    "<tr><td>Drone</td><td>Max route between lockers</td><td><div class='in v' style='width:110px'>5000 m</div></td><td>5000</td><td>—</td><td>Reset</td></tr>"
    "<tr><td>Drone</td><td>Suspend flights</td><td><div class='in v' style='width:110px'>Off</div></td><td>Off</td><td>—</td><td>Reset</td></tr>"
    "<tr><td>Voucher</td><td>Max vouchers per order</td><td><div class='in v' style='width:110px'>1</div></td><td>1</td><td>—</td><td>Reset</td></tr></table>"
    "<div class='btn' style='width:160px'>Save changes</div>")

# A4 Admin users
SCREENS["a04-users"] = browser("/admin/users", "Users",
    "<h2>Users</h2><div class='toolbar'><div class='in'>Search name / email / phone…</div><div class='in sel' style='width:150px'>All roles</div><div class='in sel' style='width:150px'>All status</div><div class='btn' style='margin:0 0 0 auto;width:150px'>+ Create staff</div></div>"
    "<table><tr><th>Name</th><th>Email</th><th>Phone</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr>"
    "<tr><td>Nguyễn Văn A</td><td>a@example.com</td><td>0901 234 567</td><td>CUSTOMER</td><td><span class='badge b-g'>ACTIVE</span></td><td>02/10/2026</td><td>View · Lock · Delete</td></tr>"
    "<tr><td>Trần Kim Nha</td><td>nhatkse182290@fpt.edu.vn</td><td>—</td><td>LOCKER_TECHNICIAN</td><td><span class='badge b-g'>ACTIVE</span></td><td>15/09/2026</td><td>View · Lock</td></tr>"
    "<tr><td>Drone Tech 01</td><td>dt01@lockr.vn</td><td>—</td><td>DRONE_TECHNICIAN</td><td><span class='badge b-g'>ACTIVE</span></td><td>20/09/2026</td><td>View · Lock</td></tr>"
    "<tr><td>Lê Văn C</td><td>c@example.com</td><td>0977 111 222</td><td>CUSTOMER</td><td><span class='badge b-r'>LOCKED</span></td><td>01/10/2026</td><td>View · Unlock</td></tr></table>")

# A5 Drone incident
SCREENS["a05-drone-incident"] = browser("/admin/drone-incidents/12", "Drone Incidents",
    "<h2>INC-261020-0012 · Parcel drop <span class='badge b-o'>RECOVERY_IN_PROGRESS</span></h2>"
    "<div style='display:flex;gap:20px'><div style='flex:1'><div class='map' style='height:200px'><div style='position:absolute;left:45%;top:45%' class='badge b-r'>Drop point 10.8411, 106.8098</div></div>"
    "<div class='card'><b>Timeline</b><div class='tl'><div class='done'>Reported by drone technician · 10:12</div><div class='done'>Delivery stopped, RTL requested · 10:12</div><div class='done'>Recovery assigned to nhatkse182290 · 10:20</div><div class='now'>Evidence submitted (3 photos, GPS) · 10:55</div><div>Admin verification</div><div>Resolution: redelivery / compensation</div></div></div></div>"
    "<div style='width:360px'><div class='card'><b>Order ORD-…0051</b><div class='muted'>DR-02 · CAB-01 → CAB-TU01 · declared 300.000 đ</div></div>"
    "<div class='card'><b>Resolution proposal</b>" + field("Type", "Free redelivery", sel=True) + field("Compensation (60 %)", "180.000 đ") +
    "<div class='btn'>Verify &amp; send to customer</div><div class='btn2'>Close incident</div></div></div></div>")


def render():
    os.makedirs(OUT, exist_ok=True)
    for name, (inner, w, h) in SCREENS.items():
        hp = os.path.join(OUT, name + ".html")
        open(hp, "w", encoding="utf-8").write(page(inner, w, h))
        png = os.path.join(OUT, name + ".png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size={w},{h}", f"--screenshot={png}", "file:///" + hp.replace(os.sep, "/")],
                       check=True, capture_output=True)
        print("ok", name)


if __name__ == "__main__":
    render()
