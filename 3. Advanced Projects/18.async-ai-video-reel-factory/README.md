# Project 18: Asynchronous AI Video Reel Factory (End-to-End Media Pipeline)

> **Autonomous media production factory that takes a scheduled topic or Telegram prompt, writes viral scripts, synthesizes voiceovers with ElevenLabs, generates 9:16 vertical video via Kling / Replicate using a resilient asynchronous polling loop, burns in dynamic subtitles via Shotstack/Creatomate, and delivers an interactive Human-in-the-Loop approval card to Telegram.**

---

## 🖼️ Workflow Architecture Canvas

![Workflow Canvas](workflow_screenshot.png)

---

## 🎯 Architecture & Workflow Diagram

```mermaid
flowchart TD
    subgraph TRIGGERS["1. MULTI-MODAL TRIGGERS"]
        T1["Cron Schedule (Daily 9:00 AM)"]
        T2["Webhook: POST /webhook/generate-reel"]
        T3["Telegram Command: /reel <topic>"]
    end

    subgraph PLANNING["2. LLM SCRIPT & CINEMATOGRAPHY"]
        P1["Normalize Input & Job ID"]
        P2["Gemini 2.0 Flash: Viral Hook & Scriptwriter"]
        P3["Camera & Prompt Optimizer (Cinematic 9:16)"]
    end

    subgraph GENERATION["3. ASYNC GENERATION & POLLING LOOP"]
        G1["ElevenLabs: Speech Synthesis (.mp3)"]
        G2["Replicate / Kling: Submit Video Job (returns prediction_id)"]
        L1["Init Polling State (attempt=1, max=15)"]
        L2["Wait 20 Seconds (Non-Blocking)"]
        L3["HTTP GET /predictions/{id}"]
        L4{"Status == succeeded?"}
    end

    subgraph STITCHING["4. MEDIA STITCHING & POST-PRODUCTION"]
        S1["Shotstack / Creatomate Render API"]
        S2["Layer 1: 9:16 Background Video"]
        S3["Layer 2: ElevenLabs High-Fidelity Audio"]
        S4["Layer 3: Dynamic Kinetic Subtitles"]
        S5["Cloud Backup / Storage Archive"]
    end

    subgraph HITL["5. INTERACTIVE APPROVAL & DISPATCH"]
        H1["Telegram Inline Review Card"]
        H2["[ ✅ Approve & Post (Instagram/YouTube) ]"]
        H3["[ 🔄 Regenerate Video ]"]
        H4["[ ✏️ Edit Script ]"]
    end

    subgraph PUBLISHING["6. MULTI-CHANNEL DISTRIBUTION"]
        D1["Telegram answerCallbackQuery (Spinner Stop)"]
        D2{"Platform Check"}
        D3["Instagram Reels: Meta Graph API v21.0"]
        D4["YouTube Shorts API (Ready)"]
        D5["Telegram Multi-Channel Dispatch Report"]
    end

    T1 --> P1
    T2 -->|Immediate 200 ACK| P1
    T3 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> G1
    P3 --> G2
    G2 --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 -->|No: Processing / Retry| L2
    L4 -->|Yes: Render Ready| S1
    G1 --> S1
    S1 --> S2
    S1 --> S3
    S1 --> S4
    S1 --> H1
    H1 --> H2
    H2 --> D1
    D1 --> D2
    D2 -->|Active| D3
    D2 -->|Pending Connect| D4
    D3 --> D5
    D4 --> D5
    S1 --> S2
    S1 --> S3
    S1 --> S4
    S4 --> S5
    S5 --> H1
    H1 --> H2
    H1 --> H3
    H1 --> H4
```

---

## ⚡ The Asynchronous Polling Loop (Advanced Architecture)

Generative video models (Kling 1.5, Luma Dream Machine, MiniMax on Replicate) cannot return video files synchronously because diffusion rendering takes **60 to 180 seconds**.

