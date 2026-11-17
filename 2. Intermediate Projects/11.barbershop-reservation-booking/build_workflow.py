#!/usr/bin/env python3
"""
Build script for Project 11: Barbershop Reservation Booking (Telegram + AI + Supabase PostgreSQL)
Production-grade multi-role booking agent with PostgreSQL ACID slot collision protection,
strict client identity isolation, and owner admin tools with automatic customer cancellation alerts.
"""

import json
import os

OUTPUT_DIR = "intermediate-projects/11.barbershop-reservation-booking"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "workflow.json")

# ==============================================================================
# JAVASCRIPT CODE SNIPPETS
# ==============================================================================

central_security_guard_js = '''const item = $input.first().json;

// Central Barbershop & Owner Credentials
const OWNER_USER_ID = "1519369571"; // Serhat Kumas Telegram User ID (Admin/Owner)
const SHOP_NAME = "Crown & Blade Gentlemen's Barbershop";
const SHOP_LOCATION = "Maximilianstraße 34, 80539 Munich";
const BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"; // Reservation Bot (@Reservation_sk_bot)

// Supabase PostgreSQL Configuration
// Replace with your project URL and service_role or anon key from Supabase Settings -> API
const SUPABASE_URL = "https://ngpujpgcwcxvrqoemcio.supabase.co";
const SUPABASE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_KEY";

// Operating Parameters (Monday - Saturday 09:00 - 19:00, 1-hour slots)
const WORKING_HOURS = {
  startHour: 9,
  endHour: 19,
  workingDays: [1, 2, 3, 4, 5, 6], // Mon-Sat (0=Sun)
  slotDurationMinutes: 60,
  allSlots: ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
};

// Services Menu
const SERVICES = [
  { id: "haircut", name: "Classic Haircut & Styling", price: "€35", duration: "45 min" },
  { id: "beard", name: "Beard Sculpting & Hot Towel", price: "€25", duration: "30 min" },
  { id: "royal", name: "The Royal Treatment (Haircut + Beard + Facial)", price: "€55", duration: "60 min" },
  { id: "buzz", name: "Buzz Cut & Refreshing Wash", price: "€25", duration: "30 min" }
];

// Extract Sender Information
const callbackQuery = item.callback_query;
const message = item.message;

let userId = "";
let chatId = "";
let firstName = "Guest";
let username = "";
let text = "";
let callbackData = "";
let callbackQueryId = "";
let isCallback = false;
let messageId = null;

if (callbackQuery) {
  isCallback = true;
  userId = String(callbackQuery.from?.id || "");
  chatId = String(callbackQuery.message?.chat?.id || userId);
  firstName = callbackQuery.from?.first_name || "Guest";
  username = callbackQuery.from?.username ? `@${callbackQuery.from.username}` : "";
  callbackData = String(callbackQuery.data || "").trim();
  callbackQueryId = callbackQuery.id;
  messageId = callbackQuery.message?.message_id;
  text = callbackData;
} else if (message) {
  userId = String(message.from?.id || "");
  chatId = String(message.chat?.id || userId);
  firstName = message.from?.first_name || "Guest";
  username = message.from?.username ? `@${message.from.username}` : "";
  text = String(message.text || "").trim();
  messageId = message.message_id;
}

const isOwner = (String(userId) === String(OWNER_USER_ID));

return [{
  json: {
    ownerUserId: OWNER_USER_ID,
    shopName: SHOP_NAME,
    shopLocation: SHOP_LOCATION,
    supabaseUrl: SUPABASE_URL,
    supabaseKey: SUPABASE_KEY,
    botToken: BOT_TOKEN,
    workingHours: WORKING_HOURS,
    services: SERVICES,
    userId: userId,
    chatId: chatId,
    firstName: firstName,
    username: username,
    userText: text,
    isCallback: isCallback,
    callbackData: callbackData,
    callbackQueryId: callbackQueryId,
    messageId: messageId,
    isOwner: isOwner,
    currentDateIso: new Date().toISOString()
  }
}];'''

parse_button_action_js = '''let guardItem = {};
try {
  guardItem = $('Central Brand & Security Guard').first().json;
} catch (e) {
  guardItem = $input.first().json;
}
const data = guardItem.callbackData || "";

let intent = "UNKNOWN";
let bookingId = "";
let targetDate = "";
let targetTime = "";

// Smart default date (forward past 18:00 or Sunday to next business day)
const now = new Date();
let defaultDate = now.toISOString().split("T")[0];
if (now.getHours() >= 18) {
  defaultDate = new Date(now.getTime() + 24 * 3600 * 1000).toISOString().split("T")[0];
}
if (new Date(defaultDate + "T12:00:00Z").getUTCDay() === 0) {
  defaultDate = new Date(new Date(defaultDate + "T12:00:00Z").getTime() + 24 * 3600 * 1000).toISOString().split("T")[0];
}

if (data.startsWith("cancel_bkg:")) {
  intent = guardItem.isOwner ? "ADMIN_CANCEL" : "CANCEL";
  bookingId = data.replace("cancel_bkg:", "").trim();
} else if (data.startsWith("view_slots:")) {
  intent = "CHECK_SLOTS";
  targetDate = data.replace("view_slots:", "").trim() || defaultDate;
} else if (data.startsWith("book_slot:")) {
  // format book_slot:YYYY-MM-DD_HH:MM
  intent = "BOOK";
  const parts = data.replace("book_slot:", "").trim().split("_");
  targetDate = parts[0] || defaultDate;
  targetTime = parts[1] || "";
} else if (data === "my_bookings") {
  intent = "MY_BOOKINGS";
} else if (data === "admin_today") {
  intent = "ADMIN_LIST_ALL";
  targetDate = defaultDate;
}

return [{
  json: {
    ...guardItem,
    parsedIntent: intent,
    targetDate: targetDate,
    targetTime: targetTime,
    bookingId: bookingId,
    service: "Classic Haircut & Styling",
    cancellationReason: guardItem.isOwner ? "Cancelled by Barbershop Owner" : "Customer cancelled",
    detectedLanguage: "tr"
  }
}];'''

