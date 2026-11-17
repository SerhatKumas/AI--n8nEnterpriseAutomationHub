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

# 1. Telegram Trigger
telegram_trigger_node = make_node(
    name="Telegram Trigger (Chat & Buttons)",
    node_type="n8n-nodes-base.telegramTrigger",
    type_version=1.1,
    position=[200, 300],
    parameters={
        "updates": ["message", "callback_query"]
    },
    credentials={
        "telegramApi": {
            "id": "mealPlanGeneratorBot",
            "name": "Meal Plan Generator Bot"
        }
    },
    webhook_id="p14-meal-plan-generator-telegram-trigger"
)
telegram_trigger_node["id"] = "123daa29-3880-4b9c-93f6-bdec072247f7"
nodes.append(telegram_trigger_node)

# 2. Conversation & State Router
router_code = FIX_TURKISH_MOJIBAKE_JS + r"""const input = $input.first()?.json || {};
const BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN";

const sendTg = async (chatId, text, replyMarkup = null) => {
  const payload = { chat_id: chatId, text, parse_mode: "HTML" };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  try {
    await this.helpers.httpRequest({
      method: "POST",
      url: `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`,
      headers: { "Content-Type": "application/json" },
      body: payload,
      json: true
    });
  } catch(e) {
    console.error("sendTg error:", e.message || e);
  }
};

const answerCallback = async (callbackQueryId, text = "") => {
  try {
    await this.helpers.httpRequest({
      method: "POST",
      url: `https://api.telegram.org/bot${BOT_TOKEN}/answerCallbackQuery`,
      headers: { "Content-Type": "application/json" },
      body: { callback_query_id: callbackQueryId, text },
      json: true
    });
  } catch(e) {}
};

// ========================================================
// 1. Check Callback Query (Button Clicks)
// ========================================================
if (input.callback_query) {
  const cb = input.callback_query;
  const chatId = String(cb.message?.chat?.id || cb.from?.id);
  const data = String(cb.data || "");
  const msgText = String(cb.message?.text || "");

  // A. User accepts recipes
  if (data === "p14_accept") {
    await answerCallback(cb.id, "Afiyet olsun! 👨‍🍳");
    await sendTg(chatId, `👨‍🍳 <b>Afiyet olsun!</b>\n\nHarika bir sofra, lezzetli ve keyifli bir yemek dilerim! <b>Bon appétit!</b> 🍽️✨\n\n💡 <i>Farklı bir zamanda elinizdeki yeni malzemelerle tarif üretmek için buzdolabınızın fotoğrafını gönderebilir veya yeni malzeme listenizi yazabilirsiniz.</i>`);
    return [];
  }

  // B. User requests 3 alternatives
  if (data === "p14_more") {
    await answerCallback(cb.id, "Yeni alternatifler hazırlanıyor... 🔄");
    
    // Extract ingredients from the recipe message
    let ingredients = "";
    const ingMatch = msgText.match(/(?:🧺|Malzemeler:)[\s\n*]*([^\n\r]+)/i);
    if (ingMatch) {
      ingredients = fixTurkishMojibake(ingMatch[1].replace(/^[^\w\sğüşöçıİĞÜŞÖÇ]+/, '').trim());
    }
    
    // Extract previous recipe titles to exclude
    const titles = [...msgText.matchAll(/(?:[1-3]️⃣|\b[1-3]\.|\bTarif [1-3]:)\s*([^\n\r]+)/g)].map(m => fixTurkishMojibake(m[1].trim()));
    const hasPantry = !msgText.includes("Sadece belirtilen malzemeler") && !msgText.includes("Sadece fotoğraftaki");

    if (!ingredients) {
      await sendTg(chatId, `⚠️ <i>Kayıtlı malzeme bilgisi okunamadı. Lütfen mutfağınızdaki malzemeleri yazarak veya buzdolabınızın fotoğrafını göndererek yeni bir arama başlatın.</i>`);
      return [];
    }

    const previousList = titles.length > 0 ? titles.map(t => '• ' + t).join('\n') : '• Önceki öneriler';
    await sendTg(chatId, `🔄 <b>Farklı 3 Tarif Hazırlanıyor...</b>\n━━━━━━━━━━━━━━━━━━━━\n🧺 <b>Malzemeler:</b> ${ingredients}\n🚫 <i>Daha önce önerilen tarifler hariç tutuluyor:</i>\n${previousList}\n\n⏳ <i>Lütfen bekleyin, şefimiz yepyeni alternatifler hazırlıyor...</i>`);

    return [{
      json: {
        mode: "meal",
        chatId,
        ingredients,
        hasPantry,
        previousRecipes: titles,
        isAlternative: true
      }
    }];
  }

  // C. User answers pantry question (Yes or No)
  if (data === "p14_pantry_yes" || data === "p14_pantry_no") {
    const hasPantry = (data === "p14_pantry_yes");
    await answerCallback(cb.id, "Şef tarifleri hazırlıyor... 👨‍🍳");

    // Extract ingredients from the bot's question message (handles text or photo-detected)
    let ingredients = "";
    const match = msgText.match(/(?:🧺 Kayıtlı Malzemeler:|📝 Malzemeleriniz Alındı:|📝 Fotoğraftan Tespit Edilen Malzemeler:|📸 Fotoğraftan Tespit Edilen Malzemeler:)[\s\n]*([\s\S]+?)(?:\n\nPeki mutfağınızda|\n\n🧂|$)/i);
    if (match) {
      ingredients = fixTurkishMojibake(match[1].replace(/<\/?code>/gi, '').trim());
    }

    if (!ingredients) {
      await sendTg(chatId, `⚠️ <i>Malzeme bilgisi okunamadı. Lütfen mutfağınızdaki malzemeleri yazarak veya buzdolabınızın fotoğrafını göndererek yeni bir arama başlatın.</i>`);
      return [];
    }

    const pantryDesc = hasPantry 
      ? "✅ <b>Temel kiler malzemeleri dahil</b> (Tuz, yağ, un, baharat vb.)" 
      : "🚫 <b>Sadece belirtilen / fotoğraftaki malzemelerle sınırlı</b>";

    await sendTg(chatId, `👨‍🍳 <b>Şef Mutfağa Girdi!</b>\n━━━━━━━━━━━━━━━━━━━━\n🧺 <b>Malzemeler:</b> ${ingredients}\n🧂 <b>Kiler Durumu:</b> ${pantryDesc}\n\n⏳ <i>Yapay zeka şefimiz elinizdeki malzemeleri analiz ediyor ve 3 özel tarif hazırlıyor... Lütfen birkaç saniye bekleyin.</i>`);

    return [{
      json: {
        mode: "meal",
        chatId,
        ingredients,
        hasPantry,
        previousRecipes: [],
        isAlternative: false
      }
    }];
  }

  await answerCallback(cb.id);
  return [];
}

// ========================================================
// 2. Check Standard Message (Photo or Text)
// ========================================================
const msg = input.message;
if (!msg) return [];

const chatId = String(msg.chat?.id || msg.from?.id);

// A. USER SENDS A PHOTO OF FRIDGE OR PANTRY! 📸
const hasPhoto = (msg.photo && msg.photo.length > 0) || (msg.document && msg.document.mime_type && msg.document.mime_type.startsWith('image/'));

if (hasPhoto) {
  await sendTg(chatId, `📸 <b>Buzdolabı fotoğrafınız alındı!</b>\n<i>Şefimiz fotoğrafı inceliyor ve içerideki malzemeleri tespit ediyor, lütfen birkaç saniye bekleyin...</i> 🔍`);

  let fileId = "";
  if (msg.photo && msg.photo.length > 0) {
    const largestPhoto = msg.photo[msg.photo.length - 1];
    fileId = largestPhoto.file_id || largestPhoto;
  } else if (msg.document) {
    fileId = msg.document.file_id;
  }

  try {
    const fileRes = await this.helpers.httpRequest({
      method: "GET",
      url: `https://api.telegram.org/bot${BOT_TOKEN}/getFile?file_id=${fileId}`,
      json: true
    });

    const filePath = fileRes?.result?.file_path;
    if (!filePath) throw new Error("Dosya yolu Telegram API'den alınamadı.");

    const photoBuf = await this.helpers.httpRequest({
      method: "GET",
      url: `https://api.telegram.org/file/bot${BOT_TOKEN}/${filePath}`,
      encoding: "arraybuffer",
      timeout: 30000
    });

    const imageB64 = Buffer.from(photoBuf).toString("base64");

    const userCaption = msg.caption ? String(msg.caption).trim() : "";

    let promptText = "Bu bir buzdolabı, kiler veya mutfak tezgahı fotoğrafıdır. Fotoğrafta net olarak görünen ve ayırt edilebilen tüm yenilebilir gıda maddelerini, sebzeleri, meyveleri, süt ürünlerini, et/tavuk ürünlerini, sosları ve mutfak malzemelerini tespit et.\n\nKURALLAR:\n1. SADECE fotoğrafta gerçekten var olan malzemeleri yaz.\n2. Malzemeleri Türkçe, sade ve virgülle ayrılmış tek bir liste olarak döndür (Örn: 'yumurta, süt, domates, kaşar peyniri, salatalık, yoğurt, tereyağı').\n3. Marka adları, paket detayları veya gereksiz sıfatlar ekleme; sadece malzeme adını yaz.\n4. Eğer fotoğrafta hiçbir yiyecek veya mutfak malzemesi görünmüyorsa sadece 'YOK' yaz.\n5. Yanıtında hiçbir markdown, başlık, madde işareti veya selamlama olmasın; sadece ve sadece virgülle ayrılmış malzeme isimleri olsun.";
    if (userCaption) {
      promptText += `\nKullanıcının fotoğrafla birlikte eklediği ek not: "${userCaption}". Eğer kullanıcı fotoğrafta görünmeyen ek malzemeler belirtmişse onları da listeye dahil et.`;
    }

    return [{
      json: {
        mode: "photo",
        chatId,
        geminiVisionBody: {
          contents: [
            {
              role: "user",
              parts: [
                { text: promptText },
                {
                  inlineData: {
                    mimeType: "image/jpeg",
                    data: imageB64
                  }
                }
              ]
            }
          ],
          generationConfig: {
            temperature: 0.2,
            maxOutputTokens: 300
          }
        }
      }
    }];
  } catch(e) {
    console.error("Photo download error:", e.message || e);
    await sendTg(chatId, `⚠️ <i>Fotoğraf işlenirken hata oluştu (${e.message || e}). Lütfen tekrar deneyin ya da malzemelerinizi metin olarak yazın (Örn: <code>tavuk, mantar, krema</code>).</i>`);
    return [];
  }
}

// B. USER SENDS TEXT COMMAND OR INGREDIENT LIST
if (!msg.text) return [];

const text = fixTurkishMojibake(String(msg.text).trim());
const lower = text.toLowerCase();

// Commands (/start, /help, /yardim)
if (lower === "/start" || lower === "/yardim" || lower === "/yeni" || lower === "yardım" || lower === "başla") {
  await sendTg(chatId, `👋 <b>Akıllı Mutfak Şefine Hoş Geldiniz!</b> 👨‍🍳\n━━━━━━━━━━━━━━━━━━━━\nNe pişireceğinizi düşünmek zorunda değilsiniz. Mutfağınızdaki malzemelerle saniyeler içinde <b>3 pratik ve lezzetli tarif</b> çıkarayım!\n\n📌 <b>Nasıl Kullanılır?</b>\n1️⃣ <b>Fotoğraf Gönderin:</b> Buzdolabınızın veya tezgahınızın fotoğrafını doğrudan bana gönderin 📸. Yapay zeka şefimiz malzemeleri anında tespit etsin!\n2️⃣ <b>Veya Yazarak Gönderin:</b> Elinizdeki malzemeleri tek bir mesajda yazın:\n👉 <i>Örnek 1:</i> <code>tavuk göğsü, mantar, krema</code>\n👉 <i>Örnek 2:</i> <code>yumurta, patates, kaşar, domates</code>\n👉 <i>Örnek 3:</i> <code>kıyma, soğan, un, yoğurt</code>\n\nArdından temel kiler malzemeleri durumunu onayladığınızda, tarifleriniz hem mesaj hem de şık bir <b>PDF Tarif Kartı</b> olarak iletilecek! 📜🍳`);
  return [];
}

// User sent ingredients via text!
const replyMarkup = {
  inline_keyboard: [
    [
      { text: "🧂 Temel kiler malzemeleri de var", callback_data: "p14_pantry_yes" }
    ],
    [
      { text: "🚫 Sadece yazdığım malzemeler var", callback_data: "p14_pantry_no" }
    ]
  ]
};

await sendTg(chatId, `📝 <b>Malzemeleriniz Alındı:</b>\n<code>${text}</code>\n\nPeki mutfağınızda <b>tuz, karabiber, sıvı yağ/tereyağı, un, salça, su</b> gibi temel kiler malzemeleri de bulunuyor mu?`, replyMarkup);

return [];"""

