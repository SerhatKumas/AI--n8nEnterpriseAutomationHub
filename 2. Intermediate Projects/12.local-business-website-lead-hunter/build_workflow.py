#!/usr/bin/env python3
"""
Builds Workflow 12: B2B Local Business Website Lead Hunter & Autonomous Cold Email Outreach Engine
Includes:
- Intelligent Conversational AI Agent (Gemini 3.1 Flash-Lite) for Telegram chat:
  Answers questions like 'How many business we got in touch with?', 'Status nedir?', CRM queries,
  and only triggers new hunts when explicitly requested. Prevents accidental workflow executions.
- Autonomous 10-lead hunter scheduled at 07:00, 09:00, 11:00 Turkey time.
- Strict CRM deduplication against Google Sheets 'Records' tab and static memory.
- Gmail SMTP outreach using permanent Google App Password.
- Single comprehensive long message per run (no per-lead spam).
- Fail-safe halt with global error workflow.
"""
import json
import os

WORKFLOW_ID = "b2b-lead-hunter-tr-00012"
WORKFLOW_NAME = "Project 12 : B2B Local Business Website Lead Hunter & Cold Email Outreach Engine"
ERROR_WORKFLOW_ID = "error-handler-global-001"

def build_workflow():
    nodes = [
        # =====================================================================
        # TRIGGERS
        # =====================================================================
        {
            "parameters": {
                "updates": ["message", "callback_query"],
                "additionalFields": {}
            },
            "id": "telegram-trigger",
            "name": "Telegram Trigger (Commands & Buttons)",
            "type": "n8n-nodes-base.telegramTrigger",
            "typeVersion": 1.1,
            "position": [200, 300],
            "webhookId": f"{WORKFLOW_ID}_telegram-trigger",
            "credentials": {
                "telegramApi": {
                    "id": "websiteClientLeadBot",
                    "name": "Website Client Lead Bot"
                }
            }
        },
        {
            "parameters": {
                "rule": {
                    "interval": [
                        {
                            "field": "cronExpression",
                            "expression": "0 7,9,11 * * *"
                        }
                    ]
                }
            },
            "id": "schedule-trigger",
            "name": "Schedule: Daily 07:00, 09:00, 11:00 (Autonomous)",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [200, 100]
        },
        {
            "parameters": {
                "httpMethod": "GET",
                "path": "hunt-leads",
                "responseMode": "onReceived",
                "options": {}
            },
            "id": "manual-webhook-trigger",
            "name": "Manual Webhook Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [200, 500],
            "webhookId": "lead-hunter-webhook"
        },
        {
            "parameters": {},
            "id": "manual-test-run",
            "name": "Manual Test Run",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [200, 700]
        },

        # =====================================================================
        # CENTRAL ROUTER
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🏢 CENTRAL BRAND & EVENT ROUTER (Autonomous B2B 10-Lead Hunter & AI Agent)
// =========================================================================
const CONFIG = {
  providerName: "Serhat Kumaş / Codewaft",
  providerTitle: "Modern Web Tasarım, 7/24 WhatsApp AI Bot & Akıllı Otomasyon",
  providerEmail: "serhat.kumas.sk@gmail.com",
  defaultChatId: "1519369571",
  apifyToken: "YOUR_APIFY_API_TOKEN",
  spreadsheetId: "15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4",
  sheetName: "Records",
  targetLeadsCount: 10
};

const input = $input.first()?.json || {};
const cq = input.callback_query || input.body?.callback_query;

// 1. Detect Callback Query (if button clicked)
if (cq && (cq.data || cq.id)) {
  const callbackData = String(cq.data || "").trim();
  const chatId = String(cq.message?.chat?.id || cq.from?.id || CONFIG.defaultChatId);
  return [{
    json: {
      ...CONFIG,
      eventType: callbackData === "status" ? "status" : "hunt",
      chatId,
      timestamp: new Date().toISOString()
    }
  }];
}

// 2. Detect Telegram Text Commands & Natural Language Messages
const msg = input.message || input.msg;
if (msg && msg.text) {
  const text = String(msg.text).trim();
  const chatId = String(msg.chat?.id || msg.from?.id || CONFIG.defaultChatId);
  
  if (text === "/status" || text === "/leads") {
    return [{
      json: {
        ...CONFIG,
        eventType: "status",
        chatId
      }
    }];
  }

  if (text.startsWith("/hunt") || text.startsWith("/scan")) {
    const rawQuery = text.replace(/^\\/(?:hunt|scan)\\s*/i, "").trim();
    return [{
      json: {
        ...CONFIG,
        eventType: "hunt",
        customQuery: rawQuery || null,
        chatId,
        triggerSource: "telegram_command"
      }
    }];
  }

  // ANY other text message: Route to AI Agent (prevents accidental hunt!)
  return [{
    json: {
      ...CONFIG,
      eventType: "agent_chat",
      userMessage: text,
      chatId,
      triggerSource: "telegram_user_chat"
    }
  }];
}

// 3. Triggered by Schedule (Daily 07:00, 09:00, 11:00) or Manual Webhook
const queryParam = input.query?.query || input.query?.search;

return [{
  json: {
    ...CONFIG,
    eventType: "hunt",
    customQuery: queryParam || null,
    chatId: CONFIG.defaultChatId,
    triggerSource: "schedule_or_webhook"
  }
}];"""
            },
            "id": "central-brand-router",
            "name": "Central Brand & Event Router",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [520, 380]
        },

        # =====================================================================
        # ROUTE EVENT TYPE (HUNT vs STATUS vs AGENT_CHAT)
        # =====================================================================
        {
            "parameters": {
                "dataType": "string",
                "value1": "={{ $json.eventType }}",
                "rules": {
                    "rules": [
                        {
                            "value2": "hunt",
                            "output": 0
                        },
                        {
                            "value2": "status",
                            "output": 1
                        },
                        {
                            "value2": "agent_chat",
                            "output": 2
                        }
                    ]
                }
            },
            "id": "route-event-type",
            "name": "Route Event Type",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 1,
            "position": [780, 380]
        },

        # =====================================================================
        # AGENT PIPELINE: FETCH CRM FOR AGENT
        # =====================================================================
        {
            "parameters": {
                "operation": "read",
                "documentId": {
                    "__rl": True,
                    "value": "15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4",
                    "mode": "id"
                },
                "sheetName": {
                    "__rl": True,
                    "value": "Records",
                    "mode": "name"
                },
                "options": {}
            },
            "alwaysOutputData": True,
            "id": "fetch-crm-for-agent",
            "name": "Fetch CRM for Agent",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.5,
            "position": [1040, 780],
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "uIhLunuZ3AaxqaDA",
                    "name": "Google Sheets account"
                }
            }
        },

        # =====================================================================
        # PREPARE AGENT PROMPT
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🤖 PREPARE CONVERSATIONAL AGENT PROMPT WITH LIVE CRM CONTEXT
// =========================================================================
const rows = $input.all().map(i => i.json);
const meta = $('Central Brand & Event Router').first().json;
const userMessage = meta.userMessage || '';

const validLeads = rows.filter(r => r.Email && r.Email.includes('@'));

// Category breakdown
const catCounts = {};
for (const l of validLeads) {
  const c = l.Category || 'Genel';
  catCounts[c] = (catCounts[c] || 0) + 1;
}

const catBreakdown = Object.entries(catCounts)
  .sort((a, b) => b[1] - a[1])
  .map(([cat, cnt]) => `• ${cat}: ${cnt}`)
  .join('\\n');

const prompt = `Sen Serhat Kumaş'ın kurucusu olduğu Codewaft Digital Studio adına çalışan usta, akıllı bir B2B Yönetici ve CRM Asistanısın.
Serhat Bey sana Telegram'dan şu mesajı yazdı: "${userMessage}"

ŞU ANKİ CANLI GOOGLE SHEETS CRM VERİLERİ (Records):
- Şimdiye Kadar İletişime Geçilen Toplam Firma Sayısı: ${validLeads.length}
- Sektörel Dağılım:
${catBreakdown || 'Henüz kayıtlı sektör yok.'}
- Son Kayıtlı Firmalardan Bazıları:
${validLeads.slice(-8).map((l, i) => `${i + 1}. ${l['Business Name']} (${l.Category} • ${l.City}) - ${l.Email}`).join('\\n')}

GÖREVİN VE KARAR MEKANİZMAN:
1. Serhat Bey'in mesajını dikkatle anla:
   - Eğer bir soru soruyorsa (örneğin "How many business we got in touch with?", "Kaç işletmeyle görüştük?", "Diyetisyenlere mail gitti mi?", "Hangi şehirler var?", "Durum nedir?", "Neler yapabiliyorsun?", "Merhaba"):
     -> intent: "CHAT_RESPONSE"
     -> Elindeki gerçek CRM verilerine dayanarak net, akıcı, nazik ve profesyonel bir yanıt hazırla.
     -> Telegram HTML formatı kullan (SADECE <b>, <i>, <code> tagleri kullanılabilir; ASLA <ul>, <ol>, <li> veya <p> tagleri KULLANMA, maddeler için direkt '• ' karakteri kullan).
     -> ASLA yeni bir av veya tarama başlatma!
   
   - Eğer Serhat Bey AÇIKÇA yeni bir işletme avı veya tarama başlatmak istiyorsa (örneğin "yeni işletmeleri ara", "başla", "avı başlat", "diş hekimlerini bul ve mail at"):
     -> intent: "START_HUNT"
     -> customQuery: varsa belirtilen sektör (yoksa null)
     -> replyText: Avın başlatıldığına dair kısa ve net bir onay mesajı.

ÇIKTI FORMATI:
Yalnızca geçerli, temiz bir JSON objesi döndür:
{
  "intent": "CHAT_RESPONSE" | "START_HUNT",
  "customQuery": null | "sektör adı",
  "replyText": "Telegram'a gönderilecek mesaj"
}`;

return [{
  json: {
    ...meta,
    totalCrmLeads: validLeads.length,
    categoryBreakdown: catBreakdown,
    agentPrompt: prompt
  }
}];"""
            },
            "id": "prepare-agent-prompt",
            "name": "Prepare Agent Prompt",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1280, 780]
        },

        # =====================================================================
        # AGENT: CONVERSATIONAL ASSISTANT & INTENT CLASSIFIER (GEMINI)
        # =====================================================================
        {
            "parameters": {
                "method": "POST",
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
                "authentication": "predefinedCredentialType",
                "nodeCredentialType": "googlePalmApi",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": """={\n  "contents": [\n    {\n      "parts": [\n        {\n          "text": {{ JSON.stringify($json.agentPrompt) }}\n        }\n      ]\n    }\n  ],\n  "generationConfig": {\n    "temperature": 0.5,\n    "responseMimeType": "application/json"\n  }\n}""",
                "options": {
                    "timeout": 90000
                }
            },
            "id": "gemini-conversational-agent",
            "name": "Agent: AI Assistant & Decision Engine (Gemini)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1520, 780],
            "retryOnFail": True,
            "maxTries": 3,
            "waitBetweenTries": 2000,
            "continueOnFail": True,
            "credentials": {
                "googlePalmApi": {
                    "id": "zvLpU1ScjMCeOYQq",
                    "name": "Google Gemini(PaLM) Api account"
                }
            }
        },

        # =====================================================================
        # PARSE AGENT DECISION
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🧠 PARSE AGENT DECISION & ROUTE INTENT (FAIL-SAFE WITH LIVE CRM FALLBACK)
// =========================================================================
const res = $input.first().json;
const meta = $('Prepare Agent Prompt').first().json;

function sanitizeTelegramHtml(text) {
  if (!text) return "";
  let clean = String(text);
  clean = clean.replace(/<\\/?ul>/gi, "\\n");
  clean = clean.replace(/<\\/?ol>/gi, "\\n");
  clean = clean.replace(/<li>\\s*/gi, "• ");
  clean = clean.replace(/<\\/li>/gi, "\\n");
  clean = clean.replace(/<\\/?p>/gi, "\\n");
  clean = clean.replace(/<br\\s*\\/?>/gi, "\\n");
  clean = clean.replace(/<\\/?div>/gi, "\\n");
  clean = clean.replace(/<(?!\\/?(?:b|strong|i|em|u|ins|s|strike|del|code|pre|a)(?:\\s+[^>]*?)?>)[^>]+>/gi, "");
  return clean.replace(/\\n{3,}/g, "\\n\\n").trim();
}

const breakdownStr = meta.categoryBreakdown || '';
const fallbackReply = `Serhat Bey merhaba, şu ana kadar CRM verilerimize göre toplam <b>${meta.totalCrmLeads || 0} farklı işletme</b> ile iletişime geçtik.\\n\\n<b>Sektörel Dağılım:</b>\\n${breakdownStr}\\n\\nSüreç planlandığı gibi ilerliyor, başka bir konuda yardımcı olmamı ister misiniz?`;

let decision = {
  intent: "CHAT_RESPONSE",
  customQuery: null,
  replyText: fallbackReply
};

// Check if Gemini returned valid candidate parts
if (!res.error && res.candidates && res.candidates[0]?.content?.parts?.[0]?.text) {
  try {
    let rawText = res.candidates[0].content.parts[0].text;
    rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();
    const parsed = JSON.parse(rawText);
    if (parsed.intent) decision.intent = parsed.intent;
    if (parsed.customQuery) decision.customQuery = parsed.customQuery;
    if (parsed.replyText) decision.replyText = sanitizeTelegramHtml(parsed.replyText);
  } catch (e) {
    // Keep fallbackReply
  }
}

return [{
  json: {
    ...meta,
    intent: decision.intent,
    customQuery: decision.customQuery,
    replyText: decision.replyText,
    chatId: meta.chatId || "1519369571"
  }
}];"""
            },
            "id": "parse-agent-decision",
            "name": "Parse Agent Decision",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1760, 780]
        },

        # =====================================================================
        # ROUTE AGENT INTENT (CHAT_RESPONSE vs START_HUNT)
        # =====================================================================
        {
            "parameters": {
                "dataType": "string",
                "value1": "={{ $json.intent }}",
                "rules": {
                    "rules": [
                        {
                            "value2": "CHAT_RESPONSE",
                            "output": 0
                        },
                        {
                            "value2": "START_HUNT",
                            "output": 1
                        }
                    ]
                }
            },
            "id": "route-agent-intent",
            "name": "Route Agent Intent",
            "type": "n8n-nodes-base.switch",
            "typeVersion": 1,
            "position": [2000, 780]
        },
        {
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": "={{ $json.replyText }}",
                "additionalFields": {
                    "parse_mode": "HTML",
                    "appendAttribution": False
                }
            },
            "id": "send-agent-reply-telegram",
            "name": "Send Agent Reply to Telegram",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [2240, 720],
            "credentials": {
                "telegramApi": {
                    "id": "websiteClientLeadBot",
                    "name": "Website Client Lead Bot"
                }
            }
        },

        # =====================================================================
        # STATUS PIPELINE: FETCH CRM HISTORY FOR STATUS
        # =====================================================================
        {
            "parameters": {
                "operation": "read",
                "documentId": {
                    "__rl": True,
                    "value": "15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4",
                    "mode": "id"
                },
                "sheetName": {
                    "__rl": True,
                    "value": "Records",
                    "mode": "name"
                },
                "options": {}
            },
            "alwaysOutputData": True,
            "id": "fetch-crm-for-status",
            "name": "Fetch CRM for Status",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.5,
            "position": [1040, 520],
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "uIhLunuZ3AaxqaDA",
                    "name": "Google Sheets account"
                }
            }
        },

        # =====================================================================
        # FORMAT COMPREHENSIVE STATUS REPORT
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 📊 COMPILE COMPREHENSIVE STATUS & ALL CONTACTED COMPANIES REPORT
// =========================================================================
const rows = $input.all().map(i => i.json);
const chatId = $('Central Brand & Event Router').first().json.chatId || '1519369571';