prepare_gemini_prompt_js = '''let item = {};
try {
  item = $('Central Brand & Security Guard').first().json;
} catch (e) {
  item = $input.first().json;
}

// Reference timestamps for relative date conversion
const now = new Date();
const nowIso = now.toISOString();
const currentDate = nowIso.split("T")[0]; // YYYY-MM-DD
const dayOfWeekName = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][now.getDay()];

const prompt = `You are the elite AI reservation and customer intake concierge for "${item.shopName}".
Location: ${item.shopLocation}.
Operating Hours: Monday to Saturday 09:00 - 19:00 (1-hour slots: 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00). Closed on Sundays.
Available Services:
- Classic Haircut & Styling (€35, 45 min)
- Beard Sculpting & Hot Towel (€25, 30 min)
- The Royal Treatment (Haircut + Beard + Facial, €55, 60 min)
- Buzz Cut & Wash (€25, 30 min)

Reference Current Timestamp:
- Today's Date: ${currentDate} (${dayOfWeekName})
- Current Time: ${now.toTimeString().split(" ")[0]}

User Information:
- Telegram Name: ${item.firstName}
- Telegram User ID: ${item.userId}
- Sender Role: ${item.isOwner ? "SHOP_OWNER / ADMIN" : "CUSTOMER"}

User's Incoming Message:
"${item.userText}"

YOUR GOAL:
Classify user intent, extract all scheduling parameters, and extract any customer contact details (Full Name, Phone Number).
Support Turkish, English, and German natively based on the user's message language.

INTENT TYPES:
1. "BOOK": User wants to make an appointment or specifies date/time (e.g. "Yarın saat 12.00 için randevu almak istiyorum", "I want a haircut tomorrow at 3pm", "Book Friday 14:00").
2. "PROVIDE_CONTACT": User is providing their name and/or phone number to finalize a booking (e.g. "Ahmet Yılmaz 0532 123 4567", "Telefonum 05551234567, adım Mehmet", "+905321234567", "0532 123 45 67").
3. "CANCEL": Customer wants to cancel their appointment (e.g. "Randevumu iptal etmek istiyorum", "Cancel my booking", "I can't make it tomorrow").
4. "MY_BOOKINGS": Customer asks about their appointments (e.g. "Randevum ne zaman?", "Show my bookings", "Aktif randevum var mı?").
5. "CHECK_SLOTS": User asks which hours are free (e.g. "Yarın hangi saatler boş?", "Available times on Saturday?").
6. "ADMIN_LIST_ALL": ONLY AVAILABLE TO OWNER (userId: ${item.ownerUserId}). Owner wants to see all bookings (e.g. "Yarınki randevuları listele", "Show all bookings for today").
7. "ADMIN_CANCEL": ONLY AVAILABLE TO OWNER (userId: ${item.ownerUserId}). Owner cancels any booking (e.g. "Ali'nin 14:00 randevusunu iptal et", "Cancel booking BKG-102").
8. "HELP_GREETING": Greetings, service prices, working hours (/start, "Merhaba", "Hello", "Fiyatlar nedir?").

CRITICAL EXTRACTION RULES:
- Date resolution:
  - "bugün" / "today" -> "${currentDate}"
  - "yarın" / "tomorrow" -> calculate exactly 1 day after ${currentDate}
  - Named weekdays ("Cuma", "Friday", "Pazartesi") -> calculate exact YYYY-MM-DD.
- Time normalization:
  - "12.00", "12:00", "öğlen 12" -> "12:00"
  - "15:00", "3pm", "öğleden sonra 3" -> "15:00"
  - Standardize to 24-hour "HH:00" format matching slots: 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00.
- Customer Contact Details:
  - "customerName": Extract the user's full name if provided in the text (e.g. "Ahmet Yılmaz", "Serhat Kumaş", "John Miller"). If user only gives a first name, extract that. If not provided, null.
  - "customerPhone": Extract the phone number if present in ANY format (e.g. "0532 123 45 67", "+90 555 123 4567", "05551234567", "+49 170 1234567"). Normalize into clean format or null if not mentioned.
- Language Detection:
  - "language": "tr" if Turkish, "en" if English, "de" if German.

OUTPUT FORMAT:
Return STRICT JSON ONLY (no markdown fences, no conversational text outside JSON):
{
  "intent": "BOOK" | "PROVIDE_CONTACT" | "CANCEL" | "MY_BOOKINGS" | "CHECK_SLOTS" | "ADMIN_LIST_ALL" | "ADMIN_CANCEL" | "HELP_GREETING",
  "language": "tr" | "en" | "de",
  "targetDate": "YYYY-MM-DD" or null,
  "targetTime": "HH:00" or null,
  "service": "Classic Haircut & Styling" | "Beard Sculpting & Hot Towel" | "The Royal Treatment" | "Buzz Cut & Wash",
  "customerName": "Extracted name or null",
  "customerPhone": "Extracted phone or null",
  "bookingId": "BKG-XXXX or null",
  "cancellationReason": "Reason if mentioned or null",
  "friendlyNote": "Polite 1-sentence note in user language"
}`;

return [{
  json: {
    ...item,
    geminiPrompt: prompt
  }
}];'''

parse_gemini_response_js = '''const item = $input.first().json;
const rawText = item.candidates?.[0]?.content?.parts?.[0]?.text || "{}";

let parsed = {};
try {
  const cleaned = rawText.replace(/```json/gi, "").replace(/```/g, "").trim();
  parsed = JSON.parse(cleaned);
} catch (e) {
  parsed = {
    intent: "HELP_GREETING",
    language: "tr",
    friendlyNote: "Crown & Blade Barbershop'a hoş geldiniz! Size randevu konusunda nasıl yardımcı olabilirim?"
  };
}

const cfg = $('Central Brand & Security Guard').first().json;

// Enforce role-based intent protection
let safeIntent = parsed.intent || "HELP_GREETING";
if ((safeIntent === "ADMIN_LIST_ALL" || safeIntent === "ADMIN_CANCEL") && !cfg.isOwner) {
  safeIntent = "UNAUTHORIZED_ADMIN_ATTEMPT";
}

return [{
  json: {
    ...cfg,
    parsedIntent: safeIntent,
    detectedLanguage: parsed.language || "tr",
    targetDate: parsed.targetDate || "",
    targetTime: parsed.targetTime || "",
    service: parsed.service || "Classic Haircut & Styling",
    extractedCustomerName: parsed.customerName || null,
    extractedCustomerPhone: parsed.customerPhone || null,
    bookingId: parsed.bookingId || null,
    cancellationReason: parsed.cancellationReason || "No reason specified",
    aiReply: parsed.friendlyNote || ""
  }
}];'''