router_node = make_node(
    name="Conversation & State Router",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[480, 300],
    parameters={"jsCode": router_code}
)
nodes.append(router_node)

# 3. Decision Node: Is Fridge Photo?
if_photo_node = make_node(
    name="Is Fridge Photo?",
    node_type="n8n-nodes-base.if",
    type_version=2.2,
    position=[750, 300],
    parameters={
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "strict"
            },
            "conditions": [
                {
                    "leftValue": "={{ $json.mode }}",
                    "rightValue": "photo",
                    "operator": {
                        "type": "string",
                        "operation": "equals"
                    }
                }
            ],
            "combinator": "and"
        }
    }
)
nodes.append(if_photo_node)

# ========================================================
# BRANCH 1: PHOTO PROCESSING & VISION (Top Branch)
# ========================================================

# 4. Gemini 3.1: Detect Fridge Ingredients
gemini_vision_node = make_node(
    name="Gemini 3.1: Detect Fridge Ingredients",
    node_type="n8n-nodes-base.httpRequest",
    type_version=4.2,
    position=[1040, 160],
    parameters={
        "method": "POST",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googlePalmApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.geminiVisionBody) }}",
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
nodes.append(gemini_vision_node)

# 5. Send Detected Ingredients with Pantry Buttons
photo_pantry_code = FIX_TURKISH_MOJIBAKE_JS + r"""const input = $input.first()?.json || {};
const ifNode = $('Is Fridge Photo?').first()?.json || {};
const chatId = ifNode.chatId;
const BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN";

const sendTg = async (chatId, text, replyMarkup = null) => {
  const payload = { chat_id: chatId, text, parse_mode: "HTML" };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  try {
    await this.helpers.httpRequest({
      method: "POST",
      url: `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`,
      headers: { "Content-Type": "application/json" },
      body: payload,
      json: true
    });
  } catch(e) {
    console.error("sendTg error:", e.message || e);
  }
};

let rawText = input?.candidates?.[0]?.content?.parts?.[0]?.text || "";
rawText = fixTurkishMojibake(rawText.trim().replace(/^['"`]+|['"`]+$/g, '').trim());

if (!rawText || rawText.toUpperCase() === "YOK" || rawText.toLowerCase().includes("malzeme bulunamadı") || rawText.toLowerCase().includes("tespit edilemedi")) {
  await sendTg(chatId, `🔍 <b>Buzdolabı Taraması Tamamlandı</b>\n━━━━━━━━━━━━━━━━━━━━\n❌ <i>Fotoğrafta net olarak ayırt edilebilen bir gıda maddesi veya buzdolabı içeriği tespit edilemedi.</i>\n\n💡 <b>Şefin Önerisi:</b>\n• Buzdolabının içini gösteren daha aydınlık ve net bir fotoğraf çekip gönderebilirsiniz 📸\n• Ya da elinizdeki malzemeleri doğrudan metin olarak yazabilirsiniz (Örn: <code>tavuk, mantar, krema</code>) ✍️`);
  return [];
}

// Clean and format ingredients list
const cleanIngredients = rawText
  .split(/[\n,]+/)
  .map(s => s.replace(/^[•*\-\d.]+\s*/, '').trim())
  .filter(s => s.length > 1 && !s.toLowerCase().includes('yok'))
  .join(', ');

if (!cleanIngredients) {
  await sendTg(chatId, `❌ <i>Fotoğraftan malzeme listesi çıkarılamadı. Lütfen malzemelerinizi metin olarak yazarak tekrar deneyin.</i>`);
  return [];
}

const replyMarkup = {
  inline_keyboard: [
    [
      { text: "🧂 Temel kiler malzemeleri de var", callback_data: "p14_pantry_yes" }
    ],
    [
      { text: "🚫 Sadece fotoğraftaki malzemeler var", callback_data: "p14_pantry_no" }
    ]
  ]
};

await sendTg(chatId, `📸 <b>Fotoğraftan Tespit Edilen Malzemeler:</b>\n<code>${cleanIngredients}</code>\n\nPeki mutfağınızda <b>tuz, karabiber, sıvı yağ/tereyağı, un, salça, su</b> gibi temel kiler malzemeleri de bulunuyor mu?`, replyMarkup);

return [];"""

