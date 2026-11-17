import json
import uuid

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

FIX_TURKISH_MOJIBAKE_JS = r"""
function fixTurkishMojibake(str) {
  if (!str) return "";
  return String(str)
    // GBK/CP936 Mojibake mapping (common in some LLM tokenizers when generating Turkish in JSON mode)
    .replace(/脺/g, 'Ü').replace(/脰/g, 'Ö').replace(/脟/g, 'Ç').replace(/艧/g, 'ş').replace(/艦/g, 'Ş')
    .replace(/莽/g, 'ç').replace(/臒/g, 'ğ').replace(/臑/g, 'Ğ').replace(/眉/g, 'ü').replace(/枚/g, 'ö')
    .replace(/谋/g, 'ı').replace(/陌/g, 'İ')
    // Latin-1 / Windows-1252 Mojibake mapping
    .replace(/Ã¼/g, 'ü').replace(/Ãœ/g, 'Ü').replace(/Ã¶/g, 'ö').replace(/Ã–/g, 'Ö')
    .replace(/Ã§/g, 'ç').replace(/Ã‡/g, 'Ç').replace(/ÄŸ/g, 'ğ').replace(/Äž/g, 'Ğ')
    .replace(/Ä±/g, 'ı').replace(/Ä°/g, 'İ').replace(/ÅŸ/g, 'ş').replace(/Åž/g, 'Ş');
}
"""

# =============================================================================
# 1. TELEGRAM TRIGGER (COMMANDS, CV & CALLBACK QUERY)
# =============================================================================
telegram_trigger_node = make_node(
    name="Telegram Trigger (Private Career Bot)",
    node_type="n8n-nodes-base.telegramTrigger",
    type_version=1.1,
    position=[200, 300],
    parameters={
        "updates": ["message", "callback_query"]
    },
    credentials={
        "telegramApi": {
            "id": "jobHunterBot",
            "name": "Job Hunter Bot"
        }
    },
    webhook_id="p15-ai-personal-job-hunter-telegram-trigger"
)
telegram_trigger_node["id"] = "p15-telegram-trigger-node-001"
nodes.append(telegram_trigger_node)

