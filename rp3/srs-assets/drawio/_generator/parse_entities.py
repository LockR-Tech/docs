import re, os, json, glob, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 5, "backend")   # sibling backend repo
TYPE = {"Long":"bigint","long":"bigint","Integer":"int","int":"int","String":"varchar","Boolean":"boolean","boolean":"boolean",
        "BigDecimal":"decimal","Double":"double","double":"double","Float":"float","LocalDateTime":"timestamp","Instant":"timestamp",
        "LocalDate":"date","LocalTime":"time","OffsetDateTime":"timestamptz","UUID":"uuid","Short":"smallint","byte[]":"bytea"}
def snake(n): return re.sub(r'(?<!^)(?=[A-Z])','_',n).lower()
out = {}
for f in glob.glob(ROOT + r"\*\src\main\java\**\*.java", recursive=True):
    src = open(f, encoding="utf-8").read()
    if "@Entity" not in src: continue
    svc = f.split(os.sep)[3]
    cls = re.search(r'class\s+(\w+)', src).group(1)
    m = re.search(r'@Table\(\s*name\s*=\s*"(\w+)"', src)
    table = m.group(1) if m else snake(cls)
    body = src[src.index("class " + cls):]
    fields = []
    # split into field declarations with preceding annotations
    for fm in re.finditer(r'((?:\s*@[\w.]+(?:\((?:[^()]|\([^()]*\))*\))?)*)\s*(?:private|protected)\s+(?!static)([\w<>\[\], .?]+?)\s+(\w+)\s*(?:=[^;]*)?;', body):
        ann, typ, name = fm.group(1), fm.group(2).strip(), fm.group(3)
        if "@Transient" in ann: continue
        col = re.search(r'@(?:Column|JoinColumn)\([^)]*name\s*=\s*"(\w+)"', ann)
        colname = col.group(1) if col else snake(name)
        rel = None
        if "@ManyToOne" in ann or "@OneToOne" in ann:
            rel = ("many-to-one" if "@ManyToOne" in ann else "one-to-one", typ)
            if not col: colname = snake(name) + "_id"
        elif "@OneToMany" in ann or "@ManyToMany" in ann or "@ElementCollection" in ann:
            continue
        length = re.search(r'length\s*=\s*(\d+)', ann)
        base = typ.split("<")[0].split(".")[-1]
        if rel: sqltype = "bigint"
        elif "@Enumerated" in ann: sqltype = "varchar" + (f"({length.group(1)})" if length else "")
        elif "columnDefinition" in ann:
            sqltype = re.search(r'columnDefinition\s*=\s*"([^"]+)"', ann).group(1).lower()
        else:
            sqltype = TYPE.get(base, "varchar" if base[0].isupper() else base)
            if sqltype == "varchar": sqltype += f"({length.group(1) if length else 255})"
            if sqltype == "decimal":
                p = re.search(r'precision\s*=\s*(\d+)', ann); s = re.search(r'scale\s*=\s*(\d+)', ann)
                if p: sqltype = f"decimal({p.group(1)},{s.group(1) if s else 0})"
        fields.append({"name": colname, "type": sqltype, "pk": "@Id" in ann, "rel": rel, "field": name})
    out[cls] = {"service": svc, "table": table, "fields": fields}
json.dump(out, open("entities.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for c, e in sorted(out.items(), key=lambda x: (x[1]["service"], x[0])):
    print(f'{e["service"]:22} {e["table"]:34} {len(e["fields"]):3}  ' + ", ".join(fl["name"] for fl in e["fields"] if fl["rel"] or fl["name"].endswith("_id")))