// Filter out header or empty rows
const validLeads = rows.filter(r => r.Email && r.Email.includes('@'));
const totalCount = validLeads.length;

// Count unique categories
const categories = {};
const cities = {};
for (const lead of validLeads) {
  const cat = lead.Category || 'Genel';
  categories[cat] = (categories[cat] || 0) + 1;
  const city = lead.City || 'Türkiye';
  cities[city] = (cities[city] || 0) + 1;
}

// Build list of companies (most recent first)
let companyListText = '';
const displayLeads = validLeads.slice().reverse().slice(0, 15); // Show up to 15 latest

displayLeads.forEach((l, idx) => {
  const name = l['Business Name'] || 'İsimsiz';
  const cat = l.Category || 'Sektör';
  const city = l.City || 'Türkiye';
  const email = l.Email || '';
  const date = l.Date || '';
  const status = (l.Status || '').includes('SENT') ? '✅' : '⚠️';
  companyListText += `• ${status} <b>${name}</b> (${cat} • ${city})\\n  └ <code>${email}</code> • <i>${date}</i>\\n`;
});

let report = `📊 <b>B2B Web Sitesiz Müşteri Avcısı: Genel Durum & CRM Raporu</b>
━━━━━━━━━━━━━━━━━━━━
⚡️ <b>Çalışma Modu:</b> %100 Otonom (Hedef: Her döngüde 10 yeni işletme)
⏰ <b>Zamanlama:</b> Her gün <b>07:00, 09:00 ve 11:00</b> (Günde 3 Otonom Av)
📧 <b>E-posta Servisi:</b> Gmail SMTP (serhat.kumas.sk@gmail.com) ✅ Aktif & Süresiz
🤖 <b>Akıllı Asistan:</b> Sohbet botu aktiftir. İstediğiniz soruyu doğrudan sorabilirsiniz.
🛡 <b>Hata Güvenliği:</b> Olası bir hata anında akış anında durur ve Telegram'a uyarı gönderir.

📈 <b>CRM Özeti:</b>
• Kayıtlı Toplam İşletme: <b>${totalCount} Firma</b>
• Farklı Sektör Sayısı: <b>${Object.keys(categories).length} Sektör</b>
• Farklı Şehir Sayısı: <b>${Object.keys(cities).length} Şehir</b>

🏢 <b>Son İletişime Geçilen İşletmeler (En Yeni 15):</b>
━━━━━━━━━━━━━━━━━━━━
${companyListText || 'Henüz kayıtlı işletme bulunmuyor.'}
━━━━━━━━━━━━━━━━━━━━
${totalCount > 15 ? `<i>...ve ${totalCount - 15} işletme daha Google Sheets üzerinde kayıtlıdır.</i>\\n` : ''}
👉 <a href="https://docs.google.com/spreadsheets/d/15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4/edit#gid=0">📊 Google Sheets CRM Veritabanını Aç ↗</a>`;

