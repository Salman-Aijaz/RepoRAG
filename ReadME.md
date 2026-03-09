# 🤖 Codebase Explainer AI

> Ask questions about any GitHub repository in plain English.
> Powered by **Google Gemini** + **FAISS Vector Search** + **Local Embeddings** — 100% free to run.

---

## 📌 Table of Contents

- [🤖 Codebase Explainer AI](#-codebase-explainer-ai)
  - [📌 Table of Contents](#-table-of-contents)
  - [🔍 What Does It Do?](#-what-does-it-do)
  - [⚙️ How It Works — Full Pipeline](#️-how-it-works--full-pipeline)
  - [🔬 Step-by-Step Deep Dive](#-step-by-step-deep-dive)
    - [Step 1 — Clone](#step-1--clone)
    - [Step 2 — Filter Files](#step-2--filter-files)
    - [Step 3 — Chunking (Most Important!)](#step-3--chunking-most-important)
      - [What is a Chunk?](#what-is-a-chunk)
      - [How Chunking Works — Visual Example](#how-chunking-works--visual-example)
      - [Why Overlap? — Critical!](#why-overlap--critical)
      - [Chunk Count for Full Flask App](#chunk-count-for-full-flask-app)
      - [Chunk Counts for Real-World Repos](#chunk-counts-for-real-world-repos)
    - [Step 4 — Embeddings (Turning Text into Numbers)](#step-4--embeddings-turning-text-into-numbers)
    - [Step 5 — FAISS Index](#step-5--faiss-index)
    - [Step 6 — Cosine Similarity (How Search Works)](#step-6--cosine-similarity-how-search-works)
      - [What is Cosine Similarity?](#what-is-cosine-similarity)
      - [The Math — Simple 2D Example](#the-math--simple-2d-example)
      - [Live Search Example](#live-search-example)
    - [Step 7 — Gemini Answer](#step-7--gemini-answer)
  - [🧠 Why Vector Database? (Not SQL / Keyword Search)](#-why-vector-database-not-sql--keyword-search)
    - [Option 1 — Keyword Search (`grep`, SQL `LIKE`)](#option-1--keyword-search-grep-sql-like)
    - [Option 2 — Relational Database (SQL)](#option-2--relational-database-sql)
    - [Option 3 — Vector Database ✅ (What We Use)](#option-3--vector-database--what-we-use)
  - [📦 FAISS Deep Dive](#-faiss-deep-dive)
    - [Why FAISS over others?](#why-faiss-over-others)
    - [What FAISS stores in RAM](#what-faiss-stores-in-ram)
  - [💻 CPU \& RAM Usage](#-cpu--ram-usage)
    - [Embedding Model: `all-MiniLM-L6-v2`](#embedding-model-all-minilm-l6-v2)
    - [FAISS Index RAM — How to Calculate](#faiss-index-ram--how-to-calculate)
    - [Full Resource Timeline](#full-resource-timeline)
    - [Minimum vs Recommended Specs](#minimum-vs-recommended-specs)
  - [📁 Supported File Types](#-supported-file-types)
    - [Code](#code)
    - [Config \& Infrastructure](#config--infrastructure)
    - [DevOps / Docker (no extension)](#devops--docker-no-extension)
    - [Documentation](#documentation)
    - [Web \& Database](#web--database)
    - [Always Excluded](#always-excluded)
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

---

## ⚙️ How It Works — Full Pipeline

```
GitHub Repo URL
      │
      ▼
┌─────────────────────────────┐
│  1. CLONE                   │
│  git clone --depth 1        │
│  (shallow clone = fast)     │
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
│  (a vector = meaning of     │
│   that chunk in math form)  │
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
│  (same model, same space)   │
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

### Step 1 — Clone

```bash
git clone --depth 1 https://github.com/owner/repo /tmp/repo_xyz
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
│                                            │
│ from flask import Flask, request           │
│ from auth import login_required            │
│ app = Flask(__name__)                      │
│                                            │
│ @app.route('/users')                       │
│ def get_users():                           │
│     users = User.query...                  │
└─────────────────────┬──────────────────────┘
                      │
            150 chars OVERLAP
            (last 150 chars of chunk 1
             repeated at start of chunk 2)
                      │
┌─────────────────────▼──────────────────────┐
│ CHUNK 2                chars: 850 → 1850   │
│                                            │
│     users = User.query...  ← overlap!      │
│     return jsonify(users)                  │
│                                            │
│ @app.route('/login', methods=['POST'])     │
│ def login():                               │
│     data = request.get_json()              │
│     token = generate_token(user.id)...     │
└─────────────────────┬──────────────────────┘
                      │
            150 chars OVERLAP
                      │
┌─────────────────────▼──────────────────────┐
│ CHUNK 3                chars: 1700 → 2800  │
│                                            │
│     token = generate_token... ← overlap!   │
│     return jsonify({'token': token})       │
│                                            │
│ @app.route('/profile')                     │
│ @login_required                            │
│ def profile():                             │
│     return jsonify(current_user)           │
└────────────────────────────────────────────┘
```

#### Why Overlap? — Critical!

```
WITHOUT overlap (❌ bad):

  Chunk 1 ends:    ...def login():
  Chunk 2 starts:      token = generate_token(user.id)

  AI sees chunk 2 and thinks:
  "What is token? Where did this come from?"
  Context is BROKEN! ❌

──────────────────────────────────────────────

WITH overlap (✅ good):

  Chunk 1 ends:    ...def login():
  Chunk 2 starts:  def login():        ← repeated!
                       token = generate_token(user.id)

  AI sees chunk 2 and thinks:
  "token is created inside the login function."
  Context is PRESERVED! ✅
```

#### Chunk Count for Full Flask App

```
File                Size        Chunks
────────────────────────────────────────
Dockerfile          400 chars     1
docker-compose.yml  350 chars     1
requirements.txt    200 chars     1
README.md          1200 chars     2
__init__.py         300 chars     1
routes.py          2800 chars     3
models.py          1800 chars     2
auth.py             800 chars     1
config.py           500 chars     1
────────────────────────────────────────
TOTAL                            13 chunks
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

After chunking, each chunk goes through the embedding model.
The model converts text into **384 numbers** called a vector.

```
"def generate_token(user_id):"
          ↓  all-MiniLM-L6-v2
[0.21, -0.54, 0.87, 0.12, -0.33, 0.67, ... × 384 numbers]

"def verify_token(token):"
          ↓  all-MiniLM-L6-v2
[0.19, -0.51, 0.84, 0.14, -0.30, 0.65, ... × 384 numbers]
                                               ↑
                              Very similar numbers!
                              Because both are about JWT tokens.
```

These numbers represent **meaning** — similar meaning produces similar numbers.

---

### Step 5 — FAISS Index

All chunk vectors are stored in FAISS as a table in RAM:

```
FAISS Index in RAM:
┌──────────────────────────────────────────────────────┐
│  ID  │  Vector (384 numbers)         │  Metadata     │
├──────┼───────────────────────────────┼───────────────┤
│   0  │  [0.21, -0.54, 0.87, ...]    │  auth.py      │
│   1  │  [0.19, -0.51, 0.84, ...]    │  auth.py      │
│   2  │  [-0.43, 0.12, -0.21, ...]   │  models.py    │
│   3  │  [0.05, 0.78, -0.34, ...]    │  Dockerfile   │
│   4  │  [0.11, -0.44, 0.71, ...]    │  routes.py    │
│  ... │  [...]                        │  ...          │
│  12  │  [0.22, -0.50, 0.89, ...]    │  config.py    │
└──────┴───────────────────────────────┴───────────────┘
Total: 13 rows for our Flask app example
```

---

### Step 6 — Cosine Similarity (How Search Works)

When you ask a question, it also becomes a vector.
Then we find which stored chunks are **closest** to your question vector.

#### What is Cosine Similarity?

Think of each vector as an **arrow pointing in some direction in space**.
Cosine similarity measures the **angle between two arrows** — not their length.

```
"user login"       →  arrow pointing ↗  (direction A)
"authentication"   →  arrow pointing ↗  (almost same direction!)
"database schema"  →  arrow pointing ↙  (completely different)
```

```
Angle = 0°    →  similarity = 1.0   (exact same meaning)
Angle = 90°   →  similarity = 0.0   (no relation at all)
Angle = 180°  →  similarity = -1.0  (opposite meaning)
```

#### The Math — Simple 2D Example

Real vectors have 384 dimensions but the formula is identical. Here is 2D:

```
"login"          → vector A = [3, 4]
"authentication" → vector B = [6, 8]   (same direction, just longer!)

Formula: Cosine Similarity = (A · B) / (|A| × |B|)

Step 1 — Dot product:
  A · B = (3×6) + (4×8) = 18 + 32 = 50

Step 2 — Magnitudes:
  |A| = √(3² + 4²) = √25  = 5
  |B| = √(6² + 8²) = √100 = 10

Step 3 — Result:
  50 / (5 × 10) = 50 / 50 = 1.0  ✅  PERFECT MATCH
```

Now compare "login" with something unrelated:

```
"login"          → vector A = [3,  4]
"database table" → vector C = [-8, 1]

  A · C = (3×-8) + (4×1) = -24 + 4 = -20
  |C|   = √(64+1) = 8.06

  -20 / (5 × 8.06) = -0.49  ❌  Not related
```

#### Live Search Example

```
You ask: "how does login work?"
              ↓
         becomes vector: [0.20, -0.52, 0.85, ...]
              ↓
FAISS scores all 13 chunks:

Chunk  File              Similarity    Include?
─────────────────────────────────────────────────
  0    auth.py           0.94          ✅ TOP 1
  4    routes.py         0.89          ✅ TOP 2
  1    auth.py           0.82          ✅ TOP 3
  5    routes.py         0.71          ✅ TOP 4
  7    models.py         0.61          ✅ TOP 5
  3    Dockerfile        0.08          ❌ skipped
  2    models.py         0.06          ❌ skipped
─────────────────────────────────────────────────
Top 5 chunks → sent to Gemini
```

---

### Step 7 — Gemini Answer

The top 5 chunks plus your question are sent to Gemini as a single prompt:

```
[PROMPT TO GEMINI]
──────────────────────────────────────────────────────────
You are a codebase assistant.
Answer ONLY from the context. Always mention filename.

Context:
  [chunk from auth.py  — generate_token function]
  [chunk from routes.py — /login endpoint]
  [chunk from auth.py  — verify_token function]
  [chunk from routes.py — login_required decorator]
  [chunk from models.py — User model]

Question: "how does login work?"
──────────────────────────────────────────────────────────

[GEMINI RESPONSE]
──────────────────────────────────────────────────────────
Login works in two parts (auth.py, routes.py):

1. POST /login in routes.py receives username/password,
   queries the User model, calls generate_token()

2. generate_token() in auth.py creates a JWT with
   user_id and 24hr expiry using HS256 algorithm

3. Future requests use @login_required decorator
   which calls verify_token() to validate the JWT

📁 Sources: auth.py, routes.py, models.py
──────────────────────────────────────────────────────────
```

---

## 🧠 Why Vector Database? (Not SQL / Keyword Search)

### Option 1 — Keyword Search (`grep`, SQL `LIKE`)

```
Query: "how does the app handle login?"

Keyword search looks for: l-o-g-i-n  (exact letters only)
Misses: "authenticate", "JWT verify", "session check"
```

Code meaning is spread across files with different naming styles.
Keyword search has zero understanding of *meaning*.

---

### Option 2 — Relational Database (SQL)

`SELECT * FROM files WHERE content LIKE '%login%'` — sounds reasonable, but:

| Issue | Why it fails |
|---|---|
| No semantic understanding | "authentication" ≠ "login" in SQL |
| Slow on large repos | Full table scan every query |
| No relevance ranking | All matches treated equally |
| Wrong data model | Code is unstructured, not tabular |

---

### Option 3 — Vector Database ✅ (What We Use)

Vectors are **mathematical representations of meaning**.

```
"user login"     → [0.21, -0.54, 0.87, ...]
"authentication" → [0.19, -0.51, 0.84, ...]  ← Very close!
"database query" → [-0.43, 0.12, -0.21, ...] ← Far away
```

Ask *"how does login work?"* and it finds code about **auth, JWT, sessions,
middleware** — even if the word "login" never appears in those files.

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

**FAISS** (Facebook AI Similarity Search) is the vector search engine we use.

### Why FAISS over others?

| Feature | FAISS | Pinecone | ChromaDB |
|---|---|---|---|
| Cost | **Free** | Paid API | Free |
| Setup | In-process | Cloud account | Local server |
| Speed | **Fastest** | Fast | Medium |
| Persistence | RAM (session) | Cloud | Disk |
| Best for | **Local / batch** | Production SaaS | Dev prototyping |

For a codebase Q&A tool that ingests per-session:
FAISS = no cloud account, no cost, maximum speed. Perfect fit.

### What FAISS stores in RAM

```
         dim_1   dim_2   dim_3  ... dim_384
chunk_0: [0.21,  -0.54,  0.87, ..., 0.33 ]  → auth.py
chunk_1: [0.19,  -0.51,  0.84, ..., 0.31 ]  → auth.py
chunk_2: [-0.43,  0.12, -0.21, ..., -0.55]  → models.py
chunk_3: [0.05,   0.78, -0.34, ..., 0.12 ]  → Dockerfile
  ...
chunk_N: [...]

Query:   [0.20,  -0.52,  0.85, ..., 0.32 ]  ← your question vector

FAISS scores every row against the query,
returns top-K highest scores instantly.
```

This is called **Approximate Nearest Neighbor (ANN)** search —
blazing fast even with millions of vectors.

---

## 💻 CPU & RAM Usage

### Embedding Model: `all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| Model size on disk | ~90 MB |
| RAM during inference | ~150–200 MB |
| Output dimensions | 384 per chunk |
| Speed (CPU) | ~500–2000 chunks/sec |
| GPU required? | ❌ No — pure CPU |

Downloaded once, cached forever at:
```
~/.cache/huggingface/hub/sentence-transformers_all-MiniLM-L6-v2/
```

### FAISS Index RAM — How to Calculate

```
RAM = num_chunks × 384 dimensions × 4 bytes (float32 per number)

Small repo  (500 chunks)   →   500 × 384 × 4  =   ~750 KB
Medium repo (5,000 chunks) →  5000 × 384 × 4  =   ~7.5 MB
Large repo  (50,000 chunks)→ 50000 × 384 × 4  =    ~75 MB
```

> Most repos comfortably fit under **50 MB RAM** for the vector index.

### Full Resource Timeline

```
Time     What's happening          RAM        CPU        Internet
──────────────────────────────────────────────────────────────────
0s       Python + libs load        150 MB     Low        —
10s      Embedding model loads     300 MB     Low        HuggingFace (once)
30s      Repo cloning              300 MB     Low        GitHub clone
45s      Chunking + Embedding      350 MB     HIGH 🔥    —
90s      FAISS index built         380 MB     Low        —
         (temp repo deleted)
─ ready ──────────────────────────────────────────────────────────
95s      Query embedding           380 MB     Medium     —
97s      FAISS search (RAM only)   380 MB     Low        —
98s      Gemini API call           380 MB     Low        Gemini API
100s     Answer returned ✅        380 MB     Low        —
```

### Minimum vs Recommended Specs

```
               MINIMUM          RECOMMENDED
               ───────          ───────────
RAM:           4 GB             8 GB
CPU:           2 cores          4+ cores
Disk:          200 MB free      500 MB free
Internet:      Required         Required
GPU:           ❌ Not needed    ❌ Not needed
```

---

## 📁 Supported File Types

### Code
`.py` `.js` `.ts` `.jsx` `.tsx` `.java` `.cpp` `.c` `.go` `.rs` `.rb` `.php` `.cs` `.swift` `.kt`

### Config & Infrastructure
`.yml` `.yaml` `.toml` `.ini` `.cfg` `.env` `.sh` `.bash` `.xml` `.json`

### DevOps / Docker (no extension)
`Dockerfile` `Makefile` `Procfile` `.gitignore` `.dockerignore` `nginx.conf`

### Documentation
`.md` `.txt` `.rst`

### Web & Database
`.html` `.css` `.scss` `.sql`

### Always Excluded
`node_modules/` `.git/` `venv/` `__pycache__/` `.next/` `coverage/` and `*.min.js`

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- Google Gemini API Key — free at [aistudio.google.com](https://aistudio.google.com)

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
```

---

## 🎮 Usage

```bash
python main.py
```

```
🤖 Codebase Explainer AI (ENV + FREE MODE)

✅ Gemini API key loaded from ENV
📥 Loading local embedding model...
✅ Local embeddings ready!

Enter GitHub repository URL: https://github.com/owner/repo

🔄 Cloning repository...
✅ Repository cloned
🔍 Filtering code files...
✅ Found 87 relevant files
📁 Root-level files: ['Dockerfile', 'docker-compose.yml', '.env.example']
📄 Chunking files...
✅ Created 1,243 chunks
🧠 Creating FAISS index...
✅ FAISS index ready with 1,243 vectors
⚙️  Q&A chain ready
✅ Repository ingestion complete

💬 Ask questions (type 'quit' to exit)

You: What does the Dockerfile do?
🤖 The Dockerfile sets up a Node.js 18 Alpine base image, copies package.json,
   runs npm install, copies source files, and exposes port 3000.
📁 Sources: Dockerfile, docker-compose.yml

You: quit
```

---

## 🗂 Project Structure

```
codebase-explainer/
├── main.py              # Entry point — run this
├── .env                 # API keys (never commit!)
├── .env.example         # Template for new devs
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## ⚠️ Limitations

| Limitation | Details |
|---|---|
| **No persistence** | FAISS index is in RAM — lost when program exits |
| **Private repos** | Need SSH key or token in the URL |
| **Very large repos** | 100k+ chunks may need 500 MB+ RAM |
| **Binary files** | Images, compiled bin