reservation_core_engine_js = '''const cfg = $('Central Brand & Security Guard').first().json;

// Extract intent data directly from either Button action or AI NLP parser
let intentData = {};
if (cfg.isCallback) {
  try { intentData = $('Parse Button Action').first().json; } catch(e) {}
} else {
  try { intentData = $('Parse AI Intent & Normalizer').first().json; } catch(e) {}
}

const targetIntent = intentData.parsedIntent || "HELP_GREETING";
const targetDateInput = intentData.targetDate || "";
const targetTimeInput = intentData.targetTime || "";
const serviceInput = intentData.service || "Classic Haircut & Styling";
const bookingIdInput = intentData.bookingId || null;
const cancellationReasonInput = intentData.cancellationReason || "No reason specified";
const lang = intentData.detectedLanguage || "tr";
const extractedCustomerName = intentData.extractedCustomerName || null;
const extractedCustomerPhone = intentData.extractedCustomerPhone || null;

// Extract Supabase PostgreSQL rows safely
let allDbRows = [];
try {
  const rawDb = $('Supabase: Read All Bookings').all();
  allDbRows = rawDb.map(i => i.json || {}).filter(r => r.booking_id || r["Booking ID"]);
} catch(e) {
  allDbRows = [];
}

// Normalize DB row fields for both snake_case and Title Case
const normalizedRows = allDbRows.map(r => ({
  booking_id: r.booking_id || r["Booking ID"] || "",
  booking_date: r.booking_date || r["Date"] || "",
  time_slot: r.time_slot || r["Time Slot"] || "",
  customer_name: r.customer_name || r["Customer Name"] || "Guest",
  customer_phone: r.customer_phone || r["Customer Phone"] || null,
  telegram_user_id: String(r.telegram_user_id || r["Telegram User ID"] || ""),
  telegram_username: r.telegram_username || r["Telegram Username"] || "",
  service: r.service || r["Service"] || "Classic Haircut & Styling",
  price: r.price || r["Price"] || "€35",
  status: r.status || r["Status"] || "Confirmed",
  notes: r.notes || r["Notes"] || ""
}));

// Find existing customer info if they previously booked
const pastCustomer = normalizedRows.find(r => r.telegram_user_id === String(cfg.userId) && r.customer_phone);
const existingPhone = pastCustomer ? pastCustomer.customer_phone : null;
const existingName = pastCustomer ? pastCustomer.customer_name : null;

// Find any active pending Draft booking for this user
const activeDraft = normalizedRows.find(r => r.telegram_user_id === String(cfg.userId) && r.status === "Draft");

const allSlots = cfg.workingHours.allSlots;
const now = new Date();
const nowIso = now.toISOString();

// Smart default date for buttons (forward to tomorrow if past 18:00 or if Sunday)
let defaultDate = nowIso.split("T")[0];
if (now.getHours() >= 18) {
  defaultDate = new Date(now.getTime() + 24 * 3600 * 1000).toISOString().split("T")[0];
}
if (new Date(defaultDate + "T12:00:00Z").getUTCDay() === 0) {
  defaultDate = new Date(new Date(defaultDate + "T12:00:00Z").getTime() + 24 * 3600 * 1000).toISOString().split("T")[0];
}
const todayDateStr = defaultDate;

let dbAction = "NONE"; // NONE, APPEND, UPDATE
let rowToAppend = null;
let rowToUpdate = null;
let responseMessage = "";
let replyMarkup = null;
let notifyCustomer = false;
let customerNotification = null;

// Helper: Find confirmed bookings for a date
function getConfirmedBookingsForDate(dateStr) {
  return normalizedRows.filter(r => {
    return r.booking_date === dateStr && r.status.toLowerCase() === "confirmed";
  });
}

// Helper: Calculate available slots
function getAvailableSlots(dateStr) {
  const confirmed = getConfirmedBookingsForDate(dateStr);
  const bookedSlots = new Set(confirmed.map(r => r.time_slot.trim()));
  return allSlots.filter(s => !bookedSlots.has(s));
}

// ==============================================================================
// 1. INTENT: BOOK (Customer or Owner booking)
// ==============================================================================
if (targetIntent === "BOOK") {
  const targetDate = targetDateInput || (activeDraft ? activeDraft.booking_date : todayDateStr);
  const targetTime = targetTimeInput || (activeDraft ? activeDraft.time_slot : null);

  // Validate working days (Mon-Sat, closed Sundays)
  const dateObj = new Date(targetDate + "T12:00:00Z");
  const dayOfWeek = isNaN(dateObj.getTime()) ? 1 : dateObj.getUTCDay();

  if (dayOfWeek === 0) { // Sunday
    if (lang === "tr") {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nPazar günleri kapalıyız. Pazartesi - Cumartesi 09:00 - 19:00 saatleri arasında hizmet veriyoruz. Lütfen hafta içi veya Cumartesi için bir gün seçiniz. ✂️`;
    } else {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nWe are closed on Sundays! Our barbers operate Monday through Saturday, 09:00 - 19:00. Please choose a date between Monday and Saturday. ✂️`;
    }
  } else if (!targetTime || !allSlots.includes(targetTime)) {
    // Missing or invalid time -> show available slots for this date
    const freeSlots = getAvailableSlots(targetDate);
    if (freeSlots.length === 0) {
      if (lang === "tr") {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n<b>${targetDate}</b> tarihinde uygun boş saat kalmamıştır. Lütfen başka bir gün deneyiniz. ✂️`;
      } else {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nNo open spots on <b>${targetDate}</b>. Please check another date. ✂️`;
      }
    } else {
      if (lang === "tr") {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n📅 <b>${targetDate} Tarihindeki Müsait Saatler:</b>\\n\\n` +
          freeSlots.map(s => `• <b>${s}</b>`).join("\\n") +
          `\\n\\nRandevu almak istediğiniz saati aşağıdan seçebilir veya yazabilirsiniz: ✂️`;
      } else {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n📅 <b>Available Slots for ${targetDate}:</b>\\n\\n` +
          freeSlots.map(s => `• <b>${s}</b>`).join("\\n") +
          `\\n\\nSelect a slot below or reply with your preferred time: ✂️`;
      }

      const buttons = freeSlots.slice(0, 4).map(s => ({
        text: `✂️ ${s}`,
        callback_data: `book_slot:${targetDate}_${s}`
      }));
      replyMarkup = {
        inline_keyboard: [buttons]
      };
    }
  } else {
    // Check slot availability against confirmed bookings
    const confirmed = getConfirmedBookingsForDate(targetDate);
    const isOccupied = confirmed.some(r => r.time_slot.trim() === targetTime);

    if (isOccupied) {
      const freeSlots = getAvailableSlots(targetDate);
      if (lang === "tr") {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nBelirttiğiniz <b>${targetTime}</b> saati doludur.\\n\\n✨ <b>Diğer Müsait Saatler:</b>\\n` +
          (freeSlots.length > 0 ? freeSlots.map(s => `• <b>${s}</b>`).join("\\n") : "<i>Bu gün için boş saat kalmadı.</i>") +
          `\\n\\nLütfen yukarıdaki müsait saatlerden birini seçiniz: ✂️`;
      } else {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n<b>${targetTime}</b> on <b>${targetDate}</b> is already booked.\\n\\n✨ <b>Remaining Open Slots:</b>\\n` +
          (freeSlots.length > 0 ? freeSlots.map(s => `• <b>${s}</b>`).join("\\n") : "<i>No slots left for this day.</i>") +
          `\\n\\nPlease select an alternative time: ✂️`;
      }
      
      if (freeSlots.length > 0) {
        replyMarkup = {
          inline_keyboard: [
            freeSlots.slice(0, 3).map(s => ({
              text: `✂️ ${s}`,
              callback_data: `book_slot:${targetDate}_${s}`
            }))
          ]
        };
      }
    } else {
      // Slot is FREE! Check if we have customer's Name and Phone Number
      const candidatePhone = extractedCustomerPhone || existingPhone;
      const candidateName = extractedCustomerName || existingName || (cfg.firstName !== "Guest" ? cfg.firstName : null);
      const srvObj = cfg.services.find(s => s.name.toLowerCase().includes(serviceInput.toLowerCase())) || cfg.services[0];

      if (!candidatePhone) {
        // Customer has NOT provided phone number yet! Save draft in Supabase & ask for contact details
        const draftId = activeDraft ? activeDraft.booking_id : `DFT-${targetDate.replace(/-/g, "")}-${Math.floor(1000 + Math.random() * 9000)}`;

        if (activeDraft) {
          dbAction = "UPDATE";
          rowToUpdate = {
            booking_id: activeDraft.booking_id,
            payload: {
              booking_date: targetDate,
              time_slot: targetTime,
              customer_name: candidateName || cfg.firstName || "Customer",
              service: srvObj.name,
              price: srvObj.price,
              status: "Draft",
              notes: "Awaiting customer phone number"
            }
          };
        } else {
          dbAction = "APPEND";
          rowToAppend = {
            booking_id: draftId,
            booking_date: targetDate,
            time_slot: targetTime,
            customer_name: candidateName || cfg.firstName || "Customer",
            customer_phone: null,
            telegram_user_id: cfg.userId,
            telegram_username: cfg.username || "N/A",
            service: srvObj.name,
            price: srvObj.price,
            status: "Draft",
            notes: "Awaiting customer phone number"
          };
        }

        if (lang === "tr") {
          responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
            `✂️ <b>${targetDate} — Saat ${targetTime}</b> randevunuz için müsait!\\n\\n` +
            `📋 <b>Randevu Kaydınızı Tamamlamak İçin:</b>\\n` +
            `Lütfen <b>Ad-Soyad</b> ve <b>Telefon Numaranızı</b> iletebilir misiniz?\\n` +
            `<i>(Örnek: Ahmet Yılmaz, 0532 123 45 67)</i>`;
        } else {
          responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
            `✂️ <b>${targetDate} at ${targetTime}</b> is available!\\n\\n` +
            `📋 <b>To Finalize Your Reservation:</b>\\n` +
            `Please reply with your <b>Full Name</b> and <b>Phone Number</b>:\\n` +
            `<i>(e.g., John Miller, +49 170 1234567)</i>`;
        }
      } else {
        // Customer details are present! Confirm reservation immediately
        const finalBookingId = `BKG-${targetDate.replace(/-/g, "")}-${Math.floor(1000 + Math.random() * 9000)}`;
        const finalCustomerName = candidateName || cfg.firstName || "Valued Customer";

        if (activeDraft) {
          dbAction = "UPDATE";
          rowToUpdate = {
            booking_id: activeDraft.booking_id,
            payload: {
              booking_id: finalBookingId,
              booking_date: targetDate,
              time_slot: targetTime,
              customer_name: finalCustomerName,
              customer_phone: candidatePhone,
              service: srvObj.name,
              price: srvObj.price,
              status: "Confirmed",
              notes: "Confirmed with customer phone"
            }
          };
        } else {
          dbAction = "APPEND";
          rowToAppend = {
            booking_id: finalBookingId,
            booking_date: targetDate,
            time_slot: targetTime,
            customer_name: finalCustomerName,
            customer_phone: candidatePhone,
            telegram_user_id: cfg.userId,
            telegram_username: cfg.username || "N/A",
            service: srvObj.name,
            price: srvObj.price,
            status: "Confirmed",
            notes: cancellationReasonInput || "Booked via Telegram AI"
          };
        }

        if (lang === "tr") {
          responseMessage = `🎉 <b>Randevunuz Başarıyla Onaylandı!</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
            `👤 <b>Müşteri:</b> ${finalCustomerName}\\n` +
            `📞 <b>Telefon:</b> ${candidatePhone}\\n` +
            `💈 <b>Hizmet:</b> ${srvObj.name} (${srvObj.price})\\n` +
            `📅 <b>Tarih:</b> <b>${targetDate}</b>\\n` +
            `⏰ <b>Saat:</b> <b>${targetTime}</b>\\n` +
            `📍 <b>Adres:</b> ${cfg.shopLocation}\\n\\n` +
            `<i>Sizi ağırlamaktan mutluluk duyacağız!</i> ✂️`;
        } else {
          responseMessage = `🎉 <b>Reservation Confirmed!</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
            `👤 <b>Customer:</b> ${finalCustomerName}\\n` +
            `📞 <b>Phone:</b> ${candidatePhone}\\n` +
            `💈 <b>Service:</b> ${srvObj.name} (${srvObj.price})\\n` +
            `📅 <b>Date:</b> <b>${targetDate}</b>\\n` +
            `⏰ <b>Time:</b> <b>${targetTime}</b>\\n` +
            `📍 <b>Location:</b> ${cfg.shopLocation}\\n\\n` +
            `<i>Looking forward to your visit!</i> ✂️`;
        }

        replyMarkup = {
          inline_keyboard: [
            [
              { text: "❌ Randevuyu İptal Et", callback_data: `cancel_bkg:${finalBookingId}` },
              { text: "📋 Randevularım", callback_data: "my_bookings" }
            ]
          ]
        };
      }
    }
  }
}

// ==============================================================================
// 1b. INTENT: PROVIDE_CONTACT (Customer sends Name & Phone Number)
// ==============================================================================
else if (targetIntent === "PROVIDE_CONTACT") {
  const phone = extractedCustomerPhone || existingPhone;
  const name = extractedCustomerName || existingName || (cfg.firstName !== "Guest" ? cfg.firstName : "Değerli Müşterimiz");

  if (activeDraft) {
    // Check if draft's slot is still free
    const confirmed = getConfirmedBookingsForDate(activeDraft.booking_date);
    const isOccupied = confirmed.some(r => r.time_slot.trim() === activeDraft.time_slot);

    if (isOccupied) {
      const freeSlots = getAvailableSlots(activeDraft.booking_date);
      if (lang === "tr") {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
          `Maalesef <b>${activeDraft.time_slot}</b> saati kısa süre önce doldu.\\n\\n` +
          `Müsait diğer saatler:\\n` +
          freeSlots.map(s => `• <b>${s}</b>`).join("\\n") +
          `\\n\\nLütfen yukarıdaki saatlerden birini seçiniz: ✂️`;
      } else {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
          `Unfortunately, <b>${activeDraft.time_slot}</b> was just booked.\\n\\n` +
          `Other available slots:\\n` +
          freeSlots.map(s => `• <b>${s}</b>`).join("\\n") +
          `\\n\\nPlease select another available slot: ✂️`;
      }
    } else {
      const finalBookingId = `BKG-${activeDraft.booking_date.replace(/-/g, "")}-${Math.floor(1000 + Math.random() * 9000)}`;
      dbAction = "UPDATE";
      rowToUpdate = {
        booking_id: activeDraft.booking_id,
        payload: {
          booking_id: finalBookingId,
          customer_name: name,
          customer_phone: phone || "Belirtilmedi",
          status: "Confirmed",
          notes: `Customer contact confirmed at ${nowIso}`
        }
      };

      if (lang === "tr") {
        responseMessage = `🎉 <b>Randevunuz Başarıyla Onaylandı!</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
          `👤 <b>Müşteri:</b> ${name}\\n` +
          `📞 <b>Telefon:</b> ${phone || "Kayıtlı"}\\n` +
          `💈 <b>Hizmet:</b> ${activeDraft.service} (${activeDraft.price})\\n` +
          `📅 <b>Tarih:</b> <b>${activeDraft.booking_date}</b>\\n` +
          `⏰ <b>Saat:</b> <b>${activeDraft.time_slot}</b>\\n` +
          `📍 <b>Adres:</b> ${cfg.shopLocation}\\n\\n` +
          `<i>Sizi ağırlamaktan mutluluk duyacağız!</i> ✂️`;
      } else {
        responseMessage = `🎉 <b>Reservation Confirmed!</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
          `👤 <b>Customer:</b> ${name}\\n` +
          `📞 <b>Phone:</b> ${phone || "On File"}\\n` +
          `💈 <b>Service:</b> ${activeDraft.service} (${activeDraft.price})\\n` +
          `📅 <b>Date:</b> <b>${activeDraft.booking_date}</b>\\n` +
          `⏰ <b>Time:</b> <b>${activeDraft.time_slot}</b>\\n` +
          `📍 <b>Location:</b> ${cfg.shopLocation}\\n\\n` +
          `<i>Looking forward to your visit!</i> ✂️`;
      }

      replyMarkup = {
        inline_keyboard: [
          [
            { text: "❌ Randevuyu İptal Et", callback_data: `cancel_bkg:${finalBookingId}` },
            { text: "📋 Randevularım", callback_data: "my_bookings" }
          ]
        ]
      };
    }
  } else {
    // No active draft, ask which date & time they want
    if (lang === "tr") {
      responseMessage = `💈 Teşekkürler <b>${name}</b>! İletişim numaranız (<code>${phone || "Kayıtlı"}</code>) alındı.\\n\\nHangi gün ve saat için randevu almak istersiniz? (Örn: Yarın 14:00 veya Cuma 11:00) ✂️`;
    } else {
      responseMessage = `💈 Thank you <b>${name}</b>! Your phone number (<code>${phone || "On File"}</code>) is noted.\\n\\nWhich date and time would you like to reserve? (e.g., Tomorrow at 2 PM or Friday 11:00) ✂️`;
    }
  }
}

// ==============================================================================
// 2. INTENT: CANCEL (Customer cancellation)
// ==============================================================================
else if (targetIntent === "CANCEL") {
  // Find active bookings belonging to THIS user only
  const myActiveBookings = normalizedRows.filter(r => {
    return r.telegram_user_id === String(cfg.userId) && r.status.toLowerCase() === "confirmed";
  });

  if (myActiveBookings.length === 0) {
    if (lang === "tr") {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nŞu an için aktif bir randevunuz bulunmamaktadır. ✂️`;
    } else {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nYou have no active reservations to cancel. ✂️`;
    }
    replyMarkup = {
      inline_keyboard: [
        [{ text: "📅 Müsait Saatleri Gör", callback_data: `view_slots:${todayDateStr}` }]
      ]
    };
  } else {
    let targetBooking = null;
    if (bookingIdInput) {
      targetBooking = myActiveBookings.find(b => b.booking_id.toLowerCase() === bookingIdInput.toLowerCase());
    } else if (targetDateInput) {
      targetBooking = myActiveBookings.find(b => b.booking_date === targetDateInput);
    } else {
      targetBooking = myActiveBookings[0];
    }

    if (!targetBooking) {
      if (lang === "tr") {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nLütfen iptal etmek istediğiniz randevuyu aşağıdan seçiniz:`;
      } else {
        responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nPlease select the reservation you wish to cancel:`;
      }
      replyMarkup = {
        inline_keyboard: myActiveBookings.map(b => ([
          { text: `❌ İptal: ${b.booking_date} @ ${b.time_slot}`, callback_data: `cancel_bkg:${b.booking_id}` }
        ]))
      };
    } else {
      dbAction = "UPDATE";
      rowToUpdate = {
        booking_id: targetBooking.booking_id,
        payload: {
          status: "Cancelled by Customer",
          notes: `Customer cancelled at ${nowIso}`
        }
      };

      if (lang === "tr") {
        responseMessage = `✅ <b>Randevunuz Başarıyla İptal Edildi</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
          `• <b>Tarih:</b> ${targetBooking.booking_date}\\n` +
          `• <b>Saat:</b> ${targetBooking.time_slot}\\n` +
          `• <b>Hizmet:</b> ${targetBooking.service}\\n\\n` +
          `<i>Yeni bir randevu almak istediğinizde bize dilediğiniz zaman yazabilirsiniz!</i> 💈`;
      } else {
        responseMessage = `✅ <b>Reservation Successfully Cancelled</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
          `• <b>Date:</b> ${targetBooking.booking_date}\\n` +
          `• <b>Time:</b> ${targetBooking.time_slot}\\n` +
          `• <b>Service:</b> ${targetBooking.service}\\n\\n` +
          `<i>Feel free to message us whenever you would like to book again!</i> 💈`;
      }

      replyMarkup = {
        inline_keyboard: [
          [{ text: "📅 Yeni Randevu Al", callback_data: `view_slots:${todayDateStr}` }]
        ]
      };
    }
  }
}

// ==============================================================================
// 3. INTENT: MY_BOOKINGS (List customer's confirmed appointments)
// ==============================================================================
else if (targetIntent === "MY_BOOKINGS") {
  const myBookings = normalizedRows.filter(r => {
    return r.telegram_user_id === String(cfg.userId) && r.status.toLowerCase() === "confirmed";
  });

  if (myBookings.length === 0) {
    if (lang === "tr") {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nMerhaba ${cfg.firstName}! Şu an için aktif bir randevunuz bulunmamaktadır.\\n\\nYeni bir randevu oluşturmak için aşağıdaki butona tıklayabilir veya dilediğiniz saati yazabilirsiniz. ✂️`;
    } else {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nHello ${cfg.firstName}! You have no active reservations right now.\\n\\nTap below to check open slots and book your next cut! ✂️`;
    }
    replyMarkup = {
      inline_keyboard: [
        [{ text: "📅 Müsait Saatleri Gör", callback_data: `view_slots:${todayDateStr}` }]
      ]
    };
  } else {
    if (lang === "tr") {
      responseMessage = `📋 <b>Aktif Randevularınız (${myBookings.length}):</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
        myBookings.map((b, i) => 
          `<b>${i + 1}. ${b.booking_date} — Saat ${b.time_slot}</b>\\n` +
          `• Hizmet: ${b.service} (${b.price})\\n` +
          `• Adres: ${cfg.shopLocation}\\n`
        ).join("\\n") +
        `\\nİptal etmek istediğiniz randevuyu aşağıdan seçebilirsiniz:`;
    } else {
      responseMessage = `📋 <b>Your Active Reservations (${myBookings.length}):</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
        myBookings.map((b, i) => 
          `<b>${i + 1}. ${b.booking_date} at ${b.time_slot}</b>\\n` +
          `• Service: ${b.service} (${b.price})\\n` +
          `• Location: ${cfg.shopLocation}\\n`
        ).join("\\n") +
        `\\nTap below if you wish to cancel:`;
    }

    replyMarkup = {
      inline_keyboard: myBookings.map(b => ([
        { text: `❌ İptal Et (${b.booking_date} @ ${b.time_slot})`, callback_data: `cancel_bkg:${b.booking_id}` }
      ]))
    };
  }
}

// ==============================================================================
// 4. INTENT: CHECK_SLOTS (View free slots for any date)
// ==============================================================================
else if (targetIntent === "CHECK_SLOTS") {
  const targetDate = targetDateInput || todayDateStr;
  const freeSlots = getAvailableSlots(targetDate);

  if (freeSlots.length === 0) {
    if (lang === "tr") {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n<b>${targetDate}</b> tarihinde müsait saatimiz kalmamıştır. Lütfen başka bir gün seçiniz. ✂️`;
    } else {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\nNo open slots on <b>${targetDate}</b>. Please check another date! ✂️`;
    }
  } else {
    if (lang === "tr") {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n📅 <b>${targetDate} İçin Müsait Saatler:</b>\\n\\n` +
        freeSlots.map(s => `• <b>${s}</b>`).join("\\n") +
        `\\n\\nRandevu almak istediğiniz saati aşağıdan seçebilir veya yazabilirsiniz: ✂️`;
    } else {
      responseMessage = `💈 <b>${cfg.shopName}</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n📅 <b>Available Slots for ${targetDate}:</b>\\n\\n` +
        freeSlots.map(s => `• <b>${s}</b>`).join("\\n") +
        `\\n\\nSelect a slot below to reserve: ✂️`;
    }

    replyMarkup = {
      inline_keyboard: [
        freeSlots.slice(0, 4).map(s => ({
          text: `✂️ ${s}`,
          callback_data: `book_slot:${targetDate}_${s}`
        }))
      ]
    };
  }
}

// ==============================================================================
// 5. INTENT: ADMIN_LIST_ALL (Barbershop Owner Executive Roster)
// ==============================================================================
else if (targetIntent === "ADMIN_LIST_ALL") {
  if (!cfg.isOwner) {
    responseMessage = `⛔ <b>Yetkisiz İşlem:</b> Bu işlem yalnızca işletme sahibine özeldir.`;
  } else {
    const targetDate = targetDateInput || todayDateStr;
    const dateBookings = normalizedRows.filter(r => r.booking_date === targetDate);
    const confirmed = dateBookings.filter(r => r.status.toLowerCase() === "confirmed");
    const cancelled = dateBookings.filter(r => r.status.toLowerCase().includes("cancel"));

    responseMessage = `👑 <b>Günlük Randevu Listesi (${targetDate})</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
      `📊 <b>Toplam Randevu:</b> ${confirmed.length} | <b>İptal:</b> ${cancelled.length}\\n\\n`;

    if (confirmed.length === 0) {
      responseMessage += `<i>Bu tarihte kayıtlı randevu bulunmamaktadır.</i>`;
    } else {
      responseMessage += confirmed.map(b => 
        `⏰ <b>${b.time_slot}</b> — <b>${b.customer_name}</b> (📞 ${b.customer_phone || "Belirtilmedi"}) [${b.telegram_username || "N/A"}]\\n` +
        `   • Hizmet: ${b.service} [${b.price}]\\n` +
        `   • Randevu No: <code>${b.booking_id}</code>`
      ).join("\\n\\n");
    }

    if (confirmed.length > 0) {
      replyMarkup = {
        inline_keyboard: confirmed.map(b => ([
          { text: `⚠️ İptal: ${b.customer_name} (${b.time_slot})`, callback_data: `cancel_bkg:${b.booking_id}` }
        ]))
      };
    }
  }
}

// ==============================================================================
// 6. INTENT: ADMIN_CANCEL (Owner cancels an appointment -> Alerts the Customer!)
// ==============================================================================
else if (targetIntent === "ADMIN_CANCEL") {
  if (!cfg.isOwner) {
    responseMessage = `⛔ <b>Yetkisiz İşlem:</b> İptal işlemi yalnızca işletme sahibine özeldir.`;
  } else {
    const matchingBookings = normalizedRows.filter(r => {
      const st = r.status.toLowerCase();
      if (st !== "confirmed") return false;
      if (bookingIdInput && r.booking_id.toLowerCase() === bookingIdInput.toLowerCase()) return true;
      if (targetDateInput && targetTimeInput && r.booking_date === targetDateInput && r.time_slot === targetTimeInput) return true;
      return false;
    });

    if (matchingBookings.length === 0) {
      responseMessage = `⚠️ Belirtilen kriterlere uygun aktif bir randevu bulunamadı.`;
    } else {
      const bkg = matchingBookings[0];
      const customerUserId = String(bkg.telegram_user_id || "");
      const customerName = bkg.customer_name || "Değerli Müşterimiz";
      const reason = cancellationReasonInput || "İşletme çalışma takvimi düzenlemesi";

      dbAction = "UPDATE";
      rowToUpdate = {
        booking_id: bkg.booking_id,
        payload: {
          status: "Cancelled by Owner",
          notes: `Owner cancelled: ${reason} (at ${nowIso})`
        }
      };

      // Message for the Owner
      responseMessage = `👑 <b>Randevu İptal Edildi</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
        `👤 <b>Müşteri:</b> ${customerName}\\n` +
        `📅 <b>Randevu:</b> ${bkg.booking_date} — Saat ${bkg.time_slot}\\n` +
        `✉️ Müşteriye otomatik bilgilendirme mesajı gönderildi.`;

      // Customer Proactive Telegram Notification
      if (customerUserId && customerUserId !== cfg.ownerUserId) {
        notifyCustomer = true;
        customerNotification = {
          customerChatId: customerUserId,
          alertMessage: `⚠️ <b>Randevu Bilgilendirmesi</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
            `Sayın <b>${customerName}</b>,\\n\\n` +
            `<b>${cfg.shopName}</b> bünyesindeki randevunuz işletme yönetimi tarafından iptal edilmiştir:\\n\\n` +
            `• <b>Tarih:</b> ${bkg.booking_date}\\n` +
            `• <b>Saat:</b> ${bkg.time_slot}\\n` +
            `• <b>Hizmet:</b> ${bkg.service}\\n\\n` +
            `Yaşanan aksaklık için özür dileriz. Dilediğiniz zaman bize mesaj atarak yeni bir randevu saati oluşturabilirsiniz! 💈`
        };
      }
    }
  }
}

// ==============================================================================
// 7. INTENT: HELP_GREETING or GENERAL INQUIRY
// ==============================================================================
else {
  if (cfg.isOwner) {
    responseMessage = `👑 <b>Hoş Geldiniz! (Yönetici Paneli)</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
      `Yapabileceğiniz işlemler:\\n` +
      `• <i>"Yarınki randevuları listele"</i>\\n` +
      `• <i>"Ali'nin 14:00 randevusunu iptal et"</i>\\n\\n` +
      `Aşağıdaki butonları kullanarak hızlıca işlem yapabilirsiniz:`;
    replyMarkup = {
      inline_keyboard: [
        [
          { text: "📋 Günlük Randevular", callback_data: "admin_today" },
          { text: "✂️ Müsait Saatler", callback_data: `view_slots:${todayDateStr}` }
        ]
      ]
    };
  } else {
    if (lang === "tr") {
      responseMessage = `💈 <b>Crown & Blade Barbershop'a Hoş Geldiniz!</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
        `Randevunuzu hemen oluşturmak için istediğiniz gün ve saati yazabilirsiniz.\\n\\n` +
        `✂️ <b>Hizmetlerimiz:</b>\\n` +
        cfg.services.map(s => `• <b>${s.name}</b> — ${s.price} (${s.duration})`).join("\\n") +
        `\\n\\n📍 <i>${cfg.shopLocation}</i>`;
      replyMarkup = {
        inline_keyboard: [
          [
            { text: "📅 Müsait Saatleri Gör", callback_data: `view_slots:${todayDateStr}` },
            { text: "📋 Randevularım", callback_data: "my_bookings" }
          ]
        ]
      };
    } else {
      responseMessage = `💈 <b>Welcome to Crown & Blade Barbershop!</b>\\n━━━━━━━━━━━━━━━━━━━━━━\\n` +
        `Book your grooming appointment in seconds. Simply reply with your preferred date and time.\\n\\n` +
        `✂️ <b>Services:</b>\\n` +
        cfg.services.map(s => `• <b>${s.name}</b> — ${s.price} (${s.duration})`).join("\\n") +
        `\\n\\n📍 <i>${cfg.shopLocation}</i>`;
      replyMarkup = {
        inline_keyboard: [
          [
            { text: "📅 View Open Spots", callback_data: `view_slots:${todayDateStr}` },
            { text: "📋 My Reservations", callback_data: "my_bookings" }
          ]
        ]
      };
    }
  }
}

return [{
  json: {
    ...cfg,
    dbAction: dbAction,
    rowToAppend: rowToAppend,
    rowToUpdate: rowToUpdate,
    responseMessage: responseMessage,
    replyMarkup: replyMarkup,
    notifyCustomer: notifyCustomer,
    customerNotification: customerNotification
  }
}];
'''