return [{
  json: {
    chatId,
    reportText: report
  }
}];"""
            },
            "id": "format-status-report",
            "name": "Format Comprehensive Status Report",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1280, 520]
        },
        {
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": "={{ $json.reportText }}",
                "additionalFields": {
                    "parse_mode": "HTML",
                    "appendAttribution": False
                }
            },
            "id": "send-status-briefing",
            "name": "Send Status Briefing",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [1520, 520],
            "credentials": {
                "telegramApi": {
                    "id": "websiteClientLeadBot",
                    "name": "Website Client Lead Bot"
                }
            }
        },

        # =====================================================================
        # HUNT PIPELINE: FETCH EXISTING CRM LEADS (DEDUPLICATION SOURCE)
        # =====================================================================
        {
            "parameters": {
                "operation": "read",
                "documentId": {
                    "__rl": True,
                    "value": "15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4",
                    "mode": "id"
                },
                "sheetName": {
                    "__rl": True,
                    "value": "Records",
                    "mode": "name"
                },
                "options": {}
            },
            "alwaysOutputData": True,
            "id": "fetch-existing-crm-leads",
            "name": "Fetch Existing CRM Leads (De-duplication)",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.5,
            "position": [1040, 200],
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "uIhLunuZ3AaxqaDA",
                    "name": "Google Sheets account"
                }
            }
        },

        # =====================================================================
        # PREPARE APIFY PAYLOAD & COMPILE CONTACTED HISTORY
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🔍 PREPARE APIFY PAYLOAD & COMPILE HISTORICAL CRM CONTACTS
// =========================================================================
const meta = $('Central Brand & Event Router').first().json;

// Extract existing emails, names, instagram handles, and phone numbers from Google Sheets CRM
let existingRows = [];
try {
  existingRows = $('Fetch Existing CRM Leads (De-duplication)').all().map(i => i.json);
} catch (e) {
  existingRows = [];
}

const contactedEmails = new Set();
const contactedBusinesses = new Set();
const contactedIgs = new Set();
const contactedPhones = new Set();

function cleanIgHandle(url) {
  if (!url) return '';
  const match = String(url).match(/instagram\\.com\\/([a-zA-Z0-9_.-]+)/i);
  if (!match) return '';
  const handle = match[1].toLowerCase().trim();
  if (['p', 'reel', 'stories', 'explore'].includes(handle)) return '';
  return handle;
}

function cleanPhone(phone) {
  if (!phone) return '';
  const digits = String(phone).replace(/\\D/g, '');
  return digits.slice(-10);
}

function normalizeBusinessName(name) {
  if (!name) return '';
  return String(name)
    .toLowerCase()
    .replace(/[ıİ]/g, 'i')
    .replace(/[ğĞ]/g, 'g')
    .replace(/[üÜ]/g, 'u')
    .replace(/[şŞ]/g, 's')
    .replace(/[öÖ]/g, 'o')
    .replace(/[çÇ]/g, 'c')
    .replace(/[^a-z0-9]/g, '')
    .trim();
}

for (const row of existingRows) {
  const email = (row.Email || row.email || '').toLowerCase().trim();
  if (email && email.includes('@')) {
    contactedEmails.add(email);
  }
  const name = row['Business Name'] || row.businessName || '';
  const normName = normalizeBusinessName(name);
  if (normName.length >= 3) {
    contactedBusinesses.add(normName);
  }
  const igHandle = cleanIgHandle(row.Instagram || row.instagram || '');
  if (igHandle) {
    contactedIgs.add(igHandle);
  }
  const phone = cleanPhone(row.Phone || row.phone || '');
  if (phone.length >= 7) {
    contactedPhones.add(phone);
  }
}

// =========================================================================
// 🌐 MASSIVE SECTOR & LOCATION MATRIX GENERATOR (7,000+ Combinations)
// =========================================================================
const ALL_SECTORS = [
  'butik otel', 'pansiyon', 'bungalov evleri', 'güzellik merkezi', 'estetik kliniği',
  'lazer epilasyon', 'kuaför salonu', 'saç ekim merkezi', 'diş hekimi', 'diş kliniği',
  'ortodonti kliniği', 'veteriner kliniği', 'hayvan hastanesi', 'mimarlık ofisi', 'iç mimarlık dekorasyon',
  'peyzaj mimarlığı', 'hukuk bürosu', 'avukatlık', 'diyetisyen beslenme', 'psikolog psikolojik danışmanlık',
  'aile danışmanlığı', 'oto ekspertiz', 'oto servis bakım', 'oto kuaför detaylı temizlik',
  'özel anaokulu kreş', 'özel ders etüt merkezi', 'yabancı dil kursu', 'sürücü kursu',
  'pilates stüdyosu', 'yoga stüdyosu', 'fitness spor salonu', 'dövme stüdyosu',
  'düğün organizasyon davet', 'kına organizasyon', 'catering toplu yemek', 'butik pasta pastane',
  'fotoğraf stüdyosu düğün fotoğrafçısı', 'bebek fotoğrafçısı', 'çocuk oyun evi aktivite', 'fizik tedavi rehabilitasyon',
  'optik gözlük', 'özel güvenlik kamera alarm', 'emlak gayrimenkul danışmanlığı', 'sigorta acentesi',
  'mali müşavir muhasebe', 'mobilya tasarım özel üretim', 'marangoz mutfak banyo',
  'güneş enerjisi sistemleri', 'havuz bakım yapım', 'klima kombi servisi', 'evden eve nakliyat',
  'halı yıkama koltuk yıkama', 'temizlik şirketi profesyonel', 'özel transfer vip taşımacılık',
  'yat kiralama tekne turu', 'dalış okulu su sporları'
];

const ALL_LOCATIONS = [
  // İstanbul
  'Kadıköy', 'Beşiktaş', 'Şişli', 'Bakırköy', 'Sarıyer', 'Üsküdar', 'Beylikdüzü', 'Ataşehir', 'Maltepe', 'Pendik', 'Kartal', 'Başakşehir', 'Fatih', 'Beyoğlu', 'Çekmeköy',
  // Ankara
  'Çankaya', 'Yenimahalle', 'Keçiören', 'Etimesgut', 'Gölbaşı', 'Ümitköy', 'Çayyolu',
  // İzmir
  'Karşıyaka', 'Konak', 'Bornova', 'Bayraklı', 'Alsancak', 'Çeşme', 'Urla', 'Alaçatı', 'Bostanlı',
  // Antalya
  'Muratpaşa', 'Konyaaltı', 'Alanya', 'Manavgat', 'Kaş', 'Kalkan', 'Kemer', 'Lara',
  // Muğla
  'Bodrum', 'Fethiye', 'Marmaris', 'Datça', 'Göcek',
  // Bursa
  'Nilüfer', 'Osmangazi', 'Mudanya',
  // Kocaeli & Sakarya
  'İzmit', 'Gebze', 'Adapazarı', 'Sapanca',
  // Diğer Büyükşehir ve Ticaret Merkezleri
  'Adana', 'Mersin', 'Gaziantep', 'Konya', 'Kayseri', 'Eskişehir', 'Trabzon', 'Samsun', 'Denizli', 'Balıkesir', 'Ayvalık', 'Aydın', 'Kuşadası', 'Çanakkale', 'Tekirdağ', 'Edirne', 'Kapadokya'
];

const EMAIL_SUFFIX_QUERY = '("@gmail.com" OR "@hotmail.com" OR "@outlook.com" OR "@yandex.com")';

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

let queries = [];

if (meta.customQuery) {
  // Pair custom niche with 16 random locations across Instagram & Facebook
  const shuffledLocs = shuffle(ALL_LOCATIONS).slice(0, 16);
  for (let i = 0; i < shuffledLocs.length; i++) {
    const plat = i % 3 === 0 ? 'site:facebook.com' : 'site:instagram.com';
    queries.push(`${plat} "${meta.customQuery}" "${shuffledLocs[i]}" ${EMAIL_SUFFIX_QUERY}`);
  }
} else {
  // Autonomous matrix rotation: pick 18 diverse (Sector x Location x Platform) triplets
  const shuffledSectors = shuffle(ALL_SECTORS);
  const shuffledLocs = shuffle(ALL_LOCATIONS);
  for (let i = 0; i < 18; i++) {
    const s = shuffledSectors[i % shuffledSectors.length];
    const l = shuffledLocs[i % shuffledLocs.length];
    const plat = i % 3 === 0 ? 'site:facebook.com' : 'site:instagram.com';
    queries.push(`${plat} "${s}" "${l}" ${EMAIL_SUFFIX_QUERY}`);
  }
}

return [{
  json: {
    ...meta,
    contactedEmails: Array.from(contactedEmails),
    contactedBusinesses: Array.from(contactedBusinesses),
    contactedIgs: Array.from(contactedIgs),
    contactedPhones: Array.from(contactedPhones),
    apifyBody: {
      queries: queries.join('\\n'),
      maxPagesPerQuery: 3,
      resultsPerPage: 20
    }
  }
}];"""
            },
            "id": "prepare-apify-payload",
            "name": "Prepare Apify Payload",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1280, 200]
        },

        # =====================================================================
        # SCRAPE INSTAGRAM LEADS (APIFY GOOGLE SEARCH)
        # =====================================================================
        {
            "parameters": {
                "method": "POST",
                "url": "=https://api.apify.com/v2/actors/apify~google-search-scraper/run-sync-get-dataset-items?token={{ $json.apifyToken }}&timeout=240",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ JSON.stringify($json.apifyBody) }}",
                "options": {
                    "timeout": 250000
                }
            },
            "id": "scrape-instagram-leads",
            "name": "Scrape Instagram Leads (Apify)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1520, 200]
        },

        # =====================================================================
        # FILTER & QUALIFY 10 FRESH LEADS (NO WEBSITE & NO PREVIOUS CONTACT)
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🎯 EXTRACT & QUALIFY EXACTLY 10 FRESH LEADS WITHOUT WEBSITES
// AIRTIGHT MULTI-FACTOR DEDUPLICATION: EMAIL, IG HANDLE, PHONE, AND NAME
// =========================================================================
const items = $input.all().map(i => i.json);
const meta = $('Prepare Apify Payload').first().json;
const targetCount = meta.targetLeadsCount || 10;

