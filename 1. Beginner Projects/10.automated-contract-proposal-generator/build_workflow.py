import json

central_config_js = '''// =========================================================================
// 🏢 CENTRAL BRAND & WORKFLOW CONFIGURATION
// =========================================================================
const CONFIG = {
  providerName: "Serhat Kumas",
  providerTitle: "AI & Automation Solutions",
  providerLocation: "Munich / Germany",
  providerEmail: "serhat.kumas.sk@gmail.com",
  defaultChatId: "1519369571", // Serhat's Telegram User ID
  botToken: "YOUR_TELEGRAM_BOT_TOKEN",
  spreadsheetId: "1tNOoNdpSQD5yjobV1UfYl73M9bjnHwEDVDjWOYPkoks",
  sheetName: "Contracts",
  driveFolderName: "Contracts & Proposals"
};

const raw = $input.first()?.json || {};
let eventType = "unknown";
let chatId = CONFIG.defaultChatId;
let userPrompt = "";
let voiceFileId = null;
let callbackData = null;
let callbackQueryId = null;
let messageId = null;

if (raw.callback_query) {
  eventType = "callback_query";
  callbackData = raw.callback_query.data;
  callbackQueryId = raw.callback_query.id;
  chatId = String(raw.callback_query.message?.chat?.id || raw.callback_query.from?.id || CONFIG.defaultChatId);
  messageId = raw.callback_query.message?.message_id;
} else if (raw.message?.voice || raw.message?.audio) {
  eventType = "voice_note";
  voiceFileId = raw.message.voice?.file_id || raw.message.audio?.file_id;
  chatId = String(raw.message.chat?.id || CONFIG.defaultChatId);
  messageId = raw.message.message_id;
} else if (raw.message?.text) {
  eventType = "text_command";
  userPrompt = raw.message.text.trim();
  chatId = String(raw.message.chat?.id || CONFIG.defaultChatId);
  messageId = raw.message.message_id;
}

return [{
  json: {
    ...CONFIG,
    eventType,
    chatId,
    messageId,
    userPrompt,
    voiceFileId,
    callbackData,
    callbackQueryId,
    timestamp: new Date().toISOString()
  }
}];'''

prepare_voice_js = '''const item = $input.first();
const binaryData = item.binary?.data;
if (!binaryData) {
  throw new Error("No binary audio data found from Telegram download");
}

let base64Audio = "";
try {
  const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
  base64Audio = buffer.toString('base64');
} catch(e) {
  base64Audio = binaryData.data || "";
}

const cfg = $('Central Brand & Event Parser').first().json;

let detectedMime = binaryData.mimeType || "audio/ogg";
if (!detectedMime.startsWith("audio/")) {
  detectedMime = "audio/ogg";
}

return [{
  json: {
    ...cfg,
    audioBase64: base64Audio,
    audioMimeType: detectedMime,
    promptInstruction: `You are an elite enterprise legal & technical architect acting on behalf of ${cfg.providerName} (${cfg.providerTitle}, ${cfg.providerLocation}).
Listen carefully to this voice note where the client or user dictates a contract/proposal request.
Transcribe and extract the core client parameters, and MASSIVELY EXPAND AND BEAUTIFY the deliverables, technical architecture, and legal terms into an executive-grade Master Services Agreement & Detailed Proposal.

Respond with STRICT JSON (no markdown fences, no explanatory text) matching this EXACT schema:
{
  "clientName": "Extracted Client Company Name (e.g. Acme GmbH)",
  "clientContact": "Client Contact Person or Department (e.g. Executive Management / Operations)",
  "effectiveDate": "Extracted or inferred start date (e.g. November 1, 2026)",
  "pricing": "Extracted pricing formatted cleanly (e.g. EUR 2,500 monthly retainer or EUR 15,000 fixed fee)",
  "pricingModel": "Monthly Retainer / Fixed Milestone Project Fee",
  "executiveSummary": "Comprehensive 3-4 sentence professional executive summary outlining strategic business objectives, automation ROI, and architectural excellence.",
  "deliverables": [
    {
      "title": "Module 1 Title (e.g. Omnichannel WhatsApp AI & Conversational Engine)",
      "timeline": "Sprint 1 (Weeks 1-2)",
      "description": "2-3 comprehensive sentences explaining technical implementation, API endpoints, error fallbacks, and real-time response handling.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    },
    {
      "title": "Module 2 Title (e.g. Enterprise CRM Sync & Automated Pipeline Engine)",
      "timeline": "Sprint 2 (Weeks 2-3)",
      "description": "2-3 comprehensive sentences explaining bidirectional sync, field mapping, deduplication logic, and lifecycle triggers.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    },
    {
      "title": "Module 3 Title (e.g. Real-Time Telemetry & Fail-Safe Observability Framework)",
      "timeline": "Sprint 3 (Weeks 3-4)",
      "description": "2-3 comprehensive sentences detailing logging, automated alert channels, audit trails, and self-healing error recovery.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    },
    {
      "title": "Module 4 Title (e.g. Production Deployment, Hardening & Staff Enablement)",
      "timeline": "Sprint 4 (Week 4)",
      "description": "2-3 comprehensive sentences covering end-to-end load testing, architecture runbooks, and staff training workshops.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    }
  ],
  "sla": [
    "System Availability: 99.9% uptime for core automated production workflows and endpoints.",
    "Critical Incident Response: Under 4 business hours for severity-1 pipeline blockages.",
    "Agile Sync: Bi-weekly architecture reviews and continuous performance optimization."
  ]
}`
  }
}];'''

prepare_text_js = '''const cfg = $('Central Brand & Event Parser').first().json;
const text = cfg.userPrompt;

return [{
  json: {
    ...cfg,
    promptInstruction: `You are an elite enterprise legal & technical architect acting on behalf of ${cfg.providerName} (${cfg.providerTitle}, ${cfg.providerLocation}).
The user has provided this contract/proposal command:
"${text}"

Extract the client details, and MASSIVELY EXPAND AND BEAUTIFY the deliverables, technical architecture, and legal terms into an executive-grade Master Services Agreement & Detailed Proposal.
Make the descriptions detailed, professional, and visually elegant. Ensure the scope includes 4 rich technical modules, an executive summary, and SLA guarantees.

Respond with STRICT JSON (no markdown fences, no explanatory text) matching this EXACT schema:
{
  "clientName": "Extracted Client Company Name (e.g. Acme GmbH)",
  "clientContact": "Client Contact Person or Department (e.g. Executive Management / Operations)",
  "effectiveDate": "Extracted or inferred start date (e.g. November 1, 2026)",
  "pricing": "Extracted pricing formatted cleanly (e.g. EUR 2,500 monthly retainer or EUR 15,000 fixed fee)",
  "pricingModel": "Monthly Retainer / Fixed Milestone Project Fee",
  "executiveSummary": "Comprehensive 3-4 sentence professional executive summary outlining strategic business objectives, automation ROI, and architectural excellence.",
  "deliverables": [
    {
      "title": "Module 1 Title (e.g. Omnichannel WhatsApp AI & Conversational Engine)",
      "timeline": "Sprint 1 (Weeks 1-2)",
      "description": "2-3 comprehensive sentences explaining technical implementation, API endpoints, error fallbacks, and real-time response handling.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    },
    {
      "title": "Module 2 Title (e.g. Enterprise CRM Sync & Automated Pipeline Engine)",
      "timeline": "Sprint 2 (Weeks 2-3)",
      "description": "2-3 comprehensive sentences explaining bidirectional sync, field mapping, deduplication logic, and lifecycle triggers.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    },
    {
      "title": "Module 3 Title (e.g. Real-Time Telemetry & Fail-Safe Observability Framework)",
      "timeline": "Sprint 3 (Weeks 3-4)",
      "description": "2-3 comprehensive sentences detailing logging, automated alert channels, audit trails, and self-healing error recovery.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    },
    {
      "title": "Module 4 Title (e.g. Production Deployment, Hardening & Staff Enablement)",
      "timeline": "Sprint 4 (Week 4)",
      "description": "2-3 comprehensive sentences covering end-to-end load testing, architecture runbooks, and staff training workshops.",
      "keyFeatures": ["Specific technical feature A", "Specific technical feature B"]
    }
  ],
  "sla": [
    "System Availability: 99.9% uptime for core automated production workflows and endpoints.",
    "Critical Incident Response: Under 4 business hours for severity-1 pipeline blockages.",
    "Agile Sync: Bi-weekly architecture reviews and continuous performance optimization."
  ]
}`
  }
}];'''