# =============================================================================
# 2. CENTRAL AUTH & EVENT ROUTER
# =============================================================================
router_node = make_node(
    name="Central Auth & Command Router",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[440, 300],
    parameters={
        "jsCode": """// =========================================================================
// 🔒 CENTRAL AUTH & COMMAND ROUTER (SERHAT KUMAŞ PRIVATE CAREER BOT)
// =========================================================================
const item = $input.first().json;

// Extract update data
const message = item.message || {};
const callbackQuery = item.callback_query || {};
const fromUser = message.from || callbackQuery.from || {};
const chatId = String(message.chat?.id || callbackQuery.message?.chat?.id || '');
const username = fromUser.username || '';
const rawText = (message.text || message.caption || callbackQuery.data || '').trim();

// 🔒 SECURITY CHECK: Private to Serhat Kumaş (chatId: 1519369571)
const AUTHORIZED_CHAT_ID = '1519369571';
if (chatId !== AUTHORIZED_CHAT_ID && !username.toLowerCase().includes('serhatkumas')) {
  return [{
    json: {
      action: 'UNAUTHORIZED',
      chatId: chatId,
      replyText: '⛔ <b>Erişim Engellendi</b>\\n\\nBu bot Serhat Kumaş için özel olarak geliştirilmiş otonom kariyer & iş avcısı ajanıdır. Dışarıdan kullanıma kapalıdır.',
      isJobHunt: false
    }
  }];
}

// Persistent Profile in Workflow Static Data
const staticData = $getWorkflowStaticData('global');
staticData.userProfile = {
  name: 'Serhat Kumaş',
  title: 'Solutions Architect & AI Engineer',
  seniority: 'Solutions Architect / AI & Backend Software Engineer',
  targetRoles: [
    'AI Engineer',
    'AI Solutions Architect',
    'Forward Deployed Engineer (FDE)',
    'Forward Deployed Software Developer',
    'Backend Developer',
    'AI Integrations & Applications Engineer'
  ],
  focusArea: 'Where AI applications and software meet: Production AI engineering, LLM integrations, AI agents, RAG, tool calling, API design, scalable backends, workflow automation (not academic ML training, but practical applied AI).',
  currentRole: 'Solutions Architect @ BSH Hausgeräte (Munich) - Multi-agent systems with Google ADK, AWS video platform, enterprise AI solutions',
  education: [
    'M.Sc. in Computer Science - Universität Passau (2025 - Current)',
    'B.Sc. in Computer Engineering - Izmir Institute of Technology (2018 - 2023)',
    'B.Sc. in Business Administration - Anadolu University (2020 - 2025)'
  ],
  languages: ['Turkish (Native)', 'English (C1 - Advanced)', 'German (A2 - In Progress)'],
  primarySkills: [
    'Python', 'Java', 'C#', 'JavaScript (ES6+)', 'SQL',
    'Agentic AI & Multi-Agent Systems',
    'Google Agent Development Kit (ADK)',
    'A2A (Agent-to-Agent) Protocols & Intent Routing',
    'LLM Orchestration & Context Engineering',
    'Retrieval-Augmented Generation (RAG)',
    'Guardrails & AI Governance',
    'OpenAI API & Gemini API & Dialogflow CX',
    'System Design & Microservices Architecture',
    'Event-Driven Architecture & RESTful APIs',
    'Node.js & Spring Boot & Flask',
    'AWS & Google Cloud (GCP)',
    'PostgreSQL & SQLite & Redis',
    'OAuth 2.0 & Enterprise SSO',
    'React.js & Vue.js & Modern Web',
    'Docker & CI/CD & Git & Postman',
    'n8n (Advanced Workflow Automation)',
    'Distributed Systems & OOP'
  ],
  preferredLocations: ['Passau / Munich / Germany', 'Remote (Global & EU)', 'Europe (UK / Netherlands)', 'Turkey'],
  updatedAt: new Date().toISOString()
};
let storedProfile = staticData.userProfile;

const lower = rawText.toLowerCase();

// 1. HELP / START
if (lower === '/start' || lower === '/help' || lower === '/yardim' || lower === 'start') {
  const intro = `👋 <b>Hoş Geldiniz Serhat Bey!</b>
🎯 <b>AI Personal Job Hunter & Kariyer Ajanınız Aktif</b>
━━━━━━━━━━━━━━━━━━━━
Bu bot sizin adınıza <b>LinkedIn</b>, <b>Indeed</b>, <b>Greenhouse</b>, <b>Lever</b> ve dev teknoloji şirketlerinin (Google, Amazon, Meta vb.) kariyer sayfalarını tarayarak profilinize en uygun <b>10 iş ilanını</b> bulur ve yapay zeka ile skorlar.

🛠️ <b>Kayıtlı Hedef Roller:</b>
• AI Engineer & AI Solutions Architect
• Forward Deployed Engineer (FDE)
• Forward Deployed Software Developer
• Backend Developer & AI Integrations

📍 <b>Kullanabileceğiniz Komutlar:</b>
• <code>/hunt</code> ➔ En güncel 10 global/remote iş fırsatını tara
• <code>/hunt remote</code> ➔ Yalnızca %100 Remote ilanları listele
• <code>/hunt Germany</code> / <code>/hunt London</code> ➔ Belirli ülke/şehirdeki ilanları listele
• <code>/mycv</code> ➔ Sistem hafızasındaki güncel CV profilinizi görüntüleyin
• <i>(Yeni bir CV metni veya PDF göndererek profilinizi dilediğiniz an güncelleyebilirsiniz)</i>

👇 Aşağıdaki butonları kullanarak hemen bir arama başlatabilirsiniz:`;

  return [{
    json: {
      action: 'DIRECT_REPLY',
      chatId: chatId,
      replyText: intro,
      replyButtons: [
        [
          { text: '🎯 10 İş İlanı Bul (/hunt)', callback_data: 'hunt_default' },
          { text: '🌐 Yalnızca Remote', callback_data: 'hunt_remote' }
        ],
        [
          { text: '🇪🇺 Avrupa İlanları', callback_data: 'hunt_eu' },
          { text: '🇹🇷 Türkiye İlanları', callback_data: 'hunt_tr' }
        ],
        [
          { text: '📄 Kayıtlı CV Profilim', callback_data: 'view_cv' }
        ]
      ],
      isJobHunt: false
    }
  }];
}

// 2. VIEW CV PROFILE
if (lower === '/mycv' || lower === 'view_cv' || lower === 'cv' || lower === 'profil') {
  let profileText = `📄 <b>Kayıtlı CV & Kariyer Profiliniz:</b>
━━━━━━━━━━━━━━━━━━━━
👤 <b>Aday:</b> ${storedProfile.name || 'Serhat Kumaş'}
💼 <b>Pozisyon:</b> ${storedProfile.title || 'Solutions Architect & AI Engineer'}
🏢 <b>Mevcut Rol:</b> Solutions Architect @ BSH Hausgeräte (Munich)
🎓 <b>Eğitim:</b> Universität Passau (M.Sc. CS), İYTE (B.Sc. Bilgisayar Müh.)
🗣️ <b>Diller:</b> Türkçe (Anadil), İngilizce (C1 - İleri), Almanca (A2)
🎯 <b>Odak Alanı:</b> ${storedProfile.focusArea}

🛠️ <b>Hedef Pozisyonlar:</b>
${(storedProfile.targetRoles || []).map(r => `• ${r}`).join('\\n')}

💻 <b>Öne Çıkan Yetenek Seti:</b>
• <b>AI & Ajan Sistemleri:</b> Agentic AI, Multi-Agent Systems, Google ADK, A2A Protocols, RAG, Prompt Engineering, Guardrails & Governance, OpenAI API, Dialogflow CX
• <b>Backend, Cloud & Mimari:</b> System Design, Microservices, Event-Driven, Node.js, Spring Boot, Flask, AWS, GCP, PostgreSQL, OAuth 2.0, SSO
• <b>Programlama Dilleri:</b> Python, Java, C#, JavaScript (ES6+), SQL, Solidity
• <b>Araçlar & Otomasyon:</b> n8n, Docker, Git, CI/CD, Postman, Jira, OOP

🌍 <b>Tercih Edilen Lokasyonlar:</b>
${(storedProfile.preferredLocations || ['Germany', 'Remote', 'Europe', 'Turkey']).join(' • ')}

🗓️ <i>Son Güncelleme: ${new Date(storedProfile.updatedAt || Date.now()).toLocaleString('tr-TR')}</i>
━━━━━━━━━━━━━━━━━━━━
💡 <i>Profiliniz en güncel CV'niz doğrultusunda tam senkronize edilmiştir.</i>`;

  return [{
    json: {
      action: 'DIRECT_REPLY',
      chatId: chatId,
      replyText: profileText,
      replyButtons: [
        [
          { text: '🎯 Bu Profile Uygun İlanları Tara', callback_data: 'hunt_default' },
          { text: '🌐 Remote Ara', callback_data: 'hunt_remote' }
        ]
      ],
      isJobHunt: false
    }
  }];
}

// 3. CV UPDATE VIA TEXT (User pasted or typed CV text)
if (rawText.length > 150 && (lower.includes('experience') || lower.includes('deneyim') || lower.includes('skills') || lower.includes('yetenek') || lower.includes('education') || lower.includes('eğitim') || lower.includes('developer') || lower.includes('engineer'))) {
  // Update rawCvText in stored profile
  const updatedProfile = {
    ...(storedProfile || {}),
    name: 'Serhat Kumaş',
    chatId: chatId,
    updatedAt: new Date().toISOString(),
    rawCvText: rawText,
    summary: rawText.slice(0, 300) + '...'
  };
  staticData.userProfile = updatedProfile;
  storedProfile = updatedProfile;

  return [{
    json: {
      action: 'DIRECT_REPLY',
      chatId: chatId,
      replyText: `✅ <b>CV Metniniz Başarıyla Kaydedildi!</b>\\n━━━━━━━━━━━━━━━━━━━━\\nSistem hafızası güncellendi. Artık <code>/hunt</code> komutuyla iş araması yaptığınızda yeni profil detaylarınız dikkate alınacaktır.`,
      replyButtons: [
        [{ text: '🎯 Hemen 10 Eşleşen İlan Bul', callback_data: 'hunt_default' }]
      ],
      isJobHunt: false
    }
  }];
}

// 4. JOB HUNT TRIGGER
let locationFilter = 'remote';
let customRole = '';

if (lower.startsWith('/hunt') || lower.startsWith('hunt') || lower.startsWith('iş bul') || lower.startsWith('iş ara')) {
  const parts = rawText.replace(/^\\/hunt/i, '').replace(/^hunt/i, '').trim();
  if (parts) {
    locationFilter = parts;
  }
} else if (rawText === 'hunt_default' || rawText === 'hunt_remote') {
  locationFilter = 'remote';
} else if (rawText === 'hunt_eu') {
  locationFilter = 'Europe OR Germany OR UK OR Netherlands';
} else if (rawText === 'hunt_tr') {
  locationFilter = 'Turkey OR Istanbul OR Ankara';
}

return [{
  json: {
    action: 'JOB_HUNT',
    chatId: chatId,
    locationFilter: locationFilter,
    targetRoles: storedProfile?.targetRoles || [
      'AI Engineer',
      'AI Solutions Architect',
      'Forward Deployed Engineer',
      'Forward Deployed Software Developer',
      'Backend Developer',
      'AI Integrations Engineer'
    ],
    primarySkills: storedProfile?.primarySkills || [],
    focusArea: storedProfile?.focusArea || '',
    isJobHunt: true
  }
}];"""
    }
)
nodes.append(router_node)

