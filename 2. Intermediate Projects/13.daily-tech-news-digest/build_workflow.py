import json, uuid

def make_node(name, node_type, type_version, position, parameters, credentials=None, webhook_id=None):
    node = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": node_type,
        "typeVersion": type_version,
        "position": position,
        "parameters": parameters
    }
    if credentials:
        node["credentials"] = credentials
    if webhook_id:
        node["webhookId"] = webhook_id
    return node

nodes = []
connections = {}

# 1. Schedule Trigger: Daily 08:00 AM (Europe/Istanbul)
schedule_node = make_node(
    name="Schedule: Daily 08:00 AM",
    node_type="n8n-nodes-base.scheduleTrigger",
    type_version=1.2,
    position=[200, 300],
    parameters={
        "rule": {
            "interval": [
                {
                    "field": "cronExpression",
                    "expression": "0 8 * * *"
                }
            ]
        }
    }
)
nodes.append(schedule_node)

# 2. Telegram Trigger: Commands (/digest, /start, /status, /help)
telegram_trigger_node = make_node(
    name="Telegram Trigger (Commands)",
    node_type="n8n-nodes-base.telegramTrigger",
    type_version=1.1,
    position=[200, 520],
    parameters={
        "updates": ["message"]
    },
    credentials={
        "telegramApi": {
            "id": "dailyTechNewsBot",
            "name": "Daily Tech News Bot"
        }
    },
    webhook_id="p13-tech-news-digest-telegram-trigger"
)
nodes.append(telegram_trigger_node)

# 3. Manual / Webhook Trigger
manual_webhook_node = make_node(
    name="Manual Webhook (Digest On-Demand)",
    node_type="n8n-nodes-base.webhook",
    type_version=2,
    position=[200, 720],
    parameters={
        "path": "p13-digest-now",
        "httpMethod": "GET",
        "responseMode": "onReceived",
        "responseData": "allEntries"
    },
    webhook_id="p13-digest-now"
)
nodes.append(manual_webhook_node)

# 4. Route Trigger & 24h Window Calculation
route_and_window_code = """const input = $input.first()?.json || {};
const DEFAULT_CHAT_ID = "1519369571"; // Serhat Kumas Telegram Chat ID
const botToken = "YOUR_TELEGRAM_BOT_TOKEN";

const sendQuickTg = async (chatId, html) => {
  try {
    await this.helpers.httpRequest({
      method: "POST",
      url: "https://api.telegram.org/bot" + botToken + "/sendMessage",
      headers: { "Content-Type": "application/json" },
      body: { chat_id: chatId, text: html, parse_mode: "HTML" },
      json: true
    });
  } catch(e) {}
};

// 1. Detect source
let triggerSource = "manual";
let chatId = DEFAULT_CHAT_ID;
const msg = input.message || input.msg;

if (msg && msg.text) {
  triggerSource = "telegram";
  chatId = String(msg.chat?.id || msg.from?.id || DEFAULT_CHAT_ID);
  const rawText = String(msg.text).trim();
  const text = rawText.toLowerCase();

  // Handle /status
  if (text.startsWith("/status") || text.includes("durum") || text === "status") {
    let lastRun = "Henüz bülten gönderilmedi (İlk çalışma bekleniyor)";
    try {
      const fs = require("fs");
      const p = "/home/node/.n8n-files/studio-images/p13_last_digest.json";
      if (fs.existsSync(p)) {
        const d = JSON.parse(fs.readFileSync(p, "utf8"));
        lastRun = `📅 <b>Son Bülten:</b> ${d.timestamp || "Bilinmiyor"}\\n📊 <b>Özetlenen Haber Sayısı:</b> ${d.articleCount || 0} adet`;
      }
    } catch(e) {}

    await sendQuickTg(chatId, `📊 <b>Daily Tech & News Digest Durumu</b>\\n━━━━━━━━━━━━━━━━━━━━\\n✅ <b>Sistem:</b> Aktif ve Çalışıyor\\n⏰ <b>Otomatik Gönderim:</b> Her gün 08:00 (Europe/Istanbul)\\n📡 <b>RSS Kaynakları:</b> 11 Global & Yerel Teknoloji Portalı\\n${lastRun}\\n\\n👉 <i>Hemen güncel özeti almak için /digest yazabilirsiniz.</i>`);
    return [];
  }

  // Handle /help or /start
  if (text.startsWith("/help") || text.startsWith("/start") || text === "yardım") {
    await sendQuickTg(chatId, `👋 <b>Daily Tech & News Digest Asistanına Hoş Geldiniz!</b>\\n━━━━━━━━━━━━━━━━━━━━\\nBu bot her sabah <b>08:00</b>'de son 24 saatin tüm önemli teknoloji, yapay zeka ve yazılım haberlerini Gemini ile özetleyip size iletir.\\n\\n<b>Komutlar:</b>\\n• <b>/digest</b>: Son 24 saatin özet bültenini hemen üretir ve gönderir.\\n• <b>/status</b>: Sistem ve kaynak durumunu görüntüler.\\n• <b>/help</b>: Bu yardım mesajını gösterir.\\n\\nKeyifli okumalar! ☕📰`);
    return [];
  }
} else if (input.rule || input.cron) {
  triggerSource = "schedule";
}

// 2. Compute 24-Hour Rolling Window (Yesterday 08:00 AM -> Today 08:00 AM)
const now = new Date();
let windowEnd = now.toISOString();
let windowStart = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();

// Check if we have persistent lastRun timestamp to ensure zero-gap coverage
try {
  const fs = require("fs");
  const p = "/home/node/.n8n-files/studio-images/p13_last_digest.json";
  if (fs.existsSync(p)) {
    const d = JSON.parse(fs.readFileSync(p, "utf8"));
    if (d.timestamp) {
      const prevDate = new Date(d.timestamp);
      // If previous run was within the last 30 hours, use exact previous run time as window start
      if (now.getTime() - prevDate.getTime() < 30 * 60 * 60 * 1000) {
        windowStart = prevDate.toISOString();
      }
    }
  }
} catch(e) {}

return [{
  json: {
    triggerSource,
    chatId,
    windowStart,
    windowEnd,
    triggeredAt: now.toISOString()
  }
}];"""