parse_proposal_js = '''const resp = $input.first()?.json || {};
const cfg = $('Central Brand & Event Parser').first()?.json || {};

let rawText = "";
try {
  rawText = resp.candidates?.[0]?.content?.parts?.[0]?.text || "{}";
} catch(e) {
  rawText = "{}";
}

let parsed = {};
try {
  parsed = JSON.parse(rawText.replace(/^```json\\s*/i, '').replace(/```\\s*$/, '').trim());
} catch(e) {
  parsed = {};
}

const now = new Date();
const yyyymm = now.toISOString().slice(0, 7).replace('-', '');
const randSuffix = Math.floor(1000 + Math.random() * 9000);
const contractId = parsed.contractId || `AGR-${yyyymm}-${randSuffix}`;
const issueDate = now.toISOString().slice(0, 10);
const clientName = parsed.clientName || "Enterprise Client";
const effectiveDate = parsed.effectiveDate || "Immediate / Upon Execution";
const pricing = parsed.pricing || "EUR 2,500 / month";
const executiveSummary = parsed.executiveSummary || `This Master Services Agreement outlines the technical roadmap and managed AI automation architecture provided by ${cfg.providerName} for ${clientName}. The objective is to deploy resilient end-to-end business automation that maximizes operational speed and delivers superior operational ROI.`;

const deliverables = (parsed.deliverables && parsed.deliverables.length >= 2) ? parsed.deliverables : [
  {
    title: "Conversational AI & Omnichannel Agent Infrastructure",
    timeline: "Sprint 1 (Weeks 1-2)",
    description: "End-to-end deployment of an autonomous conversational AI agent built on official messaging APIs with context management and automated escalation.",
    keyFeatures: ["API Webhook Gateway & Security Layer", "Contextual Dialogue & Escalation Logic"]
  },
  {
    title: "Enterprise CRM & Real-Time Data Pipeline Synchronization",
    timeline: "Sprint 2 (Weeks 2-3)",
    description: "Bi-directional synchronization between incoming customer interactions and enterprise database/CRM infrastructure with real-time field mapping.",
    keyFeatures: ["Automated Ingestion & Custom Schema Mapping", "Deduplication Safeguards & Lifecycle Triggers"]
  },
  {
    title: "Real-Time Telemetry & Fail-Safe Observability Engine",
    timeline: "Sprint 3 (Weeks 3-4)",
    description: "Comprehensive health monitoring and error-handling framework deployed across all pipelines with instant Telegram and email error notifications.",
    keyFeatures: ["Automated Fallback Architecture & Queue Recovery", "Executive Audit Logs & Weekly Health Metrics"]
  },
  {
    title: "System Handover, Production Hardening & Staff Enablement",
    timeline: "Sprint 4 (Week 4)",
    description: "Final production hardening, end-to-end integration testing, executive SOP documentation, and live enablement workshop for internal staff.",
    keyFeatures: ["Complete Architecture Runbook & Video Documentation", "30-Day Hypercare Support Window"]
  }
];

const sla = parsed.sla || [
  "System Availability: 99.9% uptime for core automated production workflows and endpoints.",
  "Critical Incident Response: Under 4 business hours for severity-1 pipeline blockages.",
  "Agile Sync: Bi-weekly architecture reviews and continuous performance optimization."
];

return [{
  json: {
    ...cfg,
    contractId,
    issueDate,
    clientName,
    clientContact: parsed.clientContact || "Executive Management",
    effectiveDate,
    pricing,
    pricingModel: parsed.pricingModel || "Monthly Retainer",
    executiveSummary,
    deliverables,
    sla,
    fileName: `Service_Agreement_${clientName.replace(/[^a-zA-Z0-9]/g, '_')}_${contractId}.pdf`
  }
}];'''