# =============================================================================
# 3. IF NODE: IS JOB HUNT REQUEST?
# =============================================================================
is_job_hunt_if = make_node(
    name="Is Job Hunt Request?",
    node_type="n8n-nodes-base.if",
    type_version=1,
    position=[680, 300],
    parameters={
        "conditions": {
            "boolean": [
                {
                    "value1": "={{ $json.isJobHunt }}",
                    "value2": True
                }
            ]
        }
    }
)
nodes.append(is_job_hunt_if)

# =============================================================================
# 4. DIRECT TELEGRAM REPLY (FOR HELP, MYCV, INFO)
# =============================================================================
direct_reply_node = make_node(
    name="Send Direct Telegram Reply",
    node_type="n8n-nodes-base.telegram",
    type_version=1.2,
    position=[920, 480],
    parameters={
        "chatId": "={{ $json.chatId }}",
        "text": "={{ $json.replyText }}",
        "additionalFields": {
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": "={{ $json.replyButtons || [] }}"
            }
        }
    },
    credentials={
        "telegramApi": {
            "id": "jobHunterBot",
            "name": "Job Hunter Bot"
        }
    }
)
nodes.append(direct_reply_node)

# =============================================================================
# 5. SEND SEARCHING NOTICE TO TELEGRAM
# =============================================================================
send_searching_notice = make_node(
    name="Send Searching Notice to Telegram",
    node_type="n8n-nodes-base.telegram",
    type_version=1.2,
    position=[920, 180],
    parameters={
        "chatId": "={{ $json.chatId }}",
        "text": """=🔍 <b>Kişiselleştirilmiş İş Avı Başlatıldı!</b>
━━━━━━━━━━━━━━━━━━━━
🎯 <b>Hedef Pozisyonlar:</b> AI Engineer, Forward Deployed, AI Solutions Architect, Backend Developer
📍 <b>Konum / Filtre:</b> <code>{{ $json.locationFilter }}</code>
🌐 <b>Taranan Kaynaklar:</b> LinkedIn Jobs, Indeed, Greenhouse, Lever, Google & Amazon Careers
🧠 <b>Eşleştirme Modeli:</b> Gemini 3.1 Flash-Lite AI Matchmaker

⏳ <i>Canlı ilanlar taranıyor ve CV profilinizle kıyaslanıyor (yaklaşık 20-30 saniye)...</i>""",
        "additionalFields": {
            "parse_mode": "HTML"
        }
    },
    credentials={
        "telegramApi": {
            "id": "jobHunterBot",
            "name": "Job Hunter Bot"
        }
    }
)
nodes.append(send_searching_notice)

