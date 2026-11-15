"""OCR every screenshot used by Report 6 and list text that should not be published: e-mail addresses, phone
numbers, bank account numbers, GPS coordinates and bank-account holder names. Writes pii_boxes.json
({image: [[x0, y0, x1, y1, text], ...]}, not committed) for manual review / pixelation. Run: uv run --with pytesseract --with pillow python find_pii.py
"""
import json
import os
import re
import sys

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.dirname(HERE)
DOCS = os.path.abspath(os.path.join(ASSETS, "..", ".."))

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
SAFE_EMAIL = re.compile(r"(example\.com|demo\.lockr\.test|\*{2,})", re.I)
DIGITS = re.compile(r"\+?\d[\d .]{7,}\d")
COORD = re.compile(r"\b(?:8|9|1[0-9]|10[5-9])\.\d{4,}\b")
NAMES = ["TRUONG", "NGUYEN", "QUOC", "BAO", "HUY", "THAI", "BINH", "YEN", "TRAN", "KIM", "NHA", "VI"]


def used_images():
    imgs = set()
    for n in range(1, 5):
        d = json.load(open(os.path.join(ASSETS, "data", f"wf{n}.json"), encoding="utf-8"))
        for p in d["parts"]:
            for s in p["steps"]:
                imgs.update(s["images"])
    imgs.update(["png/install/i05-admin-login.png", "png/install/i06-mobile-login.png", "png/install/i07-admin-otp.png",
                 "png/i01-github-release-apk.png", "png/i02-swagger-ui.png", "png/i03-github-actions-deploy.png"])
    return sorted(imgs)


def resolve(p):
    if os.path.isabs(p):
        return p
    for b in (DOCS, ASSETS):
        if os.path.exists(os.path.join(b, p)):
            return os.path.join(b, p)
    raise FileNotFoundError(p)


out = {}
for img in used_images():
    im = Image.open(resolve(img)).convert("RGB")
    scale = 2 if im.width < 1000 else 1
    big = im.resize((im.width * scale, im.height * scale)) if scale > 1 else im
    data = pytesseract.image_to_data(big, lang="eng", output_type=pytesseract.Output.DICT, config="--psm 11")
    words = [(data["text"][i].strip(), data["left"][i] // scale, data["top"][i] // scale,
              (data["left"][i] + data["width"][i]) // scale, (data["top"][i] + data["height"][i]) // scale,
              data["block_num"][i], data["line_num"][i], data["par_num"][i])
             for i in range(len(data["text"])) if data["text"][i].strip()]
    hits = []
    for w in words:
        t = w[0]
        reason = None
        if EMAIL.search(t) and not SAFE_EMAIL.search(t):
            reason = "email"
        elif COORD.search(t):
            reason = "coord"
        else:
            digits = re.sub(r"\D", "", t)
            if len(digits) >= 9 and not re.match(r"^20\d{6}", digits) and not t.startswith("ORD") and not t.startswith("RPT"):
                reason = "number"
        if reason:
            hits.append([w[1], w[2], w[3], w[4], f"{reason}: {t}"])
    # uppercase full names (bank account holder)
    seq = [w for w in words if w[0].isupper() and w[0].isalpha() and w[0] in NAMES]
    if len(seq) >= 3:
        for w in seq:
            hits.append([w[1], w[2], w[3], w[4], f"name: {w[0]}"])
    if hits:
        out[img] = hits
        print(img)
        for h in hits:
            print("   ", h)
    sys.stdout.flush()

json.dump(out, open(os.path.join(HERE, "pii_boxes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("images with hits:", len(out))
