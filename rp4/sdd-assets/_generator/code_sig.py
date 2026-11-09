"""Read method signatures from the Java code so that the class diagrams show them exactly as written.

sync(cls_name, signature) -> signature taken from the code (UML style "name(p: Type, ...): Return"),
or None when the class / method cannot be found (the hand-written signature is kept then).
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SKIP_PARAM_TYPES = {"HttpServletRequest", "HttpServletResponse"}
_FILES = {}
for _f in glob.glob(os.path.join(ROOT, "backend", "*", "src", "main", "java", "**", "*.java"), recursive=True):
    _FILES.setdefault(os.path.basename(_f)[:-5], []).append(_f)
_CACHE = {}

MOD = r"(?:(?:public|protected|private|static|final|default|abstract|synchronized)\s+)*"
DECL = re.compile(r"^[ \t]*" + MOD + r"(?:<[^>]+>\s+)?((?:[A-Za-z_][\w.]*)(?:\s*<[^;{}()=]*?>)?(?:\[\])?)\s+(\w+)\s*\(", re.M)
KEYWORDS = {"return", "new", "else", "throw", "if", "for", "while", "switch", "catch", "case"}


def simple(t):
    t = re.sub(r"\b(?:[a-z]\w*\.)+([A-Z]\w*)", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*<\s*", "<", t)
    t = re.sub(r"\s*>", ">", t)
    return re.sub(r"\s*,\s*", ", ", t)


def split_top(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "<(":
            depth += 1
        elif ch in ">)":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out]


def strip_annotations(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"@[\w.]+\s*\((?:[^()]|\([^()]*\))*\)", " ", s)
    s = re.sub(r"@[\w.]+", " ", s)
    return re.sub(r"\bfinal\b", " ", s)


def strip_comments(src):
    """Remove // and /* */ comments; string, text-block and char literals are kept as they are."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'":
            if src.startswith('"""', i):
                j = src.find('"""', i + 3)
                j = n if j == -1 else j + 3
            else:
                j = i + 1
                while j < n and src[j] != c and src[j] != "\n":
                    j += 2 if src[j] == "\\" else 1
                j += 1
            out.append(src[i:j])
            i = j
        elif src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j == -1 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def methods(path):
    if path in _CACHE:
        return _CACHE[path]
    src = open(path, encoding="utf-8", errors="ignore").read()
    src = strip_comments(src)
    out = []
    for m in DECL.finditer(src):
        ret, name = m.group(1), m.group(2)
        if ret.split(".")[0] in KEYWORDS or name in KEYWORDS:
            continue
        i, depth = m.end(), 1
        j = i
        while depth and j < len(src):
            depth += {"(": 1, ")": -1}.get(src[j], 0)
            j += 1
        tail = src[j:j + 200].lstrip()
        if not (tail.startswith("{") or tail.startswith(";") or tail.startswith("throws")):
            continue
        params = []
        for p in split_top(strip_annotations(src[i:j - 1])):
            p = re.sub(r"\s+", " ", p).strip()
            if not p:
                continue
            typ, _, pname = p.rpartition(" ")
            typ = simple(typ.replace("...", "[]"))
            if typ not in SKIP_PARAM_TYPES:
                params.append((pname, typ))
        out.append((name, simple(ret), params))
    _CACHE[path] = out
    return out


def nparams(sig):
    inside = sig[sig.index("(") + 1:sig.rindex(")")] if "(" in sig else ""
    return len(split_top(inside)) if inside.strip() else 0


def candidates(cls, name):
    return [(f, m) for f in _FILES.get(cls, []) for m in methods(f) if m[0] == name]


def sync(cls, sig, prefer=None):
    """sig: "name(...): Ret" (without the leading +). prefer: substring of the file path (e.g. 'order-service')."""
    name = sig.split("(")[0].strip()
    cands = candidates(cls, name)
    if prefer:
        cands = [c for c in cands if prefer in c[0]] or cands
    if not cands:
        return None
    n = nparams(sig)
    exact = [c for c in cands if len(c[1][2]) == n]
    f, (nm, ret, params) = (exact or cands)[0]
    if re.fullmatch(r"[A-Z]", ret):              # generic Spring Data override (<S extends T> S save(S)): use T
        return None
    return f"{nm}({', '.join(f'{p}: {t}' for p, t in params)}): {ret}"


def service_of(cls):
    return sorted({os.path.relpath(f, os.path.join(ROOT, "backend")).split(os.sep)[0] for f in _FILES.get(cls, [])})
