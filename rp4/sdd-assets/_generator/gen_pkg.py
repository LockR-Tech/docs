"""1.2 Package diagrams: backend overview, one per microservice, admin web, mobile app, IoT controller."""
import json, os
from dl import Diagram, PKG_FRAME, PKG_GROUP, PKG, DEP

SCAN = json.load(open(os.path.join(os.path.dirname(__file__), "..", "scan.json"), encoding="utf-8"))
CW, CH = 150, 52


class Pk:
    """Package diagram on a free canvas; groups hold sub-packages in a grid."""

    def __init__(self, name, title):
        self.d = Diagram(name)
        self.title = title
        self.items = []      # (key, label, x, y, w, h, style, subs)
        self.edges = []

    def group(self, key, label, x, y, subs, cols=3, cw=CW):
        cols = max(1, min(cols, len(subs))) if subs else 1
        rows = (len(subs) + cols - 1) // cols if subs else 0
        w = 26 + cols * (cw + 22) + 4
        h = 56 + rows * (CH + 20) + (10 if subs else 30)
        self.items.append((key, label, x, y, w, h, PKG_GROUP, subs, cols, cw))
        return x, y, w, h

    def single(self, key, label, x, y, w=CW + 10, h=CH + 10):
        self.items.append((key, label, x, y, w, h, PKG, [], 1, CW))
        return x, y, w, h

    def dep(self, a, b, ex=None, en=None, pts=(), label=""):
        self.edges.append((a, b, ex, en, pts, label))

    def save(self):
        d = self.d
        mx = max(it[2] + it[4] for it in self.items) + 40
        my = max(it[3] + it[5] for it in self.items) + 40
        d.v(self.title, 0, 0, mx, my, PKG_FRAME)
        ids = {}
        for key, label, x, y, w, h, st, subs, cols, cw in self.items:
            ids[key] = d.v(label, x, y, w, h, st if key != "pad" else "text;html=1;")
            for i, s in enumerate(subs):
                r, c = divmod(i, cols)
                ids[f"{key}/{s}"] = d.v(s, x + 26 + c * (cw + 22), y + 52 + r * (CH + 20), cw, CH, PKG)
        for a, b, ex, en, pts, label in self.edges:
            st = DEP
            if ex:
                st += f"exitX={ex[0]};exitY={ex[1]};exitDx=0;exitDy=0;"
            if en:
                st += f"entryX={en[0]};entryY={en[1]};entryDx=0;entryDy=0;"
            d.e(ids[a], ids[b], st + "fontSize=10;labelBackgroundColor=#dae8fc;", label, pts=pts)
        d.save()


# ------------------------------------------------------------------ backend overview
p = Pk("pkg_backend_overview", "Backend Package Diagram (Maven multi-module)")
g1 = p.group("edge", "Edge", 40, 90, ["api-gateway", "discovery-server"], cols=1, cw=160)
g2 = p.group("svc", "Business Services", 330, 90,
             ["auth-service", "user-service", "order-service", "locker-service", "payment-service",
              "notification-service", "iot-service", "store-service", "loyalty-service", "assistant-service"], cols=2, cw=170)
g3 = p.group("lib", "common-lib", 790, 90,
             ["config", "dto", "event", "exception", "i18n", "media", "security", "settings", "util", "web"], cols=2, cw=130)
p.dep("edge", "svc", (1, 0.4), (0, 0.18), label="routes (lb://)")
p.dep("svc", "lib", (1, 0.3), (0, 0.3))
yb = max(g2[1] + g2[3], g3[1] + g3[3]) + 30
p.dep("edge", "lib", (0.5, 1), (0.5, 1), pts=[(40 + g1[2] / 2, yb), (790 + g3[2] / 2, yb)], label="depends on")
p.single("pad", "", 40, yb + 10, 1, 1)
p.save()

# ------------------------------------------------------------------ one diagram per microservice
LAYER = [("api", "API Layer", ["controller", "dto", "admin", "internal"]),
         ("app", "Application Layer", ["service", "client", "channel", "email", "chat", "knowledge", "query", "eval",
                                       "orders", "settings"]),
         ("dom", "Domain Layer", ["model"]),
         ("inf", "Infrastructure Layer", ["repository", "provider", "config"])]
SERVICES = ["auth-service", "user-service", "order-service", "locker-service", "payment-service",
            "notification-service", "iot-service", "store-service", "loyalty-service", "assistant-service"]