# =============================================================================
# 6. PREPARE APIFY JOB SEARCH QUERIES
# =============================================================================
prepare_apify_queries = make_node(
    name="Prepare Apify Job Search Queries",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1160, 180],
    parameters={
        "jsCode": """// =========================================================================
// 🌐 PREPARE HIGH-PRECISION APIFY JOB SEARCH QUERIES
// =========================================================================
const huntData = $('Central Auth & Command Router').first().json;
const loc = huntData.locationFilter || 'remote';

// Formulate queries targeted at live job openings
const queries = [
  // 1. LinkedIn Jobs - AI Engineer & Forward Deployed
  `("AI Engineer" OR "Forward Deployed Engineer") ("${loc}") site:linkedin.com/jobs/view`,
  
  // 2. LinkedIn Jobs - AI Solutions Architect & AI Integration
  `("AI Solutions Architect" OR "AI Integration Engineer" OR "AI Application Engineer") ("${loc}") site:linkedin.com/jobs/view`,
  
  // 3. Indeed Jobs - Backend Developer AI & LLM
  `("Backend Developer" OR "Software Engineer") ("AI" OR "LLM") ("${loc}") site:indeed.com/viewjob`,
  
  // 4. Greenhouse & Lever (Top tech startups & scaleups)
  `("AI Engineer" OR "Forward Deployed" OR "AI Integrations") ("${loc}") (site:jobs.lever.co OR site:boards.greenhouse.io)`,
  
  // 5. Big Tech Career Portals (Google, Amazon, Meta, Microsoft)
  `("AI Engineer" OR "Forward Deployed Software Developer" OR "Solutions Architect") site:amazon.jobs OR site:careers.google.com`,
  
  // 6. Direct Remote AI Software Roles
  `("AI Engineer" OR "Forward Deployed Engineer") ("remote" OR "work from home") site:linkedin.com/jobs/view`
];

return [{
  json: {
    ...huntData,
    queries: queries,
    apifyPayload: {
      queries: queries.join('\\n'),
      maxPagesPerQuery: 2,
      resultsPerPage: 10,
      customDataFunction: `async ({ input, $, request, response, html }) => {
        return {
          url: request.url
        };
      };`
    }
  }
}];"""
    }
)
nodes.append(prepare_apify_queries)