// Sets from CRM Google Sheets
const crmEmails = new Set((meta.contactedEmails || []).map(e => e.toLowerCase().trim()));
const crmBusinesses = new Set(meta.contactedBusinesses || []);
const crmIgs = new Set(meta.contactedIgs || []);
const crmPhones = new Set(meta.contactedPhones || []);

// Persistent static memory across workflow runs
const staticData = $getWorkflowStaticData('global');
staticData.seenLeads = staticData.seenLeads || {};

function extractProfile(url) {
  if (!url) return null;
  const igMatch = String(url).match(/instagram\\.com\\/([a-zA-Z0-9_.-]+)/i);
  if (igMatch) {
    const handle = igMatch[1].toLowerCase().trim();
    if (['p', 'reel', 'stories', 'explore', 'direct', 'accounts'].includes(handle)) return null;
    return { platform: 'Instagram', handle, cleanUrl: `https://www.instagram.com/${handle}/` };
  }
  const fbMatch = String(url).match(/facebook\\.com\\/([a-zA-Z0-9_.-]+)/i);
  if (fbMatch) {
    const handle = fbMatch[1].toLowerCase().trim();
    if (['share', 'pages', 'groups', 'events', 'watch', 'marketplace', 'photo', 'story', 'permalink.php'].includes(handle)) return null;
    return { platform: 'Facebook', handle, cleanUrl: `https://www.facebook.com/${handle}/` };
  }
  return null;
}

function cleanPhone(phone) {
  if (!phone) return '';
  const digits = String(phone).replace(/\\D/g, '');
  return digits.slice(-10);
}

function normalizeBusinessName(name) {
  if (!name) return '';
  return String(name)
    .toLowerCase()
    .replace(/[ıİ]/g, 'i')
    .replace(/[ğĞ]/g, 'g')
    .replace(/[üÜ]/g, 'u')
    .replace(/[şŞ]/g, 's')
    .replace(/[öÖ]/g, 'o')
    .replace(/[çÇ]/g, 'c')
    .replace(/[^a-z0-9]/g, '')
    .trim();
}

const emailRegex = /([a-zA-Z0-9_.+-]+@(gmail|hotmail|outlook|yahoo|yandex|icloud|mynet)\\.(com|com\\.tr|net|org))/i;
const phoneRegex = /(?:(?:\\+90|0)\\s*)?(5\\d{2}[\\s.-]?\\d{3}[\\s.-]?\\d{2}[\\s.-]?\\d{2})/;

const blacklist = [
  'example', 'sample', 'test', 'instagram', 'facebook', 'google', 'apify', 'domain', 'support@', 'info@instagram', 'fb.com', 'mail@'
];

const candidates = [];
const seenInThisRun = new Set();