photo_pantry_node = make_node(
    name="Send Detected Ingredients with Pantry Buttons",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1320, 160],
    parameters={"jsCode": photo_pantry_code}
)
nodes.append(photo_pantry_node)

# ========================================================
# BRANCH 2: MEAL GENERATION & RECIPE FLOW (Bottom Branch)
# ========================================================

# 6. Prepare Gemini Meal Prompt
prompt_prep_code = FIX_TURKISH_MOJIBAKE_JS + r"""const input = $input.first()?.json || {};
const rawIngredients = input.ingredients || "";
const ingredients = fixTurkishMojibake(rawIngredients);
const hasPantry = input.hasPantry !== false;
const previousRecipes = (input.previousRecipes || []).map(fixTurkishMojibake);
const isAlternative = input.isAlternative === true;
const chatId = input.chatId;

const systemPrompt = `Sen Türkiye'nin en yaratıcı, tecrübeli ve pratik şefisin.
Kullanıcının mutfağında bulunan malzemeleri değerlendirerek evde yapılabilecek en mantıklı, lezzetli ve uygulanabilir 3 farklı yemek tarifi üretirsin.

KRİTİK KURALLAR:
1. YETERLİLİK KONTROLÜ (isPossible):
   - Eğer kullanıcının verdiği malzemelerle yenilebilir gerçek bir yemek yapılması mümkün DEĞİLSE (Örn: sadece "su ve tuz", veya taş/kağıt gibi yenilemez maddeler, veya tek başına bir yemek oluşturamayacak sadece kimyon gibi baharatlar):
     "isPossible": false yap ve "reason" alanına kullanıcının anlayacağı nazik, esprili ve Türkçe bir açıklama yaz (hangi temel gıdayı eklemesi gerektiğini belirt). "recipes" dizisini boş bırak.
   - Ancak basit de olsa temel bir yemek çıkabiliyorsa (Örn: "un, tuz, su" varsa lavaş/bazlama/ekmek yapılabilir, "yumurta ve domates" varsa menemen yapılabilir): "isPossible": true yap.
   - Eğer kiler malzemeleri mevcutsa (hasPantry: true), evdeki tuz, karabiber, sıvı yağ/zeytinyağı, un, su ve temel baharatların da kullanılabileceğini varsay.
   - Eğer kiler malzemeleri YOKSA (hasPantry: false), KESİNLİKLE sadece ve sadece kullanıcının yazdığı malzemelerle hazırlanabilecek tarifler üret!

2. 3 FARKLI TARİF:
   - "isPossible": true ise, tam 3 adet farklı konseptte tarif üret (örneğin: 1 ana yemek/tencere yemeği, 1 pratik fırın/tava yemeği, 1 hafif atıştırmalık/meze veya çorba).
   - Her tarif için:
     * title: Çekici Türkçe yemek adı (Örn: "Kremalı Mantarlı Tavuk Sote")
     * time: Tahmini hazırlama ve pişirme süresi (Örn: "25 dk")
     * difficulty: Kolay / Orta / Pratik
     * portions: Porsiyon (Örn: "2-3 Kişilik")
     * calories: Porsiyon başı yaklaşık kalori (Örn: "380 kcal")
     * ingredientsUsed: Kullanılan malzemeler ve yaklaşık ölçüleri dizi olarak
     * steps: Adım adım, anlaşılır pişirme adımları dizi olarak (en az 4 adım)
     * chefTip: Yemeği daha lezzetli kılacak şefin püf noktası

3. ALTERNATİF TALEBİ & ÇEŞİTLİLİK:
   - Eğer önceki tarifler listelenmişse, KESİNLİKLE o tariflerden tamamen farklı yeni 3 alternatif tarif üret.

4. ÇIKTI FORMATI:
   - SADECE ve SADECE saf JSON üret. Markdown blokları veya ek açıklama yazma.
   - JSON Şeması:
   {
     "isPossible": true / false,
     "reason": "Yetersizse nazik açıklama, yetersiz değilse boş string",
     "recipes": [
       {
         "title": "Yemek Adı",
         "time": "25 dk",
         "difficulty": "Kolay",
         "portions": "2-3 Kişilik",
         "calories": "350 kcal",
         "ingredientsUsed": ["300g tavuk", "1 paket krema"],
         "steps": ["Adım 1...", "Adım 2..."],
         "chefTip": "Püf noktası..."
       }
     ]
   }

5. DİL VE KODLAMA ZORUNLULUĞU (UTF-8):
   - TÜM yemek adları, malzeme listeleri, açıklamalar ve adımlar KESİNLİKLE doğru Türkçe karakterlerle (ç, ğ, ı, ö, ş, ü, Ç, Ğ, İ, Ö, Ş, Ü) ve düzgün Türkçe grameriyle yazılmalıdır.
   - Asla bozuk karakterler, Çince semboller veya yabancı alfabe karakterleri KULLANMA.`;

let userPrompt = `MUTFAKTAKİ MALZEMELER: ${ingredients}\n`;
userPrompt += `TEMEL KİLER MALZEMELERİ DURUMU (Tuz, Yağ, Un vb.): ${hasPantry ? "MEVCUT (Kullanılabilir)" : "YOK (SADECE verilen malzemeler kullanılabilir)"}\n`;

if (isAlternative && previousRecipes.length > 0) {
  userPrompt += `\nDAHA ÖNCE ÖNERİLEN TARİFLER (Lütfen bunları önerme, tamamen yeni 3 alternatif sun):\n`;
  previousRecipes.forEach(r => { userPrompt += `- ${r}\n`; });
}

return [{
  json: {
    chatId,
    ingredients,
    hasPantry,
    previousRecipes,
    geminiBody: {
      contents: [
        {
          role: "user",
          parts: [{ text: systemPrompt + "\n\n" + userPrompt }]
        }
      ],
      generationConfig: {
        temperature: 0.4,
        maxOutputTokens: 2500,
        responseMimeType: "application/json"
      }
    }
  }
}];"""

