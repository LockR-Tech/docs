"""3. Detailed design: class + sequence diagrams for every feature; writes features.json for the docx builder.

Method signatures of controllers, services, components, Feign clients and repositories are taken from the Java
code (code_sig); methods inherited from Spring Data (save, findById, ...) are written with the entity type of the
repository. ApiResponse is not drawn as a class: it only appears in the return types, as in the code."""
import json, os, re
import feat_common
import feat_1_accounts, feat_2_orders, feat_3_ops  # noqa: F401  (register features)
import code_sig as CS
from dl import class_diagram, sequence

# hand-written names that differ from the code
RENAME = {("CloudinaryMediaStorage", "signUpload"): "createUploadSignatures",
          ("DronePositionBroadcaster", "publish"): "broadcast",
          ("ChunkRepository", "insertAll"): "replace"}
SPLIT = {"getInt / getDecimal / getBoolean / getString(key)": ["getInt(key)", "getDecimal(key)", "getBoolean(key)",
                                                              "getString(key)"]}
JPA = {"save": "save(entity: {E}): {E}", "saveAndFlush": "saveAndFlush(entity: {E}): {E}",
       "saveAll": "saveAll(entities: Iterable<{E}>): List<{E}>", "findById": "findById(id: {ID}): Optional<{E}>",
       "findAllById": "findAllById(ids: Iterable<{ID}>): List<{E}>"}


def repo_types(cls, prefer):
    for f in CS._FILES.get(cls, []):
        if prefer and prefer not in f:
            continue
        m = re.search(r"JpaRepository<\s*(\w+)\s*,\s*(\w+)\s*>", open(f, encoding="utf-8").read())
        if m:
            return m.group(1), m.group(2)
    return None


def prefer_of(F, cls):
    svcs = CS.service_of(cls)
    if len(svcs) <= 1:
        return None
    users = [a for a, b, k, l in F["edges"] if b == cls] or [b for a, b, k, l in F["edges"] if a == cls]
    us = {s for u in users for s in CS.service_of(u) if len(CS.service_of(u)) == 1} & set(svcs)
    assert len(us) == 1, (F["id"], cls, svcs, us)
    return us.pop()


def unwrap(t, wrapper):
    """wrapper<X> -> X (generic arguments may be nested)."""
    while True:
        i = t.find(wrapper + "<")
        if i == -1 or (i > 0 and (t[i - 1].isalnum() or t[i - 1] == "_")):
            return t
        j, depth = i + len(wrapper) + 1, 1
        k = j
        while depth:
            depth += {"<": 1, ">": -1}.get(t[k], 0)
            k += 1
        inner = t[j:k - 1]
        t = t[:i] + ("void" if inner == "Void" else inner) + t[k:]


def no_api_response(sig):
    """The class diagrams do not show the ApiResponse envelope of common-lib: ApiResponse<X> is written X."""
    params, ret = sig.rsplit("): ", 1) if "): " in sig else (sig, None)
    if ret is None:
        return sig
    ret = unwrap(unwrap(ret, "ResponseEntity"), "ApiResponse")
    return f"{params}): {'void' if ret == 'ApiResponse' else ret}"


def sync_sig(F, cls, sig):
    return no_api_response(_sync_sig(F, cls, sig))


def _sync_sig(F, cls, sig):
    name = sig.split("(")[0]
    if (cls, name) in RENAME:
        sig = RENAME[(cls, name)] + sig[len(name):]
        name = RENAME[(cls, name)]
    prefer = prefer_of(F, cls)
    new = CS.sync(cls, sig, prefer)
    if new:
        return new
    rt = repo_types(cls, prefer)
    if rt and name in JPA:
        return JPA[name].format(E=rt[0], ID=rt[1])
    if rt and name == "findAll":
        return (f"findAll(spec: Specification<{rt[0]}>): List<{rt[0]}>" if "spec" in sig else f"findAll(): List<{rt[0]}>")
    raise SystemExit(f"{F['id']} {cls}: no method for {sig}")


# features that are no longer part of the system (wallet removed, BLE open test not documented)
REMOVED = {"wallet", "ble"}
feat_common.FEATURES[:] = [f for f in feat_common.FEATURES if f["id"] not in REMOVED]

SIG_MAP = []
for F in feat_common.FEATURES:
    for cls, (kind, attrs, methods) in list(F["boxes"].items()):
        if kind in ("entity", "external", "dto"):
            continue
        ms = []
        for m in methods:
            for s in SPLIT.get(m[1:], [m[1:]]):
                new = sync_sig(F, cls, s)
                ms.append("+" + new)
                SIG_MAP.append((F["id"], cls, s, new))
        F["boxes"][cls] = (kind, attrs, ms)
    F["specs"] = [(cls, [(sync_sig(F, cls, s), desc) for sig, desc in methods for s in SPLIT.get(sig, [sig])])
                  for cls, methods in F["specs"]]
    assert not any("ApiResponse" == n for n in F["boxes"]), F["id"]

out = []
for f in feat_common.FEATURES:
    class_diagram("cls_" + f["id"], f["rows"], f["boxes"], f["edges"])
    seqs = []
    for i, (title, parts, steps) in enumerate(f["seqs"], 1):
        name = f"seq_{f['id']}_{i}"
        sequence(name, parts, steps)
        seqs.append({"title": title, "image": name})
    out.append({"id": f["id"], "title": f["title"], "intro": f["intro"], "class_image": "cls_" + f["id"],
                "classes": [{"name": n, "kind": b[0]} for n, b in f["boxes"].items()],
                "specs": [{"cls": n, "methods": [list(m) for m in ms]} for n, ms in f["specs"]], "seqs": seqs})
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
os.makedirs(OUT, exist_ok=True)
json.dump(out, open(os.path.join(OUT, "features.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(SIG_MAP, open(os.path.join(OUT, "sig_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "features,", sum(len(f["seqs"]) for f in out), "sequence diagrams")