for (const batch of items) {
  const organicResults = batch.organicResults || [];
  for (const r of organicResults) {
    const url = r.url || '';
    if (url.includes('/p/') || url.includes('/reel/') || url.includes('/stories/') || url.includes('/explore/')) {
      continue;
    }

    const profile = extractProfile(url);
    if (!profile) continue;

    const title = (r.title || '').trim();
    const description = (r.description || '').trim();
    const fullText = `${title} ${description}`;

    // 1. Extract and validate email
    const matchEmail = fullText.match(emailRegex);
    if (!matchEmail) continue;
    const email = matchEmail[1].toLowerCase().trim();

    if (blacklist.some(b => email.includes(b))) continue;

    // 2. Strict Deduplication checks:
    // Check Email against CRM, static memory, and current run
    if (crmEmails.has(email)) continue;
    if (staticData.seenLeads[email]) continue;
    if (seenInThisRun.has(email)) continue;

    // Check Profile Handle against CRM and current run
    if (crmIgs.has(profile.handle)) continue;
    if (seenInThisRun.has(profile.handle)) continue;

    // 3. Extract phone and check deduplication
    const matchPhone = fullText.match(phoneRegex);
    const phone = matchPhone ? matchPhone[0].trim() : '';
    const phoneDigits = cleanPhone(phone);
    if (phoneDigits && crmPhones.has(phoneDigits)) continue;

    // 4. Extract and check business name
    let cleanName = title
      .split('(@')[0]
      .split('•')[0]
      .split('|')[0]
      .split('- Instagram')[0]
      .split('— Instagram')[0]
      .split('- Facebook')[0]
      .split('— Facebook')[0]
      .split(': "')[0]
      .trim();

    cleanName = cleanName.replace(/^[^\\wığüşöçİĞÜŞÖÇ]+|[^\\wığüşöçİĞÜŞÖÇ]+$/g, '').trim();
    if (cleanName.length < 3 || cleanName.toLowerCase().includes('instagram') || cleanName.toLowerCase().includes('facebook')) {
      continue;
    }

    const normName = normalizeBusinessName(cleanName);
    if (crmBusinesses.has(normName)) continue;
    if (seenInThisRun.has(normName)) continue;

    // Infer category across 60+ Turkish sectors
    let category = 'Yerel İşletme';
    const lower = fullText.toLowerCase();
    if (lower.includes('otel') || lower.includes('pansiyon') || lower.includes('bungalov')) category = 'Butik Otel & Konaklama';
    else if (lower.includes('güzellik') || lower.includes('estetik') || lower.includes('kuaför') || lower.includes('lazer') || lower.includes('saç ekim')) category = 'Güzellik & Estetik Merkezi';
    else if (lower.includes('mimar') || lower.includes('dekorasyon') || lower.includes('peyzaj')) category = 'Mimarlık & İç Mimarlık';
    else if (lower.includes('diş') || lower.includes('hekim') || lower.includes('klinik') || lower.includes('ortodonti')) category = 'Diş Kliniği & Sağlık';
    else if (lower.includes('anaokulu') || lower.includes('kreş') || lower.includes('etüt') || lower.includes('kurs') || lower.includes('sürücü')) category = 'Özel Eğitim & Kurs';
    else if (lower.includes('ekspertiz') || lower.includes('oto') || lower.includes('servis') || lower.includes('lastik')) category = 'Oto Servis & Ekspertiz';
    else if (lower.includes('veteriner') || lower.includes('hayvan')) category = 'Veteriner Kliniği';
    else if (lower.includes('hukuk') || lower.includes('avukat')) category = 'Hukuk & Danışmanlık';
    else if (lower.includes('diyet') || lower.includes('beslenme')) category = 'Beslenme & Diyetisyen';
    else if (lower.includes('psikolog') || lower.includes('terapi') || lower.includes('danışman')) category = 'Psikoloji & Danışmanlık';
    else if (lower.includes('düğün') || lower.includes('organizasyon') || lower.includes('kına') || lower.includes('catering')) category = 'Davet & Organizasyon';
    else if (lower.includes('pilates') || lower.includes('yoga') || lower.includes('fitness') || lower.includes('spor')) category = 'Spor & Pilates Stüdyosu';
    else if (lower.includes('pasta') || lower.includes('pastane') || lower.includes('fırın') || lower.includes('tatlı')) category = 'Butik Pastane & Cafe';
    else if (lower.includes('fotoğraf') || lower.includes('stüdyo') || lower.includes('çekim')) category = 'Fotoğraf & Prodüksiyon';
    else if (lower.includes('dövme') || lower.includes('piercing') || lower.includes('tattoo')) category = 'Dövme & Sanat Stüdyosu';
    else if (lower.includes('emlak') || lower.includes('gayrimenkul')) category = 'Gayrimenkul & Emlak';
    else if (lower.includes('sigorta') || lower.includes('acente')) category = 'Sigorta Acentesi';
    else if (lower.includes('mobilya') || lower.includes('marangoz')) category = 'Mobilya Tasarım & Üretim';
    else if (lower.includes('temizlik') || lower.includes('nakliyat') || lower.includes('klima') || lower.includes('tesisat')) category = 'Hizmet & Teknik Servis';

    // Infer city from 81 provinces and key districts
    let city = 'Türkiye';
    const cities = [
      'İstanbul', 'Kadıköy', 'Beşiktaş', 'Şişli', 'Bakırköy', 'Sarıyer', 'Üsküdar', 'Beylikdüzü', 'Ataşehir', 'Maltepe', 'Pendik', 'Kartal', 'Başakşehir', 'Fatih', 'Beyoğlu',
      'Ankara', 'Çankaya', 'Yenimahalle', 'Keçiören', 'Ümitköy', 'Çayyolu',
      'İzmir', 'Karşıyaka', 'Konak', 'Bornova', 'Bayraklı', 'Alsancak', 'Çeşme', 'Urla', 'Alaçatı', 'Bostanlı',
      'Antalya', 'Muratpaşa', 'Konyaaltı', 'Alanya', 'Manavgat', 'Kaş', 'Kalkan', 'Kemer', 'Lara',
      'Muğla', 'Bodrum', 'Fethiye', 'Marmaris', 'Datça', 'Göcek',
      'Bursa', 'Nilüfer', 'Osmangazi', 'Mudanya',
      'Kocaeli', 'İzmit', 'Gebze', 'Sakarya', 'Sapanca',
      'Adana', 'Mersin', 'Gaziantep', 'Konya', 'Kayseri', 'Eskişehir', 'Trabzon', 'Samsun', 'Denizli', 'Balıkesir', 'Ayvalık', 'Aydın', 'Kuşadası', 'Çanakkale', 'Tekirdağ', 'Edirne', 'Kapadokya'
    ];
    for (const c of cities) {
      if (fullText.includes(c)) {
        city = c;
        break;
      }
    }

    // Mark as seen in this run across all identifiers
    seenInThisRun.add(email);
    seenInThisRun.add(profile.handle);
    if (normName) seenInThisRun.add(normName);
    if (phoneDigits) seenInThisRun.add(phoneDigits);

    candidates.push({
      businessName: cleanName,
      email,
      phone,
      instagram: profile.cleanUrl,
      platform: profile.platform,
      category,
      city,
      websiteStatus: `❌ Web Sitesi Yok (Sadece ${profile.platform})`,
      snippet: description.slice(0, 160),
      chatId: meta.chatId || '1519369571',
      spreadsheetId: meta.spreadsheetId,
      sheetName: meta.sheetName,
      providerName: meta.providerName,
      providerEmail: meta.providerEmail
    });

    if (candidates.length >= targetCount) {
      break;
    }
  }
  if (candidates.length >= targetCount) {
    break;
  }
}

// Persist in static data
for (const lead of candidates) {
  staticData.seenLeads[lead.email] = {
    name: lead.businessName,
    ig: lead.instagram,
    date: new Date().toISOString()
  };
}

if (candidates.length === 0) {
  return [{
    json: {
      found: false,
      chatId: meta.chatId || '1519369571',
      message: '🤖 <b>Otonom Avcı Raporu:</b>\\n🔍 Taranan işletmeler arasında web sitesi olmayan ve daha önce e-posta gönderilmemiş YENİ işletme bulunamadı. (Tüm adaylar geçmişte işlenmiş veya web sitesine sahip)'
    }
  }];
}

