"""3. Detailed design: class + sequence diagrams for every feature; writes features.json for the docx builder."""
import json, os
import feat_common
import feat_1_accounts, feat_2_orders, feat_3_ops  # noqa: F401  (register features)
from dl import class_diagram, sequence

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
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "out", "features.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(len(out), "features,", sum(len(f["seqs"]) for f in out), "sequence diagrams")
