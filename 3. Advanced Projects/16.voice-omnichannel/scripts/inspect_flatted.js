const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');
const zlib = require('zlib');
const { parse } = require('/usr/local/lib/node_modules/n8n/node_modules/flatted');

const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

db.all("SELECT executionId, data FROM execution_data WHERE executionId IN (20, 21)", (err, rows) => {
  if (err) { console.error(err); return; }
  for (const row of rows) {
    console.log(`\n================= EXECUTION ${row.executionId} =================`);
    let raw = row.data;
    if (Buffer.isBuffer(raw)) {
      try { raw = zlib.gunzipSync(raw).toString(); } catch(e) { raw = raw.toString(); }
    }
    try {
      const parsed = parse(raw);
      const runData = parsed.resultData?.runData || {};
      const webhookData = runData['Vapi End-of-Call Webhook']?.[0]?.data?.main?.[0]?.[0]?.json?.body || {};
      console.log('Webhook message type:', webhookData.message?.type);
      console.log('Ended Reason:', webhookData.message?.endedReason || webhookData.message?.call?.endedReason);
      console.log('Transcript:', webhookData.message?.transcript);
      console.log('Customer number:', webhookData.message?.customer?.number);
      if (parsed.resultData?.error) {
        console.log('Execution Error:', parsed.resultData.error.message);
      }
    } catch(e) {
      console.log('Error parsing:', e.message);
    }
  }
  db.close();
});
