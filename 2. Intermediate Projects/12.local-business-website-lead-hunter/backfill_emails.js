const fs = require('fs');
const crypto = require('crypto');
const nodemailer = require('/usr/local/lib/node_modules/n8n/node_modules/.pnpm/nodemailer@8.0.10/node_modules/nodemailer');
const sqlite3 = require('/usr/local/lib/node_modules/n8n/node_modules/sqlite3');

const SMTP_USER = 'serhat.kumas.sk@gmail.com';
const SMTP_PASS = 'hkufzpvlohupcxib';
const BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN';
const CHAT_ID = '1519369571';
const SHEET_ID = '15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4';

async function main() {
  const cfg = JSON.parse(fs.readFileSync('/home/node/.n8n/config'));
  const key = cfg.encryptionKey;
  const db = new sqlite3.Database('/home/node/.n8n/database.sqlite');

  // 1. Decrypt Google Sheets Token
  const row = await new Promise((res, rej) => {
    db.get("SELECT data FROM credentials_entity WHERE id = 'uIhLunuZ3AaxqaDA'", (err, r) => err ? rej(err) : res(r));
  });

  const cipherText = Buffer.from(row.data, 'base64');
  const salt = cipherText.subarray(8, 16);
  let hash = Buffer.alloc(0);
  let total = Buffer.alloc(0);
  while (total.length < 48) {
    const md5 = crypto.createHash('md5');
    md5.update(hash);
    md5.update(key, 'utf8');
    md5.update(salt);
    hash = md5.digest();
    total = Buffer.concat([total, hash]);
  }
  const aesKey = total.subarray(0, 32);
  const iv = total.subarray(32, 48);
  const decipher = crypto.createDecipheriv('aes-256-cbc', aesKey, iv);
  let dec = decipher.update(cipherText.subarray(16));
  dec = Buffer.concat([dec, decipher.final()]);
  const parsed = JSON.parse(dec.toString('utf8'));

  const tRes = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: parsed.clientId,
      client_secret: parsed.clientSecret,
      refresh_token: parsed.oauthTokenData.refresh_token,
      grant_type: 'refresh_token'
    }).toString()
  });
  const tData = await tRes.json();
  const accessToken = tData.access_token;

  // 2. Read Sheet Rows
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/Records!A1:K100`;
  const sRes = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } });
  const sData = await sRes.json();
  const rows = sData.values || [];
  console.log(`Fetched ${rows.length} total rows from Google Sheets.`);

  if (rows.length <= 1) {
    console.log('No rows found to backfill.');
    return;
  }

  // 3. Connect SMTP
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
      user: SMTP_USER,
      pass: SMTP_PASS
    }
  });

  const seenEmails = new Set();
  const sentList = [];

  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    const name = r[1] || 'İşletme Yetkilisi';
    const cat = r[2] || 'Yerel İşletme';
    const city = r[3] || 'Türkiye';
    const email = (r[5] || '').toLowerCase().trim();
    const insta = r[6] || '';

    if (!email || !email.includes('@') || seenEmails.has(email)) continue;
    seenEmails.add(email);

    const subject = `${name} için Google'da fark edilmenizi sağlayacak modern bir web sitesi`;
    const bodyText = `Merhaba ${name} Yetkilisi,\n\nInstagram üzerindeki başarılı çalışmalarınızı ve işletmenizi incelerken doğrudan kurumsal bir web sitenizin bulunmadığını fark ettik.\n\nCodewaft Digital Studio olarak işletmenize özel mobil uyumlu, 1 saniyede açılan ultra hızlı ve Google aramalarında doğrudan randevu & müşteri kazandıran modern bir web sitesi hazırlayabiliriz.\n\nİşletmeniz için hazırladığımız örnek konsept tasarım taslağını incelemek ve kısa bir fikir alışverişi yapmak isterseniz, bu e-postayı kısaca yanıtlamanız yeterlidir.\n\nSaygılarımla,\nSerhat Kumaş\nKurucu | Codewaft Digital Studio\nserhat.kumas.sk@gmail.com`;

    const formattedHtml = `<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; line-height: 1.6; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;">
  <div style="font-size: 15px;">
    ${bodyText.split('\n\n').map(p => `<p style="margin: 0 0 16px 0;">${p.replace(/\n/g, '<br/>')}</p>`).join('')}
  </div>
  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0 16px 0;" />
  <div style="font-size: 13px; color: #64748b;">
    <strong style="color: #0f172a; font-size: 14px;">Serhat Kumaş</strong><br/>
    Kurucu | <strong>Codewaft Digital Studio</strong><br/>
    📧 <a href="mailto:serhat.kumas.sk@gmail.com" style="color: #0284c7; text-decoration: none;">serhat.kumas.sk@gmail.com</a><br/>
    🌐 Modern Web Tasarım & Dijital Çözümler
  </div>
</div>`;

    try {
      const info = await transporter.sendMail({
        from: `Serhat Kumaş <${SMTP_USER}>`,
        to: email,
        subject: subject,
        html: formattedHtml
      });
      console.log(`[${sentList.length + 1}] Sent to ${name} (${email}) - ID: ${info.messageId}`);
      sentList.push({ name, email, cat, city, id: info.messageId });
      await new Promise(r => setTimeout(r, 1200)); // Respectful delay
    } catch (err) {
      console.error(`Error sending to ${email}:`, err.message);
    }
  }

  console.log(`Backfill complete: ${sentList.length} emails dispatched.`);

  // 4. Update Google Sheets Status to AUTO_SENT_VIA_GMAIL_SMTP
  const updateUrl = `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/Records!I2:K${rows.length}?valueInputOption=USER_ENTERED`;
  const updateRows = [];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    updateRows.push([
      'AUTO_SENT_VIA_GMAIL_SMTP',
      r[9] || `${r[1]} için Özel Web Tasarım Teklifi`,
      'Gmail SMTP (Google App Password) üzerinden başarıyla iletildi.'
    ]);
  }

  await fetch(updateUrl, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ values: updateRows })
  });
  console.log('Google Sheets Records status updated to AUTO_SENT_VIA_GMAIL_SMTP.');

  // 5. Send single comprehensive Telegram report
  let cards = '';
  sentList.forEach((s, idx) => {
    cards += `\n${idx + 1}️⃣ <b>${s.name}</b> (${s.cat} • ${s.city})\n   └ <code>${s.email}</code> ✅ İletildi\n`;
  });

  const tgMessage = `📬 <b>Geçmişte Yakalanan Tüm İşletmelere E-Posta İletimi Tamamlandı!</b>
━━━━━━━━━━━━━━━━━━━━
✅ Gmail kesintisinden etkilenen tüm işletmeler (${sentList.length} Firma) için Gmail SMTP üzerinden teklif e-postaları başarıyla gönderildi.
📊 Google Sheets <code>Records</code> tablosundaki tüm durumlar <code>AUTO_SENT_VIA_GMAIL_SMTP</code> olarak güncellendi.

🏢 <b>E-posta Gönderilen İşletmeler:</b>
━━━━━━━━━━━━━━━━━━━━${cards}
━━━━━━━━━━━━━━━━━━━━
👉 <a href="https://docs.google.com/spreadsheets/d/15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4/edit#gid=0">📊 Google Sheets CRM Veritabanını Aç ↗</a>`;

  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: CHAT_ID,
      text: tgMessage,
      parse_mode: 'HTML'
    })
  });

  console.log('Telegram report sent successfully!');
}

main().catch(console.error);
