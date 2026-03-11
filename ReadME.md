# 🤖 Codebase Explainer AI

> Ask questions about any GitHub repository in plain English.
> Powered by **Google Gemini** + **FAISS Vector Search** + **Local Embeddings** — 100% free to run.
> Supports both **public** and **private** repositories.

---

## 📌 Table of Contents

- [🤖 Codebase Explainer AI](#-codebase-explainer-ai)
  - [📌 Table of Contents](#-table-of-contents)
  - [🔍 What Does It Do?](#-what-does-it-do)
  - [⚙️ How It Works — Full Pipeline](#️-how-it-works--full-pipeline)
  - [🔬 Step-by-Step Deep Dive](#-step-by-step-deep-dive)
    - [Step 1 — Clone (Public or Private)](#step-1--clone-public-or-private)
    - [Step 2 — Filter Files](#step-2--filter-files)
    - [Step 3 — Chunking (Most Important!)](#step-3--chunking-most-important)
      - [What is a Chunk?](#what-is-a-chunk)
      - [How Chunking Works — Visual Example](#how-chunking-works--visual-example)
      - [Why Overlap? — Critical!](#why-overlap--critical)
      - [Chunk Counts for Real-World Repos](#chunk-counts-for-real-world-repos)
    - [Step 4 — Embeddings (Turning Text into Numbers)](#step-4--embeddings-turning-text-into-numbers)
    - [Step 5 — FAISS Index](#step-5--faiss-index)
    - [Step 6 — Cosine Similarity (How Search Works)](#step-6--cosine-similarity-how-search-works)
    - [Step 7 — Gemini Answer](#step-7--gemini-answer)
  - [🔒 Private Repository Support](#-private-repository-support)
    - [How Detection Works](#how-detection-works)
    - [Flow — Private Repo](#flow--private-repo)
    - [How to Get a GitHub Token (PAT)](#how-to-get-a-github-token-pat)
    - [Token Options](#token-options)
    - [Security — Why Only YOU Can Access Your Private Repo](#security--why-only-you-can-access-your-private-repo)
  - [🧠 Why Vector Database? (Not SQL / Keyword Search)](#-why-vector-database-not-sql--keyword-search)
    - [Option 1 — Keyword Search (`grep`, SQL `LIKE`)](#option-1--keyword-search-grep-sql-like)
    - [Option 2 — Relational Database (SQL)](#option-2--relational-database-sql)
    - [Option 3 — Vector Database ✅ (What We Use)](#option-3--vector-database--what-we-use)
  - [📦 FAISS Deep Dive](#-faiss-deep-dive)
  - [💻 CPU \& RAM Usage](#-cpu--ram-usage)
    - [Embedding Model: `all-MiniLM-L6-v2`](#embedding-model-all-minilm-l6-v2)
    - [FAISS Index RAM Formula](#faiss-index-ram-formula)
    - [Minimum vs Recommended Specs](#minimum-vs-recommended-specs)
  - [📁 Supported File Types](#-supported-file-types)
  - [🚀 Setup \& Installation](#-setup--installation)
    - [Prerequisites](#prerequisites)
    - [Install](#install)
    - [requirements.txt](#requirementstxt)
    - [Configure](#configure)
  - [🎮 Usage](#-usage)
  - [🗂 Project Structure](#-project-structure)
  - [⚠️ Limitations](#️-limitations)

---

## 🔍 What Does It Do?

You give it a GitHub repo URL. It clones the repo, reads **all the code, configs,
Dockerfiles, YAMLs, docs** — everything — and lets you ask questions like:

```
"What does the Dockerfile do?"
"Where is authentication handled?"
"What environment variables does this project need?"
"Explain the database schema."
```

No more manually hunting through hundreds of files.
Works with **both public and private repositories**.

---

## ⚙️ How It Works — Full Pipeline

```
GitHub Repo URL
      │
      ▼
┌─────────────────────────────┐
│  0. VISIBILITY CHECK        │
│  GitHub API → Public?       │
│  Private? → Ask for Token   │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  1. CLONE                   │
│  git clone --depth 1        │
│  (shallow clone = fast)     │
│  Token injected if private  │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  2. FILTER FILES            │
│  Include: .py .js .yml      │
│  Dockerfile, Makefile etc.  │
│  Exclude: node_modules,     │
│  .git, venv, __pycache__    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  3. CHUNK                   │
│  Split files into 1000-char │
│  overlapping pieces         │
│  overlap = 150 chars        │
│  So context never breaks    │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  4. EMBED  (LOCAL, FREE)    │
│  all-MiniLM-L6-v2 model     │
│  Each chunk → 384 numbers   │
│  Runs entirely on CPU       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  5. FAISS INDEX             │
│  All vectors stored in RAM  │
│  Ready for instant search   │
└────────────┬────────────────┘
             │
          [Ready]
             │
      User asks question
             │
             ▼
┌─────────────────────────────┐
│  6. EMBED QUERY             │
│  Question → 384-dim vector  │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  7. COSINE SIMILARITY       │
│  Compare query vector with  │
│  every stored chunk vector  │
│  Return top-5 closest       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  8. GEMINI LLM              │
│  Top-5 chunks + question    │
│  sent to Gemini 2.5 Flash   │
│  → Accurate answer with     │
│     source filenames        │
└─────────────────────────────┘
```

---

## 🔬 Step-by-Step Deep Dive

### Step 1 — Clone (Public or Private)

```bash
# Public repo — no token needed
git clone --depth 1 https://github.com/owner/repo /tmp/repo_xyz

# Private repo — token injected automatically
git clone --depth 1 https://<token>@github.com/owner/repo /tmp/repo_xyz
```

`--depth 1` means only the latest snapshot — no git history.
Faster download, less disk space. After ingestion, this temp folder is **deleted**.

---

### Step 2 — Filter Files

Not every file in a repo is useful. We skip junk and keep only meaningful files:

```
KEEP ✅                          SKIP ❌
──────────────────────────────────────────────────
.py  .js  .ts  .go  .java       node_modules/
.yml .yaml .toml .json          .git/
Dockerfile  Makefile            venv/  __pycache__/
.md  .txt  .env.example         *.min.js  (minified)
.html .css .sql                 dist/ build/
```

**Real example — Flask app:**
```
my-flask-app/
├── Dockerfile          ✅ kept
├── docker-compose.yml  ✅ kept
├── requirements.txt    ✅ kept
├── README.md           ✅ kept
├── app/
│   ├── __init__.py     ✅ kept
│   ├── routes.py       ✅ kept
│   ├── models.py       ✅ kept
│   └── auth.py         ✅ kept
├── node_modules/       ❌ skipped (entire folder)
└── .git/               ❌ skipped (entire folder)

Result: 8 files kept out of potentially hundreds
```

---

### Step 3 — Chunking (Most Important!)

#### What is a Chunk?

A chunk is a **small piece of a file**. We cannot send an entire 5000-line file
to the AI — it is too big. So we cut files into smaller, manageable pieces.

```
Settings used:
  chunk_size    = 1000 characters
  chunk_overlap = 150 characters
```

#### How Chunking Works — Visual Example

Take `auth.py` (800 characters) — fits in ONE chunk:

```
auth.py (800 chars)
┌────────────────────────────────────────────┐
│ CHUNK 1                                    │
│                                            │
│ import jwt                                 │
│ from datetime import datetime, timedelta   │
│ ...                                        │
│ def generate_token(user_id): ...           │
│ def verify_token(token): ...               │
│ def login_required(f): ...                 │
└────────────────────────────────────────────┘
  chars 1 → 800   (whole file = 1 chunk)
```

Now take `routes.py` (2800 characters) — splits into 3 chunks:

```
routes.py (2800 chars)  →  chunk_size=1000, overlap=150

┌────────────────────────────────────────────┐
│ CHUNK 1                   chars: 1 → 1000  │
│ from flask import Flask, request           │
│ from auth import login_required            │
│ @app.route('/users')                       │
│ def get_users():                           │
│     users = User.query...                  │
└─────────────────────┬──────────────────────┘
                      │  150 chars OVERLAP
┌─────────────────────▼──────────────────────┐
│ CHUNK 2                chars: 850 → 1850   │
│     users = User.query...  ← overlap!      │
│ @app.route('/login', methods=['POST'])     │
│ def login():                               │
│     token = generate_token(user.id)...     │
└─────────────────────┬──────────────────────┘
                      │  150 chars OVERLAP
┌─────────────────────▼──────────────────────┐
│ CHUNK 3                chars: 1700 → 2800  │
│     token = generate_token... ← overlap!   │
│ @app.route('/profile')                     │
│ @login_required                            │
│ def profile():                             │
│     return jsonify(current_user)           │
└────────────────────────────────────────────┘
```

#### Why Overlap? — Critical!

```
WITHOUT overlap (❌ bad):
  Chunk 2 starts: token = generate_token(user.id)
  AI thinks: "What is token? Where did this come from?" ❌

WITH overlap (✅ good):
  Chunk 2 starts: def login():        ← repeated from chunk 1!
                      token = generate_token(user.id)
  AI thinks: "token is created inside the login function." ✅
```

#### Chunk Counts for Real-World Repos

```
Project Type           Files    Chunks    Index RAM
──────────────────────────────────────────────────────
Simple Flask app          9        13        20 KB
Medium Django app        45       180       270 KB
Large Node.js API       120       800       1.2 MB
Microservices repo      400      3500       5.2 MB
Large Open Source      1200     12000      17.9 MB
```

---

### Step 4 — Embeddings (Turning Text into Numbers)

Each chunk goes through the embedding model and becomes **384 numbers** — a vector.

```
"def generate_token(user_id):"
          ↓  all-MiniLM-L6-v2
[0.21, -0.54, 0.87, 0.12, -0.33, 0.67, ... × 384 numbers]

"def verify_token(token):"
          ↓  all-MiniLM-L6-v2
[0.19, -0.51, 0.84, 0.14, -0.30, 0.65, ... × 384 numbers]
                                               ↑
                              Very similar — both are about JWT tokens.
```

---

### Step 5 — FAISS Index

All vectors stored in RAM, ready for instant search:

```
FAISS Index:
┌──────┬───────────────────────────────┬───────────────┐
│  ID  │  Vector (384 numbers)         │  Source File  │
├──────┼───────────────────────────────┼───────────────┤
│   0  │  [0.21, -0.54, 0.87, ...]    │  auth.py      │
│   1  │  [0.19, -0.51, 0.84, ...]    │  auth.py      │
│   2  │  [-0.43, 0.12, -0.21, ...]   │  models.py    │
│   3  │  [0.05, 0.78, -0.34, ...]    │  Dockerfile   │
│  ... │  [...]                        │  ...          │
└──────┴───────────────────────────────┴───────────────┘
```

---

### Step 6 — Cosine Similarity (How Search Works)

Your question becomes a vector too. FAISS finds which stored chunks are **closest** to it.

```
You ask: "how does login work?"
              ↓  becomes vector: [0.20, -0.52, 0.85, ...]
              ↓
FAISS scores all chunks:

Chunk  File              Similarity    Include?
─────────────────────────────────────────────────
  0    auth.py           0.94          ✅ TOP 1
  4    routes.py         0.89          ✅ TOP 2
  1    auth.py           0.82          ✅ TOP 3
  5    routes.py         0.71          ✅ TOP 4
  7    models.py         0.61          ✅ TOP 5
  3    Dockerfile        0.08          ❌ skipped
─────────────────────────────────────────────────
Top 5 chunks → sent to Gemini
```

---

### Step 7 — Gemini Answer

Top 5 chunks + your question → sent to Gemini as one prompt → accurate answer with filenames.

---

## 🔒 Private Repository Support

The tool **automatically detects** whether a repo is public or private and handles it accordingly.

### How Detection Works

```
You enter: https://github.com/owner/repo
                    ↓
          GitHub API called silently
                    ↓
         ┌──────────────────────┐
         │  Public?  → clone ✅ │
         │  Private? → ask token│
         └──────────────────────┘
```

### Flow — Private Repo

```
🔍 Checking repository visibility...
🔒 Repository is PRIVATE.

💡 You need a GitHub Personal Access Token (PAT).
   How to get one:
   1. Go to → https://github.com/settings/tokens
   2. Click 'Generate new token (classic)'
   3. Give it a name, set expiry
   4. Under 'Scopes' tick ✅ repo  (top checkbox)
   5. Click 'Generate token' and COPY it

🔑 Paste your GitHub Token here: ghp_xxxxxxxxxxxx
🔄 Cloning repository...
✅ Repository cloned successfully.
```

### How to Get a GitHub Token (PAT)

| Step | Action |
|------|--------|
| 1 | Go to **https://github.com/settings/tokens** |
| 2 | Click **"Generate new token (classic)"** |
| 3 | Give it any name, set expiry (e.g. 90 days) |
| 4 | Under **Scopes**, tick only ✅ **`repo`** |
| 5 | Click **"Generate token"** — copy it immediately! |

> ⚠️ GitHub shows the token **only once**. Copy it before closing the page.

### Token Options

**Option A — Enter at runtime (prompted automatically):**
```
🔑 Paste your GitHub Token here: █
```
No setup needed. Just paste when asked.

**Option B — Save in `.env` (never prompted again):**
```env
GOOGLE_API_KEY=your_gemini_key_here
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

### Security — Why Only YOU Can Access Your Private Repo

GitHub tokens are **tied to your account**. If someone else tries to clone your private repo:

```
Their token  →  Authentication failed ❌
No token     →  Authentication failed ❌
Your token   →  Clone successful      ✅
```

GitHub enforces this on its end — the tool has no extra logic needed.

---

## 🧠 Why Vector Database? (Not SQL / Keyword Search)

### Option 1 — Keyword Search (`grep`, SQL `LIKE`)

```
Query: "how does the app handle login?"
Keyword search looks for: l-o-g-i-n  (exact letters only)
Misses: "authenticate", "JWT verify", "session check"
```

### Option 2 — Relational Database (SQL)

| Issue | Why it fails |
|---|---|
| No semantic understanding | "authentication" ≠ "login" in SQL |
| Slow on large repos | Full table scan every query |
| No relevance ranking | All matches treated equally |

### Option 3 — Vector Database ✅ (What We Use)

```
Query: "how is the user authenticated?"
─────────────────────────────────────────────────────
Keyword search finds:
  ✅ auth.py          (has the word "authenticated")
  ❌ middleware.py    (has "verify_token" — no match)
  ❌ guards.ts        (has "isLoggedIn" — no match)

Vector search finds:
  ✅ auth.py          (similarity: 0.94)
  ✅ middleware.py    (similarity: 0.87 — semantically same!)
  ✅ guards.ts        (similarity: 0.81 — semantically same!)
─────────────────────────────────────────────────────
```

---

## 📦 FAISS Deep Dive

**FAISS** (Facebook AI Similarity Search) — the vector search engine we use.

| Feature | FAISS | Pinecone | ChromaDB |
|---|---|---|---|
| Cost | **Free** | Paid API | Free |
| Setup | In-process | Cloud account | Local server |
| Speed | **Fastest** | Fast | Medium |
| Persistence | RAM (session) | Cloud | Disk |
| Best for | **Local / batch** | Production SaaS | Dev prototyping |

---

## 💻 CPU & RAM Usage

### Embedding Model: `all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| Model size on disk | ~90 MB |
| RAM during inference | ~150–200 MB |
| Output dimensions | 384 per chunk |
| GPU required? | ❌ No — pure CPU |

### FAISS Index RAM Formula

```
RAM = num_chunks × 384 × 4 bytes

500 chunks   →   ~750 KB
5,000 chunks →   ~7.5 MB
50,000 chunks→   ~75 MB
```

### Minimum vs Recommended Specs

```
               MINIMUM          RECOMMENDED
               ───────          ───────────
RAM:           4 GB             8 GB
CPU:           2 cores          4+ cores
Disk:          200 MB free      500 MB free
GPU:           ❌ Not needed    ❌ Not needed
```

---

## 📁 Supported File Types

**Code:** `.py` `.js` `.ts` `.jsx` `.tsx` `.java` `.cpp` `.c` `.go` `.rs` `.rb` `.php` `.cs` `.swift` `.kt`

**Config & Infrastructure:** `.yml` `.yaml` `.toml` `.ini` `.cfg` `.env` `.sh` `.bash` `.xml` `.json`

**DevOps / Docker (no extension):** `Dockerfile` `Makefile` `Procfile` `.gitignore` `.dockerignore` `nginx.conf`

**Documentation:** `.md` `.txt` `.rst`

**Web & Database:** `.html` `.css` `.scss` `.sql`

**Always Excluded:** `node_modules/` `.git/` `venv/` `__pycache__/` `.next/` `coverage/` `*.min.js`

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- Google Gemini API Key — free at [aistudio.google.com](https://aistudio.google.com)
- GitHub Token — only needed for **private repos** (see [🔒 Private Repository Support](#-private-repository-support))

### Install

```bash
git clone <this-repo>
cd codebase-explainer
pip install -r requirements.txt
```

### requirements.txt

```
gitpython
python-dotenv
requests
langchain
langchain-community
langchain-google-genai
faiss-cpu
sentence-transformers
```

### Configure

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional — only needed for private repos
# If not set, the tool will ask at runtime
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

---

## 🎮 Usage

```bash
python main.py
```

**Public repo:**
```
🤖 Codebase Explainer AI

✅ Gemini API key loaded from ENV
📥 Loading local embedding model...
✅ Local embeddings ready!

Enter GitHub repository URL: https://github.com/owner/public-repo

🔍 Checking repository visibility...
🌐 Repository is PUBLIC — no token needed.
🔄 Cloning repository...
✅ Repository cloned successfully.
✅ Found 87 relevant files (skipped ~34 excluded)
✅ Created 1,243 chunks
✅ FAISS index ready
✅ Repository ingestion complete

💬 Ask questions (type 'quit' to exit)

You: What does the Dockerfile do?
🤖 The Dockerfile sets up a Node.js 18 Alpine base image...
📁 Sources: Dockerfile, docker-compose.yml
```

**Private repo:**
```
Enter GitHub repository URL: https://github.com/owner/private-repo

🔍 Checking repository visibility...
🔒 Repository is PRIVATE.

💡 You need a GitHub Personal Access Token (PAT).
   1. Go to → https://github.com/settings/tokens
   2. Generate new token (classic)
   3. Tick ✅ repo scope
   4. Copy the token

🔑 Paste your GitHub Token here: ghp_xxxxxxxxxxxx
🔄 Cloning repository...
✅ Repository cloned successfully.
```

---

## 🗂 Project Structure

```
codebase-explainer/
│
├── main.py                  ← Entry point, CLI loop
├── .env                     ← API keys (never commit!)
├── .env.example             ← Template for new devs
├── requirements.txt
├── README.md
│
├── config/
│   └── settings.py          ← All constants (models, chunk size, extensions)
│
├── core/
│   ├── explainer.py         ← Main class, orchestrates everything
│   ├── qa_chain.py          ← Gemini LLM + RetrievalQA setup
│   └── vector_store.py      ← FAISS index + embeddings
│
└── utils/
    ├── file_filter.py       ← Which files to include/exclude
    ├── chunker.py           ← Read files and create chunks
    └── repo_manager.py      ← Git clone, visibility check, cleanup
```

---

## ⚠️ Limitations

| Limitation | Details |
|---|---|
| **No persistence** | FAISS index is in RAM — lost when program exits |
| **Very large repos** | 100k+ chunks may need 500 MB+ RAM |
| **Binary files** | Images, compiled binaries are skipped |
| **Rate limits** | Gemini free tier has query limits |
| **GitHub only** | GitLab / Bitbucket URLs not supported yet |