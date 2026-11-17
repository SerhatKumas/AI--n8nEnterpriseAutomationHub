import sqlite3
import json
import uuid

with open("/tmp/workflow_12.json") as f:
    wf = json.load(f)

db_path = "/var/lib/docker/volumes/n8n_storage/_data/database.sqlite"
conn = sqlite3.connect(db_path)
c = conn.cursor()

new_version_id = str(uuid.uuid4())
wf_id = "b2b-lead-hunter-tr-00012"
wf_name = wf.get("name", "Project 12 : B2B Local Business Website Lead Hunter & Cold Email Outreach Engine")
nodes_json = json.dumps(wf["nodes"])
conns_json = json.dumps(wf["connections"])
settings_json = json.dumps(wf.get("settings", {}))
authors_json = json.dumps(["Serhat Kumas"])

# 1. Insert into workflow_history
c.execute("""
INSERT INTO workflow_history (versionId, workflowId, authors, nodes, connections, name, autosaved, nodeGroups)
VALUES (?, ?, ?, ?, ?, ?, 0, '[]')
""", (new_version_id, wf_id, authors_json, nodes_json, conns_json, wf_name))

# 2. Update workflow_published_version
c.execute("""
UPDATE workflow_published_version 
SET publishedVersionId = ?, updatedAt = datetime('now')
WHERE workflowId = ?
""", (new_version_id, wf_id))

# 3. Update workflow_entity
c.execute("""
UPDATE workflow_entity
SET versionId = ?, activeVersionId = ?, nodes = ?, connections = ?, settings = ?, updatedAt = datetime('now')
WHERE id = ?
""", (new_version_id, new_version_id, nodes_json, conns_json, settings_json, wf_id))

conn.commit()
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.commit()
print(f"Successfully published new version {new_version_id} for {wf_id}!")
conn.close()