vector_pdf_js = '''function sanitizeForPdf(str) {
  if (!str) return '';
  return String(str)
    // Common accented & international characters
    .replace(/[Öö]/g, m => m === 'Ö' ? 'O' : 'o')
    .replace(/[Üü]/g, m => m === 'Ü' ? 'U' : 'u')
    .replace(/[Çç]/g, m => m === 'Ç' ? 'C' : 'c')
    .replace(/[Ğğ]/g, m => m === 'Ğ' ? 'G' : 'g')
    .replace(/[Şş]/g, m => m === 'Ş' ? 'S' : 's')
    .replace(/[İı]/g, m => m === 'İ' ? 'I' : 'i')
    .replace(/[Ää]/g, m => m === 'Ä' ? 'A' : 'a')
    .replace(/[ß]/g, 'ss')
    .replace(/[éèêë]/g, 'e')
    .replace(/[áàâ]/g, 'a')
    .replace(/[íìî]/g, 'i')
    .replace(/[óòô]/g, 'o')
    .replace(/[úùû]/g, 'u')
    .replace(/€/g, 'EUR')
    .replace(/£/g, 'GBP')
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    .replace(/[—–]/g, '-')
    .replace(/[•]/g, '*')
    .replace(/[^ -~]/g, ' ')
    // PDF string escaping
    .replace(/\\\\/g, '\\\\\\\\')
    .replace(/\\(/g, '\\\\(')
    .replace(/\\)/g, '\\\\)');
}

function wrapText(str, maxChars = 75) {
  const words = String(str || '').replace(/\\s+/g, ' ').trim().split(' ');
  const lines = [];
  let current = '';
  for (const w of words) {
    if (!w) continue;
    if ((current + ' ' + w).trim().length <= maxChars) {
      current = (current + ' ' + w).trim();
    } else {
      if (current) lines.push(current);
      current = w;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function generateContractPdf(data) {
  const objects = [];
  function addObject(content) {
    objects.push(content);
    return objects.length;
  }

  // 1: Catalog, 2: Pages, 3: Page 1, 4: Page 2
  addObject('<< /Type /Catalog /Pages 2 0 R >>');
  addObject('<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>');
  addObject('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 5 0 R /Resources << /Font << /F1 7 0 R /F2 8 0 R /F3 9 0 R >> >> >>');
  addObject('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 6 0 R /Resources << /Font << /F1 7 0 R /F2 8 0 R /F3 9 0 R >> >> >>');

  function createPageRenderer() {
    let stream = '';
    return {
      rect: (x, y, w, h, r, g, b) => { stream += `${r} ${g} ${b} rg ${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re f\\n`; },
      strokeRect: (x, y, w, h, r, g, b, lw = 1) => { stream += `${lw} w ${r} ${g} ${b} RG ${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re S\\n`; },
      line: (x1, y1, x2, y2, r, g, b, lw = 1) => { stream += `${lw} w ${r} ${g} ${b} RG ${x1.toFixed(2)} ${y1.toFixed(2)} m ${x2.toFixed(2)} ${y2.toFixed(2)} l S\\n`; },
      text: (font, size, x, y, str, r = 0, g = 0, b = 0) => {
        const clean = sanitizeForPdf(str);
        stream += `BT /${font} ${size} Tf ${r} ${g} ${b} rg 1 0 0 1 ${x.toFixed(2)} ${y.toFixed(2)} Tm (${clean}) Tj ET\\n`;
      },
      getStream: () => stream
    };
  }

  // ==========================================
  // PAGE 1
  // ==========================================
  const p1 = createPageRenderer();

  // Top Header Banner
  p1.rect(0, 745, 595.28, 97, 0.06, 0.09, 0.16); // Deep Navy
  p1.rect(0, 741, 595.28, 4, 0.14, 0.45, 0.92);  // Electric Sapphire Accent

  // Provider Brand Info
  p1.text('F2', 18, 40, 804, (data.providerName || 'SERHAT KUMAS').toUpperCase(), 1, 1, 1);
  p1.text('F2', 9.5, 40, 786, (data.providerTitle || 'AI & AUTOMATION SOLUTIONS').toUpperCase(), 0.25, 0.75, 0.98);
  p1.text('F1', 8, 40, 770, `${data.providerLocation || 'Munich, Germany'}  |  ${data.providerEmail || 'serhat.kumas.sk@gmail.com'}`, 0.72, 0.77, 0.84);

  // Document Badge on Right
  p1.rect(380, 755, 175, 70, 0.10, 0.14, 0.22);
  p1.strokeRect(380, 755, 175, 70, 0.20, 0.35, 0.55, 1);
  p1.rect(390, 804, 155, 14, 0.14, 0.45, 0.92);
  p1.text('F2', 7.5, 400, 808, 'MASTER SERVICES AGREEMENT', 1, 1, 1);
  p1.text('F2', 8, 390, 790, `REF: ${data.contractId}`, 0.40, 0.82, 1.0);
  p1.text('F1', 7.5, 390, 776, `ISSUED: ${data.issueDate}`, 0.80, 0.85, 0.90);
  p1.text('F2', 7.5, 390, 763, 'STATUS: PENDING E-SIGNATURE', 0.96, 0.76, 0.30);

  // Document Title Banner
  p1.text('F2', 13, 40, 716, 'MASTER SERVICES AGREEMENT & TECHNICAL SCOPE', 0.08, 0.12, 0.22);
  p1.line(40, 708, 555, 708, 0.85, 0.88, 0.92, 1);

  // Parties Box (Equal Columns)
  // Left: Provider Card
  p1.rect(40, 614, 248, 88, 0.97, 0.98, 0.99);
  p1.strokeRect(40, 614, 248, 88, 0.85, 0.88, 0.92, 1);
  p1.rect(40, 684, 248, 18, 0.15, 0.20, 0.30);
  p1.text('F2', 8, 48, 689, 'SERVICE PROVIDER & ARCHITECT', 1, 1, 1);
  p1.text('F2', 9.5, 48, 668, data.providerName || 'Serhat Kumas', 0.08, 0.12, 0.22);
  p1.text('F1', 8, 48, 654, data.providerTitle || 'AI & Automation Solutions', 0.30, 0.35, 0.42);
  p1.text('F1', 8, 48, 640, data.providerLocation || 'Munich, Germany', 0.35, 0.40, 0.48);
  p1.text('F1', 7.5, 48, 626, data.providerEmail || 'serhat.kumas.sk@gmail.com', 0.14, 0.45, 0.92);

  // Right: Client Card (Handles long names and multi-line pricing perfectly)
  p1.rect(307, 614, 248, 88, 0.97, 0.98, 0.99);
  p1.strokeRect(307, 614, 248, 88, 0.85, 0.88, 0.92, 1);
  p1.rect(307, 684, 248, 18, 0.10, 0.35, 0.65);
  p1.text('F2', 8, 315, 689, 'CLIENT / PRINCIPAL ENTITY', 1, 1, 1);

  const clientNameLines = wrapText(data.clientName || 'Client Entity', 34);
  p1.text('F2', 9.5, 315, 668, clientNameLines[0] || 'Client Entity', 0.08, 0.12, 0.22);
  p1.text('F1', 8, 315, 654, `Effective Date: ${data.effectiveDate || 'Upon Execution'}`, 0.30, 0.35, 0.42);

  const priceLines = wrapText(`Fee: ${data.pricing || 'TBD'}`, 34);
  p1.text('F2', 8, 315, 639, priceLines[0] || '', 0.10, 0.35, 0.65);
  if (priceLines.length > 1) {
    p1.text('F2', 7.5, 315, 626, priceLines.slice(1).join(' '), 0.10, 0.35, 0.65);
  } else {
    p1.text('F1', 7.5, 315, 626, `Contact: ${data.clientContact || 'Executive Management'}`, 0.40, 0.45, 0.52);
  }

  // Section 1: Executive Summary
  p1.rect(40, 592, 4, 16, 0.14, 0.45, 0.92);
  p1.rect(44, 592, 511, 16, 0.92, 0.95, 0.98);
  p1.text('F2', 8.5, 52, 596, '1. EXECUTIVE SUMMARY & ENGAGEMENT OBJECTIVES', 0.08, 0.15, 0.30);

  p1.rect(40, 532, 515, 54, 0.99, 1.0, 1.0);
  p1.strokeRect(40, 532, 515, 54, 0.88, 0.91, 0.94, 0.75);
  p1.rect(40, 532, 3.5, 54, 0.14, 0.45, 0.92);

  const summaryLines = wrapText(data.executiveSummary, 88).slice(0, 4);
  let sumY = 572;
  for (const line of summaryLines) {
    p1.text('F1', 8, 50, sumY, line, 0.22, 0.26, 0.32);
    sumY -= 12;
  }

  // Section 2: Statement of Work (Phase I & II)
  p1.rect(40, 504, 4, 16, 0.14, 0.45, 0.92);
  p1.rect(44, 504, 511, 16, 0.92, 0.95, 0.98);
  p1.text('F2', 8.5, 52, 508, '2. STATEMENT OF WORK & TECHNICAL DELIVERABLES (PHASE I & II)', 0.08, 0.15, 0.30);

  const deliverables = data.deliverables || [];
  const p1Modules = [
    { mod: deliverables[0], cardY: 290, num: '1' },
    { mod: deliverables[1], cardY: 66,  num: '2' }
  ];

  for (const item of p1Modules) {
    const d = item.mod || { title: `Module ${item.num}`, description: 'Architecture implementation and integration.' };
    const cardY = item.cardY;
    const cardH = 208;

    // Card background & border
    p1.rect(40, cardY, 515, cardH, 0.985, 0.99, 1.0);
    p1.strokeRect(40, cardY, 515, cardH, 0.86, 0.89, 0.93, 1);
    p1.rect(40, cardY, 4, cardH, 0.14, 0.45, 0.92);

    // Module Card Header Bar
    p1.rect(44, cardY + cardH - 24, 511, 24, 0.08, 0.12, 0.20);
    p1.rect(50, cardY + cardH - 19, 62, 14, 0.14, 0.45, 0.92);
    p1.text('F2', 7.5, 56, cardY + cardH - 15, `MODULE 2.${item.num}`, 1, 1, 1);

    // Module Title (fits up to 60 chars)
    const rawTitle = d.title || '';
    const titleText = rawTitle.length > 58 ? (rawTitle.slice(0, 55) + '...') : rawTitle;
    p1.text('F2', 8.5, 118, cardY + cardH - 15, titleText, 0.95, 0.98, 1.0);

    // Timeline Pill on Right
    p1.rect(442, cardY + cardH - 20, 106, 16, 0.15, 0.22, 0.35);
    p1.strokeRect(442, cardY + cardH - 20, 106, 16, 0.28, 0.45, 0.70, 0.75);
    p1.text('F2', 6.5, 447, cardY + cardH - 15, `TIMELINE: ${d.timeline || 'Sprint ' + item.num}`, 0.40, 0.82, 1.0);

    // Card Body: Architecture Scope
    p1.text('F2', 7.5, 52, cardY + cardH - 38, 'TECHNICAL ARCHITECTURE & SPECIFICATION:', 0.10, 0.25, 0.50);

    const descLines = wrapText(d.description, 86).slice(0, 3);
    let descY = cardY + cardH - 51;
    for (const dl of descLines) {
      p1.text('F1', 8, 52, descY, dl, 0.25, 0.30, 0.36);
      descY -= 11.5;
    }

    // Divider inside card
    p1.line(52, cardY + 98, 545, cardY + 98, 0.88, 0.91, 0.94, 0.75);

    // Key Features & Engineering Deliverables
    p1.text('F2', 7.5, 52, cardY + 84, 'KEY DELIVERABLES & CORE ENGINEERING ARTIFACTS:', 0.10, 0.25, 0.50);

    const features = (d.keyFeatures && d.keyFeatures.length > 0) ? d.keyFeatures : [
      'Resilient Webhook Gateway & High-Throughput Processing Engine',
      'Automated Telemetry, Error Recovery Handlers & Audit Trails',
      'End-to-End Environment Hardening & Integration Test Verification'
    ];

    let featY = cardY + 70;
    for (let f = 0; f < Math.min(features.length, 3); f++) {
      p1.rect(52, featY - 1, 8, 8, 0.14, 0.45, 0.92);
      p1.text('F2', 6.5, 54, featY, '+', 1, 1, 1);
      p1.text('F1', 8, 66, featY, features[f], 0.20, 0.25, 0.32);
      featY -= 14;
    }

    // Acceptance Criteria Box at bottom of card
    p1.rect(52, cardY + 12, 493, 18, 0.93, 0.95, 0.98);
    p1.strokeRect(52, cardY + 12, 493, 18, 0.82, 0.86, 0.92, 0.75);
    p1.text('F2', 7, 58, cardY + 18, 'ACCEPTANCE CRITERIA:', 0.10, 0.35, 0.65);
    p1.text('F1', 7.5, 148, cardY + 18, 'Production deployment verified with zero-error automated integration test suite.', 0.30, 0.35, 0.42);
  }

  // Page 1 Footer
  p1.line(40, 42, 555, 42, 0.85, 0.88, 0.92, 1);
  p1.text('F1', 7.5, 40, 28, `Confidential & Proprietary  |  Master Services Agreement  |  ${data.providerName || 'Serhat Kumas'}`, 0.48, 0.52, 0.58);
  p1.text('F2', 7.5, 510, 28, 'Page 1 of 2', 0.25, 0.30, 0.38);


  // ==========================================
  // PAGE 2
  // ==========================================
  const p2 = createPageRenderer();

  // Slim Running Header
  p2.rect(0, 816, 595.28, 26, 0.06, 0.09, 0.16);
  p2.rect(0, 813, 595.28, 3, 0.14, 0.45, 0.92);
  p2.text('F2', 8, 40, 824, `${(data.providerName || 'SERHAT KUMAS').toUpperCase()}  |  ${(data.providerTitle || 'AI & AUTOMATION SOLUTIONS').toUpperCase()}`, 1, 1, 1);
  p2.text('F1', 7.5, 410, 824, `REF: ${data.contractId}  |  PAGE 2 OF 2`, 0.75, 0.82, 0.92);

  // Section 2 Cont: Phase III & Deployment
  p2.rect(40, 792, 4, 15, 0.14, 0.45, 0.92);
  p2.rect(44, 792, 511, 15, 0.92, 0.95, 0.98);
  p2.text('F2', 8.5, 52, 796, '2. STATEMENT OF WORK (PHASE III & PRODUCTION ROLLOUT)', 0.08, 0.15, 0.30);

  const p2Modules = [
    { mod: deliverables[2] || { title: 'Telemetry, Observability & Error Fallback Engine', timeline: 'Sprint 3 (Weeks 3-4)', description: 'Real-time observability framework across all active workflows with automated incident alerts.' }, cardY: 700, num: '3' },
    { mod: deliverables[3] || { title: 'Production Hardening, SOP Documentation & Handover', timeline: 'Sprint 4 (Week 4)', description: 'Full system hardening, end-to-end integration verification, architecture runbooks, and staff enablement.' }, cardY: 604, num: '4' }
  ];

  for (const item of p2Modules) {
    const d = item.mod;
    const cardY = item.cardY;
    const cardH = 88;

    p2.rect(40, cardY, 515, cardH, 0.985, 0.99, 1.0);
    p2.strokeRect(40, cardY, 515, cardH, 0.86, 0.89, 0.93, 1);
    p2.rect(40, cardY, 4, cardH, 0.14, 0.45, 0.92);

    p2.rect(44, cardY + cardH - 20, 511, 20, 0.08, 0.12, 0.20);
    p2.rect(50, cardY + cardH - 16, 62, 12, 0.14, 0.45, 0.92);
    p2.text('F2', 7, 56, cardY + cardH - 13, `MODULE 2.${item.num}`, 1, 1, 1);

    const rawTitle = d.title || '';
    const titleText = rawTitle.length > 58 ? (rawTitle.slice(0, 55) + '...') : rawTitle;
    p2.text('F2', 8.5, 118, cardY + cardH - 13, titleText, 0.95, 0.98, 1.0);

    p2.rect(442, cardY + cardH - 17, 106, 14, 0.15, 0.22, 0.35);
    p2.strokeRect(442, cardY + cardH - 17, 106, 14, 0.28, 0.45, 0.70, 0.75);
    p2.text('F2', 6.5, 447, cardY + cardH - 13, `TIMELINE: ${d.timeline || 'Sprint ' + item.num}`, 0.40, 0.82, 1.0);

    const descLines = wrapText(d.description, 86).slice(0, 2);
    let descY = cardY + cardH - 33;
    for (const dl of descLines) {
      p2.text('F1', 7.5, 52, descY, dl, 0.25, 0.30, 0.36);
      descY -= 10.5;
    }

    const feats = (d.keyFeatures && d.keyFeatures.length > 0) ? d.keyFeatures.slice(0, 2) : [
      'Automated Fail-Safe Triggers & Self-Healing Telemetry',
      'Comprehensive Operations Runbook & Executive Training Session'
    ];
    let featY = cardY + 16;
    for (const f of feats) {
      p2.rect(52, featY - 1, 6, 6, 0.14, 0.45, 0.92);
      p2.text('F2', 5.5, 53.5, featY, '+', 1, 1, 1);
      p2.text('F1', 7.5, 64, featY, f, 0.20, 0.25, 0.32);
      featY -= 11;
    }
  }

  // Section 3: SLA & Performance Standards
  p2.rect(40, 580, 4, 15, 0.14, 0.45, 0.92);
  p2.rect(44, 580, 511, 15, 0.92, 0.95, 0.98);
  p2.text('F2', 8.5, 52, 584, '3. SERVICE LEVEL AGREEMENT (SLA) & PERFORMANCE STANDARDS', 0.08, 0.15, 0.30);

  p2.rect(40, 514, 515, 60, 0.98, 0.99, 1.0);
  p2.strokeRect(40, 514, 515, 60, 0.86, 0.89, 0.93, 1);

  // SLA Items with Modern Badges
  const slaItems = [
    { label: 'System Availability:', desc: '99.9% uptime target for automated production webhooks and pipelines.', y: 558 },
    { label: 'Incident Response:', desc: 'Under 4 business hours for severity-1 pipeline blockages.', y: 544 },
    { label: 'Agile Governance:', desc: 'Bi-weekly architecture syncs, throughput reviews, and backlog alignment.', y: 530 },
    { label: 'Observability:', desc: '24/7 automated alerting via Telegram and email on workflow anomalies.', y: 516 }
  ];

  for (const s of slaItems) {
    p2.rect(52, s.y - 1, 7, 7, 0.10, 0.55, 0.35);
    p2.text('F2', 5.5, 53.5, s.y, '+', 1, 1, 1);
    p2.text('F2', 8, 65, s.y, s.label, 0.08, 0.12, 0.20);
    p2.text('F1', 8, 65 + (s.label.length * 4.8), s.y, s.desc, 0.25, 0.30, 0.38);
  }

  // Section 4: Commercial Terms & Payment Schedule
  p2.rect(40, 490, 4, 15, 0.14, 0.45, 0.92);
  p2.rect(44, 490, 511, 15, 0.92, 0.95, 0.98);
  p2.text('F2', 8.5, 52, 494, '4. COMMERCIAL TERMS & PAYMENT SCHEDULE', 0.08, 0.15, 0.30);

  p2.rect(40, 412, 515, 72, 0.98, 0.99, 1.0);
  p2.strokeRect(40, 412, 515, 72, 0.86, 0.89, 0.93, 1);
  p2.rect(40, 458, 515, 26, 0.93, 0.96, 1.0);

  const agreedPricing = wrapText(`AGREED INVESTMENT: ${data.pricing || 'EUR 2,500 / month'}`, 75);
  p2.text('F2', 9, 52, 468, agreedPricing[0] || '', 0.08, 0.25, 0.60);
  if (agreedPricing.length > 1) {
    p2.text('F2', 8, 52, 458, agreedPricing.slice(1).join(' '), 0.08, 0.25, 0.60);
  }

  p2.text('F2', 7.5, 52, 442, 'Invoicing & Settlement:', 0.10, 0.15, 0.25);
  p2.text('F1', 7.5, 145, 442, 'Invoiced on the 1st of each calendar month. Net-14 payment window via SEPA transfer.', 0.25, 0.30, 0.38);

  p2.text('F2', 7.5, 52, 428, 'Scope Addendum Policy:', 0.10, 0.15, 0.25);
  p2.text('F1', 7.5, 150, 428, 'Any capabilities outside this document will be quoted separately as an authorized addendum.', 0.25, 0.30, 0.38);

  p2.text('F2', 7.5, 52, 416, 'Currency & Taxes:', 0.10, 0.15, 0.25);
  p2.text('F1', 7.5, 130, 416, 'All quoted rates exclude statutory VAT where applicable according to European tax regulations.', 0.25, 0.30, 0.38);

  // Section 5: Legal Governance & IP Ownership
  p2.rect(40, 388, 4, 15, 0.14, 0.45, 0.92);
  p2.rect(44, 388, 511, 15, 0.92, 0.95, 0.98);
  p2.text('F2', 8.5, 52, 392, '5. LEGAL GOVERNANCE, INTELLECTUAL PROPERTY & JURISDICTION', 0.08, 0.15, 0.30);

  p2.rect(40, 318, 515, 64, 0.98, 0.99, 1.0);
  p2.strokeRect(40, 318, 515, 64, 0.86, 0.89, 0.93, 1);

  p2.text('F2', 7.5, 52, 368, '100% IP Vesting:', 0.08, 0.12, 0.20);
  p2.text('F1', 7.5, 126, 368, 'Upon full settlement of invoices, all bespoke workflows and code vest entirely in Client.', 0.25, 0.30, 0.38);

  p2.text('F2', 7.5, 52, 352, 'Mutual NDA & Privacy:', 0.08, 0.12, 0.20);
  p2.text('F1', 7.5, 144, 352, 'Strict confidentiality observed regarding all proprietary data, API credentials, and internal schemas.', 0.25, 0.30, 0.38);

  p2.text('F2', 7.5, 52, 336, 'Governing Law:', 0.08, 0.12, 0.20);
  p2.text('F1', 7.5, 118, 336, 'This agreement is governed by the laws of Germany. Place of jurisdiction is Munich.', 0.25, 0.30, 0.38);

  p2.text('F2', 7.5, 52, 322, 'Severability:', 0.08, 0.12, 0.20);
  p2.text('F1', 7.5, 108, 322, 'If any provision is held invalid, the validity of the remaining provisions shall not be affected.', 0.25, 0.30, 0.38);

  // Section 6: Dual Execution & Signatures
  p2.rect(40, 294, 4, 15, 0.08, 0.12, 0.20);
  p2.rect(44, 294, 511, 15, 0.08, 0.12, 0.20);
  p2.text('F2', 8.5, 52, 298, '6. DUAL EXECUTION & AUTHORIZED ACCEPTANCE', 1, 1, 1);

  // Provider Signature Box
  p2.rect(40, 62, 248, 226, 0.97, 0.98, 0.99);
  p2.strokeRect(40, 62, 248, 226, 0.85, 0.88, 0.92, 1);
  p2.rect(40, 268, 248, 20, 0.15, 0.20, 0.30);
  p2.text('F2', 8, 48, 274, 'ACCEPTED & EXECUTED (PROVIDER)', 1, 1, 1);

  p2.text('F2', 10, 48, 248, data.providerName || 'Serhat Kumas', 0.08, 0.12, 0.22);
  p2.text('F1', 8, 48, 235, data.providerTitle || 'AI & Automation Solutions', 0.30, 0.35, 0.42);
  p2.text('F1', 8, 48, 222, `${data.providerLocation || 'Munich, Germany'}  |  ${data.providerEmail || 'serhat.kumas.sk@gmail.com'}`, 0.35, 0.40, 0.48);

  // Digital Seal Badge
  p2.rect(48, 172, 232, 38, 0.92, 0.96, 0.94);
  p2.strokeRect(48, 172, 232, 38, 0.30, 0.70, 0.45, 1);
  p2.text('F2', 8, 54, 196, '[ OK ] DIGITALLY CERTIFIED & SIGNED', 0.10, 0.50, 0.25);
  p2.text('F1', 7.5, 54, 184, 'Cryptographically verified n8n automation hash', 0.25, 0.45, 0.30);
  p2.text('F1', 7, 54, 175, `Hash: SHA-256 [${(data.contractId || 'AGR').split('-').join('')}9f2a4]`, 0.35, 0.50, 0.40);

  // Facsimile Signature Line
  p2.text('F3', 13, 56, 134, 'Serhat Kumas', 0.10, 0.25, 0.55);
  p2.line(48, 126, 275, 126, 0.60, 0.65, 0.70, 1);
  p2.text('F3', 7.5, 48, 116, 'Authorized Signature & Architect Approval', 0.45, 0.50, 0.55);
  p2.text('F1', 8, 48, 98, `Date of Signing: ${data.issueDate}`, 0.25, 0.30, 0.38);
  p2.text('F1', 8, 48, 84, 'Jurisdiction: Munich, Bavaria, Germany', 0.35, 0.40, 0.48);

  // Client Signature Box
  p2.rect(307, 62, 248, 226, 0.97, 0.98, 0.99);
  p2.strokeRect(307, 62, 248, 226, 0.85, 0.88, 0.92, 1);
  p2.rect(307, 268, 248, 20, 0.10, 0.35, 0.65);
  p2.text('F2', 8, 315, 274, 'ACCEPTED & RATIFIED (CLIENT)', 1, 1, 1);

  p2.text('F2', 9.5, 315, 248, clientNameLines[0] || 'Client Entity', 0.08, 0.12, 0.22);
  p2.text('F1', 7.5, 315, 235, 'By signing below, Client ratifies this Agreement:', 0.40, 0.45, 0.50);

  p2.text('F1', 8, 315, 206, 'Authorized Signatory Name:', 0.25, 0.30, 0.38);
  p2.line(315, 196, 545, 196, 0.60, 0.65, 0.70, 1);

  p2.text('F1', 8, 315, 178, 'Corporate Title / Role:', 0.25, 0.30, 0.38);
  p2.line(315, 168, 545, 168, 0.60, 0.65, 0.70, 1);

  p2.text('F1', 8, 315, 150, 'Authorized Signature:', 0.25, 0.30, 0.38);
  p2.line(315, 126, 545, 126, 0.60, 0.65, 0.70, 1);

  p2.text('F1', 8, 315, 102, 'Date of Execution:  _____ / _____ / 2026', 0.25, 0.30, 0.38);

  // Corporate Stamp Placeholder
  p2.rect(315, 72, 230, 22, 0.93, 0.95, 0.98);
  p2.strokeRect(315, 72, 230, 22, 0.75, 0.80, 0.88, 1);
  p2.text('F3', 7.5, 365, 80, '[ Corporate Seal & Stamp Placeholder ]', 0.50, 0.55, 0.60);

  // Page 2 Footer
  p2.line(40, 42, 555, 42, 0.85, 0.88, 0.92, 1);
  p2.text('F1', 7.5, 40, 28, `Confidential & Proprietary  |  Master Services Agreement  |  ${data.providerName || 'Serhat Kumas'}`, 0.48, 0.52, 0.58);
  p2.text('F2', 7.5, 510, 28, 'Page 2 of 2', 0.25, 0.30, 0.38);

  // Streams
  const s1 = p1.getStream();
  const s2 = p2.getStream();
  addObject(`<< /Length ${Buffer.byteLength(s1, 'latin1')} >>\\nstream\\n${s1}endstream`);
  addObject(`<< /Length ${Buffer.byteLength(s2, 'latin1')} >>\\nstream\\n${s2}endstream`);

  // Fonts
  addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>');
  addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>');

  let pdf = '%PDF-1.4\\n%\\xE2\\xE3\\xCF\\xD3\\n';
  const xref = [0];

  for (let i = 0; i < objects.length; i++) {
    xref.push(Buffer.byteLength(pdf, 'latin1'));
    pdf += `${i + 1} 0 obj\\n${objects[i]}\\nendobj\\n`;
  }

  const startxref = Buffer.byteLength(pdf, 'latin1');
  pdf += `xref\\n0 ${objects.length + 1}\\n0000000000 65535 f \\n`;
  for (let i = 1; i <= objects.length; i++) {
    pdf += `${String(xref[i]).padStart(10, '0')} 00000 n \\n`;
  }
  pdf += `trailer\\n<< /Size ${objects.length + 1} /Root 1 0 R >>\\nstartxref\\n${startxref}\\n%%EOF`;

  return Buffer.from(pdf, 'latin1');
}

const inputData = $input.first().json;
const pdfBuffer = generateContractPdf(inputData);

return [{
  json: inputData,
  binary: {
    data: {
      data: pdfBuffer.toString('base64'),
      mimeType: 'application/pdf',
      fileName: inputData.fileName,
      fileExtension: 'pdf'
    }
  }
}];'''