# =============================================================================
# 7. EXECUTE APIFY GOOGLE SEARCH SCRAPER
# =============================================================================
apify_job_scraper = make_node(
    name="Scrape Live Job Postings (Apify)",
    node_type="n8n-nodes-base.httpRequest",
    type_version=4.2,
    position=[1400, 180],
    parameters={
        "method": "POST",
        "url": "https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items",
        "authentication": "none",
        "sendQuery": True,
        "queryParameters": {
            "parameters": [
                {"name": "token", "value": "YOUR_APIFY_API_TOKEN"}
            ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.apifyPayload) }}",
        "options": {
            "timeout": 120000
        }
    }
)
nodes.append(apify_job_scraper)

# =============================================================================
# 8. FILTER & CLEAN RAW JOB OPPORTUNITIES
# =============================================================================
filter_raw_jobs = make_node(
    name="Filter & Clean Raw Job Opportunities",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1640, 180],
    parameters={
        "jsCode": """// =========================================================================
// 🧹 EXTRACT, CLEAN & DEDUPLICATE RAW JOB POSTINGS
// =========================================================================
const items = $input.all();
const huntData = $('Central Auth & Command Router').first().json;

const rawJobs = [];
const seenUrls = new Set();

for (const it of items) {
  const row = it.json;
  const organicResults = row.organicResults || [];
  
  for (const org of organicResults) {
    const url = org.url || '';
    const title = org.title || '';
    const description = org.description || '';
    
    if (!url || seenUrls.has(url)) continue;
    
    // Check if it's a job posting URL
    const isJobUrl = url.includes('linkedin.com/jobs') ||
                     url.includes('indeed.com') ||
                     url.includes('jobs.lever.co') ||
                     url.includes('boards.greenhouse.io') ||
                     url.includes('amazon.jobs') ||
                     url.includes('careers.google.com') ||
                     url.includes('smartrecruiters.com') ||
                     url.includes('workable.com') ||
                     url.includes('ashbyhq.com');
                     
    if (!isJobUrl && !title.toLowerCase().includes('engineer') && !title.toLowerCase().includes('developer')) {
      continue;
    }
    
    seenUrls.add(url);
    
    // Extract company name heuristically
    let company = 'Tech Company';
    if (url.includes('linkedin.com')) {
      const match = title.match(/at\\s+([^|\\-\\–]+)/i) || title.match(/\\-\\s+([^|\\-\\–]+)/);
      if (match) company = match[1].trim();
    } else if (url.includes('lever.co')) {
      const parts = url.split('/');
      company = parts[3] ? parts[3].toUpperCase() : 'Startup';
    } else if (url.includes('greenhouse.io')) {
      const parts = url.split('/');
      company = parts[3] ? parts[3].toUpperCase() : 'Company';
    } else if (url.includes('amazon.jobs')) {
      company = 'Amazon';
    } else if (url.includes('careers.google.com')) {
      company = 'Google';
    }
    
    rawJobs.push({
      title: title.replace(/\\|.*$/, '').replace(/\\-.*$/, '').trim(),
      company: company,
      snippet: description,
      url: url
    });
  }
}

// Keep up to 35 candidates for Gemini evaluation
const candidates = rawJobs.slice(0, 35);

return [{
  json: {
    ...huntData,
    candidateCount: candidates.length,
    candidates: candidates
  }
}];"""
    }
)
nodes.append(filter_raw_jobs)

