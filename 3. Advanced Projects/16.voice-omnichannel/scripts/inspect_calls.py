import sqlite3
import zlib
import re

conn = sqlite3.connect("/var/lib/docker/volumes/n8n_storage/_data/database.sqlite")
c = conn.cursor()
for eid in [17, 18, 19, 20, 21]:
    c.execute("SELECT data FROM execution_data WHERE executionId = ?", (eid,))
    row = c.fetchone()
    if not row:
        continue
    raw = row[0]
    if isinstance(raw, bytes):
        try:
            raw = zlib.decompress(raw).decode()
        except Exception:
            raw = raw.decode(errors="ignore")
    print("=== EID:", eid)
    for m in re.finditer(r'"endedReason":"([^"]+)"', raw):
        print("  endedReason:", m.group(1))
    for m in re.finditer(r'"transcript":"([^"]+)"', raw):
        print("  transcript:", m.group(1))
    for m in re.finditer(r'"error":\{"message":"([^"]+)"', raw):
        print("  node error:", m.group(1))