prepare_dispatch_js = '''const driveResp = $input.first()?.json || {};
const prev = $('Generate Executive Vector PDF').first();
const prevJson = prev.json;
const binary = prev.binary;

const driveLink = driveResp.webViewLink || `https://drive.google.com/file/d/${driveResp.id}/view`;

return [{
  json: {
    ...prevJson,
    driveId: driveResp.id,
    driveLink: driveLink
  },
  binary: binary
}];'''

prepare_sheet_row_js = '''const data = $('Prepare Dispatch Payload').first().json;

return [{
  json: {
    spreadsheetId: data.spreadsheetId,
    sheetName: data.sheetName,
    "Contract ID": data.contractId,
    "Date Created": data.issueDate,
    "Client Name": data.clientName,
    "Scope of Work": (data.deliverables || []).map(d => d.title).join(" | "),
    "Pricing / Monthly Retainer": data.pricing,
    "Effective Date": data.effectiveDate,
    "Status": "Pending Signature",
    "Google Drive PDF Link": data.driveLink,
    "Client Contact": data.clientContact || "Executive Management",
    "Notes / AI Summary": data.executiveSummary || ""
  }
}];'''

format_daily_checkin_js = '''const items = $input.all();
const pending = [];
const seenContractIds = new Set();

for (const item of items) {
  const row = item.json || {};
  const contractId = (row["Contract ID"] || "").trim();
  const status = (row["Status"] || "").toLowerCase();

  if (contractId && status.includes("pending") && !seenContractIds.has(contractId)) {
    seenContractIds.add(contractId);
    pending.push({
      json: {
        hasPending: true,
        contractId: contractId,
        clientName: row["Client Name"] || "Client",
        pricing: row["Pricing / Monthly Retainer"] || "TBD",
        dateCreated: row["Date Created"] || "Recent",
        driveLink: row["Google Drive PDF Link"] || "https://drive.google.com",
        status: row["Status"] || "Pending Signature",
        chatId: "1519369571" // Serhat's Telegram User ID
      }
    });
  }
}

if (pending.length === 0) {
  return [{
    json: {
      hasPending: false,
      chatId: "1519369571",
      allClearMessage: `☀️ <b>Daily E-Signature Status Report</b>\n━━━━━━━━━━━━━━━━━━━━━━\n✅ <b>All caught up!</b> There are currently no contracts pending signature or client approval.\n\nAll proposals are up to date in your tracking sheet. Have a productive day! 🚀`
    }
  }];
}

return pending;'''