# =============================================================================
# 9. PREPARE GEMINI MATCHMAKER PROMPT
# =============================================================================
prepare_gemini_prompt = make_node(
    name="Prepare Gemini Matchmaker Prompt",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1880, 180],
    parameters={
        "jsCode": """// =========================================================================
// ✍️ PREPARE GEMINI 3.1 AI CAREER MATCHMAKER PROMPT
// =========================================================================
const data = $input.first().json;
const candidates = data.candidates || [];

// Read full CV profile from staticData or fallback
const staticData = $getWorkflowStaticData('global');
const profile = staticData.userProfile || {
  name: 'Serhat Kumaş',
  seniority: 'Mid-to-Senior / Lead AI Solutions & Software Engineer',
  targetRoles: data.targetRoles || [],
  focusArea: data.focusArea || 'Pratik AI mühendisliği, LLM entegrasyonları, yapay zeka ajanları (agents), RAG sistemleri, API orkestrasyonu, ölçeklenebilir backend yazılım mimarisi.',
  primarySkills: data.primarySkills || []
};

const prompt = `Sen dünya çapında üst düzey teknoloji yeteneklerini değerlendiren uzman bir AI Kariyer Danışmanı ve Başvuru Stratejistisin.

ADAY PROFİLİ:
- İsim: Serhat Kumaş
- Unvan & Kıdem: Solutions Architect / AI & Backend Software Engineer (M.Sc. CS at Univ Passau, B.Sc. Comp Eng at IZTECH)
- Güncel Deneyim: Solutions Architect @ BSH Hausgeräte (Munich) - Google Agent Development Kit (ADK), Agent-to-Agent (A2A) hiyerarşik çoklu ajan sistemleri, AWS üzerinde full-stack video platformu (React/Node.js/SSO/OAuth), kurumsal AI çözümleri.
- Hedef Roller: ${JSON.stringify(profile.targetRoles)}
- Odak Alanı: ${profile.focusArea || 'Where AI applications and software meet: Production AI engineering, LLM integrations, AI agents, RAG, tool calling, API design, scalable backends, workflow automation (not academic ML training, but practical applied AI).'}
- Temel Yetenekler:
  * AI & Ajanlar: Agentic AI, Multi-Agent Systems, Google Agent Development Kit (ADK), A2A Protocols, RAG, Prompt Engineering, Guardrails & AI Governance, OpenAI API, Gemini API, Dialogflow CX
  * Backend & Cloud: System Design, Microservices, Event-Driven Architecture, RESTful APIs, Node.js, Spring Boot, Flask, AWS, GCP, PostgreSQL, OAuth 2.0, SSO, Distributed Systems
  * Diller: Python, Java, C#, JavaScript (ES6+), SQL, Solidity
  * Araçlar & Otomasyon: n8n (Workflow Automation), Docker, Git, CI/CD, Postman, Jira, OOP
- Diller: Türkçe (Anadil), İngilizce (C1 - İleri Seviye), Almanca (A2)
- Tercih Edilen Lokasyonlar: ${JSON.stringify(profile.preferredLocations || ['Germany', 'Remote', 'Europe', 'Turkey'])}

GÖREVİN:
Aşağıda verilen ${candidates.length} adet ham iş ilanını Serhat'ın profil ve yetenekleriyle derinlemesine kıyasla.
Adayın profiline EN ÇOK UYAN en kaliteli 10 iş ilanını seç, her birine 100 üzerinden uygunluk skoru ver ve aşağıdaki formatta JSON olarak döndür.

DEĞERLENDİRME KRİTERLERİ:
1. Pratik AI mühendisliği, Forward Deployed geliştirme, LLM/Agent entegrasyonu ve backend mimarisi içeren ilanlara EN YÜKSEK skorları (%90-99) ver.
2. Neden uygun olduğunu (whyFit) samimi, profesyonel ve ikna edici 1-2 cümleyle açıkla (Serhat'ın hangi gücüyle bu işin tam oturduğunu belirt).
3. Eşleşen kritik yetenekleri (matchingSkills) adayın CV'sinden 3-4 madde olarak belirt.
4. Çalışma modelini belirle (Remote, Hybrid, London, Istanbul, vb.).

İŞ İLANLARI LİSTESİ:
${JSON.stringify(candidates, null, 2)}

ÇIKTI FORMATI:
Yalnızca geçerli bir JSON array döndür (kesinlikle markdown bloğu veya fazladan metin ekleme):
[
  {
    "title": "İlan Başlığı (Örn: Forward Deployed AI Engineer)",
    "company": "Şirket Adı",
    "location": "Remote / London / Istanbul",
    "fitScore": 95,
    "fitBadge": "🌟 Mükemmel Eşleşme (%95)",
    "whyFit": "Neden Serhat'ın profiline tam oturuyor (1-2 profesyonel Türkçe cümle)",
    "matchingSkills": ["Python", "LLM Agents", "FastAPI", "API Integrations"],
    "applyUrl": "İlanın orijinal başvuru URL adresi"
  }
]`;

return [{
  json: {
    ...data,
    geminiPrompt: prompt
  }
}];"""
    }
)
nodes.append(prepare_gemini_prompt)