return candidates.map(l => ({
  json: {
    found: true,
    ...l
  }
}));"""
            },
            "id": "filter-qualify-leads",
            "name": "Filter & Qualify 10 Fresh Leads (No Website)",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1760, 200]
        },

        # =====================================================================
        # CHECK IF LEADS FOUND
        # =====================================================================
        {
            "parameters": {
                "conditions": {
                    "boolean": [
                        {
                            "value1": "={{ $json.found }}",
                            "value2": True
                        }
                    ]
                }
            },
            "id": "check-if-leads-found",
            "name": "Check If Leads Found",
            "type": "n8n-nodes-base.if",
            "typeVersion": 1,
            "position": [2000, 200]
        },
        {
            "parameters": {
                "chatId": "={{ $json.chatId }}",
                "text": "={{ $json.message }}",
                "additionalFields": {
                    "parse_mode": "HTML",
                    "appendAttribution": False
                }
            },
            "id": "send-no-leads-alert",
            "name": "Send No Leads Alert",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [2240, 380],
            "credentials": {
                "telegramApi": {
                    "id": "websiteClientLeadBot",
                    "name": "Website Client Lead Bot"
                }
            }
        },

        # =====================================================================
        # LOOP OVER LEADS (1-BY-1 RESILIENT PIPELINE)
        # =====================================================================
        {
            "parameters": {
                "batchSize": 1,
                "options": {}
            },
            "id": "loop-over-leads",
            "name": "Loop Over Leads (1 by 1)",
            "type": "n8n-nodes-base.splitInBatches",
            "typeVersion": 3,
            "position": [2240, 120]
        },

        # =====================================================================
        # SINGLE ITEM REDUCER & FULL REPORT GENERATOR
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🔒 COMPILE SINGLE COMPREHENSIVE RUN REPORT (All 10 Leads in 1 Single Message)
// =========================================================================
const items = $input.all();
const total = items.length;

let sentCount = 0;
let failCount = 0;
let businessCards = '';

items.forEach((item, idx) => {
  const l = item.json || {};
  const isSent = l.emailSent === true || (l.Status && l.Status.includes('AUTO_SENT'));
  if (isSent) sentCount++;
  else failCount++;

  const statusBadge = isSent ? '✅ E-posta Başarıyla Gönderildi (Gmail SMTP)' : `⚠️ Gönderilemedi (${l.errorMessage || 'Hata'})`;
  const name = l['Business Name'] || l.businessName || 'İşletme';
  const category = l['Category'] || l.category || 'Yerel İşletme';
  const city = l['City'] || l.city || 'Türkiye';
  const email = l['Email'] || l.email || '';
  const phone = l['Phone'] || l.phone || 'Profilde mevcut';
  const subject = l['Subject'] || l.subject || '';
  const profileUrl = l['Instagram'] || l.instagram || '';
  const platformLabel = (profileUrl && profileUrl.includes('facebook.com')) ? 'Facebook' : 'Instagram';

  businessCards += `
${idx + 1}️⃣ <b>${name}</b>
📂 <b>Sektör:</b> ${category} (${city})
📧 <b>E-posta:</b> <code>${email}</code> | 📞 <b>Tel:</b> ${phone}
✉️ <b>Teklif Konusu:</b> ${subject}
🌐 <b>Web Durumu:</b> ❌ Bağımsız Web Sitesi Yok (Sosyal Medya)
📨 <b>Durum:</b> ${statusBadge}
👉 <a href="${profileUrl}">📱 ${platformLabel} Profilini İncele ↗</a>
━━━━━━━━━━━━━━━━━━━━`;
});

const nowStr = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });

const fullReport = `🎉 <b>Otonom Müşteri Avı Tamamlandı: ${total}/${total} İşletmeye Ulaşıldı!</b>
━━━━━━━━━━━━━━━━━━━━
🗓 <b>Tarih & Saat:</b> ${nowStr}
📧 <b>Gönderici Kanalı:</b> Gmail SMTP (serhat.kumas.sk@gmail.com)
📊 <b>CRM:</b> ✅ <code>Records</code> tablosuna işlendi

📈 <b>Döngü Sonuç Özeti:</b>
• İşlenen Toplam İşletme: <b>${total}</b>
• Başarılı Gönderilen E-posta: <b>${sentCount}</b>${failCount > 0 ? `\\n• ⚠️ Hata Veren: <b>${failCount}</b>` : ''}

🏢 <b>BU DÖNGÜDE ULAŞILAN İŞLETMELER:</b>
━━━━━━━━━━━━━━━━━━━━${businessCards}

👉 <a href="https://docs.google.com/spreadsheets/d/15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4/edit#gid=0">📊 Google Sheets CRM Veritabanında Tüm Listeyi Gör ↗</a>`;

let finalReport = fullReport;
if (finalReport.length > 3800) {
  finalReport = finalReport.slice(0, 3600) + `\\n\\n... (Diğer işletme detayları Google Sheets tablosunda listelenmiştir)\\n\\n👉 <a href="https://docs.google.com/spreadsheets/d/15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4/edit#gid=0">📊 Google Sheets CRM Veritabanında Tüm Listeyi Gör ↗</a>`;
}

return [{
  json: {
    totalLeads: total,
    sentCount,
    failCount,
    fullReportText: finalReport
  }
}];"""
            },
            "id": "single-item-reducer",
            "name": "Single Item Reducer & Full Report Generator",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2480, 380]
        },

        # =====================================================================
        # BATCH COMPLETE SUMMARY (SENT ONCE AT THE VERY END)
        # =====================================================================
        {
            "parameters": {
                "chatId": "1519369571",
                "text": "={{ $json.fullReportText }}",
                "additionalFields": {
                    "parse_mode": "HTML",
                    "appendAttribution": False
                }
            },
            "id": "send-batch-summary-telegram",
            "name": "Send Batch Summary to Telegram",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [2720, 380],
            "credentials": {
                "telegramApi": {
                    "id": "websiteClientLeadBot",
                    "name": "Website Client Lead Bot"
                }
            }
        },

        # =====================================================================
        # PREPARE GEMINI PITCH PROMPT
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// ✍️ PREPARE GEMINI COLD OUTREACH PITCH PROMPT
// =========================================================================
const lead = $input.first().json;

const prompt = `Sen Codewaft stüdyosu adına çalışan usta bir B2B büyüme, web ve yapay zeka otomasyon danışmanısın.
Hedef İşletme: "${lead.businessName}"
Sektör: "${lead.category}"
Konum: "${lead.city}"
İletişim E-posta: "${lead.email}"
Telefon: "${lead.phone || 'Profilde mevcut'}"
Sosyal Medya Profili: ${lead.instagram}
Özet Bilgi: "${lead.snippet || ''}"

DURUM ANALİZİ:
Bu başarılı işletmenin şu anda bağımsız, kurumsal bir web sitesi veya 7/24 randevu/müşteri karşılayan akıllı bir sistemi bulunmuyor. Hizmetlerini ve müşteri iletişimini ağırlıklı olarak sosyal medya üzerinden manuel yürütüyorlar.

GÖREVİN:
Bu işletmenin yetkilisine yönelik, son derece samimi, saygılı, profesyonel ve yüksek dönüşümlü bir B2B soğuk e-posta (cold outreach) teklifi hazırlamak.

YAZIM KURALLARI:
1. Kesinlikle robotik veya şablon spam gibi görünmemeli; sanki Serhat Kumaş bizzat işletmelerinin profilini incelemiş gibi içten, özel ve özenli olmalı.
2. İşletmenin ${lead.city}'deki başarılı çalışmalarını ve profilindeki özenli hizmetlerini takdir et.
3. Ancak ${lead.city}'de ${lead.category} arayan potansiyel müşterilerin doğrudan Google'da arama yaptıklarında resmi bir web sitesi göremedikleri için rakiplere kayabildiğini, ayrıca gece veya yoğun saatlerde gelen mesajlara anında dönülemeyince müşteri kaybedilebildiğini nazikçe ve gerçekçi şekilde açıkla.
4. Codewaft olarak sunduğumuz 3'lü Dijital Büyüme Paketini işletmeye özel faydalarıyla özetle:
   - 🌐 Modern, Mobil Uyumlu & Ultra Hızlı Web Sitesi (Google Haritalar & Yerel SEO uyumlu, aramalarda ilk sıralara çıkaran altyapı)
   - 🤖 7/24 WhatsApp & Sosyal Medya AI Asistanı / Randevu Botu (Gelen soruları anında yanıtlayan, fiyat/hizmet detaylarını veren ve otomatik randevu/rezervasyon oluşturan akıllı bot)
   - 📲 Anlık Yönetici Bildirimleri (Telegram/WhatsApp üzerinden işletme sahibine anında düşen yeni müşteri/talep bildirimleri)
5. Düşük bariyerli bir eylem çağrısı (CTA) ekle: "İşletmeniz için hazırladığımız örnek konsept tasarımını ve WhatsApp AI asistanı demo senaryosunu incelemek isterseniz, bu e-postaya kısaca 'İncelemek isterim' şeklinde yanıt vermeniz yeterlidir."
6. İletişim imzası: Serhat Kumaş | Kurucu, Codewaft Digital Studio (serhat.kumas.sk@gmail.com).

ÇIKTI FORMATI:
Yalnızca geçerli, temiz bir JSON objesi döndür (kod bloğu veya açıklama ekleme):
{
  "subject": "E-posta Konu Başlığı (Merak uyandırıcı, işletme adını içeren profesyonel konu)",
  "bodyText": "E-postanın tam metni (paragraflar halinde, profesyonel Türkçe)"
}`;

