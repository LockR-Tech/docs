"""For every FK column in erd_data.REL: is it NOT NULL? (JPA annotations + Flyway/SQL migrations)"""
import glob, re, json, os
from erd_data import ENT, REL
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 5, "backend")   # sibling backend repo
java = {}
for f in glob.glob(ROOT + r"\*\src\main\java\**\*.java", recursive=True):
    s = open(f, encoding="utf-8").read()
    m = re.search(r'class\s+(\w+)', s)
    if "@Entity" in s and m:
        java[m.group(1)] = s
sql = "\n".join(open(f, encoding="utf-8", errors="ignore").read() for f in glob.glob(ROOT + r"\*\src\main\resources\**\*.sql", recursive=True))


def notnull(child, col):
    tbl = ENT[child]["table"]
    fld = next(x for x in ENT[child]["fields"] if x["name"] == col)
    src = java.get(child, "")
    ann_hit = None
    if src:
        m = re.search(r'((?:\s*@[\w.]+(?:\((?:[^()]|\([^()]*\))*\))?)*)\s*(?:private|protected)\s+[\w<>\[\], .?]+?\s+' + re.escape(fld.get("field") or "") + r'\s*[;=]', src)
        if m:
            a = m.group(1)
            ann_hit = bool(re.search(r'nullable\s*=\s*false|optional\s*=\s*false|@NotNull', a))
            prim = re.search(r'(?:private|protected)\s+(long|int)\s+' + re.escape(fld["field"]), src)
            ann_hit = ann_hit or bool(prim)
    sql_hit = None
    for m in re.finditer(r'create\s+table\s+(?:if\s+not\s+exists\s+)?(?:\w+\.)?' + tbl + r'\s*\((.*?)\);', sql, re.S | re.I):
        cm = re.search(r'^\s*' + col + r'\s+[^,\n]*', m.group(1), re.M | re.I)
        if cm:
            sql_hit = "not null" in cm.group(0).lower() or "primary key" in cm.group(0).lower()
    for m in re.finditer(r'alter\s+table\s+(?:\w+\.)?' + tbl + r'\s+alter\s+column\s+' + col + r'\s+set\s+not\s+null', sql, re.I):
        sql_hit = True
    return bool(ann_hit) or bool(sql_hit), ann_hit, sql_hit


if __name__ == "__main__":
    res = {}
    for c, col, p, k in REL:
        nn, a, s = notnull(c, col)
        res[f"{c}.{col}"] = nn
        print(f"{c:32} {col:24} -> {p:22} {'NOT NULL' if nn else 'nullable':9} jpa={a} sql={s}")
    json.dump(res, open("fk_notnull.json", "w"), indent=1)