prompt_prep_node = make_node(
    name="Prepare Gemini Meal Prompt",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1040, 440],
    parameters={"jsCode": prompt_prep_code}
)
nodes.append(prompt_prep_node)

# 7. Gemini 3.1: Generate Meal Plan
gemini_api_node = make_node(
    name="Gemini 3.1: Generate Meal Plan",
    node_type="n8n-nodes-base.httpRequest",
    type_version=4.2,
    position=[1320, 440],
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

# 8. Parse Recipes & Check Feasibility
parse_code = FIX_TURKISH_MOJIBAKE_JS + r"""const input = $input.first()?.json || {};
const promptNode = $("Prepare Gemini Meal Prompt").first()?.json || {};
const chatId = promptNode.chatId;
const ingredients = fixTurkishMojibake(promptNode.ingredients);
const hasPantry = promptNode.hasPantry;
const previousRecipes = (promptNode.previousRecipes || []).map(fixTurkishMojibake);
const BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN";

const sendTg = async (chatId, text, replyMarkup = null) => {
  const payload = { chat_id: chatId, text, parse_mode: "HTML" };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  try {
    await this.helpers.httpRequest({
      method: "POST",
      url: `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`,
      headers: { "Content-Type": "application/json" },
      body: payload,
      json: true
    });
  } catch(e) {}
};

// Parse Gemini Response
let rawText = input?.candidates?.[0]?.content?.parts?.[0]?.text || "{}";
rawText = fixTurkishMojibake(rawText);
let parsed = {};
try {
  parsed = JSON.parse(rawText.replace(/```json/g, "").replace(/```/g, "").trim());
} catch(e) {
  parsed = { isPossible: false, reason: "Yapay zeka yanıtı çözümlenemedi. Lütfen tekrar deneyin." };
}

// 1. If not possible to cook a meal
if (parsed.isPossible === false || !parsed.recipes || parsed.recipes.length === 0) {
  const reason = fixTurkishMojibake(parsed.reason || "Mevcut malzemelerle doyurucu veya tüketilebilir bir yemek yapılamıyor.");
  await sendTg(chatId, `❌ <b>Yetersiz Malzeme Uyarısı</b>\n━━━━━━━━━━━━━━━━━━━━\n${reason}\n\n💡 <b>Şefin Önerisi:</b>\nLütfen elinize en az bir ana besin maddesi (örneğin: yumurta, sebze, tavuk, et, bakliyat veya un) ekleyip malzeme listenizi yeniden yazın veya daha net bir buzdolabı fotoğrafı çekin! 🍳`);
  return [];
}

const recipes = (parsed.recipes || []).slice(0, 3).map(r => ({
  title: fixTurkishMojibake(r.title || ""),
  time: fixTurkishMojibake(r.time || "25 dk"),
  difficulty: fixTurkishMojibake(r.difficulty || "Kolay"),
  portions: fixTurkishMojibake(r.portions || "2-3 Kişilik"),
  calories: fixTurkishMojibake(r.calories || ""),
  ingredientsUsed: (r.ingredientsUsed || []).map(fixTurkishMojibake),
  steps: (r.steps || []).map(fixTurkishMojibake),
  chefTip: fixTurkishMojibake(r.chefTip || "")
}));

// 2. Format Telegram Message
let tgMsg = `🍽️ <b>GÜNÜN MENÜSÜ & 3 ÖZEL TARİF</b>\n`;
tgMsg += `🧺 <b>Malzemeler:</b> ${ingredients}\n`;
tgMsg += `🧂 <b>Kiler:</b> ${hasPantry ? "Temel kiler malzemeleri dahil" : "Sadece belirtilen / fotoğraftaki malzemeler"}\n`;
tgMsg += `━━━━━━━━━━━━━━━━━━━━\n\n`;

recipes.forEach((r, idx) => {
  const icons = ["1️⃣", "2️⃣", "3️⃣"];
  const cleanTitle = (r.title || "")
    .replace(/ı/g, 'I')
    .replace(/i/g, 'İ')
    .toLocaleUpperCase("tr-TR");
  tgMsg += `${icons[idx]} <b>${cleanTitle}</b>\n`;
  tgMsg += `⏱️ <b>Süre:</b> ${r.time}  |  📊 <b>Zorluk:</b> ${r.difficulty}  |  👥 <b>Porsiyon:</b> ${r.portions || "2-3 Kişilik"}\n\n`;
  
  tgMsg += `🥗 <b>Kullanılan Malzemeler:</b>\n`;
  (r.ingredientsUsed || []).forEach(ing => {
    tgMsg += `• ${ing}\n`;
  });
  
  tgMsg += `\n👩‍🍳 <b>Nasıl Yapılır?</b>\n`;
  (r.steps || []).forEach((s, sIdx) => {
    const cleanStep = s.replace(/^[0-9]+[.\s-]+/, "");
    tgMsg += `<b>${sIdx + 1}.</b> ${cleanStep}\n`;
  });
  
  if (r.chefTip) {
    tgMsg += `\n💡 <b>Şefin Püf Noktası:</b> <i>${r.chefTip}</i>\n`;
  }
  tgMsg += `\n────────────────────\n\n`;
});

tgMsg += `👉 <i>Tariflerinizin çıktısını alabilmeniz için yukarıda özel <b>PDF Tarif Kartı</b> da hazırlanmıştır!</i>`;

return [{
  json: {
    chatId,
    ingredients,
    hasPantry,
    recipes,
    telegramMessage: tgMsg
  }
}];"""

parse_node = make_node(
    name="Parse Recipes & Check Feasibility",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1600, 440],
    parameters={"jsCode": parse_code}
)
nodes.append(parse_node)