### How Traditional Workflows Fail:
- Synchronous HTTP requests exceed reverse-proxy timeouts (`504 Gateway Timeout` or n8n node execution limits).
- Unbounded loops can crash n8n memory or spin infinitely if an upstream GPU cluster stalls.

### How This Pipeline Solves It:
1. **Initial Dispatch:** `POST /v1/predictions` returns an HTTP 201 with `{"id": "pred_xyz", "status": "starting"}` in under 500ms.
2. **Stateful Wait Node:** Uses n8n's native, non-blocking `Wait` node configured for 20 seconds. This releases thread execution and prevents CPU locking.
3. **Evaluation Gate:** `Code - Evaluate Status` checks status:
   - If `"succeeded"`, breaks the loop and passes the video CDN URL downstream.
   - If `"processing"`, increments `pollAttempt` and loops back to `Wait 20 Seconds`.
   - If `pollAttempt >= maxRetries` (15 retries = 300s), gracefully aborts and triggers an alert.

---

## 🎬 Multi-Track Cloud Video Stitching

Once the audio and video assets are generated, they are composited via **Shotstack** or **Creatomate**:

```json
{
  "timeline": {
    "soundtrack": { "src": "https://api.elevenlabs.io/.../audio.mp3" },
    "tracks": [
      {
        "clips": [
          {
            "asset": {
              "type": "title",
              "text": "Stop writing prompts. Build swarms instead.",
              "style": "chunk",
              "color": "#FFE500"
            },
            "start": 0,
            "length": 30
          }
        ]
      },
      {
        "clips": [
          {
            "asset": {
              "type": "video",
              "src": "https://replicate.delivery/.../output.mp4"
            },
            "start": 0,
            "length": 30,
            "fit": "cover"
          }
        ]
      }
    ]
  },
  "output": {
    "format": "mp4",
    "resolution": "1080",
    "aspectRatio": "9:16"
  }
}
```

---

## 📱 Interactive Telegram Human-in-the-Loop Review

The rendered video is delivered to Telegram with inline buttons for full editorial control:

*   **`[ ✅ Approve & Post ]`**: Schedules or publishes immediately to Instagram Graph API & YouTube Data API.
*   **`[ 🔄 Regenerate Video ]`**: Re-rolls the visual diffusion prompt with fresh seeds while keeping the approved audio.
*   **`[ ✏️ Edit Script ]`**: Opens a prompt to adjust the hook or body text.
*   **`[ ❌ Reject & Discard ]`**: Archives the project and halts publication.

---

## 📁 Project Structure

```
18.async-ai-video-reel-factory/
├── configs/
│   └── .env.example                                # API keys for ElevenLabs, Replicate, Shotstack, Telegram
├── prompts/
│   ├── reel_scriptwriting_prompt.txt               # High-retention short-form script prompt
│   └── video_prompt_optimizer.txt                  # Diffusion prompt optimization for Kling / Luma
├── scripts/
│   ├── poll_job_status.py                          # Reference python implementation of polling loop
│   └── stitch_video_preview.py                     # Multi-track timeline JSON generator
├── sample-data/
│   ├── sample_reel_script.json                     # Sample generated script & prompts
│   ├── sample_polling_response.json                # Step-by-step polling state progression
│   ├── sample_creatomate_shotstack_payload.json    # Shotstack / Creatomate JSON manifest
│   └── sample_telegram_approval_card.json          # Telegram inline keyboard payload
├── n8n-workflows/
│   └── async_video_reel_factory.json               # Master n8n production workflow
└── README.md
```

---

## 🧪 Testing the Workflow

### 1. Trigger via Webhook
```bash
curl -X POST https://n8n.codewaft.com/webhook/generate-reel \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Why Multi-Agent AI Swarms Replace Prompts in 2026",
    "chat_id": "1519369571"
  }'
```

### 2. Trigger via Telegram Bot
Send a message to `@customer_call_sk_bot`:
```text
/reel The Future of Quantum Computing and AI
```

The system will acknowledge the request, execute the async polling loop, assemble the media tracks, and return your interactive video approval card with actionable buttons.