# =============================================================================
# 10. GEMINI 3.1 AI CAREER MATCHMAKER
# =============================================================================
gemini_matcher = make_node(
    name="Agent: AI Career Matchmaker (Gemini 3.1)",
    node_type="n8n-nodes-base.httpRequest",
    type_version=4.2,
    position=[2120, 180],
    parameters={
        "method": "POST",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googlePalmApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": """={\n  "contents": [\n    {\n      "parts": [\n        {\n          "text": {{ JSON.stringify($json.geminiPrompt) }}\n        }\n      ]\n    }\n  ],\n  "generationConfig": {\n    "temperature": 0.4,\n    "responseMimeType": "application/json"\n  }\n}""",
        "options": {
            "timeout": 60000
        }
    },
    credentials={
        "googlePalmApi": {
            "id": "zvLpU1ScjMCeOYQq",
            "name": "Google Gemini(PaLM) Api account"
        }
    }
)
nodes.append(gemini_matcher)

# =============================================================================
# 11. FORMAT TOP 10 JOB CARDS FOR TELEGRAM
# =============================================================================
format_job_cards = make_node(
    name="Format Top 10 Job Cards with Action Buttons",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[2360, 180],
    parameters={
        "jsCode": FIX_TURKISH_MOJIBAKE_JS + """
// =========================================================================
// 📱 FORMAT TOP 10 JOB MATCHES INTO BEAUTIFUL TELEGRAM CARDS
// =========================================================================
const res = $input.first().json;
const huntData = $('Central Auth & Command Router').first().json;

let matchedJobs = [];
try {
  let rawText = res.candidates?.[0]?.content?.parts?.[0]?.text || '[]';
  rawText = rawText.replace(/```json/g, '').replace(/```/g, '').trim();
  rawText = fixTurkishMojibake(rawText);
  matchedJobs = JSON.parse(rawText);
} catch (e) {
  matchedJobs = [];
}

if (!Array.isArray(matchedJobs) || matchedJobs.length === 0) {
  return [{
    json: {
      chatId: huntData.chatId,
      messageText: `⚠️ <b>Arama Tamamlandı Fakat Doğrudan Eşleşen İlan Bulunamadı</b>\\n\\nFiltre: <code>${huntData.locationFilter}</code>\\n\\nLütfen arama teriminizi genişleterek tekrar deneyin (Örn: <code>/hunt remote</code> veya <code>/hunt Europe</code>).`,
      replyButtons: [
        [{ text: '🔄 Tekrar Dene (Remote)', callback_data: 'hunt_remote' }],
        [{ text: '🌍 Tümünü Tara', callback_data: 'hunt_default' }]
      ]
    }
  }];
}

// Sort by fitScore descending & take top 10
matchedJobs.sort((a, b) => (b.fitScore || 0) - (a.fitScore || 0));
const top10 = matchedJobs.slice(0, 10);

// Build Part 1 (Jobs 1 to 5)
let part1Text = `🎯 <b>Serhat Kumaş için En Uygun 10 İş Fırsatı (Bölüm 1/2)</b>
━━━━━━━━━━━━━━━━━━━━
📍 <b>Filtre:</b> <code>${huntData.locationFilter}</code> | ⚡ <b>AI Skorlama:</b> Gemini 3.1
`;

// Build Part 2 (Jobs 6 to 10)
let part2Text = `🎯 <b>Serhat Kumaş için En Uygun 10 İş Fırsatı (Bölüm 2/2)</b>
━━━━━━━━━━━━━━━━━━━━
`;

top10.forEach((j, idx) => {
  const num = idx + 1;
  const title = fixTurkishMojibake(j.title || 'AI Software Engineer');
  const company = fixTurkishMojibake(j.company || 'Teknoloji Şirketi');
  const loc = fixTurkishMojibake(j.location || 'Remote');
  const badge = fixTurkishMojibake(j.fitBadge || `⭐ %${j.fitScore || 90} Uygunluk`);
  const why = fixTurkishMojibake(j.whyFit || 'Profilinizdeki AI mühendisliği ve entegrasyon yetenekleriyle tam örtüşüyor.');
  const skills = (j.matchingSkills || []).join(' • ');
  const applyUrl = j.applyUrl || '#';

  const card = `
${num}️⃣ <b>${title}</b>
🏢 <b>Şirket:</b> ${company} | 📍 <b>Konum:</b> ${loc}
📊 <b>Uyum:</b> <b>${badge}</b>
💡 <b>Neden Uygun:</b> ${why}
🛠️ <b>Eşleşen Yetenekler:</b> <code>${skills}</code>
🔗 👉 <a href="${applyUrl}"><b>[ Hemen Başvur & Detayları Gör ↗ ]</b></a>
━━━━━━━━━━━━━━━━━━━━`;

  if (idx < 5) {
    part1Text += card;
  } else {
    part2Text += card;
  }
});

const inlineButtons = [
  [
    { text: '🔄 Yeniden Ara', callback_data: 'hunt_default' },
    { text: '🌐 Sadece Remote', callback_data: 'hunt_remote' }
  ],
  [
    { text: '🇪🇺 Avrupa İlanları', callback_data: 'hunt_eu' },
    { text: '🇹🇷 Türkiye İlanları', callback_data: 'hunt_tr' }
  ],
  [
    { text: '📄 CV Profilimi Gör', callback_data: 'view_cv' }
  ]
];

return [
  {
    json: {
      chatId: huntData.chatId,
      messageText: part1Text,
      replyButtons: []
    }
  },
  {
    json: {
      chatId: huntData.chatId,
      messageText: part2Text,
      replyButtons: inlineButtons
    }
  }
];"""
    }
)
nodes.append(format_job_cards)

# =============================================================================
# 12. SEND TOP 10 MATCHES TO TELEGRAM
# =============================================================================
send_job_matches = make_node(
    name="Send Top 10 Job Matches to Telegram",
    node_type="n8n-nodes-base.telegram",
    type_version=1.2,
    position=[2600, 180],
    parameters={
        "chatId": "={{ $json.chatId }}",
        "text": "={{ $json.messageText }}",
        "additionalFields": {
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": "={{ $json.replyButtons || [] }}"
            }
        }
    },
    credentials={
        "telegramApi": {
            "id": "jobHunterBot",
            "name": "Job Hunter Bot"
        }
    }
)
nodes.append(send_job_matches)

# =============================================================================
# CONNECTIONS GRAPH
# =============================================================================
connections = {
    "Telegram Trigger (Private Career Bot)": {
        "main": [[{"node": "Central Auth & Command Router", "type": "main", "index": 0}]]
    },
    "Central Auth & Command Router": {
        "main": [[{"node": "Is Job Hunt Request?", "type": "main", "index": 0}]]
    },
    "Is Job Hunt Request?": {
        "main": [
            # Output 0 (True: Job Hunt)
            [{"node": "Send Searching Notice to Telegram", "type": "main", "index": 0}],
            # Output 1 (False: Help, Profile, CV text)
            [{"node": "Send Direct Telegram Reply", "type": "main", "index": 0}]
        ]
    },
    "Send Searching Notice to Telegram": {
        "main": [[{"node": "Prepare Apify Job Search Queries", "type": "main", "index": 0}]]
    },
    "Prepare Apify Job Search Queries": {
        "main": [[{"node": "Scrape Live Job Postings (Apify)", "type": "main", "index": 0}]]
    },
    "Scrape Live Job Postings (Apify)": {
        "main": [[{"node": "Filter & Clean Raw Job Opportunities", "type": "main", "index": 0}]]
    },
    "Filter & Clean Raw Job Opportunities": {
        "main": [[{"node": "Prepare Gemini Matchmaker Prompt", "type": "main", "index": 0}]]
    },
    "Prepare Gemini Matchmaker Prompt": {
        "main": [[{"node": "Agent: AI Career Matchmaker (Gemini 3.1)", "type": "main", "index": 0}]]
    },
    "Agent: AI Career Matchmaker (Gemini 3.1)": {
        "main": [[{"node": "Format Top 10 Job Cards with Action Buttons", "type": "main", "index": 0}]]
    },
    "Format Top 10 Job Cards with Action Buttons": {
        "main": [[{"node": "Send Top 10 Job Matches to Telegram", "type": "main", "index": 0}]]
    }
}

workflow = {
    "id": "ai-personal-job-hunter-00015",
    "name": "Project 15 : AI Personal Job Hunter & Career Matchmaker",
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

out_path = "intermediate-projects/15.ai-personal-job-hunter/workflow.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"Generated {out_path} with {len(nodes)} nodes successfully!")