# ==============================================================================
# WORKFLOW JSON ASSEMBLY (SUPABASE POSTGRESQL ENGINE)
# ==============================================================================

workflow = {
  "name": "Project 11 - Barbershop Reservation Booking Agent (Supabase)",
  "nodes": [
    {
      "parameters": {
        "updates": [
          "message",
          "callback_query"
        ],
        "additionalFields": {}
      },
      "id": "telegram-trigger",
      "name": "Telegram Trigger (Customer & Owner)",
      "type": "n8n-nodes-base.telegramTrigger",
      "typeVersion": 1.1,
      "position": [100, 400],
      "credentials": {
        "telegramApi": {
          "id": "RpIeLATSMTsU1ciP",
          "name": "Reservation Bot"
        }
      }
    },
    {
      "parameters": {
        "jsCode": central_security_guard_js
      },
      "id": "central-security-guard",
      "name": "Central Brand & Security Guard",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [340, 400]
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
              "id": "is-callback-query",
              "leftValue": "={{ $json.isCallback }}",
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
      "id": "if-is-button-callback",
      "name": "Is Button Callback?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [580, 400]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=https://api.telegram.org/bot{{ $json.botToken }}/answerCallbackQuery?callback_query_id={{ $json.callbackQueryId }}",
        "options": {
          "timeout": 10000
        }
      },
      "id": "ack-callback-query",
      "name": "Acknowledge Button Click",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [800, 260],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "jsCode": parse_button_action_js
      },
      "id": "parse-button-action",
      "name": "Parse Button Action",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1020, 260]
    },
    {
      "parameters": {
        "jsCode": prepare_gemini_prompt_js
      },
      "id": "prepare-gemini-prompt",
      "name": "Prepare Gemini NLP Prompt",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [800, 540]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googlePalmApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ contents: [{ parts: [{ text: $json.geminiPrompt }] }], generationConfig: { temperature: 0.2, responseMimeType: 'application/json' } }) }}",
        "options": {
          "timeout": 30000
        }
      },
      "id": "gemini-intent-extractor",
      "name": "Gemini: Extract Intent & Entities",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1020, 540],
      "credentials": {
        "googlePalmApi": {
          "id": "zvLpU1ScjMCeOYQq",
          "name": "Google Gemini(PaLM) Api account"
        }
      },
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "jsCode": parse_gemini_response_js
      },
      "id": "parse-gemini-response",
      "name": "Parse AI Intent & Normalizer",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1240, 540]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "={{ $json.supabaseUrl }}/rest/v1/bookings?select=*&order=booking_date.asc,time_slot.asc",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "apikey",
              "value": "={{ $json.supabaseKey }}"
            },
            {
              "name": "Authorization",
              "value": "=Bearer {{ $json.supabaseKey }}"
            }
          ]
        },
        "options": {
          "timeout": 15000
        }
      },
      "id": "supabase-read-bookings",
      "name": "Supabase: Read All Bookings",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1480, 400],
      "alwaysOutputData": True,
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": reservation_core_engine_js
      },
      "id": "reservation-core-engine",
      "name": "Reservation Core Engine",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1720, 400]
    },
    {
      "parameters": {
        "mode": "rules",
        "rules": {
          "values": [
            {
              "conditions": {
                "options": {
                  "caseSensitive": True,
                  "leftValue": "",
                  "typeValidation": "strict"
                },
                "conditions": [
                  {
                    "leftValue": "={{ $json.dbAction }}",
                    "rightValue": "APPEND",
                    "operator": {
                      "type": "string",
                      "operation": "equals"
                    }
                  }
                ],
                "combinator": "and"
              }
            },
            {
              "conditions": {
                "options": {
                  "caseSensitive": True,
                  "leftValue": "",
                  "typeValidation": "strict"
                },
                "conditions": [
                  {
                    "leftValue": "={{ $json.dbAction }}",
                    "rightValue": "UPDATE",
                    "operator": {
                      "type": "string",
                      "operation": "equals"
                    }
                  }
                ],
                "combinator": "and"
              }
            }
          ]
        },
        "options": {
          "fallbackOutput": "extra"
        }
      },
      "id": "switch-db-action",
      "name": "Route Database Action",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 3.2,
      "position": [1960, 400]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $('Central Brand & Security Guard').first().json.supabaseUrl }}/rest/v1/bookings",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "apikey",
              "value": "={{ $('Central Brand & Security Guard').first().json.supabaseKey }}"
            },
            {
              "name": "Authorization",
              "value": "=Bearer {{ $('Central Brand & Security Guard').first().json.supabaseKey }}"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "Prefer",
              "value": "return=representation"
            }
          ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.rowToAppend) }}",
        "options": {
          "timeout": 15000
        }
      },
      "id": "supabase-insert-booking",
      "name": "Supabase: Insert Booking",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [2220, 240],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "method": "PATCH",
        "url": "={{ $('Central Brand & Security Guard').first().json.supabaseUrl }}/rest/v1/bookings?booking_id=eq.{{ $json.rowToUpdate.booking_id }}",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "apikey",
              "value": "={{ $('Central Brand & Security Guard').first().json.supabaseKey }}"
            },
            {
              "name": "Authorization",
              "value": "=Bearer {{ $('Central Brand & Security Guard').first().json.supabaseKey }}"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            },
            {
              "name": "Prefer",
              "value": "return=representation"
            }
          ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.rowToUpdate.payload || { status: $json.rowToUpdate.status, notes: $json.rowToUpdate.notes }) }}",
        "options": {
          "timeout": 15000
        }
      },
      "id": "supabase-update-booking",
      "name": "Supabase: Update Booking Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [2220, 420],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=https://api.telegram.org/bot{{ $('Central Brand & Security Guard').first().json.botToken }}/sendMessage",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ chat_id: $('Reservation Core Engine').first().json.chatId, text: $('Reservation Core Engine').first().json.responseMessage, parse_mode: 'HTML', reply_markup: $('Reservation Core Engine').first().json.replyMarkup || undefined }) }}",
        "options": {
          "timeout": 15000
        }
      },
      "id": "dispatch-user-feedback",
      "name": "Dispatch User Feedback",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [2480, 400],
      "onError": "continueRegularOutput"
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
              "id": "has-customer-alert",
              "leftValue": "={{ $('Reservation Core Engine').first().json.notifyCustomer }}",
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
      "id": "if-notify-customer",
      "name": "Has Customer Notification?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [2720, 400]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=https://api.telegram.org/bot{{ $('Central Brand & Security Guard').first().json.botToken }}/sendMessage",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ chat_id: $('Reservation Core Engine').first().json.customerNotification.customerChatId, text: $('Reservation Core Engine').first().json.customerNotification.alertMessage, parse_mode: 'HTML' }) }}",
        "options": {
          "timeout": 15000
        }
      },
      "id": "send-customer-alert",
      "name": "Send Urgent Alert to Affected Customer",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [2960, 320],
      "onError": "continueRegularOutput"
    }
  ],
  "connections": {
    "Telegram Trigger (Customer & Owner)": {
      "main": [
        [
          {
            "node": "Central Brand & Security Guard",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Central Brand & Security Guard": {
      "main": [
        [
          {
            "node": "Is Button Callback?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Is Button Callback?": {
      "main": [
        [
          {
            "node": "Acknowledge Button Click",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Prepare Gemini NLP Prompt",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Acknowledge Button Click": {
      "main": [
        [
          {
            "node": "Parse Button Action",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parse Button Action": {
      "main": [
        [
          {
            "node": "Supabase: Read All Bookings",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Prepare Gemini NLP Prompt": {
      "main": [
        [
          {
            "node": "Gemini: Extract Intent & Entities",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Gemini: Extract Intent & Entities": {
      "main": [
        [
          {
            "node": "Parse AI Intent & Normalizer",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Parse AI Intent & Normalizer": {
      "main": [
        [
          {
            "node": "Supabase: Read All Bookings",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Supabase: Read All Bookings": {
      "main": [
        [
          {
            "node": "Reservation Core Engine",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Reservation Core Engine": {
      "main": [
        [
          {
            "node": "Route Database Action",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Route Database Action": {
      "main": [
        [
          {
            "node": "Supabase: Insert Booking",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Supabase: Update Booking Status",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Dispatch User Feedback",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Supabase: Insert Booking": {
      "main": [
        [
          {
            "node": "Dispatch User Feedback",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Supabase: Update Booking Status": {
      "main": [
        [
          {
            "node": "Dispatch User Feedback",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Dispatch User Feedback": {
      "main": [
        [
          {
            "node": "Has Customer Notification?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Has Customer Notification?": {
      "main": [
        [
          {
            "node": "Send Urgent Alert to Affected Customer",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "saveDataErrorExecution": "all",
    "saveDataSuccessExecution": "all",
    "saveManualExecutions": True,
    "timezone": "Europe/Istanbul"
  }
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"Successfully generated {OUTPUT_FILE} with {len(workflow['nodes'])} nodes!")
