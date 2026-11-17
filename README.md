<div align="center">

# ⚡ n8n Enterprise AI Automation Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge)](LICENSE)
[![n8n Version](https://img.shields.io/badge/n8n-v2.x-orange.svg?style=for-the-badge&logo=n8n)](https://n8n.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg?style=for-the-badge&logo=docker)](setup/docker-compose.yml)
[![AI Models](https://img.shields.io/badge/LLM-Gemini_|_DeepSeek_|_Vapi-purple.svg?style=for-the-badge)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/Production-Ready-success.svg?style=for-the-badge)](https://n8n.codewaft.com)

**A curated, production-tested suite of 18 autonomous AI workflows across 3 complexity tiers.**  
From conversational WhatsApp/Telegram assistants and automated PDF legal suites to real-time Voice AI receptionists and asynchronous video rendering factories.

[Explore Projects](#-comprehensive-projects-portfolio) • [Quick Start](#-quick-start--import-guide) • [Docker Deployment](#-self-hosted-deployment) • [License (MIT)](#-license)

</div>

---

## 📖 About This Repository

This repository is an end-to-end open-source blueprint for developers, agencies, and automation builders looking to deploy high-margin, enterprise-ready n8n automations. 

Every single workflow has been designed, sanitized, benchmarked, and verified in production environments. All projects include:
- 🧩 **Complete JSON Workflow Exports** (compatible with modern n8n 2.x+).
- 🖼️ **High-Resolution Canvas Screenshots** illustrating the dataflow and architecture.
- 📋 **Production Documentation** detailing node logic, credential mapping, and fallback paths.
- 🔒 **Zero Hardcoded Secrets** (clean `.env.example` templates for instant deployment).

---

## 🏛️ Comprehensive Projects Portfolio

### 🟢 1. Beginner Projects (Core Integrations & Chatbots)
> Focus on essential API integrations, messaging webhooks, document generation, and scheduled tracking.

| # | Project Name | Integrations & Tools | Highlights | Docs & Canvas |
| :-: | :--- | :--- | :--- | :-: |
| **01** | **[WhatsApp AI Chatbot Suite](1.%20Beginner%20Projects/01.whatsapp-ai-chatbot-projects/README.md)** | Evolution API / Meta Cloud API, Gemini, LangChain | Dual architecture: QR-code scanning (no verification) + Official Meta Cloud API. | [Open](1.%20Beginner%20Projects/01.whatsapp-ai-chatbot-projects/README.md) |
| **02** | **[Telegram AI Calendar Assistant](1.%20Beginner%20Projects/02.telegram-ai-calendar-assistant/README.md)** | Google Calendar, Google Meet, Telegram, Gemini | Natural speech booking, auto Google Meet generation, conflict checks & 07:00 AM reminders. | [Open](1.%20Beginner%20Projects/02.telegram-ai-calendar-assistant/README.md) |
| **03** | **[Automated PDF Invoice Generator](1.%20Beginner%20Projects/03.telegram-invoice-generator/README.md)** | Google Drive, Gmail, Telegram, Vector PDF Kit | Natural language slot-filling, vector PDF rendering, Drive archiving & 1-tap forward. | [Open](1.%20Beginner%20Projects/03.telegram-invoice-generator/README.md) |
| **04** | **[Daily Social Media Growth Tracker](1.%20Beginner%20Projects/04.daily-social-media-tracker/README.md)** | Instagram Graph API, Google Sheets, Telegram | Automated multi-account tracking, historical delta calculations & daily Telegram briefings. | [Open](1.%20Beginner%20Projects/04.daily-social-media-tracker/README.md) |
| **05** | **[Interactive Telegram To-Do App](1.%20Beginner%20Projects/05.interactive-telegram-todo-app/README.md)** | Google Tasks 2-Way Sync, Inline Keyboard | Natural task entry, 08:00 AM daily task review & inline button updates (`[Done]`, `[Delete]`). | [Open](1.%20Beginner%20Projects/05.interactive-telegram-todo-app/README.md) |
| **06** | **[Telegram Content Studio](1.%20Beginner%20Projects/06.telegram-social-content-studio/README.md)** | Gemini 3.5, Google Imagen 3, Instagram API | Multimodal voice/text prompt to carousel concept, image rendering & 1-tap IG publish. | [Open](1.%20Beginner%20Projects/06.telegram-social-content-studio/README.md) |
| **07** | **[Receipt & Expense Tracker](1.%20Beginner%20Projects/07.receipt-expense-tracker/README.md)** | Gemini 2.0 Flash Vision, Google Drive, Sheets | Snap receipt photos: OCR extracts Merchant/Total/Date, backs up image to Drive & logs to Sheets. | [Open](1.%20Beginner%20Projects/07.receipt-expense-tracker/README.md) |
| **08** | **[Instagram Lead Responder](1.%20Beginner%20Projects/08.instagram-lead-responder/README.md)** | Instagram Graph API, Meta Webhooks, Sheets | Webhook push (<1s) & 2-min Polling modes: public comment reply + instant tracked DM dispatch. | [Open](1.%20Beginner%20Projects/08.instagram-lead-responder/README.md) |
| **09** | **[Daily AI Instagram Content Engine](1.%20Beginner%20Projects/09.daily-ai-instagram-content-engine/README.md)** | Dual-Agent Gemini 3.5, Instagram API, Sheets | Strategist + Creative Director dual agent cluster, 4:5 visual slides & Human-in-the-Loop review. | [Open](1.%20Beginner%20Projects/09.daily-ai-instagram-content-engine/README.md) |
| **10** | **[Contract & Proposal Generator](1.%20Beginner%20Projects/10.automated-contract-proposal-generator/README.md)** | Vector PDF, Google Drive, Gmail, Google Sheets | Voice-driven legal suite: converts voice notes to 2-page Service Agreements with e-signature tracking. | [Open](1.%20Beginner%20Projects/10.automated-contract-proposal-generator/README.md) |

---

### 🟡 2. Intermediate Projects (Databases, Vision & Outbound Pipelines)
> Focus on ACID databases (Supabase), web scrapers (Apify), multimodal photo recognition, and autonomous cold email outreach.

| # | Project Name | Integrations & Tools | Highlights | Docs & Canvas |
| :-: | :--- | :--- | :--- | :-: |
| **11** | **[Barbershop Booking Agent](2.%20Intermediate%20Projects/11.barbershop-reservation-booking/README.md)** | Supabase PostgreSQL, Gemini, Telegram | ACID-safe slot collision check, strict client isolation (`from.id`) & owner admin cancellation alerts. | [Open](2.%20Intermediate%20Projects/11.barbershop-reservation-booking/README.md) |
| **12** | **[B2B Lead Hunter & Cold Outreach](2.%20Intermediate%20Projects/12.local-business-website-lead-hunter/README.md)** | Apify Google Maps, Gemini AI, Gmail, Sheets | Scrapes local businesses with no website, deduplicates against CRM, drafts AI pitches & sends via Gmail. | [Open](2.%20Intermediate%20Projects/12.local-business-website-lead-hunter/README.md) |
| **13** | **[Daily Tech News Digest](2.%20Intermediate%20Projects/13.daily-tech-news-digest/README.md)** | 11 RSS Feeds, Gemini 3.1 Flash-Lite, Telegram | Parallel ingestion across 11 feeds, rolling 24h window filter & distraction-free executive summary. | [Open](2.%20Intermediate%20Projects/13.daily-tech-news-digest/README.md) |
| **14** | **[Ingredient to Meal Plan & PDF](2.%20Intermediate%20Projects/14.ingredient-to-meal-plan/README.md)** | Gemini Vision, Vector PDF Engine, Telegram | Multimodal fridge photo recognition, 3 chef recipes tailored to available ingredients & PDF delivery. | [Open](2.%20Intermediate%20Projects/14.ingredient-to-meal-plan/README.md) |
| **15** | **[AI Personal Job Hunter](2.%20Intermediate%20Projects/15.ai-personal-job-hunter/README.md)** | Job Scrapers, Gemini Matcher, Telegram | Autonomous career matchmaker: ranks live postings against user CV with match score & 1-click links. | [Open](2.%20Intermediate%20Projects/15.ai-personal-job-hunter/README.md) |

---

### 🔴 3. Advanced Projects (Voice AI, Telephony & Asynchronous Video Pipelines)
> Enterprise-grade architectures combining sub-second telephony, multi-agent swarms, and non-blocking asynchronous polling loops.

| # | Project Name | Integrations & Tools | Highlights | Docs & Canvas |
| :-: | :--- | :--- | :--- | :-: |
| **16** | **[Voice Omnichannel AI Agent](3.%20Advanced%20Projects/16.voice-omnichannel/README.md)** | Vapi.ai, Twilio SIP, Google Calendar, Telegram | Real-time inbound phone receptionist with interruption handling (Barge-in), live calendar booking & hangup analytics. | [Open](3.%20Advanced%20Projects/16.voice-omnichannel/README.md) |
| **17** | **[AI Video Repurposing Engine](3.%20Advanced%20Projects/17.ai-video-repurposing-engine/README.md)** | YouTube API, Gemini 2.0 Flash Swarm, Telegram | Long-form video ingestion to 3 viral moments (exact timestamps & 3s hooks), 10-slide LinkedIn carousel & 1500w SEO blog. | [Open](3.%20Advanced%20Projects/17.ai-video-repurposing-engine/README.md) |
| **18** | **[Async AI Video Reel Factory](3.%20Advanced%20Projects/18.async-ai-video-reel-factory/README.md)** | Polling Loop, Multi-Video Library, Instagram API | Asynchronous rendering polling loop, persistent channel memory (`/context`, `/set_context`), keyword video matcher & live Reels publish. | [Open](3.%20Advanced%20Projects/18.async-ai-video-reel-factory/README.md) |

---

## 🚀 Quick Start & Import Guide

### 1. Clone the Repository
```bash
git clone https://github.com/SerhatKumas/AI--n8nEnterpriseAutomationHub.git
cd AI--n8nEnterpriseAutomationHub
```

### 2. Import into n8n
1. Open your n8n workspace (self-hosted or n8n Cloud).
2. Go to **Workflows** > Click **Add workflow**.
3. In the canvas menu (`...` top right), click **Import from File...**
4. Select the `workflow.json` from the project of your choice.

### 3. Configure Credentials
1. Copy the `.env.example` in the project's config directory (or follow the project `README.md`).
2. Add your API keys (Google Gemini, Telegram Bot, Meta Graph, etc.).
3. Toggle the workflow to **Active**!

---

## 🐳 Self-Hosted Deployment (Docker + Caddy)

This repository includes a production-ready, one-command deployment stack configured for **Docker Compose** and **Caddy** (with automatic Let's Encrypt HTTPS / HTTP/3):

```bash
cd setup
cp .env.example .env
# Edit .env with your domain name and secret key
nano .env

# Launch the stack
docker compose up -d
```

Full deployment instructions, Oracle Cloud setup, firewall rules, and SSL configuration are detailed in [setup/DEPLOYMENT.md](setup/DEPLOYMENT.md).

---

## 👨‍💻 Author

<div align="center">

### **Serhat Kumaş**
*Solutions Architect & AI Engineer*

Specializing in multi-agent AI architectures, enterprise automation systems, scalable cloud platforms, and full-stack engineering.

[![Website](https://img.shields.io/badge/Website-serhatkumas.github.io-6366f1?style=for-the-badge&logo=googlechrome&logoColor=white)](https://serhatkumas.github.io/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/serhatkumas/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SerhatKumas)
[![Email](https://img.shields.io/badge/Email-serhatkumas%40outlook.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:serhatkumas@outlook.com)

</div>

---

## 📄 License & Commercial Rights

This project is licensed under the **[MIT License](LICENSE)**.

> **Commercial Freedom:** You are fully permitted to use, modify, distribute, sublicense, and **sell** these workflows, templates, and systems commercially for your own projects, client deliverables, or SaaS applications without royalty obligations.

---

<div align="center">
Built with ❤️ for the global AI automation community.
</div>