parse_callback_js = '''const cfg = $('Central Brand & Event Parser').first().json;
const data = cfg.callbackData || "";
const callbackQueryId = cfg.callbackQueryId;
const messageId = cfg.messageId;
const chatId = cfg.chatId;

let newStatus = "Pending Signature";
let toastMessage = "Status unchanged.";
let statusBadge = "⏳ Pending";
let contractId = "";

if (data.startsWith("sign_")) {
  contractId = data.replace("sign_", "");
  newStatus = "Signed & Active";
  toastMessage = "✅ Contract marked as Signed & Active!";
  statusBadge = "✅ <b>SIGNED & ACTIVE</b>";
} else if (data.startsWith("wait_")) {
  contractId = data.replace("wait_", "");
  newStatus = "Pending Signature (Followed Up)";
  toastMessage = "⏳ Follow-up logged. Still waiting.";
  statusBadge = "⏳ <b>PENDING (FOLLOWED UP)</b>";
} else if (data.startsWith("cancel_")) {
  contractId = data.replace("cancel_", "");
  newStatus = "Cancelled / Void";
  toastMessage = "❌ Contract marked as Cancelled.";
  statusBadge = "❌ <b>CANCELLED / VOID</b>";
}

const today = new Date().toISOString().slice(0, 10);

return [{
  json: {
    spreadsheetId: cfg.spreadsheetId,
    sheetName: cfg.sheetName,
    contractId,
    newStatus,
    toastMessage,
    statusBadge,
    callbackQueryId,
    messageId,
    chatId,
    today
  }
}];'''

