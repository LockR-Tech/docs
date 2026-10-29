"""Helpers shared by the detailed-design feature definitions."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "erd"))
import erd_data  # noqa: E402

ENT = erd_data.ENT
JT = {"bigint": "Long", "bigserial": "Long", "int": "Integer", "integer": "Integer", "boolean": "Boolean",
      "timestamp": "LocalDateTime", "date": "LocalDate", "double": "Double", "text": "String", "jsonb": "String",
      "uuid": "UUID"}


def jtype(t):
    t = t.lower()
    if t.startswith("varchar") or t.startswith("char"):
        return "String"
    if t.startswith("decimal") or t.startswith("numeric"):
        return "BigDecimal"
    return JT.get(t, "String")


def camel(n):
    p = n.split("_")
    return p[0] + "".join(x.title() for x in p[1:])


def E(entity, n=9, pick=None):
    """Entity class box: (kind, attrs, methods) using real columns."""
    fields = ENT[entity]["fields"]
    if pick:
        fields = [f for f in fields if f["name"] in pick]
    attrs = [f"-{f.get('field') or camel(f['name'])}: {jtype(f['type'])}" for f in fields[:n]]
    if len(ENT[entity]["fields"]) > len(attrs):
        attrs.append(f"… ({len(ENT[entity]['fields']) - len(attrs)} more)")
    return ("entity", attrs, ["+getters() / setters()"])


def C(kind, methods, attrs=None):
    """methods: list of (signature, description) or plain signature strings."""
    sigs = [m[0] if isinstance(m, tuple) else m for m in methods]
    return (kind, attrs or [], ["+" + s for s in sigs]), [m for m in methods if isinstance(m, tuple)]


FEATURES = []


def feature(fid, title, intro, classes, rows, edges, seqs, actor_note=""):
    """classes: name -> (box, spec) as returned by C()/E() (E has no spec)."""
    boxes, specs = {}, []
    for n, v in classes.items():
        if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], tuple):
            boxes[n] = v[0]
            if v[1] and v[0][0] in ("controller", "service", "component"):
                specs.append((n, v[1]))
        else:
            boxes[n] = v
    FEATURES.append(dict(id=fid, title=title, intro=intro, boxes=boxes, rows=rows, edges=edges, seqs=seqs,
                         specs=specs))