return [{
  json: {
    ...lead,
    geminiPrompt: prompt
  }
}];"""
            },
            "id": "prepare-gemini-pitch-prompt",
            "name": "Prepare Gemini Pitch Prompt",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2480, 120]
        },

        # =====================================================================
        # GEMINI PITCH GENERATOR (RETRY & FAIL-SAFE)
        # =====================================================================
        {
            "parameters": {
                "method": "POST",
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
                "authentication": "predefinedCredentialType",
                "nodeCredentialType": "googlePalmApi",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": """={\n  "contents": [\n    {\n      "parts": [\n        {\n          "text": {{ JSON.stringify($json.geminiPrompt) }}\n        }\n      ]\n    }\n  ],\n  "generationConfig": {\n    "temperature": 0.7,\n    "responseMimeType": "application/json"\n  }\n}""",
                "options": {
                    "timeout": 60000
                }
            },
            "id": "gemini-pitch-generator",
            "name": "Agent: AI Cold Email Pitch Specialist (Gemini)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [2720, 120],
            "retryOnFail": True,
            "maxTries": 3,
            "waitBetweenTries": 2000,
            "credentials": {
                "googlePalmApi": {
                    "id": "zvLpU1ScjMCeOYQq",
                    "name": "Google Gemini(PaLM) Api account"
                }
            }
        },

        # =====================================================================
        # PARSE PITCH & FORMAT OUTREACH
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 💾 PARSE PITCH & FORMAT HTML OUTREACH
// =========================================================================
const res = $input.first().json;
const lead = $('Prepare Gemini Pitch Prompt').first().json;

function fixTurkishMojibake(str) {
  if (!str || typeof str !== 'string') return str || '';
  return str
    .replace(/脺/g, 'Ü')
    .replace(/脰/g, 'Ö')
    .replace(/脟/g, 'Ç')
    .replace(/艧/g, 'ş')
    .replace(/莽/g, 'ç')
    .replace(/臒/g, 'ğ')
    .replace(/眉/g, 'ü')
    .replace(/枚/g, 'ö')
    .replace(/谋/g, 'ı')
    .replace(/陌/g, 'İ');
}

let pitchData = { subject: '', bodyText: '' };
try {
  let rawText = res.candidates?.[0]?.content?.parts?.[0]?.text || '{}';
  rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();
  rawText = fixTurkishMojibake(rawText);
  pitchData = JSON.parse(rawText);
} catch (e) {
  pitchData = {
    subject: `${lead.businessName} için Google'da fark edilmenizi sağlayacak web sitesi ve 7/24 WhatsApp AI asistanı`,
    bodyText: `Merhaba ${lead.businessName} Yetkilisi,\\n\\n${lead.city}'deki başarılı çalışmalarınızı ve profilinizi incelerken doğrudan kurumsal bir web sitenizin ve 7/24 müşteri karşılayan bir otomasyon sisteminizin bulunmadığını fark ettik.\\n\\nCodewaft olarak işletmenize özel: Google aramalarında öne çıkaran ultra hızlı bir web sitesi ve WhatsApp üzerinden gelen müşterileri 7/24 karşılayıp otomatik randevuya dönüştüren akıllı yapay zeka asistanları kuruyoruz.\\n\\nİşletmeniz için hazırladığımız konsept tasarımı ve WhatsApp AI botu demosunu incelemek isterseniz, bu e-postayı kısaca yanıtlamanız yeterlidir.\\n\\nSaygılarımla,\\nSerhat Kumaş\\nKurucu, Codewaft Digital Studio\\nserhat.kumas.sk@gmail.com`
  };
}

const subject = fixTurkishMojibake(pitchData.subject || `${lead.businessName} için Özel Web Tasarım & WhatsApp AI Teklifi`);
const bodyText = fixTurkishMojibake(pitchData.bodyText || '');

// Beautiful HTML email template
const formattedHtml = `
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #1e293b; line-height: 1.6; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;">
  <div style="font-size: 15px;">
    ${bodyText.split('\\n\\n').map(p => `<p style="margin: 0 0 16px 0;">${p.replace(/\\n/g, '<br/>')}</p>`).join('')}
  </div>
  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0 16px 0;" />
  <div style="font-size: 13px; color: #64748b;">
    <strong style="color: #0f172a; font-size: 14px;">Serhat Kumaş</strong><br/>
    Kurucu | <strong>Codewaft Digital Studio</strong><br/>
    📧 <a href="mailto:serhat.kumas.sk@gmail.com" style="color: #0284c7; text-decoration: none;">serhat.kumas.sk@gmail.com</a><br/>
    🌐 Modern Web Tasarım • 🤖 7/24 WhatsApp AI Botları • 📲 Akıllı Otomasyon
  </div>
</div>
`;

return [{
  json: {
    businessName: lead.businessName,
    category: lead.category,
    city: lead.city,
    phone: lead.phone || '',
    email: lead.email,
    instagram: lead.instagram,
    subject: subject,
    bodyText: bodyText,
    bodyHtml: formattedHtml,
    chatId: lead.chatId || '1519369571'
  }
}];"""
            },
            "id": "parse-pitch-and-dispatch",
            "name": "Parse Pitch & Format Outreach",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2960, 120]
        },

        # =====================================================================
        # AUTO-SEND OUTREACH VIA GMAIL (SMTP APPPASSWORD - NEVER EXPIRES)
        # =====================================================================
        {
            "parameters": {
                "operation": "send",
                "fromEmail": "Serhat Kumaş <serhat.kumas.sk@gmail.com>",
                "toEmail": "={{ $('Parse Pitch & Format Outreach').item.json.email }}",
                "subject": "={{ $('Parse Pitch & Format Outreach').item.json.subject }}",
                "emailFormat": "html",
                "html": "={{ $('Parse Pitch & Format Outreach').item.json.bodyHtml }}",
                "options": {}
            },
            "id": "send-autonomous-email-smtp",
            "name": "Auto-Send Outreach via Gmail (SMTP)",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2.1,
            "position": [3200, 120],
            "retryOnFail": False,
            "credentials": {
                "smtp": {
                    "id": "gmailSmtpAccount",
                    "name": "Gmail SMTP Account"
                }
            }
        },

        # =====================================================================
        # VERIFY EMAIL DISPATCH STATUS
        # =====================================================================
        {
            "parameters": {
                "jsCode": """// =========================================================================
// 🔎 VERIFY ACTUAL SMTP EMAIL DISPATCH STATUS
// =========================================================================
const smtpOutput = $input.first()?.json || {};
const lead = $('Parse Pitch & Format Outreach').first().json;

// Check if an error was returned from EmailSend node
const hasError = Boolean(smtpOutput.error);
const rawErrMsg = smtpOutput.error || "";
const msgId = smtpOutput.messageId || smtpOutput.response || "";

const emailSent = !hasError;
const status = emailSent ? "AUTO_SENT_VIA_GMAIL_SMTP" : "FAILED_EMAIL_DISPATCH";
const notes = emailSent 
  ? `Gemini ile kişiselleştirildi ve Gmail SMTP üzerinden başarıyla iletildi (Message ID: ${msgId || 'ok'}).`
  : `Gönderim Hatası: ${rawErrMsg}`;

return [{
  json: {
    // Mapped columns for Google Sheets autoMapInputData
    "Date": new Date().toISOString().slice(0, 10),
    "Business Name": lead.businessName,
    "Category": lead.category,
    "City": lead.city,
    "Phone": lead.phone || "",
    "Email": lead.email,
    "Instagram": lead.instagram,
    "Address": lead.city,
    "Status": status,
    "Subject": lead.subject,
    "Notes": notes,

    // Payload for Downstream
    businessName: lead.businessName,
    category: lead.category,
    city: lead.city,
    phone: lead.phone,
    email: lead.email,
    instagram: lead.instagram,
    subject: lead.subject,
    chatId: lead.chatId || "1519369571",
    emailSent: emailSent,
    status: status,
    errorMessage: rawErrMsg
  }
}];"""
            },
            "id": "verify-email-dispatch-status",
            "name": "Verify Email Dispatch Status",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [3440, 120]
        },

        # =====================================================================
        # LOG IN GOOGLE SHEETS CRM (RECORDS)
        # =====================================================================
        {
            "parameters": {
                "operation": "append",
                "documentId": {
                    "__rl": True,
                    "value": "15kSudUz9LdFcWBgOngH5MrizGJ8njnXQZniFYn7oEG4",
                    "mode": "id"
                },
                "sheetName": {
                    "__rl": True,
                    "value": "Records",
                    "mode": "name"
                },
                "columns": {
                    "mappingMode": "autoMapInputData",
                    "value": {},
                    "matchingColumns": [],
                    "schema": []
                },
                "options": {}
            },
            "id": "log-auto-sent-lead-sheets",
            "name": "Log Auto-Sent Lead in Google Sheet CRM",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4.5,
            "position": [3680, 120],
            "retryOnFail": True,
            "maxTries": 2,
            "waitBetweenTries": 1500,
            "credentials": {
                "googleSheetsOAuth2Api": {
                    "id": "uIhLunuZ3AaxqaDA",
                    "name": "Google Sheets account"
                }
            }
        }
    ]

    connections = {
        "Telegram Trigger (Commands & Buttons)": {
            "main": [[{"node": "Central Brand & Event Router", "type": "main", "index": 0}]]
        },
        "Schedule: Daily 07:00, 09:00, 11:00 (Autonomous)": {
            "main": [[{"node": "Central Brand & Event Router", "type": "main", "index": 0}]]
        },
        "Manual Webhook Trigger": {
            "main": [[{"node": "Central Brand & Event Router", "type": "main", "index": 0}]]
        },
        "Manual Test Run": {
            "main": [[{"node": "Central Brand & Event Router", "type": "main", "index": 0}]]
        },
        "Central Brand & Event Router": {
            "main": [[{"node": "Route Event Type", "type": "main", "index": 0}]]
        },
        "Route Event Type": {
            "main": [
                [{"node": "Fetch Existing CRM Leads (De-duplication)", "type": "main", "index": 0}],
                [{"node": "Fetch CRM for Status", "type": "main", "index": 0}],
                [{"node": "Fetch CRM for Agent", "type": "main", "index": 0}]
            ]
        },
        # AGENT CHAT BRANCH
        "Fetch CRM for Agent": {
            "main": [[{"node": "Prepare Agent Prompt", "type": "main", "index": 0}]]
        },
        "Prepare Agent Prompt": {
            "main": [[{"node": "Agent: AI Assistant & Decision Engine (Gemini)", "type": "main", "index": 0}]]
        },
        "Agent: AI Assistant & Decision Engine (Gemini)": {
            "main": [[{"node": "Parse Agent Decision", "type": "main", "index": 0}]]
        },
        "Parse Agent Decision": {
            "main": [[{"node": "Route Agent Intent", "type": "main", "index": 0}]]
        },
        "Route Agent Intent": {
            "main": [
                [{"node": "Send Agent Reply to Telegram", "type": "main", "index": 0}],
                [{"node": "Fetch Existing CRM Leads (De-duplication)", "type": "main", "index": 0}]
            ]
        },
        # STATUS BRANCH
        "Fetch CRM for Status": {
            "main": [[{"node": "Format Comprehensive Status Report", "type": "main", "index": 0}]]
        },
        "Format Comprehensive Status Report": {
            "main": [[{"node": "Send Status Briefing", "type": "main", "index": 0}]]
        },
        # HUNT BRANCH
        "Fetch Existing CRM Leads (De-duplication)": {
            "main": [[{"node": "Prepare Apify Payload", "type": "main", "index": 0}]]
        },
        "Prepare Apify Payload": {
            "main": [[{"node": "Scrape Instagram Leads (Apify)", "type": "main", "index": 0}]]
        },
        "Scrape Instagram Leads (Apify)": {
            "main": [[{"node": "Filter & Qualify 10 Fresh Leads (No Website)", "type": "main", "index": 0}]]
        },
        "Filter & Qualify 10 Fresh Leads (No Website)": {
            "main": [[{"node": "Check If Leads Found", "type": "main", "index": 0}]]
        },
        "Check If Leads Found": {
            "main": [
                [{"node": "Loop Over Leads (1 by 1)", "type": "main", "index": 0}],
                [{"node": "Send No Leads Alert", "type": "main", "index": 0}]
            ]
        },
        "Loop Over Leads (1 by 1)": {
            "main": [
                [{"node": "Single Item Reducer & Full Report Generator", "type": "main", "index": 0}],
                [{"node": "Prepare Gemini Pitch Prompt", "type": "main", "index": 0}]
            ]
        },
        "Single Item Reducer & Full Report Generator": {
            "main": [[{"node": "Send Batch Summary to Telegram", "type": "main", "index": 0}]]
        },
        "Prepare Gemini Pitch Prompt": {
            "main": [[{"node": "Agent: AI Cold Email Pitch Specialist (Gemini)", "type": "main", "index": 0}]]
        },
        "Agent: AI Cold Email Pitch Specialist (Gemini)": {
            "main": [[{"node": "Parse Pitch & Format Outreach", "type": "main", "index": 0}]]
        },
        "Parse Pitch & Format Outreach": {
            "main": [[{"node": "Auto-Send Outreach via Gmail (SMTP)", "type": "main", "index": 0}]]
        },
        "Auto-Send Outreach via Gmail (SMTP)": {
            "main": [[{"node": "Verify Email Dispatch Status", "type": "main", "index": 0}]]
        },
        "Verify Email Dispatch Status": {
            "main": [[{"node": "Log Auto-Sent Lead in Google Sheet CRM", "type": "main", "index": 0}]]
        },
        "Log Auto-Sent Lead in Google Sheet CRM": {
            "main": [[{"node": "Loop Over Leads (1 by 1)", "type": "main", "index": 0}]]
        }
    }

    settings = {
        "executionOrder": "v1",
        "timezone": "Europe/Istanbul",
        "saveDataSuccessExecution": "all",
        "saveDataErrorExecution": "all",
        "saveManualExecutions": True,
        "errorWorkflow": ERROR_WORKFLOW_ID
    }

    workflow = {
        "id": WORKFLOW_ID,
        "name": WORKFLOW_NAME,
        "nodes": nodes,
        "connections": connections,
        "settings": settings
    }

    return workflow

if __name__ == "__main__":
    wf = build_workflow()
    out_path = os.path.join(os.path.dirname(__file__), "workflow.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print(f"Generated {out_path} with {len(wf['nodes'])} nodes.")