SERVICE_PKGS = {}
for svc in SERVICES:
    pk = sorted({c["pkg"] for c in SCAN[svc]} - {svc.split("-")[0]})
    SERVICE_PKGS[svc] = pk
    title = svc.replace("-", " ").title().replace("Iot", "IoT") + " Package Diagram"
    p = Pk("pkg_" + svc.replace("-service", ""), title)
    lay = {k: [x for x in names if x in pk] for k, _, names in LAYER}
    if not lay["dom"]:
        lay["dom"] = []
    lbl = dict((k, l) for k, l, _ in LAYER)
    y0 = 90
    A = p.group("api", lbl["api"], 40, y0, lay["api"], cols=2)
    P = p.group("app", lbl["app"], A[0] + A[2] + 90, y0, lay["app"], cols=3 if len(lay["app"]) > 4 else 2)
    y1 = y0 + max(A[3], P[3]) + 90
    Dm = p.group("dom", lbl["dom"], 40, y1, lay["dom"] or ["model (JDBC rows)"], cols=2)
    I = p.group("inf", lbl["inf"], P[0], y1, lay["inf"], cols=2)
    L = p.single("lib", "common-lib", P[0], y1 + max(Dm[3], I[3]) + 70, 180)
    gap = y0 + max(A[3], P[3]) + 45
    p.dep("api", "app", (1, 40 / A[3]), (0, 40 / P[3]))
    p.dep("app", "dom", (0.12, 1), (0.6, 0), pts=[(P[0] + 0.12 * P[2], gap), (40 + 0.6 * Dm[2], gap)])
    p.dep("app", "inf", (0.5, 1), (0.5, 0), pts=[(P[0] + 0.5 * P[2], gap + 15), (I[0] + 0.5 * I[2], gap + 15)])
    p.dep("inf", "dom", (0, 40 / I[3]), (1, 40 / Dm[3]))
    rx = max(P[0] + P[2], I[0] + I[2]) + 30
    p.dep("app", "lib", (1, 0.5), (1, 0.5), pts=[(rx, P[1] + P[3] / 2), (rx, L[1] + L[3] / 2)])
    if "dto" in lay["api"] and "controller" in lay["api"]:
        p.dep("api/controller", "api/dto")
    p.save()

# ------------------------------------------------------------------ admin web (frontend/fe/src)
p = Pk("pkg_admin_web", "Admin Web Application Package Diagram (frontend/fe/src)")
R = p.group("routes", "routes", 40, 90, ["app-router", "protected-route", "routes-config"], cols=3, cw=130)
PG = p.group("pages", "pages", 40, 290, ["Admin", "auth", "Error", "RootLayout"], cols=4, cw=120)
CMP = p.group("components", "components", 40, 500, ["ui", "shared"], cols=2, cw=120)
ST = p.group("stores", "stores", 660, 290, ["apis", "baseApi", "store"], cols=3, cw=110)
HK = p.single("hooks", "hooks", 360, 520)
CT = p.single("context", "context", 560, 520)
LB = p.single("lib", "lib", 760, 520)
SC = p.single("schemas", "schemas", 700, 110)
TY = p.single("types", "types", 900, 110)
CO = p.single("constants", "constants", 960, 520)
UT = p.single("utils", "utils", 1100, 300)
p.dep("routes", "pages", (0.5, 1), (0.5, 0))
p.dep("pages", "components", (0.3, 1), (0.5, 0))
p.dep("pages", "hooks", (0.72, 1), (0.5, 0))
p.dep("pages", "context", (0.92, 1), (0.5, 0))
p.dep("pages", "stores", (1, 0.5), (0, 0.5))
p.dep("pages", "schemas", (0.95, 0), (0, 0.5), pts=[(40 + PG[2] * 0.95, 140)])
p.dep("stores", "types", (0.6, 0), (0.5, 1))
p.dep("stores", "utils", (1, 0.5), (0, 0.5))
p.dep("stores", "constants", (0.85, 1), (0.5, 0))
p.dep("hooks", "lib", (0.5, 1), (0.5, 1), pts=[(445, 620), (845, 620)])
p.save()

# ------------------------------------------------------------------ mobile app (lib/)
p = Pk("pkg_mobile_app", "Mobile Application Package Diagram (mobile/lib)")
MN = p.single("main", "main.dart · injection_container", 40, 90, 260, 62)
F = p.group("features", "features", 40, 210,
            ["auth", "home", "stores", "locker", "orders", "payment", "wallet", "transactions", "promotions", "vouchers",
             "delegations", "qr_login", "notifications", "profile", "subscription", "drone_delivery", "drone_mission",
             "drone_telemetry", "maintenance", "locker_ops", "assistant"], cols=4, cw=128)
