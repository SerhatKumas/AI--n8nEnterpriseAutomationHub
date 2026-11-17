import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "/var/lib/docker/volumes/n8n_storage/_data/database.sqlite"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

with open("/tmp/unified.json") as f:
    wf = json.load(f)

wf_id = wf["id"]
wf_name = wf["name"]
nodes_str = json.dumps(wf["nodes"])
connections_str = json.dumps(wf["connections"])
now = datetime.now(timezone.utc).isoformat()

# Delete old workflows
old_ids = ['vapi-voice-tools-00016', 'vapi-end-of-call-00016', 'project-16-voice-omnichannel']
for old_id in old_ids:
    c.execute("DELETE FROM workflow_entity WHERE id = ?", (old_id,))
    c.execute("DELETE FROM shared_workflow WHERE workflowId = ?", (old_id,))
    c.execute("DELETE FROM webhook_entity WHERE workflowId = ?", (old_id,))
    c.execute("DELETE FROM workflow_history WHERE workflowId = ?", (old_id,))
    c.execute("DELETE FROM workflow_published_version WHERE workflowId = ?", (old_id,))

version_id = "v-unified-001"

# Insert unified workflow
c.execute("""
INSERT INTO workflow_entity (id, name, active, nodes, connections, createdAt, updatedAt, settings, staticData, versionId, activeVersionId)
VALUES (?, ?, 1, ?, ?, ?, ?, '{}', '{}', ?, ?)
""", (wf_id, wf_name, nodes_str, connections_str, now, now, version_id, version_id))

# Insert into workflow_history
c.execute("""
INSERT INTO workflow_history (versionId, workflowId, authors, createdAt, updatedAt, nodes, connections, name, autosaved, description, nodeGroups)
VALUES (?, ?, '[]', ?, ?, ?, ?, ?, 0, NULL, '[]')
""", (version_id, wf_id, now, now, nodes_str, connections_str, wf_name))

# Insert into workflow_published_version
c.execute("""
INSERT INTO workflow_published_version (workflowId, publishedVersionId, createdAt, updatedAt)
VALUES (?, ?, ?, ?)
""", (wf_id, version_id, now, now))

# Link to default personal project
c.execute("SELECT id FROM project LIMIT 1")
proj = c.fetchone()
proj_id = proj[0] if proj else '6nFAkOIBdxy8Xt7Y'

c.execute("""
INSERT INTO shared_workflow (workflowId, projectId, role, createdAt, updatedAt)
VALUES (?, ?, 'workflow:owner', ?, ?)
""", (wf_id, proj_id, now, now))

# Insert both webhooks into webhook_entity
c.execute("""
INSERT INTO webhook_entity (webhookPath, method, node, webhookId, workflowId, pathLength)
VALUES ('vapi-tools', 'POST', 'Vapi Tool Webhook', 'vapi-tools', ?, 10)
""", (wf_id,))

c.execute("""
INSERT INTO webhook_entity (webhookPath, method, node, webhookId, workflowId, pathLength)
VALUES ('vapi-end-of-call', 'POST', 'Vapi End-of-Call Webhook', 'vapi-end-of-call', ?, 16)
""", (wf_id,))

conn.commit()
print(f"SUCCESS: Deployed to old server under ID '{wf_id}' in project '{proj_id}'")

print("Workflows in database:")
c.execute("SELECT id, name, active FROM workflow_entity WHERE id = ?", (wf_id,))
for row in c.fetchall():
    print(f"  {row}")

print("Webhooks in database:")
c.execute("SELECT webhookPath, method, node, workflowId, pathLength FROM webhook_entity WHERE workflowId = ?", (wf_id,))
for row in c.fetchall():
    print(f"  {row}")

conn.close()