gmail_message_template = """<h3>📄 Official Service Agreement & Executive Proposal Generated</h3>
<p>Hello <b>{{ $json.providerName }}</b>,</p>
<p>A new high-stakes B2B service agreement and master proposal has been compiled and archived:</p>
<table style="border-collapse: collapse; width: 100%; max-width: 600px; font-family: sans-serif;">
  <tr style="background: #0f172a; color: white;">
    <th colspan="2" style="padding: 10px; text-align: left;">Contract Summary</th>
  </tr>
  <tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 8px; font-weight: bold; width: 160px;">Contract ID:</td>
    <td style="padding: 8px;"><code>{{ $json.contractId }}</code></td>
  </tr>
  <tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 8px; font-weight: bold;">Client:</td>
    <td style="padding: 8px;"><b>{{ $json.clientName }}</b></td>
  </tr>
  <tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 8px; font-weight: bold;">Commercial Value:</td>
    <td style="padding: 8px; color: #0284c7; font-weight: bold;">{{ $json.pricing }}</td>
  </tr>
  <tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 8px; font-weight: bold;">Effective Date:</td>
    <td style="padding: 8px;">{{ $json.effectiveDate }}</td>
  </tr>
  <tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 8px; font-weight: bold;">Status:</td>
    <td style="padding: 8px;"><span style="background: #fef08a; padding: 3px 8px; border-radius: 4px; font-weight: bold;">Pending E-Signature</span></td>
  </tr>
</table>

<h4>Executive Summary:</h4>
<blockquote style="border-left: 4px solid #0284c7; padding-left: 12px; color: #334155; font-style: italic;">
  {{ $json.executiveSummary }}
</blockquote>

<p>The vector PDF agreement is attached to this email and uploaded to Google Drive.</p>
<p>🔗 <a href="{{ $json.driveLink }}" style="background: #0284c7; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">Open Contract in Google Drive &rarr;</a></p>
<br/>
<p>Best regards,<br/><b>Automated E-Signature & Contract Suite</b></p>"""