C = p.group("core", "core", F[0] + F[2] + 90, 210,
            ["network", "routing", "services", "config", "constants", "domain", "enums", "errors", "media",
             "presentation", "theme", "utils"], cols=3, cw=112)
SH = p.single("shared", "shared (widgets, icons, utils)", C[0], C[1] + C[3] + 70, 260, 62)
p.dep("main", "features", (0.5, 1), (0.1, 0))
p.dep("main", "core", (1, 0.5), (0.5, 0), pts=[(C[0] + C[2] / 2, 121)])
p.dep("features", "core", (1, 0.3), (0, 0.3))
p.dep("features", "shared", (0.7, 1), (0, 0.5), pts=[(40 + F[2] * 0.7, SH[1] + 31)])
p.save()

# feature module (clean architecture inside each feature)
p = Pk("pkg_mobile_feature", "Mobile Feature Module Package Diagram (lib/features/<feature>)")
PR = p.group("pres", "presentation", 40, 90, ["pages", "providers", "widgets"], cols=3, cw=120)
AP = p.group("appl", "application", 40, 300, ["use_cases"], cols=1, cw=140)
DO = p.group("domain", "domain", 330, 300, ["entities", "repositories"], cols=2, cw=120)
IN = p.group("infra", "infrastructure", 40, 500, ["data_sources", "models", "repositories"], cols=3, cw=120)
CN = p.single("core", "core/network (dio ApiClient)", 660, 520, 230, 62)
p.dep("pres", "appl", (0.2, 1), (0.5, 0))
p.dep("appl", "domain", (1, 0.5), (0, 0.5))
p.dep("pres", "domain", (0.8, 1), (0.5, 0))
p.dep("infra", "domain", (0.85, 0), (0.5, 1), pts=[(40 + IN[2] * 0.85, 460), (330 + DO[2] / 2, 460)], label="implements")
p.dep("infra", "core", (1, 0.5), (0, 0.5))
p.save()

# ------------------------------------------------------------------ IoT locker controller (iot/)
p = Pk("pkg_iot_controller", "IoT Locker Controller Package Diagram (iot/)")
MP = p.single("main", "main.py", 40, 90)
SV = p.group("services", "services", 40, 210,
             ["locker_service", "heartbeat_service", "discovery_service", "setup_handler", "ble_service",
              "ble_gatt_service", "ble_open_token", "control_log"], cols=4, cw=130)
INF = p.group("infra", "infracstructure", 40, 450,
              ["mqtt_client", "serial_manager", "database", "cabinet_state", "config_api", "service_panel", "wifi"], cols=4, cw=130)
HW = p.group("hw", "hardware", 720, 450, ["factory", "gpio_locker", "rpi_locker", "lid_controller", "gpio_pins"], cols=2, cw=120)
DM = p.single("domain", "domain (models, enums)", 760, 90, 200, 62)
CF = p.single("config", "config (settings, wiring)", 1000, 90, 200, 62)
UI = p.group("ui", "ui (Kiosk React)", 720, 210, ["screens", "components", "api.js"], cols=3, cw=110)
AR = p.single("arduino", "arduino/locker_controller", 1000, 800, 220, 62)
DR = p.single("drone", "drone-iot/lockr_drone", 40, 800, 220, 62)
p.dep("main", "services", (0.5, 1), (0.1, 0))
p.dep("services", "infra", (0.3, 1), (0.3, 0))
p.dep("services", "hw", (1, 0.85), (0.2, 0), pts=[(720 + HW[2] * 0.2, 210 + SV[3] * 0.85)])
p.dep("services", "domain", (0.85, 0), (0, 0.5), pts=[(40 + SV[2] * 0.85, 121)])
p.dep("infra", "config", (1, 0.2), (0.5, 1), pts=[(690, 450 + INF[3] * 0.2), (690, 180), (1100, 180)])
p.dep("hw", "arduino", (1, 0.6), (0.5, 0), pts=[(1110, 450 + HW[3] * 0.6)], label="RS485")
p.dep("ui", "infra", (0.3, 1), (0.95, 0), pts=[(720 + UI[2] * 0.3, 425), (40 + INF[2] * 0.95, 425)], label="HTTP local API")
p.save()
