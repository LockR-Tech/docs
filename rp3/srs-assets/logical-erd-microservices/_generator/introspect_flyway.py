"""Chạy toàn bộ Flyway migration của từng service vào một Postgres nhúng tạm (pgserver) rồi đọc lại schema thật.
Cần Python 3.12 + `pip install pgserver psycopg2-binary` (pgserver có sẵn pgvector). Thư mục dữ liệu Postgres tạm đặt
trong %TEMP%, xoá sau khi chạy. Ghi ra physical_schema.json: {db: {"service":…, "tables": {tên: {"columns": [...], "pk": [...], "fks": [...], "uniques": [...],
"indexes": [...], "checks": [...]}}}}"""
import json
import os
import re
import shutil
import sys
import tempfile

import pgserver
import psycopg2

BACKEND = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 5, "backend"))  # repo backend cạnh docs
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(tempfile.gettempdir(), "lockr-physical-pgdata")
SERVICES = ["auth", "user", "store", "locker", "iot", "order", "payment", "loyalty", "notification", "assistant"]

shutil.rmtree(DATA, ignore_errors=True)
srv = pgserver.get_server(DATA, cleanup_mode="stop")
uri = srv.get_uri()
print("postgres:", uri.split("@")[-1])


def vnum(name):
    return int(re.match(r"V(\d+)__", name).group(1))


def connect(db):
    c = psycopg2.connect(uri.rsplit("/", 1)[0] + "/" + db)
    c.autocommit = True
    return c


root = connect("postgres")
out = {}
for s in SERVICES:
    db = f"{s}_db"
    root.cursor().execute(f'DROP DATABASE IF EXISTS "{db}"')
    root.cursor().execute(f'CREATE DATABASE "{db}"')
    mig = os.path.join(BACKEND, f"{s}-service", "src", "main", "resources", "db", "migration")
    files = sorted((f for f in os.listdir(mig) if f.endswith(".sql")), key=vnum)
    yml = open(os.path.join(BACKEND, f"{s}-service", "src", "main", "resources", "application.yml"), encoding="utf-8").read()
    m = re.search(r"default-schema:\s*(\w+)", yml)
    schema = m.group(1) if m else "public"     # assistant-service: container pgvector riêng, schema public   # Flyway: create-schemas + default-schema
    conn = connect(db)
    conn.cursor().execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"; SET search_path TO "{schema}"')
    for f in files:
        sql = open(os.path.join(mig, f), encoding="utf-8").read()
        try:
            conn.cursor().execute(sql)          # Flyway chạy mỗi file trong một giao dịch – ở đây chạy cả file một lần
        except Exception as ex:
            print(f"  LỖI {db} {f}: {str(ex).splitlines()[0]}")
            sys.exit(1)
    cur = conn.cursor()
    cur.execute("""select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
                   where n.nspname=%s and c.relkind in ('r','p') order by c.relname""", (schema,))
    tables = [r[0] for r in cur.fetchall()]
    info = {}
    for t in tables:
        q = f'"{schema}"."{t}"'
        cur.execute("""select a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull,
                              pg_get_expr(d.adbin, d.adrelid), a.attidentity
                       from pg_attribute a left join pg_attrdef d on d.adrelid=a.attrelid and d.adnum=a.attnum
                       where a.attrelid=%s::regclass and a.attnum>0 and not a.attisdropped order by a.attnum""", (q,))
        cols = [{"name": n, "type": ty, "notnull": nn, "default": df, "identity": idn} for n, ty, nn, df, idn in cur.fetchall()]
        cur.execute("""select con.contype, con.conname, pg_get_constraintdef(con.oid),
                              array(select a.attname from unnest(con.conkey) k join pg_attribute a
                                    on a.attrelid=con.conrelid and a.attnum=k order by array_position(con.conkey, k)),
                              cf.relname,
                              array(select a.attname from unnest(con.confkey) k join pg_attribute a
                                    on a.attrelid=con.confrelid and a.attnum=k order by array_position(con.confkey, k)),
                              con.confdeltype
                       from pg_constraint con left join pg_class cf on cf.oid=con.confrelid
                       where con.conrelid=%s::regclass order by con.conname""", (q,))
        pk, fks, uniq, checks = [], [], [], []
        for typ, name, defn, cols_, ftab, fcols, deltype in cur.fetchall():
            if typ == "p":
                pk = list(cols_)
            elif typ == "f":
                fks.append({"name": name, "cols": list(cols_), "ref": ftab, "ref_cols": list(fcols),
                            "on_delete": {"a": "NO ACTION", "r": "RESTRICT", "c": "CASCADE", "n": "SET NULL", "d": "SET DEFAULT"}[deltype]})
            elif typ == "u":
                uniq.append({"name": name, "cols": list(cols_)})
            elif typ == "c":
                checks.append({"name": name, "def": defn})
        cur.execute("""select i.relname, pg_get_indexdef(ix.indexrelid), ix.indisunique, ix.indisprimary,
                              exists(select 1 from pg_constraint c where c.conindid=ix.indexrelid)
                       from pg_index ix join pg_class i on i.oid=ix.indexrelid
                       where ix.indrelid=%s::regclass order by i.relname""", (q,))
        idx = [{"name": n, "def": df, "unique": u} for n, df, u, p, iscon in cur.fetchall() if not p and not iscon]
        info[t] = {"columns": cols, "pk": pk, "fks": fks, "uniques": uniq, "indexes": idx, "checks": checks}
    out[db] = {"service": f"{s}-service", "schema": schema, "migrations": len(files), "tables": info}
    print(f"{db}: {len(files)} migration, {len(tables)} bảng: {', '.join(tables)}")
    conn.close()
json.dump(out, open(os.path.join(HERE, "physical_schema.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ghi", os.path.join(HERE, "physical_schema.json"))
srv.cleanup()
shutil.rmtree(DATA, ignore_errors=True)