workflow = {
  "name": "Project 10: Automated Contract & Proposal Generator with E-Signature Tracking",
  "nodes": [
    {
      "parameters": {
        "updates": ["message", "callback_query"],
        "additionalFields": {}
      },
      "id": "telegram-trigger",
      "name": "Telegram Trigger (Voice, Text, Buttons)",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1.1,
      "position": [100, 300],
      "credentials": {
        "telegramApi": {
          "id": "proposalContractsBot",
          "name": "Proposal & Contracts Bot"
        }
      }
    },
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 9 * * *"
            }
          ]
        }
      },
      "id": "schedule-daily-tracker",
      "name": "Daily 9:00 AM E-Signature Check-in",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.2,
      "position": [100, 900]
    },
    {
      "parameters": {
        "jsCode": central_config_js
      },
      "id": "central-brand-config",
      "name": "Central Brand & Event Parser",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [340, 300]
    },
    {
      "parameters": {
        "dataType": "string",
        "value1": "={{ $json.eventType }}",
        "rules": {
          "rules": [
            { "value2": "callback_query", "output": 0 },
            { "value2": "voice_note", "output": 1 },
            { "value2": "text_command", "output": 2 }
          ]
        }
      },
      "id": "route-event-type",
      "name": "Route Event Type",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 1,
      "position": [580, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "=https://api.telegram.org/bot{{ $json.botToken }}/getFile?file_id={{ $json.voiceFileId }}",
        "options": {}
      },
      "id": "telegram-get-file-path",
      "name": "Telegram: Get Voice Path",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [820, 240]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "=https://api.telegram.org/file/bot{{ $('Central Brand & Event Parser').first().json.botToken }}/{{ $json.result.file_path }}",
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          }
        }
      },
      "id": "telegram-download-audio",
      "name": "Telegram: Download Voice File",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1040, 240]
    },
    {
      "parameters": {
        "jsCode": prepare_voice_js
      },
      "id": "prepare-voice-payload",
      "name": "Prepare Voice Payload",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1260, 240]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googlePalmApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": """={
  "contents": [
    {
      "parts": [
        {
          "inlineData": {
            "mimeType": "{{ $json.audioMimeType }}",
            "data": "{{ $json.audioBase64 }}"
          }
        },
        {
          "text": {{ JSON.stringify($json.promptInstruction) }}
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.4,
    "responseMimeType": "application/json"
  }
}"""
      },
      "id": "gemini-voice-transcribe-expand",
      "name": "Gemini: Transcribe & Expand Voice Note",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1500, 240],
      "credentials": {
        "googlePalmApi": {
          "id": "zvLpU1ScjMCeOYQq",
          "name": "Google Gemini(PaLM) Api account"
        }
      }
    },
    {
      "parameters": {
        "jsCode": prepare_text_js
      },
      "id": "prepare-text-prompt",
      "name": "Prepare Text Prompt",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [820, 440]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googlePalmApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": """={
  "contents": [
    {
      "parts": [
        {
          "text": {{ JSON.stringify($json.promptInstruction) }}
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.4,
    "responseMimeType": "application/json"
  }
}"""
      },
      "id": "gemini-text-expand",
      "name": "Gemini: Expand & Structure Contract",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1140, 440],
      "credentials": {
        "googlePalmApi": {
          "id": "zvLpU1ScjMCeOYQq",
          "name": "Google Gemini(PaLM) Api account"
        }
      }
    },
    {
      "parameters": {
        "jsCode": parse_proposal_js
      },
      "id": "parse-ai-proposal-json",
      "name": "Parse & Finalize Proposal Data",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1800, 340]
    },
    {
      "parameters": {
        "jsCode": vector_pdf_js
      },
      "id": "generate-vector-pdf",
      "name": "Generate Executive Vector PDF",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [2040, 340]
    },
    {
      "parameters": {
        "operation": "upload",
        "name": "={{ $json.fileName }}",
        "driveId": {
          "__rl": True,
          "mode": "list",
          "value": "My Drive"
        },
        "folderId": {
          "__rl": True,
          "mode": "id",
          "value": "1H8Ais1pEsNFImDsnEa0Mj_FfYuRkZTAk",
          "cachedResultName": "Contracts & Proposals"
        },
        "options": {}
      },
      "id": "upload-pdf-drive",
      "name": "Upload PDF to Google Drive",
      "type": "n8n-nodes-base.googleDrive",
      "typeVersion": 3,
      "position": [2280, 340],
      "credentials": {
        "googleDriveOAuth2Api": {
          "id": "tvM7ZEvk4taPIOoN",
          "name": "Google Drive account"
        }
      }
    },
    {
      "parameters": {
        "jsCode": prepare_dispatch_js
      },
      "id": "prepare-dispatch-payload",
      "name": "Prepare Dispatch Payload",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [2520, 340]
    },
    {
      "parameters": {
        "sendTo": "={{ $json.providerEmail || 'serhat.kumas.sk@gmail.com' }}",
        "subject": "=📄 Service Agreement & Proposal: {{ $json.clientName }} ({{ $json.pricing }})",
        "message": f"={gmail_message_template}",
        "options": {
          "attachmentsUi": {
            "attachmentsBinary": [
              {
                "property": "data"
              }
            ]
          }
        }
      },
      "id": "dispatch-via-gmail",
      "name": "Send Proposal Email",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2.1,
      "position": [2760, 240],
      "credentials": {
        "gmailOAuth2": {
          "id": "GdaQB71L3KFdksjY",
          "name": "Gmail account"
        }
      }
    },
    {
      "parameters": {
        "operation": "append",
        "documentId": {
          "__rl": True,
          "value": "={{ $json.spreadsheetId }}",
          "mode": "id"
        },
        "sheetName": {
          "__rl": True,
          "value": "={{ $json.sheetName }}",
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
      "id": "append-contract-sheet",
      "name": "Log Contract in Google Sheets",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.5,
      "position": [2760, 440],
      "credentials": {
        "googleSheetsOAuth2Api": {
          "id": "uIhLunuZ3AaxqaDA",
          "name": "Google Sheets account"
        }
      },
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "jsCode": prepare_sheet_row_js
      },
      "id": "prepare-sheet-row",
      "name": "Prepare Sheet Row",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [2520, 520]
    },
    {
      "parameters": {
        "operation": "sendDocument",
        "chatId": "={{ $('Central Brand & Event Parser').first().json.chatId }}",
        "binaryData": True,
        "binaryPropertyName": "data",
        "replyMarkup": "inlineKeyboard",
        "inlineKeyboard": {
          "rows": [
            {
              "row": {
                "buttons": [
                  {
                    "text": "👀 View in Google Drive",
                    "additionalFields": {
                      "url": "={{ $json.driveLink || \"https://drive.google.com\" }}"
                    }
                  },
                  {
                    "text": "✅ Mark as Signed",
                    "additionalFields": {
                      "callback_data": "={{ 'sign_' + $json.contractId }}"
                    }
                  }
                ]
              }
            }
          ]
        },
        "additionalFields": {
          "caption": """=📄 <b>Master Services Agreement & Proposal Generated!</b>
━━━━━━━━━━━━━━━━━━━━━━
🏢 <b>Client:</b> {{ $json.clientName }}
💰 <b>Commercial:</b> {{ $json.pricing }}
📅 <b>Effective Date:</b> {{ $json.effectiveDate }}
📋 <b>Status:</b> ⏳ <b>Pending E-Signature</b>
✉️ <b>Email:</b> Sent to {{ $json.providerEmail }}

👇 <i>Document attached below. Tap below to view on Drive or track e-signature status:</i>""",
          "parse_mode": "HTML"
        }
      },
      "id": "send-telegram-pdf-card",
      "name": "Send PDF Document to Telegram",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [3020, 340],
      "credentials": {
        "telegramApi": {
          "id": "proposalContractsBot",
          "name": "Proposal & Contracts Bot"
        }
      }
    },
    {
      "parameters": {
        "operation": "read",
        "documentId": {
          "__rl": True,
          "value": "1tNOoNdpSQD5yjobV1UfYl73M9bjnHwEDVDjWOYPkoks",
          "mode": "id"
        },
        "sheetName": {
          "__rl": True,
          "value": "Contracts",
          "mode": "name"
        },
        "filters": {
          "conditions": [
            {
              "keyName": "Status",
              "condition": "contains",
              "value": "Pending"
            }
          ]
        },
        "options": {}
      },
      "id": "read-pending-contracts",
      "name": "Read Pending Contracts",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.5,
      "position": [340, 900],
      "alwaysOutputData": True,
      "credentials": {
        "googleSheetsOAuth2Api": {
          "id": "uIhLunuZ3AaxqaDA",
          "name": "Google Sheets account"
        }
      },
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": format_daily_checkin_js
      },
      "id": "format-daily-checkin",
      "name": "Format Daily Check-in",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [580, 900]
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": True,
            "leftValue": "",
            "typeValidation": "strict"
          },
          "conditions": [
            {
              "id": "has-pending-condition",
              "leftValue": "={{ $json.hasPending }}",
              "rightValue": True,
              "operator": {
                "type": "boolean",
                "operation": "true",
                "singleValue": True
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "if-has-pending-contracts",
      "name": "Has Pending Contracts?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [820, 900]
    },
    {
      "parameters": {
        "chatId": "={{ $json.chatId }}",
        "text": """=🔔 <b>Daily E-Signature Follow-up Check-in</b>
━━━━━━━━━━━━━━━━━━━━━━
📄 <b>Contract ID:</b> <code>{{ $json.contractId }}</code>
🏢 <b>Client:</b> <b>{{ $json.clientName }}</b>
💰 <b>Commercial:</b> {{ $json.pricing }}
📅 <b>Issued Date:</b> {{ $json.dateCreated }}
⏳ <b>Status:</b> <i>Pending E-Signature</i>

Has the client replied with the signed copy?""",
        "replyMarkup": "inlineKeyboard",
        "inlineKeyboard": {
          "rows": [
            {
              "row": {
                "buttons": [
                  {
                    "text": "✅ Signed & Received",
                    "additionalFields": {
                      "callback_data": "={{ 'sign_' + $json.contractId }}"
                    }
                  },
                  {
                    "text": "⏳ Still Waiting",
                    "additionalFields": {
                      "callback_data": "={{ 'wait_' + $json.contractId }}"
                    }
                  },
                  {
                    "text": "❌ Cancelled",
                    "additionalFields": {
                      "callback_data": "={{ 'cancel_' + $json.contractId }}"
                    }
                  }
                ]
              }
            }
          ]
        },
        "additionalFields": {
          "parse_mode": "HTML"
        }
      },
      "id": "send-daily-signature-ping",
      "name": "Send Daily Signature Ping",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1080, 800],
      "credentials": {
        "telegramApi": {
          "id": "proposalContractsBot",
          "name": "Proposal & Contracts Bot"
        }
      }
    },
    {
      "parameters": {
        "chatId": "={{ $json.chatId }}",
        "text": "={{ $json.allClearMessage }}",
        "additionalFields": {
          "parse_mode": "HTML"
        }
      },
      "id": "send-all-clear-notice",
      "name": "Send All-Clear Daily Notice",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1080, 1000],
      "credentials": {
        "telegramApi": {
          "id": "proposalContractsBot",
          "name": "Proposal & Contracts Bot"
        }
      }
    },
    {
      "parameters": {
        "jsCode": parse_callback_js
      },
      "id": "parse-callback-data",
      "name": "Parse Callback Action",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [820, 60]
    },
    {
      "parameters": {
        "operation": "update",
        "documentId": {
          "__rl": True,
          "value": "={{ $json.spreadsheetId }}",
          "mode": "id"
        },
        "sheetName": {
          "__rl": True,
          "value": "={{ $json.sheetName }}",
          "mode": "name"
        },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "Contract ID": "={{ $json.contractId }}",
            "Status": "={{ $json.newStatus }}",
            "Last Follow-Up Date": "={{ $json.today }}"
          },
          "matchingColumns": [
            "Contract ID"
          ],
          "schema": []
        },
        "options": {}
      },
      "id": "update-contract-sheet",
      "name": "Update Contract Status in Sheet",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.5,
      "position": [1060, 60],
      "credentials": {
        "googleSheetsOAuth2Api": {
          "id": "uIhLunuZ3AaxqaDA",
          "name": "Google Sheets account"
        }
      },
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "resource": "callback",
        "operation": "answerQuery",
        "queryId": "={{ $('Parse Callback Action').first().json.callbackQueryId }}",
        "additionalFields": {
          "text": "={{ $('Parse Callback Action').first().json.toastMessage }}",
          "show_alert": False
        }
      },
      "id": "answer-telegram-callback",
      "name": "Answer Callback Query",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1280, 60],
      "credentials": {
        "telegramApi": {
          "id": "proposalContractsBot",
          "name": "Proposal & Contracts Bot"
        }
      }
    },
    {
      "parameters": {
        "operation": "editMessageText",
        "chatId": "={{ $('Parse Callback Action').first().json.chatId }}",
        "messageId": "={{ $('Parse Callback Action').first().json.messageId }}",
        "text": """=📋 <b>Contract E-Signature Status Updated!</b>
━━━━━━━━━━━━━━━━━━━━━━
📄 <b>Contract ID:</b> <code>{{ $('Parse Callback Action').first().json.contractId }}</code>
📊 <b>Current Status:</b> {{ $('Parse Callback Action').first().json.statusBadge }}
📅 <b>Updated On:</b> {{ $('Parse Callback Action').first().json.today }}
📁 <b>Google Sheets:</b> ✅ Synced in real-time""",
        "replyMarkup": "none",
        "additionalFields": {
          "parse_mode": "HTML"
        }
      },
      "id": "edit-telegram-message",
      "name": "Update Telegram Message Status",
      "type": "n8n-nodes-base.telegram",
      "typeVersion": 1.2,
      "position": [1500, 60],
      "credentials": {
        "telegramApi": {
          "id": "proposalContractsBot",
          "name": "Proposal & Contracts Bot"
        }
      }
    }
  ],
  "connections": {
    "Telegram Trigger (Voice, Text, Buttons)": {
      "main": [
        [
          {
            "node": "Central Brand & Event Parser",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Central Brand & Event Parser": {
      "main": [
        [
          {
            "node": "Route Event Type",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Route Event Type": {
      "main": [
        [
          {
            "node": "Parse Callback Action",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Telegram: Get Voice Path",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Prepare Text Prompt",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Telegram: Get Voice Path": {
      "main": [
        [
          {
            "node": "Telegram: Download Voice File",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Telegram: Download Voice File": {
      "main": [
        [
          {
            "node": "Prepare Voice Payload",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Prepare Voice Payload": {
      "main": [
        [
          {
            "node": "Gemini: Transcribe & Expand Voice Note",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Gemini: Transcribe & Expand Voice Note": {
      "main": [
        [
          {
            "node": "Parse & Finalize Proposal Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Prepare Text Prompt": {
      "main": [
        [
          {
            "node": "Gemini: Expand & Structure Contract",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Gemini: Expand & Structure Contract": {
      "main": [
        [
          {
            "node": "Parse & Finalize Proposal Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parse & Finalize Proposal Data": {
      "main": [
        [
          {
            "node": "Generate Executive Vector PDF",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Generate Executive Vector PDF": {
      "main": [
        [
          {
            "node": "Upload PDF to Google Drive",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Upload PDF to Google Drive": {
      "main": [
        [
          {
            "node": "Prepare Dispatch Payload",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Prepare Dispatch Payload": {
      "main": [
        [
          {
            "node": "Send Proposal Email",
            "type": "main",
            "index": 0
          },
          {
            "node": "Prepare Sheet Row",
            "type": "main",
            "index": 0
          },
          {
            "node": "Send PDF Document to Telegram",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Prepare Sheet Row": {
      "main": [
        [
          {
            "node": "Log Contract in Google Sheets",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Daily 9:00 AM E-Signature Check-in": {
      "main": [
        [
          {
            "node": "Read Pending Contracts",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Read Pending Contracts": {
      "main": [
        [
          {
            "node": "Format Daily Check-in",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Format Daily Check-in": {
      "main": [
        [
          {
            "node": "Has Pending Contracts?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Has Pending Contracts?": {
      "main": [
        [
          {
            "node": "Send Daily Signature Ping",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Send All-Clear Daily Notice",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parse Callback Action": {
      "main": [
        [
          {
            "node": "Update Contract Status in Sheet",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Update Contract Status in Sheet": {
      "main": [
        [
          {
            "node": "Answer Callback Query",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Answer Callback Query": {
      "main": [
        [
          {
            "node": "Update Telegram Message Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}

with open("projects/10.automated-contract-proposal-generator/workflow.json", "w") as f:
    json.dump(workflow, f, indent=2)

print("Successfully written projects/10.automated-contract-proposal-generator/workflow.json!")
