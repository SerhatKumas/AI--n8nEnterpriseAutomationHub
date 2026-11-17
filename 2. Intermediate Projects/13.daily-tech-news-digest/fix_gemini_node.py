import json, sqlite3, urllib.request

wf_path = '/tmp/p13_workflow.json'
with open(wf_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

# Fix Gemini HTTP Request node parameters
for n in wf['nodes']:
    if 'Gemini' in n.get('name', ''):
        n['parameters'] = {
            "method": "POST",
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "googlePalmApi",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify($json.geminiBody) }}",
            "options": {
                "timeout": 90000
            }
        }
        print("Fixed Gemini HTTP Request node parameters!")
        break

# Save updated workflow.json
with open(wf_path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

TARGET_WORKFLOW_ID = 'error-handler-global-001'
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
PROJECT_ID = '6nFAkOIBdxy8Xt7Y'

con = sqlite3.connect('/var/lib/docker/volumes/n8n_storage/_data/database.sqlite')
cur = con.cursor()

nodes_json = json.dumps(wf['nodes'])
cur.execute("UPDATE workflow_entity SET nodes = ? WHERE id = ?;", (nodes_json, TARGET_WORKFLOW_ID))
con.commit()
print("Updated workflow_entity nodes with fixed Gemini parameters in DB!")

# Re-register Telegram Webhook with secret token
tg_node_id = None
for n in wf['nodes']:
    if 'telegramTrigger' in n.get('type', ''):
        tg_node_id = n['id']
        break

tg_path = "p13-tech-news-digest-telegram-trigger/webhook"
raw_secret = f"{TARGET_WORKFLOW_ID}_{tg_node_id}"
secret_token = "".join(c for c in raw_secret if c.isalnum() or c in "-_")
print(f"Telegram secret_token: {secret_token}")

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

print("Fix applied successfully!")
