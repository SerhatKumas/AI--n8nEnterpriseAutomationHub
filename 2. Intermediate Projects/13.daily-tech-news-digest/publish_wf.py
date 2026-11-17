import json, sqlite3, uuid, urllib.request

wf_path = '/tmp/p13_workflow.json'
with open(wf_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

WORKFLOW_ID = 'daily-tech-news-digest-p00013'
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
PROJECT_ID = '6nFAkOIBdxy8Xt7Y'

con = sqlite3.connect('/var/lib/docker/volumes/n8n_storage/_data/database.sqlite')
cur = con.cursor()

# Find telegram trigger node id
tg_node_id = None
for n in wf['nodes']:
    if 'telegramTrigger' in n.get('type', ''):
        tg_node_id = n['id']
        break

print(f"Telegram Trigger Node ID: {tg_node_id}")

nodes_json = json.dumps(wf['nodes'])
conns_json = json.dumps(wf['connections'])
settings_json = json.dumps(wf.get('settings', {}))
now = "2026-11-15 01:50:00"
version_id = str(uuid.uuid4())

# 1. Insert/Update workflow_entity
cur.execute("""
INSERT INTO workflow_entity (id, name, active, nodes, connections, settings, createdAt, updatedAt, versionId)
VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
  name=excluded.name,
  active=1,
  nodes=excluded.nodes,
  connections=excluded.connections,
  settings=excluded.settings,
  updatedAt=excluded.updatedAt,
  versionId=excluded.versionId;
""", (WORKFLOW_ID, wf['name'], nodes_json, conns_json, settings_json, now, now, version_id))

# 2. Insert/Update workflow_history
cur.execute("""
INSERT OR REPLACE INTO workflow_history (versionId, workflowId, nodes, connections, authors, createdAt, updatedAt)
VALUES (?, ?, ?, ?, 'Serhat Kumaş', ?, ?);
""", (version_id, WORKFLOW_ID, nodes_json, conns_json, now, now))

# 3. Associate with Personal Project in shared_workflow
cur.execute("""
INSERT OR REPLACE INTO shared_workflow (workflowId, projectId, role, createdAt, updatedAt)
VALUES (?, ?, 'workflow:owner', ?, ?);
""", (WORKFLOW_ID, PROJECT_ID, now, now))

# 4. Associate Credentials in shared_credentials
cur.execute("""
INSERT OR REPLACE INTO shared_credentials (credentialsId, projectId, role, createdAt, updatedAt)
VALUES ('dailyTechNewsBot', ?, 'credential:owner', ?, ?);
""", (PROJECT_ID, now, now))

# 5. Clean & Insert webhook_entity
cur.execute("DELETE FROM webhook_entity WHERE workflowId = ?;", (WORKFLOW_ID,))

# Webhook 1: Telegram Trigger
tg_path = "p13-tech-news-digest-telegram-trigger/webhook"
cur.execute("""
INSERT INTO webhook_entity (workflowId, webhookPath, method, node, webhookId, pathLength)
VALUES (?, ?, 'POST', 'Telegram Trigger (Commands)', 'p13-tech-news-digest-telegram-trigger', ?);
""", (WORKFLOW_ID, tg_path, len(tg_path)))

# Webhook 2: Manual Webhook
cur.execute("""
INSERT INTO webhook_entity (workflowId, webhookPath, method, node, webhookId, pathLength)
VALUES (?, 'p13-digest-now', 'GET', 'Manual Webhook (Digest On-Demand)', 'p13-digest-now', 14);
""", (WORKFLOW_ID,))

con.commit()
print("Database workflow, webhooks & shared_workflow registered successfully!")

# 6. Set Telegram Webhook with deterministic secret_token
raw_secret = f"{WORKFLOW_ID}_{tg_node_id}"
secret_token = "".join(c for c in raw_secret if c.isalnum() or c in "-_")
print(f"Calculated Telegram secret_token: {secret_token}")

set_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
payload = json.dumps({
    "url": f"https://n8n.codewaft.com/webhook/{tg_path}",
    "secret_token": secret_token,
    "allowed_updates": ["message"],
    "drop_pending_updates": False
}).encode('utf-8')

req = urllib.request.Request(set_webhook_url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    resp_data = json.loads(res.read().decode('utf-8'))
    print("Telegram setWebhook response:", resp_data)

print("Project 13 Deployment Complete!")