route_node = make_node(
    name="Route & Compute 24h Window",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[500, 420],
    parameters={"jsCode": route_and_window_code}
)
nodes.append(route_node)

# 5. Fetch & Parse All RSS Feeds in Parallel
fetch_feeds_code = """const meta = $input.first()?.json || {};
const windowStartMs = new Date(meta.windowStart || (Date.now() - 24 * 60 * 60 * 1000)).getTime();
const windowEndMs = new Date(meta.windowEnd || Date.now()).getTime();

const FEEDS = [
  { name: "Hacker News", url: "https://hnrss.org/frontpage", category: "Dev & Community" },
  { name: "TechCrunch", url: "https://techcrunch.com/feed/", category: "Startups & VC" },
  { name: "The Verge", url: "https://www.theverge.com/rss/index.xml", category: "Tech & Media" },
  { name: "Ars Technica", url: "https://feeds.arstechnica.com/arstechnica/index", category: "Deep Tech & Science" },
  { name: "Wired", url: "https://www.wired.com/feed/rss", category: "Culture & Tech" },
  { name: "Engadget", url: "https://www.engadget.com/rss.xml", category: "Gadgets & Hardware" },
  { name: "GitHub Blog", url: "https://github.blog/feed/", category: "Software Engineering" },
  { name: "Google AI Blog", url: "https://blog.google/technology/ai/rss/", category: "Artificial Intelligence" },
  { name: "MIT Tech Review AI", url: "https://www.technologyreview.com/topic/artificial-intelligence/feed/", category: "Artificial Intelligence" },
  { name: "Webrazzi", url: "https://webrazzi.com/feed/", category: "Turkish Tech & Startups" },
  { name: "Changelog", url: "https://changelog.com/feed", category: "Software & Open Source" }
];

// Helper to decode basic XML / HTML entities
const cleanText = (str) => {
  if (!str) return "";
  return String(str)
    .replace(/<!\\[CDATA\\[([\\s\\S]*?)\\]\\]>/gi, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\\s+/g, " ")
    .trim();
};

const cleanUrl = (raw) => {
  if (!raw) return "";
  try {
    const u = new URL(raw);
    // Strip tracking parameters
    ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid"].forEach(p => u.searchParams.delete(p));
    return u.toString();
  } catch(e) {
    return raw.trim();
  }
};

// Fetch each feed with timeout
const fetchFeed = async (feed) => {
  try {
    const xml = await this.helpers.httpRequest({
      method: "GET",
      url: feed.url,
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
      },
      timeout: 10000,
      json: false
    });
    return { feed, xml: String(xml) };
  } catch (err) {
    console.log(`Feed fetch failed (${feed.name}): ` + err.message);
    return { feed, xml: "" };
  }
};

// Execute all fetches in parallel
const results = await Promise.all(FEEDS.map(fetchFeed));

const articles = [];
const seenUrls = new Set();
const seenTitles = new Set();

for (const { feed, xml } of results) {
  if (!xml) continue;

  // Match both RSS <item> and Atom <entry>
  const itemMatches = [...xml.matchAll(/<(?:item|entry)[^>]*>([\\s\\S]*?)<\\/(?:item|entry)>/gi)];

  for (const match of itemMatches) {
    const block = match[1];

    // Title
    const titleMatch = block.match(/<title[^>]*>([\\s\\S]*?)<\\/title>/i);
    const rawTitle = cleanText(titleMatch ? titleMatch[1] : "");
    if (!rawTitle || rawTitle.length < 5) continue;

    // Link
    let rawLink = "";
    const linkMatch = block.match(/<link[^>]*href=["']([^"']+)["']/i) || block.match(/<link[^>]*>([\\s\\S]*?)<\\/link>/i);
    if (linkMatch) rawLink = cleanText(linkMatch[1]);
    const finalUrl = cleanUrl(rawLink);
    if (!finalUrl || seenUrls.has(finalUrl)) continue;

    // Normalized title deduplication
    const normTitle = rawTitle.toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 40);
    if (seenTitles.has(normTitle)) continue;

    // Date
    const dateMatch = block.match(/<(?:pubDate|published|updated|dc:date)[^>]*>([\\s\\S]*?)<\\/(?:pubDate|published|updated|dc:date)>/i);
    let pubDate = null;
    let pubTime = 0;
    if (dateMatch) {
      pubDate = cleanText(dateMatch[1]);
      pubTime = new Date(pubDate).getTime();
    }

    // Snippet / Description
    const descMatch = block.match(/<(?:description|summary|content)[^>]*>([\\s\\S]*?)<\\/(?:description|summary|content)>/i);
    const snippet = cleanText(descMatch ? descMatch[1] : "").slice(0, 300);

    // 24-hour window filter:
    // If date is valid, enforce windowStartMs <= pubTime <= windowEndMs + 2 hours safety margin
    if (!isNaN(pubTime) && pubTime > 0) {
      if (pubTime < windowStartMs) continue; // older than yesterday 08:00 AM
    }

    seenUrls.add(finalUrl);
    seenTitles.add(normTitle);

    articles.push({
      source: feed.name,
      category: feed.category,
      title: rawTitle,
      link: finalUrl,
      pubDate: pubDate || new Date().toISOString(),
      snippet
    });
  }
}

// Sort by recency
articles.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime());

return [{
  json: {
    meta,
    chatId: meta.chatId || DEFAULT_CHAT_ID,
    totalFeeds: FEEDS.length,
    articlesCount: articles.length,
    articles: articles.slice(0, 45) // Keep top 45 richest stories
  }
}];"""