# 9. Generate Vector PDF Recipe Book
pdf_code = FIX_TURKISH_MOJIBAKE_JS + r"""const input = $input.first()?.json || {};
const recipes = input.recipes || [];
const ingredients = fixTurkishMojibake(input.ingredients || "");
const hasPantry = input.hasPantry !== false;
const chatId = input.chatId;

function sanitizeForPdf(str) {
  if (!str) return '';
  return fixTurkishMojibake(String(str))
    .replace(/[Öö]/g, m => m === 'Ö' ? 'O' : 'o')
    .replace(/[Üü]/g, m => m === 'Ü' ? 'U' : 'u')
    .replace(/[Çç]/g, m => m === 'Ç' ? 'C' : 'c')
    .replace(/[Ğğ]/g, m => m === 'Ğ' ? 'G' : 'g')
    .replace(/[Şş]/g, m => m === 'Ş' ? 'S' : 's')
    .replace(/[İı]/g, m => m === 'İ' ? 'I' : 'i')
    .replace(/[éèêë]/g, 'e')
    .replace(/[áàâ]/g, 'a')
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    .replace(/[—–]/g, '-')
    .replace(/[•]/g, '*')
    .replace(/[^ -~]/g, ' ')
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)');
}

function wrapText(str, maxChars = 70) {
  const words = String(str || '').replace(/\s+/g, ' ').trim().split(' ');
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

function generateMenuPdf(recipes, ingredients, hasPantry) {
  const objects = [];
  function addObject(content) {
    objects.push(content);
    return objects.length;
  }

  // 1: Catalog, 2: Pages, 3: Page 1 (Recipe 1 & 2), 4: Page 2 (Recipe 3 & Notes)
  addObject('<< /Type /Catalog /Pages 2 0 R >>');
  addObject('<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>');
  addObject('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 5 0 R /Resources << /Font << /F1 7 0 R /F2 8 0 R /F3 9 0 R >> >> >>');
  addObject('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Contents 6 0 R /Resources << /Font << /F1 7 0 R /F2 8 0 R /F3 9 0 R >> >> >>');

  function createPageRenderer() {
    let stream = '';
    return {
      rect: (x, y, w, h, r, g, b) => { stream += `${r} ${g} ${b} rg ${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re f\n`; },
      strokeRect: (x, y, w, h, r, g, b, lw = 1) => { stream += `${lw} w ${r} ${g} ${b} RG ${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)} re S\n`; },
      line: (x1, y1, x2, y2, r, g, b, lw = 1) => { stream += `${lw} w ${r} ${g} ${b} RG ${x1.toFixed(2)} ${y1.toFixed(2)} m ${x2.toFixed(2)} ${y2.toFixed(2)} l S\n`; },
      text: (font, size, x, y, str, r = 0, g = 0, b = 0) => {
        const clean = sanitizeForPdf(str);
        stream += `BT /${font} ${size} Tf ${r} ${g} ${b} rg 1 0 0 1 ${x.toFixed(2)} ${y.toFixed(2)} Tm (${clean}) Tj ET\n`;
      },
      getStream: () => stream
    };
  }

  // PAGE 1: Header + Recipe 1 + Recipe 2
  const p1 = createPageRenderer();
  p1.rect(0, 745, 595.28, 97, 0.08, 0.28, 0.22);
  p1.rect(0, 740, 595.28, 5, 0.85, 0.65, 0.20);

  p1.text('F2', 20, 40, 804, 'AKILLI MUTFAK SEFI', 1, 1, 1);
  p1.text('F2', 10, 40, 786, 'GUNUN MENUSU VE OZEL TARIF KARTLARI', 0.85, 0.65, 0.20);
  p1.text('F1', 8.5, 40, 768, `Malzemeler: ${ingredients.slice(0, 60)}  |  Kiler: ${hasPantry ? 'Var' : 'Sadece Girilenler'}`, 0.85, 0.95, 0.88);

  function renderRecipeCard(p, r, topY, height, index) {
    if (!r) return;
    const cardY = topY - height;
    
    p.rect(40, cardY, 515.28, height, 0.98, 0.98, 0.98);
    p.strokeRect(40, cardY, 515.28, height, 0.88, 0.88, 0.88, 1);
    
    p.rect(40, topY - 28, 515.28, 28, 0.12, 0.35, 0.28);
    const titleUp = sanitizeForPdf(`${index}. ${(r.title || "").replace(/ı/g, 'I').replace(/i/g, 'İ').toLocaleUpperCase("tr-TR")}`);
    p.text('F2', 12, 52, topY - 19, titleUp, 1, 1, 1);
    p.text('F1', 9, 390, topY - 18, `Sure: ${r.time}  |  Zorluk: ${r.difficulty}  |  ${r.portions || '2-3 Kisilik'}`, 0.88, 0.95, 0.90);

    let curY = topY - 45;
    p.text('F2', 9.5, 52, curY, 'MALZEMELER:', 0.15, 0.40, 0.30);
    curY -= 14;
    
    (r.ingredientsUsed || []).slice(0, 6).forEach(ing => {
      wrapText(ing, 24).forEach(l => {
        p.text('F1', 8.5, 55, curY, `* ${l}`, 0.25, 0.25, 0.25);
        curY -= 11;
      });
    });

    let stepY = topY - 45;
    p.text('F2', 9.5, 235, stepY, 'HAZIRLANISI & PISIRME ADIMLARI:', 0.15, 0.40, 0.30);
    stepY -= 14;

    (r.steps || []).slice(0, 5).forEach((step, sIdx) => {
      const clean = step.replace(/^[0-9]+[.\s-]+/, '');
      const wrapped = wrapText(`${sIdx + 1}. ${clean}`, 46);
      wrapped.forEach((line, lIdx) => {
        p.text('F1', 8.5, 238, stepY, line, 0.20, 0.20, 0.20);
        stepY -= 11;
      });
      stepY -= 2;
    });

    if (r.chefTip) {
      stepY -= 2;
      p.rect(235, stepY - 18, 305, 20, 0.93, 0.96, 0.94);
      p.strokeRect(235, stepY - 18, 305, 20, 0.65, 0.82, 0.72, 0.8);
      p.text('F3', 8, 242, stepY - 6, `Sefin Puf Noktasi: ${wrapText(r.chefTip, 45)[0] || ''}`, 0.10, 0.35, 0.25);
    }
  }

  renderRecipeCard(p1, recipes[0], 715, 320, 1);
  renderRecipeCard(p1, recipes[1], 375, 320, 2);

  p1.line(40, 38, 555.28, 38, 0.85, 0.85, 0.85, 0.8);
  p1.text('F1', 8, 40, 26, 'Akilli Mutfak Sefi - Gunun Menusu ve Pratik Tarif Kartlari', 0.55, 0.55, 0.55);
  p1.text('F1', 8, 500, 26, 'Sayfa 1 / 2', 0.55, 0.55, 0.55);

  // PAGE 2: Recipe 3 + Notes
  const p2 = createPageRenderer();
  p2.rect(0, 775, 595.28, 67, 0.08, 0.28, 0.22);
  p2.rect(0, 770, 595.28, 5, 0.85, 0.65, 0.20);
  p2.text('F2', 16, 40, 800, 'AKILLI MUTFAK SEFI', 1, 1, 1);
  p2.text('F1', 9, 40, 785, '3. Ozel Tarif & Sefin Mutfak Notlari', 0.85, 0.95, 0.88);

  renderRecipeCard(p2, recipes[2], 745, 330, 3);

  const boxTop = 390;
  p2.rect(40, boxTop - 340, 515.28, 340, 0.97, 0.98, 0.97);
  p2.strokeRect(40, boxTop - 340, 515.28, 340, 0.80, 0.85, 0.82, 1);

  p2.rect(40, boxTop - 28, 515.28, 28, 0.15, 0.40, 0.30);
  p2.text('F2', 11, 52, boxTop - 19, 'SEFIN MUTFAK NOTLARI & SIFIR ATIK REHBERI', 1, 1, 1);

  let noteY = boxTop - 48;
  const tips = [
    { title: 'Tazelik & Saklama:', desc: 'Kalan yemeklerinizi oda sicakligina geldikten sonra hava almayan kaplarda buzdolabinda 2-3 gun taze saklayabilirsiniz.' },
    { title: 'Sifir Atik & Donusturme:', desc: 'Artan sebze koklerini veya tavuk kemiklerini atmayip buzluga kaldirin; ileride lezzetli bir bulyon corba suyu yapabilirsiniz.' },
    { title: 'Baharat Dengesi:', desc: 'Baharatlari pisirme asamasinin ortasinda eklemek lezzetin yagin icine islemesini saglar. Taze otlari ise servisten hemen once ekleyin.' },
    { title: 'Pratik Hazirlik (Mise en place):', desc: 'Pismeye baslamadan once tum malzemeleri dograyip sirayla tezgaha dizmek pisirme suresini yariya indirir ve yanmayi onler.' },
    { title: 'Afiyet Olsun:', desc: 'Yemek yapmak bir sanattir. Elinizdeki malzemelerle harikalar yarattiniz! Bon appetit!' }
  ];

  tips.forEach(t => {
    p2.text('F2', 9.5, 55, noteY, t.title, 0.12, 0.35, 0.25);
    noteY -= 13;
    wrapText(t.desc, 76).forEach(l => {
      p2.text('F1', 8.5, 58, noteY, l, 0.25, 0.25, 0.25);
      noteY -= 11;
    });
    noteY -= 6;
  });

  p2.line(40, 38, 555.28, 38, 0.85, 0.85, 0.85, 0.8);
  p2.text('F1', 8, 40, 26, 'Akilli Mutfak Sefi - Gunun Menusu ve Pratik Tarif Kartlari', 0.55, 0.55, 0.55);
  p2.text('F1', 8, 500, 26, 'Sayfa 2 / 2', 0.55, 0.55, 0.55);

  const s1 = p1.getStream();
  const s2 = p2.getStream();
  addObject(`<< /Length ${Buffer.byteLength(s1, 'binary')} >>\nstream\n${s1}endstream`);
  addObject(`<< /Length ${Buffer.byteLength(s2, 'binary')} >>\nstream\n${s2}endstream`);

  addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>');
  addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>');

  let pdf = '%PDF-1.4\n';
  const offsets = [];
  let curOffset = Buffer.byteLength(pdf, 'binary');

  for (let i = 0; i < objects.length; i++) {
    offsets.push(curOffset);
    const objStr = `${i + 1} 0 obj\n${objects[i]}\nendobj\n`;
    pdf += objStr;
    curOffset += Buffer.byteLength(objStr, 'binary');
  }

  const xrefStart = curOffset;
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 0; i < objects.length; i++) {
    pdf += `${String(offsets[i]).padStart(10, '0')} 00000 n \n`;
  }

  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF\n`;
  return Buffer.from(pdf, 'binary');
}

const pdfBuffer = generateMenuPdf(recipes, ingredients, hasPantry);

return [{
  json: {
    chatId,
    ingredients,
    telegramMessage: input.telegramMessage
  },
  binary: {
    data: {
      data: pdfBuffer.toString("base64"),
      mimeType: "application/pdf",
      fileName: "Gunun_Menusu_ve_Tarif_Kartlari.pdf"
    }
  }
}];"""

