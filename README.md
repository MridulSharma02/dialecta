<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&size=52&duration=2000&pause=2000&color=FF6B6B&center=true&vCenter=true&multiline=true&width=700&height=120&lines=⚔️+DIALECTA" alt="DIALECTA" />
<br/>
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=16&duration=4000&pause=1000&color=888888&center=true&vCenter=true&width=700&height=40&lines=13+agents.+4+sub-debates.+1+verdict.;Built+from+scratch.+Deployed+to+production.;Where+thirteen+minds+argue+so+you+don't+have+to." alt="tagline" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--Time-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Three.js](https://img.shields.io/badge/Three.js-3D%20Visualization-000000?style=for-the-badge&logo=threedotjs&logoColor=white)](https://threejs.org)

[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Cloudflare](https://img.shields.io/badge/Cloudflare-Workers%20AI-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/workers-ai/)
[![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)](https://jwt.io)

[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://dialecta-tau.vercel.app)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://dialecta-backend.onrender.com)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Try%20It%20Now-FF6B6B?style=for-the-badge&logo=googlechrome&logoColor=white)](https://dialecta-tau.vercel.app)

<br/>

> **DIALECTA** is not a chatbot. It is a structured argumentation engine — a system of thirteen specialized AI agents that decompose any topic into sub-debates, argue in real time across up to 5 dynamic rounds, detect bias, check facts, self-improve their scoring rubric, and synthesize a comprehensive downloadable report. Built from scratch. Deployed to production.

<br/>

---

</div>

## 📌 Table of Contents

- [✨ What Is DIALECTA?](#-what-is-dialecta)
- [🤖 The 13 Agents](#-the-13-agents)
- [🏗️ Architecture](#️-architecture)
- [🔄 Agent Pipeline](#-agent-pipeline)
- [⚡ System Flow](#-system-flow)
- [🚀 Features](#-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [💻 Local Setup](#-local-setup)
- [📄 Report Structure](#-report-structure)
- [🗺️ Roadmap](#️-roadmap)
- [🙏 Built With & Acknowledgements](#-built-with--acknowledgements)

---

## ✨ What Is DIALECTA?

DIALECTA is a **production-deployed, multi-agent AI debate system** that takes any topic — from geopolitics to philosophy to science — and runs it through a rigorous, structured argumentation engine.

A user enters a topic. DIALECTA:

1. **Decomposes** the topic into 4 focused sub-debates
2. **Runs** each sub-debate for up to 5 rounds with two AI debaters
3. **Monitors** every round with six independent critic/observer agents
4. **Self-improves** its own scoring rubric mid-debate
5. **Generates** a 7-section downloadable report in PDF, JSON, and Markdown

This is not RAG over a PDF. This is not a summarizer. This is an orchestrated argumentation system with memory, bias detection, fact-checking, and self-correction — running live.

---

## 🤖 The 13 Agents

<div align="center">

| # | Agent | Role |
|---|-------|------|
| 1 | 🧩 **TopicDecomposer** | Breaks the root topic into 4 targeted sub-debate questions |
| 2 | 🗣️ **DebaterA** | Argues the affirmative/pro position with evidence |
| 3 | 🗣️ **DebaterB** | Argues the negative/contra position with evidence |
| 4 | ⚖️ **Judge** | Scores each round on logic, evidence, clarity, and persuasion |
| 5 | 🔍 **BiasDetector** | Flags rhetorical bias, fallacies, and manipulative language |
| 6 | 😈 **DevilsAdvocate** | Fires when one debater dominates — introduces steelman challenges |
| 7 | 🔬 **Critic** | Rewrites the scoring rubric every 3 rounds (self-improvement) |
| 8 | ✅ **FactChecker** | Verifies factual claims via DuckDuckGo search + LLM fallback |
| 9 | 🧠 **MemoryAgent** | Tracks argument novelty via ChromaDB; detects repetition |
| 10 | 📝 **Summariser** | Produces per-round and per-sub-debate summaries |
| 11 | 👥 **AudienceAgent** | Reacts as a specific persona (policymaker, scientist, layperson, etc.) |
| 12 | 🔭 **MetaEvaluator** | Cross-evaluates the entire debate system's performance |
| 13 | 🎯 **Orchestrator** | Coordinates agent execution order, exit conditions, and state |

</div>

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Client ["🌐 Client Layer — Vercel"]
        UI["Vanilla JS Frontend"]
        VIZ["Three.js 3D Agent Visualization"]
        WS_CLIENT["WebSocket Client"]
    end

    subgraph Gateway ["⚡ API Gateway — FastAPI on Render"]
        AUTH["JWT Auth Middleware"]
        REST["REST Endpoints"]
        WS_SERVER["WebSocket Server"]
    end

    subgraph AgentEngine ["🤖 Agent Orchestration Engine"]
        ORCH["Orchestrator"]
        DECOMP["TopicDecomposer"]
        subgraph Debaters ["Debate Core"]
            DA["DebaterA"]
            DB["DebaterB"]
            JUDGE["Judge"]
        end
        subgraph Critics ["Observer Layer"]
            BIAS["BiasDetector"]
            DEVIL["DevilsAdvocate"]
            CRITIC["Critic (Self-Improving)"]
            FACT["FactChecker"]
            MEM["MemoryAgent"]
        end
        subgraph Synthesis ["Synthesis Layer"]
            SUM["Summariser"]
            AUD["AudienceAgent"]
            META["MetaEvaluator"]
        end
    end

    subgraph LLMLayer ["🧠 Triple-Fallback LLM Layer"]
        GROQ["Groq — LLaMA 3.3 70B\n(Primary)"]
        GEMINI["Gemini 2.0 Flash\n(Secondary)"]
        CF["Cloudflare Workers AI\n(Tertiary)"]
    end

    subgraph Storage ["🗄️ Persistence Layer"]
        SUPA["Supabase PostgreSQL\n(Debates, Users, History)"]
        CHROMA["ChromaDB\n(Argument Vectors)"]
        DDG["DuckDuckGo Search\n(Fact-check grounding)"]
    end

    subgraph Reports ["📄 Report Engine"]
        JINJA["Jinja2 Templates"]
        WEASY["WeasyPrint PDF"]
        JSON_OUT["JSON Export"]
        MD_OUT["Markdown Export"]
    end

    UI --> WS_CLIENT
    UI --> VIZ
    WS_CLIENT <-->|"Real-time events"| WS_SERVER
    UI -->|"REST calls"| REST
    REST --> AUTH
    WS_SERVER --> ORCH
    ORCH --> DECOMP
    ORCH --> Debaters
    ORCH --> Critics
    ORCH --> Synthesis
    AgentEngine -->|"LLM calls"| GROQ
    GROQ -->|"Fallback"| GEMINI
    GEMINI -->|"Fallback"| CF
    MEM <--> CHROMA
    FACT --> DDG
    ORCH <--> SUPA
    Synthesis --> JINJA
    JINJA --> WEASY
    JINJA --> JSON_OUT
    JINJA --> MD_OUT
```

---

## 🔄 Agent Pipeline

```mermaid
flowchart TD
    TOPIC["📥 User enters topic"] --> DECOMP

    DECOMP["🧩 TopicDecomposer\nBreaks topic → 4 sub-debates"]

    DECOMP --> SD1["Sub-debate 1"] & SD2["Sub-debate 2"] & SD3["Sub-debate 3"] & SD4["Sub-debate 4"]

    SD1 --> LOOP

    subgraph LOOP ["🔁 Per Sub-debate: Up to 5 Rounds"]
        direction TB
        DA["🗣️ DebaterA — Affirmative argument"]
        DB["🗣️ DebaterB — Counter argument"]
        FACT["✅ FactChecker — Verify claims"]
        BIAS["🔍 BiasDetector — Flag rhetoric"]
        MEM["🧠 MemoryAgent — Novelty score"]
        JUDGE["⚖️ Judge — Score round"]
        CRITIC["🔬 Critic — Update rubric (every 3 rounds)"]
        DEVIL["😈 DevilsAdvocate — Challenge dominant debater"]
        AUD["👥 AudienceAgent — Persona reaction"]
        SUM["📝 Summariser — Round summary"]
        EXIT{"🚪 Exit Condition?\nConvergence | Dominance\nRepetition"}

        DA --> DB --> FACT --> BIAS --> MEM --> JUDGE --> CRITIC --> DEVIL --> AUD --> SUM --> EXIT
        EXIT -->|"No — continue"| DA
    end

    LOOP --> META["🔭 MetaEvaluator\nSystem-wide performance review"]
    META --> REPORT["📄 Report Engine\nPDF · JSON · Markdown"]
    REPORT --> USER["📥 User downloads report"]
```

---

## ⚡ System Flow

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant FE as 🌐 Frontend
    participant WS as ⚡ WebSocket
    participant OR as 🎯 Orchestrator
    participant AG as 🤖 Agents (×13)
    participant LLM as 🧠 LLM Fallback
    participant DB as 🗄️ Supabase

    U->>FE: Submit debate topic
    FE->>WS: Connect + send topic
    WS->>OR: Initialize debate session
    OR->>DB: Save checkpoint
    OR->>AG: TopicDecomposer → 4 sub-topics
    WS-->>FE: event: topic_decomposed
    FE-->>U: 3D orbs light up (4 sub-debates)

    loop For each sub-debate (×4)
        loop Each round (up to 5)
            OR->>AG: DebaterA → argument
            AG->>LLM: Groq call (→ Gemini → Cloudflare)
            LLM-->>AG: Response
            WS-->>FE: event: argument_generated
            OR->>AG: DebaterB → counter
            WS-->>FE: event: argument_generated
            OR->>AG: FactChecker, BiasDetector, MemoryAgent (parallel)
            WS-->>FE: event: analysis_complete
            OR->>AG: Judge → score round
            WS-->>FE: event: round_scored
            OR->>DB: Save checkpoint
            OR->>OR: Check exit conditions
        end
        OR->>AG: Summariser → sub-debate summary
        WS-->>FE: event: subdebate_complete
    end

    OR->>AG: MetaEvaluator → full system review
    OR->>AG: Generate 7-section report
    WS-->>FE: event: report_ready
    FE-->>U: Download PDF / JSON / Markdown
```

---

## 🚀 Features

### 🧠 Intelligence Layer
- **🧩 Automatic Topic Decomposition** — Any topic becomes 4 structured sub-debate questions via the TopicDecomposer agent
- **😈 Dynamic Devil's Advocate** — Automatically activates when one debater's cumulative score crosses a dominance threshold, injecting steelman challenges
- **🔬 Self-Improving Rubric** — The Critic agent rewrites the scoring criteria every 3 rounds based on observed argument quality
- **🧠 Novelty Memory** — ChromaDB vector store tracks all arguments; MemoryAgent computes novelty scores and triggers early exit on repetition
- **✅ Live Fact Checking** — DuckDuckGo search grounds claims in real data; LLM fallback handles rate limiting gracefully

### ⚡ Real-Time Architecture
- **📡 WebSocket Event Streaming** — Every agent action fires a typed event to the frontend in real time
- **🌐 3D Agent Visualization** — Thirteen glowing orbs rendered in Three.js with particle systems; orbs pulse and animate as their agent fires
- **🚪 Dynamic Early Exit** — Debates end early on convergence (score gap < threshold), dominance, or repetition — no padding, no waste
- **💾 Checkpoint System** — Debate state saved to Supabase at every round; debates can be resumed after interruption

### 🔒 Production Hardening
- **🔄 Triple LLM Fallback** — Groq (primary) → Gemini 2.0 Flash (secondary) → Cloudflare Workers AI (tertiary); zero single point of failure
- **🔐 Full Auth Stack** — JWT tokens, Supabase Auth, Google OAuth, GitHub OAuth
- **📜 Persistent History** — All past debates stored and accessible from the sidebar with full transcript replay
- **👥 Audience Personas** — AudienceAgent evaluates each round through the lens of a specific persona (policymaker, scientist, layperson, skeptic)

### 📄 Report Engine
- **7-Section Structured Reports** — Comprehensive analysis covering the full debate lifecycle
- **3 Export Formats** — PDF (WeasyPrint), JSON (machine-readable), Markdown (human-readable)
- **Jinja2 Templating** — Clean, professional report layout with per-section styling

---

## 🛠️ Tech Stack

<details>
<summary><strong>Click to expand full stack breakdown</strong></summary>

<br/>

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Runtime** | Python 3.11 + FastAPI | Async API server, WebSocket handling |
| **Real-Time** | WebSockets (native FastAPI) | Bi-directional event streaming to frontend |
| **LLM — Primary** | Groq · LLaMA 3.3 70B Versatile | Ultra-fast inference for all 13 agents |
| **LLM — Secondary** | Google Gemini 2.0 Flash | Fallback when Groq quota exhausted |
| **LLM — Tertiary** | Cloudflare Workers AI · LLaMA 3.3 70B FP8 | Final fallback; always available |
| **Database** | Supabase (PostgreSQL) | Debates, users, history, checkpoints |
| **Vector Store** | ChromaDB | Argument embeddings for novelty detection |
| **Fact Checking** | DuckDuckGo Search API | Web grounding for FactChecker agent |
| **Frontend** | Vanilla JS | Lightweight, no-framework client |
| **3D Visualization** | Three.js | Agent orb visualization with particle FX |
| **Report — PDF** | WeasyPrint | HTML/CSS → production PDF rendering |
| **Report — Template** | Jinja2 | Structured 7-section report templating |
| **Auth** | JWT + Supabase Auth + OAuth | Google & GitHub login, token refresh |
| **Frontend Deploy** | Vercel | Global CDN, zero-config deployment |
| **Backend Deploy** | Render | Containerized Python service |
| **Bias Detection** | cross-encoder/nli-MiniLM2-L6-H768 | NLI-based rhetorical bias classification |

</details>

---

## 💻 Local Setup

<details>
<summary><strong>Prerequisites</strong></summary>

- Python 3.11+
- Node.js (for any frontend tooling)
- A Supabase project (free tier works)
- At least one LLM API key: [Groq](https://console.groq.com), [Google AI Studio](https://aistudio.google.com), or [Cloudflare](https://developers.cloudflare.com/workers-ai/)

</details>

### 1. Clone the repository

```bash
git clone https://github.com/MridulSharma02/dialecta.git
cd dialecta
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment variables

Create `backend/.env`:

```env
# LLM Keys (triple fallback — configure at least one)
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
CLOUDFLARE_API_KEY=your_cloudflare_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# App
SECRET_KEY=your_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### 4. Database migrations

Run the SQL migrations in your Supabase SQL editor — found in `backend/migrations/`.

### 5. Start the backend

```bash
uvicorn main:app --reload --port 8000
```

Backend will be live at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 6. Frontend setup

```bash
cd ../frontend
# No build step required — pure Vanilla JS
# Just update the WebSocket URL in config.js:
```

```javascript
// frontend/config.js
const WS_URL = "ws://localhost:8000/ws/debate";
const API_URL = "http://localhost:8000";
```

Open `frontend/index.html` in your browser, or serve it:

```bash
npx serve .
```

---

## 📄 Report Structure

Every DIALECTA debate generates a **7-section report** in PDF, JSON, and Markdown.

<details>
<summary><strong>View all 7 sections</strong></summary>

<br/>

| # | Section | Contents |
|---|---------|----------|
| **1** | 📋 **Overview** | Topic, timestamp, total rounds, agents used, LLM providers, debate duration, final outcome |
| **2** | 🧩 **Topic Decomposition** | All 4 sub-debate questions with the TopicDecomposer's reasoning for each split |
| **3** | ⚔️ **Sub-Debate Breakdowns** | Per-round arguments (A vs B), fact-check results, bias flags, novelty scores, round scores, exit condition reason |
| **4** | 🔬 **System Self-Improvement Log** | Critic agent's rubric versions — each rewrite with before/after comparison and round trigger |
| **5** | 🔭 **Meta-Evaluation** | MetaEvaluator's assessment of overall debate quality, agent performance scores, system-level insights |
| **6** | ⚖️ **Final Verdict** | Overall winner with Judge's rationale, cumulative scoring breakdown, AudienceAgent final reaction |
| **7** | 📜 **Transcript Appendix** | Full verbatim transcript of all arguments across all sub-debates, all rounds, all agents |

</details>

---

## 🗺️ Roadmap

- [ ] **Voice Mode** — Text-to-speech for each debater with distinct voices
- [ ] **Custom Agent Configs** — Let users swap LLM models per agent
- [ ] **Tournament Mode** — Multiple topics, bracket-style elimination debates
- [ ] **Public Gallery** — Browse anonymized debates from other users
- [ ] **Embedding Export** — Embeddable debate widget for external sites
- [ ] **ChromaDB Cloud** — Migrate from local ChromaDB to managed vector DB
- [ ] **Streaming Tokens** — Token-by-token frontend streaming per agent
- [ ] **Multi-language Support** — Debate in Hindi, Spanish, French

---

## 🙏 Built With & Acknowledgements

<div align="center">

| Technology | What DIALECTA Uses It For |
|-----------|--------------------------|
| [FastAPI](https://fastapi.tiangolo.com) | Async backend, WebSocket server, REST API |
| [Three.js](https://threejs.org) | Real-time 3D agent visualization |
| [Groq](https://groq.com) | Primary LLM inference (LLaMA 3.3 70B) |
| [Google Gemini](https://deepmind.google/technologies/gemini/) | Secondary LLM fallback |
| [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/) | Tertiary LLM fallback |
| [Supabase](https://supabase.com) | PostgreSQL database + auth |
| [ChromaDB](https://www.trychroma.com) | Vector store for argument memory |
| [WeasyPrint](https://weasyprint.org) | PDF report generation |
| [Jinja2](https://jinja.palletsprojects.com) | Report templating |
| [Vercel](https://vercel.com) | Frontend deployment |
| [Render](https://render.com) | Backend deployment |

</div>

<br/>

---

<div align="center">

**DIALECTA** was designed and built from scratch by [Mridul Sharma](https://linkedin.com/in/mridul-sharma-a5b9a9408) — B.Tech AI/ML, IILM University (in collaboration with IBM).

*Thirteen agents. Four sub-debates. One system that argues better than most people.*

<br/>

[![Try DIALECTA](https://img.shields.io/badge/Try%20DIALECTA%20Live-FF6B6B?style=for-the-badge&logo=googlechrome&logoColor=white)](https://dialecta-tau.vercel.app)
[![GitHub](https://img.shields.io/badge/View%20on%20GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MridulSharma02/dialecta)
[![LinkedIn](https://img.shields.io/badge/Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/mridul-sharma-a5b9a9408)

<br/>

*If DIALECTA impressed you, a ⭐ on the repo means a lot.*

</div>