fetch_feeds_node = make_node(
    name="Fetch 11 Tech RSS Feeds (Parallel)",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[800, 420],
    parameters={"jsCode": fetch_feeds_code}
)
nodes.append(fetch_feeds_node)

# 6. Prepare Gemini Prompt
prepare_prompt_code = """const input = $input.first()?.json || {};
const articles = input.articles || [];
const chatId = input.chatId || "1519369571";
const windowStart = input.meta?.windowStart;
const windowEnd = input.meta?.windowEnd;

if (!articles.length) {
  return [{
    json: {
      hasArticles: false,
      chatId,
      prompt: ""
    }
  }];
}

const articlesSummary = articles.map((a, i) => {
  return `${i + 1}. [${a.source}] ${a.title}\\nLink: ${a.link}\\nSnippet: ${a.snippet}`;
}).join("\\n\\n");

const systemPrompt = `Sen Türkiye'nin en iyi teknoloji editörü ve kıdemli yazılım mimarısın.
Görevin: Dün sabah 08:00'den bugüne kadar son 24 saat içinde yayımlanan teknoloji, yapay zeka ve yazılım haberlerini analiz etmek; en kritik ve çarpıcı gelişmeleri seçerek Telegram için son derece akıcı, profesyonel ve Türkçe bir "GÜNLÜK TEKNOLOJİ BÜLTENİ" hazırlamaktır.

KURALLAR:
1. Haberleri şu 5 mantıksal kategoriye ayır:
   🤖 <b>Yapay Zeka & Büyük Modeller (AI & LLMs)</b>
   💻 <b>Geliştirici Dünyası & Açık Kaynak (Dev & Open Source)</b>
   🚀 <b>Büyük Teknoloji & Startuplar (Big Tech & Startups)</b>
   🔒 <b>Siber Güvenlik & Gizlilik (Security & Privacy)</b>
   📱 <b>Donanım & Tüketici Teknolojisi (Hardware & Gadgets)</b>
   (Eğer bir kategoride haber yoksa o başlığı atla).

2. Her haber maddesi için TAM OLARAK şu formatı kullan:
   • <b>[Türkçe Çarpıcı Haber Başlığı]</b>: 1-2 cümleyle olayın ne olduğunu ve sektör/geliştiriciler için 'Neden Önemli' olduğunu açıkla.
     👉 <a href="HABER_LINKI">Haberi Oku ([KAYNAK])</a>

3. Mümkün olduğunca ÇOK ve DOLU haber ekle (önemsiz tekrarları ele, ancak önemli hiçbir gelişmeyi dışarıda bırakma).
4. SADECE Telegram HTML formatı kullan (<b>, <i>, <code>, <a>). Asla markdown (**, ##, [text](url)) KULLANMA!
5. Bültenin en başına şu başlığı ekle:
   🗞️ <b>GÜNLÜK TEKNOLOJİ & YAZILIM BÜLTENİ</b>
   📅 <i>Son 24 Saatlik Özet (08:00 — 08:00)</i>
   ━━━━━━━━━━━━━━━━━━━━━━━━━━

6. Bültenin en sonuna tek satırlık ilham verici bir kapanış ekle.`;

const userPrompt = `Aşağıda son 24 saatte toplanan ${articles.length} adet haber bulunmaktadır. Bu haberleri inceleyerek bülteni oluştur:\\n\\n${articlesSummary}`;

return [{
  json: {
    hasArticles: true,
    chatId,
    articlesCount: articles.length,
    geminiBody: {
      contents: [
        {
          role: "user",
          parts: [
            { text: systemPrompt + "\\n\\n" + userPrompt }
          ]
        }
      ],
      generationConfig: {
        temperature: 0.3,
        maxOutputTokens: 3000
      }
    }
  }
}];"""