pdf_node = make_node(
    name="Generate Vector PDF Recipe Book",
    node_type="n8n-nodes-base.code",
    type_version=2,
    position=[1880, 440],
    parameters={"jsCode": pdf_code}
)
nodes.append(pdf_node)

# 10. Send PDF Document to Telegram
send_pdf_node = make_node(
    name="Send PDF Document to Telegram",
    node_type="n8n-nodes-base.telegram",
    type_version=1.2,
    position=[2160, 440],
    parameters={
        "operation": "sendDocument",
        "chatId": "={{ $json.chatId }}",
        "binaryData": True,
        "binaryPropertyName": "data",
        "caption": "📋 <b>Günün Menüsü & Tarif Kartları (PDF)</b>\nElinizdeki malzemelerle hazırlanan 3 özel tarifin çıktısını alabileceğiniz tarif kartı belgeniz hazırdır.",
        "additionalFields": {
            "parse_mode": "HTML"
        }
    },
    credentials={
        "telegramApi": {
            "id": "mealPlanGeneratorBot",
            "name": "Meal Plan Generator Bot"
        }
    }
)
nodes.append(send_pdf_node)

# 11. Send Telegram Recipes Message with Action Buttons
send_msg_node = make_node(
    name="Send Recipes Message with Buttons",
    node_type="n8n-nodes-base.telegram",
    type_version=1.2,
    position=[2440, 440],
    parameters={
        "operation": "sendMessage",
        "chatId": "={{ $('Generate Vector PDF Recipe Book').first().json.chatId }}",
        "text": "={{ $('Generate Vector PDF Recipe Book').first().json.telegramMessage }}",
        "additionalFields": {
            "parse_mode": "HTML"
        },
        "replyMarkup": "inlineKeyboard",
        "inlineKeyboard": {
            "rows": [
                {
                    "row": {
                        "buttons": [
                            {
                                "text": "✅ Tarifler Harika! (Afiyet Olsun)",
                                "additionalFields": {
                                    "callback_data": "p14_accept"
                                }
                            }
                        ]
                    }
                },
                {
                    "row": {
                        "buttons": [
                            {
                                "text": "🔄 3 Farklı Alternatif Öner",
                                "additionalFields": {
                                    "callback_data": "p14_more"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    },
    credentials={
        "telegramApi": {
            "id": "mealPlanGeneratorBot",
            "name": "Meal Plan Generator Bot"
        }
    }
)
nodes.append(send_msg_node)

# Connections
connections = {
    "Telegram Trigger (Chat & Buttons)": {
        "main": [[{"node": "Conversation & State Router", "type": "main", "index": 0}]]
    },
    "Conversation & State Router": {
        "main": [[{"node": "Is Fridge Photo?", "type": "main", "index": 0}]]
    },
    "Is Fridge Photo?": {
        "main": [
            # Output 0 (True: photo)
            [{"node": "Gemini 3.1: Detect Fridge Ingredients", "type": "main", "index": 0}],
            # Output 1 (False: meal)
            [{"node": "Prepare Gemini Meal Prompt", "type": "main", "index": 0}]
        ]
    },
    "Gemini 3.1: Detect Fridge Ingredients": {
        "main": [[{"node": "Send Detected Ingredients with Pantry Buttons", "type": "main", "index": 0}]]
    },
    "Prepare Gemini Meal Prompt": {
        "main": [[{"node": "Gemini 3.1: Generate Meal Plan", "type": "main", "index": 0}]]
    },
    "Gemini 3.1: Generate Meal Plan": {
        "main": [[{"node": "Parse Recipes & Check Feasibility", "type": "main", "index": 0}]]
    },
    "Parse Recipes & Check Feasibility": {
        "main": [[{"node": "Generate Vector PDF Recipe Book", "type": "main", "index": 0}]]
    },
    "Generate Vector PDF Recipe Book": {
        "main": [[{"node": "Send PDF Document to Telegram", "type": "main", "index": 0}]]
    },
    "Send PDF Document to Telegram": {
        "main": [[{"node": "Send Recipes Message with Buttons", "type": "main", "index": 0}]]
    }
}

workflow = {
    "name": "Project 14 : Ingredient to Meal Plan & Recipe Generator (PDF & AI)",
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

out_path = "intermediate-projects/14.ingredient-to-meal-plan/workflow.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"Generated {out_path} with {len(nodes)} nodes successfully!")