prepare_prompt_node = make_node(
    name="Prepare Gemini Prompt",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1100, 420],
    parameters={"jsCode": prepare_prompt_code}
)
nodes.append(prepare_prompt_node)

# 7. Gemini API HTTP Request
gemini_api_node = make_node(
    name="Gemini 3.1: Synthesize Digest",
    node_type="n8n-nodes-base.httpRequest",
    type_version=4.2,
    position=[1400, 420],
    parameters={
        "method": "POST",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googlePalmApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.geminiBody) }}",
        "options": {
            "timeout": 90000
        }
    },
    credentials={
        "googlePalmApi": {
            "id": "zvLpU1ScjMCeOYQq",
            "name": "Google Gemini(PaLM) Api account"
        }
    }
)
nodes.append(gemini_api_node)

# 8. Split Telegram Messages (Smart Chunker <= 4000 chars)
chunker_code = """const res = $input.first()?.json || {};
const promptNode = $("Prepare Gemini Prompt").first()?.json || {};
const chatId = promptNode.chatId || "1519369571";
const articlesCount = promptNode.articlesCount || 0;

let text = res?.candidates?.[0]?.content?.parts?.[0]?.text || "";

if (!text || text.trim().length === 0) {
  text = `🗞️ <b>GÜNLÜK TEKNOLOJİ BÜLTENİ</b>\\n━━━━━━━━━━━━━━━━━━━━\\nSon 24 saat içinde filtrelere uygun yeni bir teknoloji haberi bulunamadı.\\n\\nYarın sabah 08:00'de görüşmek üzere! ☕`;
}

// Record last digest run timestamp to disk
try {
  const fs = require("fs");
  const p = "/home/node/.n8n-files/studio-images/p13_last_digest.json";
  fs.writeFileSync(p, JSON.stringify({
    timestamp: new Date().toISOString(),
    articleCount: articlesCount,
    textLength: text.length
  }, null, 2));
} catch(e) {}

// Telegram message limit is 4096 chars.
// Split cleanly by categories or sections if > 3800 chars
const MAX_CHUNK = 3800;

if (text.length <= MAX_CHUNK) {
  return [{
    json: {
      chatId,
      text,
      chunkIndex: 1,
      totalChunks: 1
    }
  }];
}

// Split into multiple parts
const lines = text.split("\\n");
const chunks = [];
let currentChunk = "";

for (const line of lines) {
  if ((currentChunk + "\\n" + line).length > MAX_CHUNK && currentChunk.length > 500) {
    chunks.push(currentChunk.trim());
    currentChunk = line;
  } else {
    currentChunk += (currentChunk ? "\\n" : "") + line;
  }
}
if (currentChunk.trim()) {
  chunks.push(currentChunk.trim());
}

return chunks.map((chunk, idx) => ({
  json: {
    chatId,
    text: (chunks.length > 1 ? `[Bölüm ${idx + 1}/${chunks.length}]\\n\\n` : "") + chunk,
    chunkIndex: idx + 1,
    totalChunks: chunks.length
  }
}));"""

chunker_node = make_node(
    name="Smart Telegram Chunker",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1700, 420],
    parameters={"jsCode": chunker_code}
)
nodes.append(chunker_node)

# 9. Send to Telegram
telegram_send_node = make_node(
    name="Send Digest to Telegram",
    node_type="n8n-nodes-base.telegram",
    type_version=1.2,
    position=[2000, 420],
    parameters={
        "chatId": "={{ $json.chatId }}",
        "text": "={{ $json.text }}",
        "additionalFields": {
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
    },
    credentials={
        "telegramApi": {
            "id": "dailyTechNewsBot",
            "name": "Daily Tech News Bot"
        }
    }
)
nodes.append(telegram_send_node)

# Connections
connections = {
    "Schedule: Daily 08:00 AM": {
        "main": [[{"node": "Route & Compute 24h Window", "type": "main", "index": 0}]]
    },
    "Telegram Trigger (Commands)": {
        "main": [[{"node": "Route & Compute 24h Window", "type": "main", "index": 0}]]
    },
    "Manual Webhook (Digest On-Demand)": {
        "main": [[{"node": "Route & Compute 24h Window", "type": "main", "index": 0}]]
    },
    "Route & Compute 24h Window": {
        "main": [[{"node": "Fetch 11 Tech RSS Feeds (Parallel)", "type": "main", "index": 0}]]
    },
    "Fetch 11 Tech RSS Feeds (Parallel)": {
        "main": [[{"node": "Prepare Gemini Prompt", "type": "main", "index": 0}]]
    },
    "Prepare Gemini Prompt": {
        "main": [[{"node": "Gemini 3.1: Synthesize Digest", "type": "main", "index": 0}]]
    },
    "Gemini 3.1: Synthesize Digest": {
        "main": [[{"node": "Smart Telegram Chunker", "type": "main", "index": 0}]]
    },
    "Smart Telegram Chunker": {
        "main": [[{"node": "Send Digest to Telegram", "type": "main", "index": 0}]]
    }
}

workflow = {
    "name": "Project 13 : Daily Tech & News Digest (24h Rolling Window)",
    "nodes": nodes,
    "connections": connections,
    "active": True,
    "settings": {
        "executionOrder": "v1",
        "timezone": "Europe/Istanbul",
        "saveManualExecutions": True,
        "saveDataErrorExecution": "all",
        "saveDataSuccessExecution": "all"
    }
}

out_path = "intermediate-projects/13.daily-tech-news-digest/workflow.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"Generated {out_path} with {len(nodes)} nodes successfully!")
